"""Saving Instagram posts: the Pi looks a post up and hands each picture or video to the phone.

The phone shares an Instagram link here, shows what the post holds, and asks for the
slides the owner picked, one at a time, saving each into its gallery. yt-dlp does the
reading. A signed-in session is optional: public posts work without one, and when
Instagram asks for a login the phone sends the session cookies here once.

The session file is the owner's Instagram login, so it is written owner-only, scoped to
instagram.com lines, and never logged.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import threading
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

from .library import MediaError

POST = re.compile(r"/(?:[A-Za-z0-9_.]+/)?(p|reel|reels|tv)/([A-Za-z0-9_-]{5,40})/?$")
SIGN_IN = re.compile(r"login|log in|cookies|rate.?limit|not available|private", re.I)
CACHE_HOURS = 6


def post_code(url: str) -> tuple[str, str]:
    """The post's short code and a clean link to it, or URL_INVALID."""
    if not isinstance(url, str) or len(url) > 2048:
        raise MediaError("URL_INVALID", "Share a link to an Instagram post or reel")
    match = re.search(r"https?://\S+", url.strip())
    try:
        parsed = urlsplit(match.group(0) if match else url.strip())
        host = (parsed.hostname or "").lower()
        if parsed.scheme not in ("https", "http") or host not in ("instagram.com", "www.instagram.com", "m.instagram.com"):
            raise ValueError()
        found = POST.search(parsed.path)
        if not found:
            raise ValueError()
    except ValueError:
        raise MediaError("URL_INVALID", "Share a link to an Instagram post or reel")
    kind = "reel" if found.group(1) in ("reel", "reels") else found.group(1)
    return found.group(2), f"https://www.instagram.com/{kind}/{found.group(2)}/"


class Instagram:
    """Looks up and fetches Instagram posts with yt-dlp, keeping recent ones briefly."""

    def __init__(self, state_dir: Path, runner=None, downloader=None):
        self.cookies = state_dir / "instagram-session.txt"
        self.cache = state_dir / "instagram-cache"
        self.run = runner or self._run
        self.download = downloader or self._download
        self.posts: dict[str, tuple[float, dict]] = {}
        self.lock = threading.Lock()

    # The session

    def session_status(self) -> dict:
        return {"signedIn": self.cookies.is_file()}

    def session_set(self, text: str) -> dict:
        """Keep the owner's Instagram cookies, only the instagram.com lines."""
        if not isinstance(text, str) or len(text) > 64 * 1024:
            raise MediaError("SESSION_INVALID", "Sign in to Instagram again")
        lines = [line for line in text.splitlines()
                 if line.startswith("#") or line.split("\t", 1)[0].lstrip(".").endswith("instagram.com")]
        if not any(not line.startswith("#") and "sessionid" in line for line in lines):
            raise MediaError("SESSION_INVALID", "That sign-in did not finish. Sign in to Instagram again")
        self.cookies.parent.mkdir(parents=True, exist_ok=True)
        temp = self.cookies.with_suffix(".tmp")
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as out:
            out.write("# Netscape HTTP Cookie File\n" + "\n".join(l for l in lines if not l.startswith("#")) + "\n")
        os.replace(temp, self.cookies)
        with self.lock:
            self.posts.clear()
        return self.session_status()

    def session_clear(self) -> dict:
        try:
            self.cookies.unlink()
        except FileNotFoundError:
            pass
        return self.session_status()

    # Looking a post up

    def inspect(self, url: str) -> dict:
        """What the post holds: its slides in order, each a picture or a video, with a preview."""
        code, link = post_code(url)
        info = self._info(code, link)
        entries = info.get("entries") if info.get("_type") == "playlist" else [info]
        items = []
        for index, entry in enumerate(entries or [], start=1):
            if not isinstance(entry, dict):
                continue
            items.append({"index": index, "kind": self._kind(entry),
                          "thumbnail": self._best_image(entry) or ""})
        if not items:
            raise MediaError("POST_EMPTY", "That post has nothing that can be saved", 404)
        caption = (info.get("description") or (entries[0] or {}).get("description") or "").strip()
        uploader = info.get("uploader") or info.get("channel") or (entries[0] or {}).get("uploader") or ""
        return {"code": code, "url": link, "uploader": uploader, "caption": caption[:280],
                "items": items}

    def fetch(self, url: str, index: int) -> tuple[dict, int]:
        """One slide as a file ready to send: its name, type, and an open descriptor."""
        code, link = post_code(url)
        info = self._info(code, link)
        entries = info.get("entries") if info.get("_type") == "playlist" else [info]
        if not isinstance(index, int) or not 1 <= index <= len(entries or []):
            raise MediaError("ITEM_MISSING", "That part of the post is no longer there", 404)
        entry = entries[index - 1]
        folder = self.cache / code
        folder.mkdir(parents=True, exist_ok=True)
        self._prune()
        stem = f"{code}-{index}"
        existing = [p for p in folder.glob(stem + ".*") if not p.name.endswith((".part", ".tmp"))]
        if existing:
            path = existing[0]
        elif self._kind(entry) == "video":
            path = self._fetch_video(link, index, len(entries) > 1 or info.get("_type") == "playlist", folder, stem)
        else:
            image = self._best_image(entry)
            if not image:
                raise MediaError("ITEM_MISSING", "That picture could not be found", 404)
            path = folder / (stem + ".jpg")
            self.download(image, path)
        fd = os.open(path, os.O_RDONLY)
        mime = "video/mp4" if path.suffix == ".mp4" else "image/jpeg" if path.suffix in (".jpg", ".jpeg") \
            else "image/webp" if path.suffix == ".webp" else "application/octet-stream"
        return {"name": path.name, "mime": mime}, fd

    # Inside

    def _info(self, code: str, link: str) -> dict:
        with self.lock:
            kept = self.posts.get(code)
            if kept and time.time() - kept[0] < CACHE_HOURS * 3600:
                return kept[1]
        args = ["-J", "--ignore-no-formats-error", "--yes-playlist"]
        out = self._ytdlp(args + [link])
        try:
            info = json.loads(out)
        except ValueError:
            raise MediaError("POST_UNREADABLE", "Instagram did not describe that post", 502)
        with self.lock:
            self.posts[code] = (time.time(), info)
        return info

    def _fetch_video(self, link: str, index: int, many: bool, folder: Path, stem: str) -> Path:
        args = ["--no-part", "--no-mtime", "-f", "bv*+ba/b", "--merge-output-format", "mp4",
                "-o", str(folder / (stem + ".%(ext)s"))]
        if many:
            args += ["--yes-playlist", "--playlist-items", str(index)]
        self._ytdlp(args + [link], timeout=600)
        found = [p for p in folder.glob(stem + ".*") if p.suffix in (".mp4", ".mkv", ".webm")]
        if not found:
            raise MediaError("ITEM_MISSING", "That video could not be fetched", 502)
        return found[0]

    def _ytdlp(self, args: list[str], timeout: int = 90) -> str:
        if self.cookies.is_file():
            args = ["--cookies", str(self.cookies)] + args
        code, out, err = self.run(args, timeout)
        if code != 0:
            if SIGN_IN.search(err or ""):
                raise MediaError("INSTAGRAM_SIGN_IN", "Instagram wants you to sign in first", 403)
            raise MediaError("POST_UNREADABLE", "Instagram did not give that post up", 502)
        return out

    @staticmethod
    def _kind(entry: dict) -> str:
        formats = entry.get("formats") or []
        if any((f.get("vcodec") or "none") != "none" or f.get("ext") == "mp4" for f in formats):
            return "video"
        return "image"

    @staticmethod
    def _best_image(entry: dict) -> str | None:
        thumbs = [t for t in entry.get("thumbnails") or [] if t.get("url")]
        if thumbs:
            best = max(thumbs, key=lambda t: ((t.get("width") or 0) * (t.get("height") or 0), t.get("preference") or 0))
            return best["url"]
        return entry.get("thumbnail")

    def _prune(self):
        cutoff = time.time() - CACHE_HOURS * 3600
        for folder in self.cache.glob("*"):
            try:
                if folder.is_dir() and folder.stat().st_mtime < cutoff:
                    shutil.rmtree(folder, ignore_errors=True)
            except OSError:
                pass

    @staticmethod
    def _run(args: list[str], timeout: int) -> tuple[int, str, str]:
        binary = Path.home() / ".local/bin/yt-dlp"
        command = [str(binary) if binary.is_file() else "yt-dlp", "--quiet", "--no-warnings"] + args
        try:
            done = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise MediaError("POST_SLOW", "Instagram took too long to answer", 504)
        except FileNotFoundError:
            raise MediaError("DOWNLOADER_MISSING", "The Pi has no downloader for Instagram", 503)
        return done.returncode, done.stdout, done.stderr

    @staticmethod
    def _download(url: str, path: Path):
        temp = path.with_suffix(".tmp")
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(request, timeout=60) as answer, temp.open("wb") as out:
                shutil.copyfileobj(answer, out)
        except OSError:
            temp.unlink(missing_ok=True)
            raise MediaError("ITEM_MISSING", "That picture could not be fetched", 502)
        os.replace(temp, path)
