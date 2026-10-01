"""Read-only removable-drive library with stable, checked file references."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import mimetypes
import os
import re
import secrets
import stat
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


MEDIA_SUFFIXES = frozenset({
    ".mp4", ".m4v", ".mkv", ".mov", ".avi", ".wmv", ".webm", ".ts", ".m2ts", ".mpg", ".mpeg",
    ".mp3", ".m4a", ".aac", ".flac", ".wav", ".ogg", ".opus", ".wma",
})
VIDEO_SUFFIXES = frozenset({".mp4", ".m4v", ".mkv", ".mov", ".avi", ".wmv", ".webm", ".ts", ".m2ts", ".mpg", ".mpeg"})
# Still pictures mpv can decode with the Pi's stock ffmpeg. HEIC is left out
# because Debian's ffmpeg cannot read it.
IMAGE_SUFFIXES = frozenset({".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"})
SLIDESHOW_LIMIT = 1000


def _media_file(path: Path) -> bool:
    return not path.name.startswith(".") and path.suffix.casefold() in MEDIA_SUFFIXES


class MediaError(Exception):
    """A failure the phone can show as a sentence, with a stable code to branch on.

    `field` names the request field at fault when one input was out of range.
    """

    def __init__(self, code: str, message: str, status: int = 400, field: str | None = None):
        super().__init__(message)
        self.code = code
        self.status = status
        self.field = field


@dataclass(frozen=True)
class Drive:
    id: str
    label: str
    root: Path
    uuid: str


def _version(st: os.stat_result) -> str:
    material = f"{st.st_dev}:{st.st_ino}:{st.st_size}:{st.st_mtime_ns}"
    return hashlib.sha256(material.encode()).hexdigest()[:24]


class Library:
    def __init__(self, drives: list[Drive], token: str, *, fixture_mounts: bool = False):
        self.drives = {drive.id: drive for drive in drives}
        self.secret = hashlib.sha256(token.encode()).digest()
        self.fixture_mounts = fixture_mounts
        self.upload_lock = threading.Lock()

    def import_media(self, drive_id: str, name: str, length: int, source) -> dict:
        if not isinstance(length, int) or length < 1 or length > 16 * 1024**3:
            raise MediaError("UPLOAD_SIZE", "Choose a media file under 16 GB", 400)
        if not isinstance(name, str) or not name or len(name) > 240:
            raise MediaError("UPLOAD_NAME", "Choose a named media file", 400)
        clean = re.sub(r"[/\\\x00-\x1f\x7f]", "_", name).strip(" .")
        if not clean or Path(clean).suffix.casefold() not in MEDIA_SUFFIXES:
            raise MediaError("UPLOAD_TYPE", "Choose a video or audio file", 400)
        if not self.upload_lock.acquire(blocking=False):
            raise MediaError("UPLOAD_BUSY", "Another media file is being sent to the Pi", 409)
        candidate = None
        try:
            drive = self._drive(drive_id) if drive_id else self.cache_drive()
            if drive.uuid.startswith("LABEL:"):
                raise MediaError("UPLOAD_UNAVAILABLE", "This drive needs a confirmed identity before uploads", 409)
            incoming = self.cache_folder(drive)
            try:
                space = os.statvfs(incoming)
            except OSError:
                raise MediaError("UPLOAD_UNAVAILABLE", "The Pi cache folder is unavailable", 503)
            reserve = 0 if self.fixture_mounts else 1024**3
            if space.f_bavail * space.f_frsize < length + reserve:
                raise MediaError("DRIVE_FULL", "The Pi drive needs more free space for this file", 507)
            suffix = secrets.token_hex(8)
            candidate = incoming / f".incoming-{suffix}.upload"
            # A copy with the same name replaces the last one: the cache never asks.
            final = incoming / clean
            flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
            try:
                fd = os.open(candidate, flags, 0o600)
                with os.fdopen(fd, "wb") as output:
                    remaining = length
                    while remaining:
                        chunk = source.read(min(65536, remaining))
                        if not chunk:
                            raise MediaError("UPLOAD_INCOMPLETE", "The phone stopped sending the media file", 409)
                        output.write(chunk)
                        remaining -= len(chunk)
                    output.flush()
                    os.fsync(output.fileno())
                if not self.mounted(drive):
                    raise MediaError("DRIVE_ABSENT", f"Reconnect {drive.label} and try again", 409)
                os.replace(candidate, final)
                candidate = None
                return self.describe(drive, final)
            except (OSError, TimeoutError):
                raise MediaError("UPLOAD_FAILED", "The Pi could not save this media file", 503)
        finally:
            if candidate is not None:
                try:
                    candidate.unlink(missing_ok=True)
                except OSError:
                    pass
            self.upload_lock.release()

    def cache_drive(self) -> Drive:
        """The connected drive with the most free space, where a copy goes when none is named."""
        best, room = None, -1
        for drive in self.drives.values():
            if drive.uuid.startswith("LABEL:") or not self.mounted(drive):
                continue
            try:
                free = os.statvfs(drive.root).f_bavail * os.statvfs(drive.root).f_frsize
            except OSError:
                continue
            if free > room:
                best, room = drive, free
        if best is None:
            raise MediaError("DRIVE_ABSENT", "Connect a drive to the Pi and try again", 409)
        return best

    def cache_folder(self, drive: Drive) -> Path:
        """The drive's cache folder: temporary copies, kept until cleaned up.

        It is found by its name, shared/cache, and made again when missing, so a renamed one is
        just an ordinary folder. Media lists it like any other folder.
        """
        parent = self._path(drive, "shared") if (drive.root / "shared").is_dir() else None
        if parent is None:
            raise MediaError("UPLOAD_UNAVAILABLE", "The Pi shared folder is unavailable", 409)
        folder = parent / "cache"
        try:
            folder.mkdir(mode=0o755, exist_ok=True)
            if folder.is_symlink() or not folder.is_dir() or folder.stat().st_dev != drive.root.stat().st_dev:
                raise MediaError("UPLOAD_UNAVAILABLE", "The Pi cache folder is not on the selected drive", 503)
        except OSError:
            raise MediaError("UPLOAD_UNAVAILABLE", "The Pi cache folder cannot be created", 503)
        return folder

    def clean_cache(self) -> dict:
        """Empty every connected drive's cache folder. Only ever run when asked; nothing evicts on its own."""
        removed, freed = 0, 0
        for drive in self.drives.values():
            if drive.uuid.startswith("LABEL:") or not self.mounted(drive) or not (drive.root / "shared" / "cache").is_dir():
                continue
            folder = self.cache_folder(drive)
            for entry in folder.iterdir():
                if entry.is_symlink() or not entry.is_file():
                    continue
                try:
                    size = entry.stat().st_size
                    entry.unlink()
                except OSError:
                    continue
                removed, freed = removed + 1, freed + size
        return {"removed": removed, "freedBytes": freed}

    def mounted(self, drive: Drive) -> bool:
        if not drive.root.is_dir() or drive.root.is_symlink():
            return False
        if self.fixture_mounts:
            return True
        by_label = drive.uuid.startswith("LABEL:")
        device = Path("/dev/disk/by-label" if by_label else "/dev/disk/by-uuid") / (
            drive.uuid.partition(":")[2] if by_label else drive.uuid)
        if by_label and not device.exists():
            return False
        if device.exists() and not self._is_real_mount(drive):
            # The drives are systemd automounts: nothing is mounted until the folder
            # is first read. Asking "is it mounted" alone would never mount it, so a
            # drive that is plugged in is read once here.
            try:
                subprocess.run(["python3", "-c", "import os,sys; next(os.scandir(sys.argv[1]),None)",
                                str(drive.root)],
                               capture_output=True, timeout=7, check=False)
            except subprocess.TimeoutExpired:
                return False
        return self._is_real_mount(drive)

    def _is_real_mount(self, drive: Drive) -> bool:
        """True when the drive's own filesystem is mounted there, not just the automount placeholder."""
        if not os.path.ismount(drive.root):
            return False
        by_label = drive.uuid.startswith("LABEL:")
        result = subprocess.run(
            ["findmnt", "-n", "-o", "LABEL" if by_label else "UUID", "--target", str(drive.root)],
            capture_output=True, text=True, timeout=3, check=False,
        )
        expected = drive.uuid.partition(":")[2] if by_label else drive.uuid
        return result.returncode == 0 and expected in result.stdout.split()

    def drive_status(self) -> list[dict]:
        result = []
        for drive in self.drives.values():
            online = self.mounted(drive)
            free = None
            if online:
                try:
                    free = os.statvfs(drive.root).f_bavail * os.statvfs(drive.root).f_frsize
                except OSError:
                    online = False
            result.append({"id": drive.id, "label": drive.label, "online": online,
                           "freeBytes": free, "readOnly": True,
                           "code": None if online else "DRIVE_ABSENT"})
        return result

    def _drive(self, drive_id: str) -> Drive:
        drive = self.drives.get(drive_id)
        if drive is None:
            raise MediaError("DRIVE_UNKNOWN", "This drive is not configured", 404)
        if not self.mounted(drive):
            raise MediaError("DRIVE_ABSENT", f"Connect {drive.label} and try again", 409)
        return drive

    def _path(self, drive: Drive, relative: str) -> Path:
        if relative.startswith("/") or any(bit in ("", ".", "..") for bit in relative.split("/")):
            if relative != "":
                raise MediaError("PATH_INVALID", "Invalid media path")
        path = drive.root / relative
        # Resolving every component rejects symlinks that escape the volume.
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(drive.root.resolve(strict=True))
        except (OSError, ValueError):
            raise MediaError("ITEM_UNAVAILABLE", "This item is unavailable", 404)
        cursor = drive.root
        for part in path.relative_to(drive.root).parts:
            cursor = cursor / part
            if cursor.is_symlink():
                raise MediaError("PATH_INVALID", "Linked files are not available")
        if path.is_symlink():
            raise MediaError("PATH_INVALID", "Linked files are not available")
        return path

    def _encode(self, drive: Drive, relative: str, version: str) -> str:
        payload = json.dumps([drive.id, relative, version], separators=(",", ":")).encode()
        signature = hmac.new(self.secret, payload, hashlib.sha256).digest()[:16]
        return base64.urlsafe_b64encode(payload + signature).rstrip(b"=").decode()

    def decode(self, item_id: str, *, require_mount: bool = True) -> tuple[Drive, str, str]:
        try:
            raw = base64.urlsafe_b64decode(item_id + "=" * (-len(item_id) % 4))
            payload, signature = raw[:-16], raw[-16:]
            if not hmac.compare_digest(signature, hmac.new(self.secret, payload, hashlib.sha256).digest()[:16]):
                raise ValueError()
            drive_id, relative, version = json.loads(payload)
            if not all(isinstance(v, str) for v in (drive_id, relative, version)):
                raise ValueError()
            drive = self.drives.get(drive_id)
            if drive is None:
                raise MediaError("DRIVE_UNKNOWN", "This drive is not configured", 404)
            if require_mount and not self.mounted(drive):
                raise MediaError("DRIVE_ABSENT", f"Connect {drive.label} and try again", 409)
            return drive, relative, version
        except (ValueError, TypeError, IndexError):
            raise MediaError("ITEM_INVALID", "Invalid media item", 400)

    def describe(self, drive: Drive, path: Path) -> dict:
        relative = path.relative_to(drive.root).as_posix()
        if relative == ".":
            relative = ""
        st = path.stat()
        if not (stat.S_ISDIR(st.st_mode) or stat.S_ISREG(st.st_mode)):
            raise MediaError("ITEM_UNAVAILABLE", "Unsupported file type", 404)
        version = _version(st)
        return {"id": self._encode(drive, relative, version), "driveId": drive.id,
                "name": path.name if relative else drive.label, "relativePath": relative,
                "directory": stat.S_ISDIR(st.st_mode), "size": st.st_size if stat.S_ISREG(st.st_mode) else None,
                "modifiedNs": st.st_mtime_ns, "version": version,
                "mime": mimetypes.guess_type(path.name)[0] or "application/octet-stream"}

    def folder(self, drive_id: str, relative: str = "", offset: int = 0, limit: int = 100) -> dict:
        drive = self._drive(drive_id)
        folder = self._path(drive, relative)
        if not folder.is_dir():
            raise MediaError("NOT_A_FOLDER", "Select a folder", 400)
        if offset < 0 or limit < 1 or limit > 200:
            raise MediaError("PAGE_INVALID", "Invalid page")
        try:
            entries = [p for p in folder.iterdir() if not p.is_symlink() and
                       (p.is_dir() or (p.is_file() and _media_file(p)))]
            entries.sort(key=lambda p: (not p.is_dir(), p.name.casefold(), p.name))
            page = []
            for entry in entries[offset:offset + limit]:
                item = self.describe(drive, entry)
                if item["directory"]:
                    # How many things opening the folder would list; left out when it cannot be read.
                    try:
                        item["count"] = sum(1 for p in entry.iterdir() if not p.is_symlink() and
                                            (p.is_dir() or (p.is_file() and _media_file(p))))
                    except OSError:
                        pass
                page.append(item)
        except PermissionError:
            raise MediaError("MOUNT_UNREADABLE", "This folder cannot be read", 403)
        return {"items": page, "nextOffset": offset + limit if offset + limit < len(entries) else None,
                "total": len(entries)}

    def folder_images(self, drive_id: str, relative: str = "") -> tuple[str, list[Path]]:
        """The folder's name and the pictures directly inside it, in browser order.

        The folder resolves exactly as browsing resolves it, links and escapes included.
        """
        drive = self._drive(drive_id)
        folder = self._path(drive, relative)
        if not folder.is_dir():
            raise MediaError("NOT_A_FOLDER", "Select a folder", 400)
        try:
            images = [p for p in folder.iterdir() if not p.name.startswith(".") and
                      not p.is_symlink() and p.is_file() and p.suffix.casefold() in IMAGE_SUFFIXES]
        except PermissionError:
            raise MediaError("MOUNT_UNREADABLE", "This folder cannot be read", 403)
        images.sort(key=lambda p: (p.name.casefold(), p.name))
        return folder.name if relative else drive.label, images[:SLIDESHOW_LIMIT]

    def search(self, query: str, limit: int = 100) -> dict:
        query = query.strip().casefold()
        if not query or len(query) > 128 or limit < 1 or limit > 200:
            raise MediaError("SEARCH_INVALID", "Enter a shorter search term")
        matches = []
        scanned = 0
        for drive in self.drives.values():
            if not self.mounted(drive):
                continue
            for root, dirs, files in os.walk(drive.root, followlinks=False):
                dirs[:] = [d for d in dirs if not d.startswith(".") and
                           not (Path(root) / d).is_symlink()]
                for name in dirs + [f for f in files if _media_file(Path(f))]:
                    scanned += 1
                    if scanned > 50000:
                        return {"items": matches, "truncated": True}
                    path = Path(root) / name
                    if query in name.casefold() and not path.is_symlink():
                        try:
                            matches.append(self.describe(drive, path))
                        except (OSError, MediaError):
                            continue
                        if len(matches) >= limit:
                            return {"items": matches, "truncated": True}
        return {"items": matches, "truncated": False}

    def videos(self, offset: int = 0, limit: int = 100) -> dict:
        if offset < 0 or limit < 1 or limit > 200:
            raise MediaError("PAGE_INVALID", "Invalid page")
        found = []
        scanned = 0
        for drive in self.drives.values():
            if not self.mounted(drive):
                continue
            for root, dirs, files in os.walk(drive.root, followlinks=False):
                dirs[:] = [name for name in dirs if not name.startswith(".") and
                           not (Path(root) / name).is_symlink()]
                for name in files:
                    scanned += 1
                    if scanned > 50000:
                        raise MediaError("SCAN_LIMIT", "Too many files to list; browse a folder or search", 503)
                    path = Path(root) / name
                    if path.suffix.casefold() in VIDEO_SUFFIXES and _media_file(path) and not path.is_symlink():
                        try:
                            found.append(self.describe(drive, path))
                        except (OSError, MediaError):
                            continue
        found.sort(key=lambda item: (item["name"].casefold(), item["relativePath"].casefold()))
        return {"items": found[offset:offset + limit],
                "nextOffset": offset + limit if offset + limit < len(found) else None,
                "total": len(found)}

    def open_item(self, item_id: str) -> tuple[dict, int]:
        drive, relative, expected = self.decode(item_id)
        path = self._path(drive, relative)
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(path, flags)
            st = os.fstat(fd)
            if not stat.S_ISREG(st.st_mode) or not _media_file(path) or _version(st) != expected or not self.mounted(drive):
                os.close(fd)
                raise MediaError("ITEM_CHANGED", "This file changed; select it again", 409)
            return self.describe(drive, path), fd
        except OSError:
            raise MediaError("ITEM_UNAVAILABLE", "This file is unavailable", 404)
