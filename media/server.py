"""Token-gated media browser, byte streaming, progress, and playback control."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import queue
import re
import secrets
import shutil
import socket
import sqlite3
import stat
import subprocess
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit

from .camera import Camera
from .library import Drive, Library, MediaError

NOTE_FILE_LIMIT = 20 * 1024 * 1024


class State:
    PLAY_START_TIMEOUT = 5

    @staticmethod
    def youtube_item(url: str) -> str:
        if not isinstance(url, str) or len(url) > 2048:
            raise MediaError("URL_INVALID", "Share a single YouTube video URL")
        try:
            parsed = urlsplit(url.strip())
            if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port not in (None, 443):
                raise ValueError("invalid URL")
            host = (parsed.hostname or "").lower()
            if host in ("youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"):
                if parsed.path == "/watch":
                    video_id = parse_qs(parsed.query).get("v", [""])[0]
                else:
                    parts = parsed.path.strip("/").split("/")
                    video_id = parts[1] if len(parts) == 2 and parts[0] in ("shorts", "live") else ""
            elif host == "youtu.be":
                video_id = parsed.path.strip("/")
            else:
                raise ValueError("unsupported host")
            if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
                raise ValueError("invalid video ID")
        except ValueError:
            raise MediaError("URL_INVALID", "Share a single YouTube video URL")
        return "youtube:" + video_id

    def cast_youtube(self, url: str) -> dict:
        item_id = self.youtube_item(url)
        with self.lock:
            revision = self.pi["revision"]
        return self.command_pi({"action": "play", "itemId": item_id,
                                "expectedRevision": revision})

    def __init__(self, library: Library, database: Path, mpv_socket: Path | None = None,
                 player_command: list[str] | None = None, camera: Camera | None = None):
        self.library = library
        self.database = database
        self.mpv_socket = mpv_socket
        self.player_command = player_command
        self.camera = camera
        self.wallpaper = database.parent / "wallpaper.jpg"
        self.note_files_root = database.parent / "note-files"
        self.player_process = None
        self.lock = threading.RLock()
        self.play_lock = threading.Lock()
        self.phone: dict = {}
        self.commands: dict[str, dict] = {}
        self.pi = {"target": "pi", "state": "idle", "itemId": None, "positionMs": 0,
                   "durationMs": None, "volume": 20, "speed": 1.0,
                   "rotation": 0, "loop": False, "revision": 0}
        self.pi_session = ""
        self.pi_generation = 0
        self.pi_sequence = 0
        database.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS progress (
                item_id TEXT NOT NULL, target TEXT NOT NULL, session_id TEXT NOT NULL,
                generation INTEGER NOT NULL, sequence INTEGER NOT NULL, position_ms INTEGER NOT NULL,
                completed INTEGER NOT NULL, updated_at INTEGER NOT NULL,
                PRIMARY KEY(item_id, target))""")
            db.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value INTEGER NOT NULL)")
            columns = {row[1] for row in db.execute("PRAGMA table_info(progress)")}
            if "name" not in columns:
                db.execute("ALTER TABLE progress ADD COLUMN name TEXT")
            if "drive_label" not in columns:
                db.execute("ALTER TABLE progress ADD COLUMN drive_label TEXT")
            db.execute("""CREATE TABLE IF NOT EXISTS notes (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL,
                revision INTEGER NOT NULL, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS note_images (
                id TEXT PRIMARY KEY, note_id TEXT NOT NULL, data BLOB NOT NULL,
                created_at INTEGER NOT NULL)""")
            db.execute("CREATE INDEX IF NOT EXISTS note_images_note ON note_images(note_id, created_at)")
            db.execute("""CREATE TABLE IF NOT EXISTS pins (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, url TEXT NOT NULL,
                description TEXT NOT NULL, revision INTEGER NOT NULL,
                created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL)""")
            pin_columns = {row[1] for row in db.execute("PRAGMA table_info(pins)")}
            if "content" not in pin_columns:
                db.execute("ALTER TABLE pins ADD COLUMN content TEXT NOT NULL DEFAULT ''")
            if "tags" not in pin_columns:
                db.execute("ALTER TABLE pins ADD COLUMN tags TEXT NOT NULL DEFAULT '[]'")
            # A note's other files live on disk, one folder per note, named by
            # their id; the name the phone sent is kept only as a label.
            db.execute("""CREATE TABLE IF NOT EXISTS note_files (
                id TEXT PRIMARY KEY, note_id TEXT NOT NULL, name TEXT NOT NULL,
                mime TEXT NOT NULL, size INTEGER NOT NULL, created_at INTEGER NOT NULL)""")
            db.execute("CREATE INDEX IF NOT EXISTS note_files_note ON note_files(note_id, created_at)")

    def _db(self):
        return sqlite3.connect(self.database, timeout=5)

    @staticmethod
    def _note_fields(body: dict) -> tuple[str, str]:
        title, content = body.get("title"), body.get("body")
        if not isinstance(title, str) or not isinstance(content, str) or not title.strip() or \
                len(title) > 200 or len(content.encode("utf-8")) > 256 * 1024:
            raise MediaError("NOTE_INVALID", "Add a title and up to 256 KB of Markdown")
        return title.strip(), content

    @staticmethod
    def _note_revision(body: dict) -> int:
        value = body.get("expectedRevision")
        if type(value) is not int or value < 1:
            raise MediaError("NOTE_INVALID", "Send the note revision before changing it")
        return value

    @staticmethod
    def _note_row(row: tuple) -> dict:
        return {"id": row[0], "title": row[1], "body": row[2], "revision": row[3],
                "createdAt": row[4], "updatedAt": row[5]}

    def notes_list(self, query: str = "") -> list[dict]:
        if len(query) > 128:
            raise MediaError("NOTE_INVALID", "Search notes with up to 128 characters")
        with self._db() as db:
            if query:
                rows = db.execute(
                    "SELECT id,title,body,revision,created_at,updated_at FROM notes "
                    "WHERE instr(lower(title),lower(?))>0 OR instr(lower(body),lower(?))>0 "
                    "ORDER BY updated_at DESC,id LIMIT 500", (query, query)).fetchall()
            else:
                rows = db.execute("SELECT id,title,body,revision,created_at,updated_at FROM notes ORDER BY updated_at DESC,id LIMIT 500").fetchall()
        return [{key: value for key, value in self._note_row(row).items() if key != "body"}
                for row in rows]

    def note_get(self, note_id: str) -> dict:
        with self._db() as db:
            row = db.execute("SELECT id,title,body,revision,created_at,updated_at FROM notes WHERE id=?", (note_id,)).fetchone()
            if row is not None:
                files = db.execute("SELECT id,name,mime,size FROM note_files WHERE note_id=? "
                                   "ORDER BY created_at,id", (note_id,)).fetchall()
        if row is None:
            raise MediaError("NOTE_NOT_FOUND", "This note is no longer available", 404)
        return {**self._note_row(row),
                "files": [{"id": f[0], "name": f[1], "mime": f[2], "size": f[3]} for f in files]}

    def note_create(self, body: dict) -> dict:
        title, content = self._note_fields(body)
        note_id, now = str(uuid.uuid4()), int(time.time())
        with self._db() as db:
            db.execute("INSERT INTO notes VALUES(?,?,?,?,?,?)", (note_id, title, content, 1, now, now))
        return self.note_get(note_id)

    def note_update(self, note_id: str, body: dict) -> dict:
        title, content = self._note_fields(body)
        revision = self._note_revision(body)
        with self._db() as db:
            changed = db.execute("UPDATE notes SET title=?,body=?,revision=revision+1,updated_at=? WHERE id=? AND revision=?",
                                 (title, content, int(time.time()), note_id, revision)).rowcount
        if not changed:
            self.note_get(note_id)
            raise MediaError("NOTE_CONFLICT", "This note changed elsewhere. Reload it before saving", 409)
        return self.note_get(note_id)

    def note_delete(self, note_id: str, body: dict) -> dict:
        revision = self._note_revision(body)
        with self._db() as db:
            changed = db.execute("DELETE FROM notes WHERE id=? AND revision=?", (note_id, revision)).rowcount
            if changed:
                db.execute("DELETE FROM note_images WHERE note_id=?", (note_id,))
                db.execute("DELETE FROM note_files WHERE note_id=?", (note_id,))
        if not changed:
            self.note_get(note_id)
            raise MediaError("NOTE_CONFLICT", "This note changed elsewhere. Reload it before deleting", 409)
        folder = self._note_folder(note_id)
        if folder.is_symlink():
            folder.unlink()
        elif folder.exists():
            shutil.rmtree(folder, ignore_errors=True)
        return {"deleted": True, "id": note_id}

    def _note_folder(self, note_id: str) -> Path:
        """Where a note's files are kept. Only plain ids become folder names."""
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", note_id):
            raise MediaError("NOTE_NOT_FOUND", "This note is no longer available", 404)
        return self.note_files_root / note_id

    def note_files(self, note_id: str) -> list[dict]:
        return self.note_get(note_id)["files"]

    def note_file_add(self, note_id: str, name: str, content_type: str, length: int, source) -> dict:
        """Keep any file up to 20 MB with a note, streamed to disk and checked for length."""
        if not isinstance(length, int) or not 1 <= length <= NOTE_FILE_LIMIT:
            raise MediaError("FILE_INVALID", "Choose a file of up to 20 MB")
        clean = re.sub(r"[/\\\x00-\x1f\x7f]", "_", name or "").strip(" .")[:240]
        if not clean:
            raise MediaError("FILE_INVALID", "Send the file with its name")
        mime = content_type.split(";", 1)[0].strip().lower()
        if not re.fullmatch(r"[a-z0-9][a-z0-9!#$&^_.+-]{0,126}/[a-z0-9][a-z0-9!#$&^_.+-]{0,126}", mime) or \
                mime == "application/octet-stream":
            mime = mimetypes.guess_type(clean)[0] or "application/octet-stream"
        self.note_get(note_id)
        folder = self._note_folder(note_id)
        file_id, now = str(uuid.uuid4()), int(time.time())
        candidate, final = folder / f".{file_id}.upload", folder / file_id
        try:
            folder.mkdir(mode=0o700, parents=True, exist_ok=True)
            if folder.is_symlink() or not folder.is_dir():
                raise OSError("note folder is not a directory")
            flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
            with os.fdopen(os.open(candidate, flags, 0o600), "wb") as output:
                remaining = length
                while remaining:
                    chunk = source.read(min(65536, remaining))
                    if not chunk:
                        raise MediaError("UPLOAD_INCOMPLETE", "The phone stopped sending the file", 409)
                    output.write(chunk)
                    remaining -= len(chunk)
                output.flush()
                os.fsync(output.fileno())
            os.replace(candidate, final)
        except (OSError, TimeoutError):
            candidate.unlink(missing_ok=True)
            raise MediaError("FILE_FAILED", "The Pi could not save this file", 503)
        except MediaError:
            candidate.unlink(missing_ok=True)
            raise
        with self._db() as db:
            # The note may have been deleted while the file was arriving.
            added = db.execute("INSERT INTO note_files SELECT ?,?,?,?,?,? WHERE EXISTS "
                               "(SELECT 1 FROM notes WHERE id=?)",
                               (file_id, note_id, clean, mime, length, now, note_id)).rowcount
        if not added:
            final.unlink(missing_ok=True)
            raise MediaError("NOTE_NOT_FOUND", "This note is no longer available", 404)
        return {"id": file_id, "name": clean, "mime": mime, "size": length}

    def note_file_open(self, note_id: str, file_id: str) -> tuple[dict, int]:
        self.note_get(note_id)
        with self._db() as db:
            row = db.execute("SELECT id,name,mime,size FROM note_files WHERE note_id=? AND id=?",
                             (note_id, file_id)).fetchone()
        if row is None:
            raise MediaError("FILE_NOT_FOUND", "This file is no longer in the note", 404)
        try:
            fd = os.open(self._note_folder(note_id) / row[0], os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        except OSError:
            raise MediaError("FILE_NOT_FOUND", "This file is no longer on the Pi", 404)
        return {"id": row[0], "name": row[1], "mime": row[2], "size": row[3]}, fd

    def note_file_delete(self, note_id: str, file_id: str) -> dict:
        self.note_get(note_id)
        with self._db() as db:
            removed = db.execute("DELETE FROM note_files WHERE note_id=? AND id=?", (note_id, file_id)).rowcount
        if not removed:
            raise MediaError("FILE_NOT_FOUND", "This file is no longer in the note", 404)
        (self._note_folder(note_id) / file_id).unlink(missing_ok=True)
        return {"deleted": True, "id": file_id}

    @staticmethod
    def _pin_fields(body: dict) -> tuple[str, str, str, str, list[str]]:
        title = body.get("title", "")
        url = body.get("url", "")
        description = body.get("description", "")
        content = body.get("content", "")
        tags = body.get("tags", [])
        if not isinstance(title, str) or len(title) > 200 or \
                not isinstance(url, str) or len(url) > 2048 or \
                not isinstance(description, str) or len(description) > 4096 or \
                not isinstance(content, str) or len(content.encode("utf-8")) > 16 * 1024 or \
                not isinstance(tags, list) or len(tags) > 12 or \
                any(not isinstance(tag, str) or not tag.strip() or len(tag) > 32 for tag in tags):
            raise MediaError("PIN_INVALID", "Use a URL or text snippet with optional title, tags, and description")
        url = url.strip()
        content = content.strip()
        if not url and not content:
            raise MediaError("PIN_INVALID", "Add a URL or text snippet")
        if url:
            try:
                parsed = urlsplit(url)
                valid = parsed.scheme in ("http", "https") and parsed.hostname and \
                    not parsed.username and not parsed.password and not any(char.isspace() for char in url)
                if not valid or parsed.port == 0:
                    raise ValueError("invalid URL")
            except ValueError:
                raise MediaError("PIN_INVALID", "Use a full http or https URL")
        return title.strip(), url, description.strip(), content, [tag.strip() for tag in tags]

    @staticmethod
    def _pin_revision(body: dict) -> int:
        revision = body.get("expectedRevision")
        if type(revision) is not int or revision < 1:
            raise MediaError("PIN_INVALID", "Send the pin revision before changing it")
        return revision

    @staticmethod
    def _pin_row(row: tuple) -> dict:
        return {"id": row[0], "title": row[1], "url": row[2], "description": row[3],
                "revision": row[4], "createdAt": row[5], "updatedAt": row[6],
                "content": row[7], "tags": json.loads(row[8])}

    def pins_list(self) -> list[dict]:
        with self._db() as db:
            rows = db.execute("SELECT id,title,url,description,revision,created_at,updated_at,content,tags "
                              "FROM pins ORDER BY updated_at DESC,id LIMIT 500").fetchall()
        return [self._pin_row(row) for row in rows]

    def pin_get(self, pin_id: str) -> dict:
        with self._db() as db:
            row = db.execute("SELECT id,title,url,description,revision,created_at,updated_at,content,tags "
                             "FROM pins WHERE id=?", (pin_id,)).fetchone()
        if row is None:
            raise MediaError("PIN_NOT_FOUND", "This pin is no longer available", 404)
        return self._pin_row(row)

    def pin_create(self, body: dict) -> dict:
        title, url, description, content, tags = self._pin_fields(body)
        pin_id, now = str(uuid.uuid4()), int(time.time())
        with self._db() as db:
            db.execute("INSERT INTO pins(id,title,url,description,revision,created_at,updated_at,content,tags) "
                       "VALUES(?,?,?,?,?,?,?,?,?)",
                       (pin_id, title, url, description, 1, now, now, content, json.dumps(tags)))
        return self.pin_get(pin_id)

    def pin_update(self, pin_id: str, body: dict) -> dict:
        title, url, description, content, tags = self._pin_fields(body)
        revision = self._pin_revision(body)
        with self._db() as db:
            changed = db.execute("UPDATE pins SET title=?,url=?,description=?,content=?,tags=?,"
                                 "revision=revision+1,updated_at=? WHERE id=? AND revision=?",
                                 (title, url, description, content, json.dumps(tags), int(time.time()),
                                  pin_id, revision)).rowcount
        if not changed:
            self.pin_get(pin_id)
            raise MediaError("PIN_CONFLICT", "This pin changed elsewhere. Reload it before saving", 409)
        return self.pin_get(pin_id)

    def pin_delete(self, pin_id: str, body: dict) -> dict:
        revision = self._pin_revision(body)
        with self._db() as db:
            changed = db.execute("DELETE FROM pins WHERE id=? AND revision=?", (pin_id, revision)).rowcount
        if not changed:
            self.pin_get(pin_id)
            raise MediaError("PIN_CONFLICT", "This pin changed elsewhere. Reload it before deleting", 409)
        return {"deleted": True, "id": pin_id}

    def note_images(self, note_id: str) -> list[dict]:
        self.note_get(note_id)
        with self._db() as db:
            rows = db.execute("SELECT id,length(data),created_at FROM note_images WHERE note_id=? ORDER BY created_at,id",
                              (note_id,)).fetchall()
        return [{"id": row[0], "bytes": row[1], "createdAt": row[2]} for row in rows]

    def note_image_add(self, note_id: str, data: bytes) -> dict:
        if not 8 <= len(data) <= 1024 * 1024 or not data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise MediaError("IMAGE_INVALID", "Choose a PNG image under 1 MB")
        self.note_get(note_id)
        image_id, now = str(uuid.uuid4()), int(time.time())
        with self._db() as db:
            db.execute("INSERT INTO note_images VALUES(?,?,?,?)", (image_id, note_id, data, now))
        return {"id": image_id, "bytes": len(data), "createdAt": now}

    def note_image_get(self, note_id: str, image_id: str) -> bytes:
        self.note_get(note_id)
        with self._db() as db:
            row = db.execute("SELECT data FROM note_images WHERE note_id=? AND id=?", (note_id, image_id)).fetchone()
        if row is None:
            raise MediaError("IMAGE_NOT_FOUND", "This note image is unavailable", 404)
        return row[0]

    def history(self) -> list[dict]:
        with self._db() as db:
            rows = db.execute("SELECT item_id,target,session_id,generation,sequence,position_ms,completed,updated_at,name,drive_label FROM progress ORDER BY updated_at DESC LIMIT 200").fetchall()
        return [{"itemId": r[0], "target": r[1], "sessionId": r[2], "generation": r[3],
                 "sequence": r[4], "positionMs": r[5], "completed": bool(r[6]), "updatedAt": r[7],
                 "name": r[8], "driveLabel": r[9],
                 "mime": mimetypes.guess_type(r[8] or "")[0] or "application/octet-stream"}
                for r in rows]

    def save_progress(self, body: dict) -> dict:
        item_id = str(body.get("itemId", ""))
        target = str(body.get("target", ""))
        session_id = str(body.get("sessionId", ""))
        try:
            generation = int(body["generation"])
            sequence = int(body["sequence"])
            position = int(body["positionMs"])
        except (KeyError, TypeError, ValueError):
            raise MediaError("PROGRESS_INVALID", "Progress needs generation, sequence, and position")
        if target not in ("pi", "phone") or not item_id or not session_id or min(generation, sequence, position) < 0:
            raise MediaError("PROGRESS_INVALID", "Invalid progress")
        if re.fullmatch(r"youtube:[A-Za-z0-9_-]{11}", item_id):
            name = self.pi.get("name") or item_id
            drive_label = "YouTube"
        else:
            drive, relative, _ = self.library.decode(item_id, require_mount=False)
            name = Path(relative).name
            drive_label = drive.label
        if target == "phone":
            with self.lock:
                if self.phone and (self.phone.get("generation", 0) > generation or
                        (self.phone.get("generation") == generation and self.phone.get("id") != session_id)):
                    raise MediaError("SESSION_STALE", "This phone session is no longer active", 409)
                if (self.phone and self.phone.get("generation") == generation and
                        self.phone.get("itemId") != item_id):
                    raise MediaError("ITEM_MISMATCH", "Progress belongs to another phone item", 409)
        with self._db() as db:
            if target == "phone":
                known = db.execute("SELECT value FROM meta WHERE key='phone_generation'").fetchone()
                if not known or generation != known[0]:
                    raise MediaError("SESSION_STALE", "This phone session is no longer active", 409)
            old = db.execute("SELECT session_id,generation,sequence FROM progress WHERE item_id=? AND target=?", (item_id, target)).fetchone()
            if old and (generation < old[1] or (generation == old[1] and
                    (session_id != old[0] or sequence <= old[2]))):
                raise MediaError("PROGRESS_STALE", "A newer position is already saved", 409)
            db.execute("""INSERT INTO progress(item_id,target,session_id,generation,sequence,position_ms,completed,updated_at,name,drive_label)
                VALUES(?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(item_id,target) DO UPDATE SET session_id=excluded.session_id,
                generation=excluded.generation,sequence=excluded.sequence,position_ms=excluded.position_ms,
                completed=excluded.completed,updated_at=excluded.updated_at,name=excluded.name,
                drive_label=excluded.drive_label""",
                (item_id, target, session_id, generation, sequence, position,
                 int(bool(body.get("completed"))), int(time.time()),
                 name, drive_label))
        return {"saved": True, "positionMs": position}

    def _mpv(self, command: list) -> dict:
        if not self.mpv_socket or not self.mpv_socket.exists():
            raise MediaError("PLAYER_UNAVAILABLE", "Pi player is not running", 503)
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(3)
                client.connect(str(self.mpv_socket))
                client.sendall(json.dumps({"command": command, "request_id": 1}).encode() + b"\n")
                with client.makefile("rb") as replies:
                    while True:
                        line = replies.readline()
                        if not line:
                            raise OSError("mpv closed IPC")
                        reply = json.loads(line)
                        if reply.get("request_id") == 1:
                            if reply.get("error") != "success":
                                raise MediaError("PLAYER_REJECTED", str(reply.get("error")), 409)
                            return reply
        except (OSError, ValueError, TimeoutError):
            raise MediaError("PLAYER_UNAVAILABLE", "Pi player is not responding", 503)

    def _start_player(self):
        if not self.mpv_socket or not self.player_command:
            raise MediaError("PLAYER_UNAVAILABLE", "Pi player is not configured", 503)
        if self.mpv_socket.exists():
            try:
                self._mpv(["get_property", "mpv-version"])
                return
            except MediaError:
                self.mpv_socket.unlink(missing_ok=True)
        self.mpv_socket.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            self.player_process = subprocess.Popen(
                self.player_command + ["--idle=yes", "--keep-open=yes", "--no-terminal",
                                       f"--log-file={self.database.parent / 'mpv.log'}",
                                       f"--input-ipc-server={self.mpv_socket}"],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            for _ in range(30):
                if self.player_process.poll() is not None:
                    raise MediaError("PLAYER_UNAVAILABLE", "Pi player exited during startup", 503)
                if self.mpv_socket.exists():
                    return
                time.sleep(0.1)
        except OSError:
            raise MediaError("PLAYER_UNAVAILABLE", "Pi player could not start", 503)
        raise MediaError("PLAYER_UNAVAILABLE", "Pi player did not open its control socket", 503)

    def show_wallpaper(self) -> bool:
        if not self.wallpaper.is_file():
            return False
        self._start_player()
        self._mpv(["set_property", "video-rotate", 0])
        self._mpv(["set_property", "loop-file", "no"])
        self._mpv(["loadfile", str(self.wallpaper), "replace"])
        return True

    def set_wallpaper(self, image: bytes) -> dict:
        if len(image) < 100 or len(image) > 10 * 1024 * 1024 or not image.startswith(b"\xff\xd8\xff"):
            raise MediaError("IMAGE_INVALID", "Choose a JPEG image under 10 MB", 400)
        try:
            probe = subprocess.run([
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=codec_name,width,height", "-of", "json", "pipe:0",
            ], input=image, capture_output=True, timeout=8, check=True)
            stream = json.loads(probe.stdout)["streams"][0]
            if (stream.get("codec_name") != "mjpeg" or
                    not 100 <= stream.get("width", 0) <= 8192 or
                    not 100 <= stream.get("height", 0) <= 8192):
                raise ValueError("unsupported image")
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired,
                ValueError, IndexError, KeyError, TypeError):
            raise MediaError("IMAGE_INVALID", "Choose a valid JPEG image", 400)
        with self.lock:
            candidate = self.wallpaper.with_name(f"wallpaper-{secrets.token_hex(6)}.upload")
            candidate.write_bytes(image)
            os.replace(candidate, self.wallpaper)
            self.wallpaper.chmod(0o600)
            if self.pi.get("itemId"):
                try:
                    observed = self.pi_state()
                    self._save_pi_progress(observed, observed["state"] == "finished")
                except MediaError:
                    pass
            self.pi.update(itemId=None, state="idle", positionMs=0,
                           rotation=0, loop=False)
            self.pi.pop("error", None)
            self.pi.pop("sourcePath", None)
            self.pi["revision"] += 1
            try:
                displayed = self.show_wallpaper()
            except MediaError:
                displayed = False
        return {"stored": True, "sentToDisplay": displayed}

    def pi_state(self) -> dict:
        with self.lock:
            state = dict(self.pi)
            if state["itemId"] is None:
                return state
            if state["state"] == "loading":
                try:
                    if self._mpv(["get_property", "path"]).get("data") != state.get("sourcePath"):
                        return state
                except MediaError:
                    return state
            if not self.mpv_socket or not self.mpv_socket.exists():
                self.pi["state"] = "unavailable"
                self.pi["error"] = "Player control socket disappeared"
                return dict(self.pi)
            try:
                source_path = self.pi.get("sourcePath")
                if source_path and self._mpv(["get_property", "path"]).get("data") != source_path:
                    self.pi.update(itemId=None, state="unavailable", positionMs=0,
                                   rotation=0, loop=False,
                                   error="Pi player changed output outside this media session")
                    self.pi.pop("sourcePath", None)
                    self.pi_generation = time.time_ns()
                    self.pi["revision"] += 1
                    return dict(self.pi)
                idle = bool(self._mpv(["get_property", "idle-active"]).get("data"))
                if idle:
                    if self.pi["state"] == "loading":
                        return dict(self.pi)
                    self.pi["state"] = "unavailable"
                    self.pi["error"] = "Player became idle without an observed end of file"
                else:
                    for property_name, key in (("time-pos", "positionMs"), ("duration", "durationMs")):
                        try:
                            value = self._mpv(["get_property", property_name]).get("data")
                            if value is not None:
                                self.pi[key] = round(float(value) * 1000)
                        except (MediaError, TypeError, ValueError):
                            pass
                    paused = bool(self._mpv(["get_property", "pause"]).get("data"))
                    eof = bool(self._mpv(["get_property", "eof-reached"]).get("data"))
                    volume = self._mpv(["get_property", "volume"]).get("data")
                    if isinstance(volume, (int, float)):
                        self.pi["volume"] = round(volume)
                    self.pi["state"] = "finished" if eof else "paused" if paused else "playing"
                    if eof and self.pi.get("durationMs"):
                        self.pi["positionMs"] = self.pi["durationMs"]
                    self.pi["paused"] = paused
                    self.pi.pop("error", None)
            except MediaError:
                self.pi["state"] = "unavailable"
                self.pi["error"] = "Player did not answer"
            return dict(self.pi)

    def _save_pi_progress(self, state: dict, completed: bool = False):
        if not state.get("itemId"):
            return
        self.pi_sequence += 1
        self.save_progress({"itemId": state["itemId"], "target": "pi",
                            "sessionId": self.pi_session, "generation": self.pi_generation,
                            "sequence": self.pi_sequence, "positionMs": state.get("positionMs") or 0,
                            "completed": completed})

    def _track_pi(self, generation: int):
        while True:
            time.sleep(2)
            with self.lock:
                if generation != self.pi_generation or not self.pi["itemId"]:
                    return
                state = self.pi_state()
                try:
                    self._save_pi_progress(state, state["state"] == "finished")
                except MediaError:
                    pass
                if state["state"] == "finished":
                    try:
                        self.show_wallpaper()
                    except MediaError:
                        pass
                    self.pi.update(itemId=None, state="idle", positionMs=0,
                                   rotation=0, loop=False)
                    self.pi.pop("sourcePath", None)
                    self.pi["revision"] += 1
                    return

    def _play_pi(self, body: dict) -> dict:
        with self.play_lock:
            with self.lock:
                if body.get("expectedRevision") != self.pi["revision"]:
                    raise MediaError("STATE_CHANGED", "Refresh player state and retry", 409)
                item_id = str(body.get("itemId", ""))
                youtube = bool(re.fullmatch(r"youtube:[A-Za-z0-9_-]{11}", item_id))
                if youtube:
                    path = "ytdl://https://www.youtube.com/watch?v=" + item_id[8:]
                    name = "YouTube " + item_id[8:]
                else:
                    meta, fd = self.library.open_item(item_id)
                    os.close(fd)
                    drive, relative, _ = self.library.decode(item_id)
                    path = str(drive.root / relative)
                    name = meta["name"]
                self._start_player()
                self._mpv(["set_property", "volume", 0])
                self._mpv(["set_property", "pause", False])
                self._mpv(["set_property", "video-rotate", 0])
                self._mpv(["set_property", "loop-file", "no"])
                self.pi["volume"] = 0
                self.pi["rotation"] = 0
                self.pi["loop"] = False
                self._mpv(["loadfile", path, "replace"])
                self.pi.update(itemId=item_id, state="loading", positionMs=0,
                               durationMs=None, name=name, sourcePath=path)
                self.pi.pop("error", None)
                self.pi_session = secrets.token_urlsafe(12)
                self.pi_generation = time.time_ns()
                self.pi_sequence = 0
                self.pi["revision"] += 1
                generation = self.pi_generation
            deadline = time.monotonic() + (35 if youtube else self.PLAY_START_TIMEOUT)
            while True:
                with self.lock:
                    if generation != self.pi_generation or self.pi.get("itemId") != item_id:
                        raise MediaError("STATE_CHANGED", "Playback was stopped or replaced", 409)
                    try:
                        loaded_path = self._mpv(["get_property", "path"]).get("data")
                    except MediaError:
                        loaded_path = None
                    state = self.pi_state() if loaded_path == path else dict(self.pi)
                    if loaded_path == path and state["state"] in ("playing", "paused", "finished"):
                        if youtube:
                            try:
                                self.pi["name"] = self._mpv(["get_property", "media-title"]).get("data") or name
                            except MediaError:
                                pass
                        self._save_pi_progress(state, state["state"] == "finished")
                        threading.Thread(target=self._track_pi, args=(generation,), daemon=True).start()
                        return {"status": "applied", "player": self.pi_state()}
                    if time.monotonic() >= deadline:
                        try:
                            self._mpv(["stop"])
                        except MediaError:
                            if self.player_process and self.player_process.poll() is None:
                                self.player_process.terminate()
                                try:
                                    self.player_process.wait(timeout=2)
                                except subprocess.TimeoutExpired:
                                    self.player_process.kill()
                                    self.player_process.wait(timeout=2)
                        try:
                            self.show_wallpaper()
                        except MediaError:
                            pass
                        self.pi_generation = time.time_ns()
                        self.pi.update(itemId=None, state="unavailable", positionMs=0,
                                       rotation=0, loop=False,
                                       error="Player did not open the selected media")
                        self.pi.pop("sourcePath", None)
                        self.pi["revision"] += 1
                        raise MediaError("PLAYER_UNAVAILABLE", "Pi player did not start; check media diagnostics", 503)
                time.sleep(0.2)

    def command_pi(self, body: dict) -> dict:
        action = body.get("action")
        if action == "play":
            return self._play_pi(body)
        with self.lock:
            if body.get("expectedRevision") != self.pi["revision"]:
                raise MediaError("STATE_CHANGED", "Refresh player state and retry", 409)
            if action in ("pause", "resume"):
                self._mpv(["set_property", "pause", action == "pause"])
                self.pi["state"] = "paused" if action == "pause" else "playing"
            elif action == "stop":
                state = self.pi_state()
                if state["state"] != "loading":
                    self._save_pi_progress(state, state["state"] == "finished")
                self._mpv(["stop"])
                try:
                    self.show_wallpaper()
                except MediaError:
                    pass
                self.pi.update(itemId=None, state="idle", positionMs=0,
                               rotation=0, loop=False)
                self.pi.pop("error", None)
                self.pi.pop("sourcePath", None)
            elif action == "seek":
                position = body.get("positionMs")
                if not isinstance(position, (int, float)) or position < 0:
                    raise MediaError("COMMAND_INVALID", "Choose a valid seek position")
                self._mpv(["seek", position / 1000, "absolute"])
            elif action in ("volume", "speed"):
                value = body.get("value")
                if not isinstance(value, (int, float)) or not (0 <= value <= 100 if action == "volume" else 0.25 <= value <= 4):
                    raise MediaError("COMMAND_INVALID", "Choose a valid setting")
                self._mpv(["set_property", action, value])
                self.pi[action] = value
            elif action == "rotate":
                value = body.get("value")
                if type(value) is not int or value not in (0, 90, 180, 270):
                    raise MediaError("COMMAND_INVALID", "Choose 0, 90, 180, or 270 degrees")
                self._mpv(["set_property", "video-rotate", value])
                self.pi["rotation"] = value
            elif action == "loop":
                value = body.get("value")
                if type(value) is not bool:
                    raise MediaError("COMMAND_INVALID", "Choose whether to loop the file")
                self._mpv(["set_property", "loop-file", "inf" if value else "no"])
                self.pi["loop"] = value
            else:
                raise MediaError("COMMAND_INVALID", "Unsupported player command")
            self.pi["revision"] += 1
            return {"status": "applied", "player": self.pi_state()}

    def immediate_pi(self, body: dict) -> dict:
        action = body.get("action")
        if action not in ("pause", "mute", "stop", "volume"):
            raise MediaError("COMMAND_INVALID", "Choose pause, mute, stop, or volume")
        with self.lock:
            if action == "stop":
                if self.pi.get("itemId"):
                    try:
                        state = self.pi_state()
                        if state["state"] != "loading":
                            self._save_pi_progress(state, state["state"] == "finished")
                    except MediaError:
                        pass
                self._mpv(["stop"])
                try:
                    self.show_wallpaper()
                except MediaError:
                    pass
                self.pi.update(itemId=None, state="idle", positionMs=0,
                               rotation=0, loop=False)
                self.pi.pop("error", None)
                self.pi.pop("sourcePath", None)
            elif action == "pause":
                self._mpv(["set_property", "pause", True])
                self.pi["state"] = "paused"
            else:
                value = 0 if action == "mute" else body.get("value")
                if not isinstance(value, (int, float)) or not 0 <= value <= 100:
                    raise MediaError("COMMAND_INVALID", "Choose a volume from 0 to 100")
                self._mpv(["set_property", "volume", value])
                self.pi["volume"] = value
            self.pi["revision"] += 1
            return {"status": "applied", "player": self.pi_state()}

    def register_phone(self, body: dict) -> dict:
        item_id = str(body.get("itemId", ""))
        _, fd = self.library.open_item(item_id)
        os.close(fd)
        with self.lock:
            with self._db() as db:
                db.execute("INSERT OR IGNORE INTO meta VALUES('phone_generation',0)")
                db.execute("UPDATE meta SET value=value+1 WHERE key='phone_generation'")
                generation = db.execute("SELECT value FROM meta WHERE key='phone_generation'").fetchone()[0]
            self.phone = {"id": secrets.token_urlsafe(16), "generation": generation,
                          "itemId": item_id, "state": "loading", "positionMs": 0,
                          "durationMs": None,
                          "volume": 100, "speed": 1.0, "revision": 0,
                          "telemetrySequence": 0, "leaseUntil": time.time() + 30}
            return dict(self.phone)

    def phone_state(self) -> dict:
        with self.lock:
            if not self.phone or self.phone["leaseUntil"] < time.time():
                return {"target": "phone", "state": "offline", "observedAt": self.phone.get("observedAt")}
            return dict(self.phone)

    def phone_heartbeat(self, body: dict) -> dict:
        with self.lock:
            if (body.get("sessionId") != self.phone.get("id") or
                    body.get("generation") != self.phone.get("generation")):
                raise MediaError("SESSION_STALE", "This phone session is no longer active", 409)
            sequence = body.get("sequence")
            if not isinstance(sequence, int) or sequence <= self.phone["telemetrySequence"]:
                raise MediaError("TELEMETRY_STALE", "A newer phone state was received", 409)
            position = body.get("positionMs", 0)
            if not isinstance(position, int) or position < 0:
                raise MediaError("TELEMETRY_INVALID", "Invalid phone position")
            self.phone.update(telemetrySequence=sequence, state=str(body.get("state", "unknown")),
                              positionMs=position,
                              leaseUntil=time.time() + 30, observedAt=int(time.time()))
            duration = body.get("durationMs")
            if isinstance(duration, int) and duration >= 0:
                self.phone["durationMs"] = duration
            for key, low, high in (("volume", 0, 100), ("speed", 0.25, 4)):
                value = body.get(key)
                if isinstance(value, (int, float)) and not isinstance(value, bool) and low <= value <= high:
                    self.phone[key] = value
            return {"accepted": True}

    def command_phone(self, body: dict) -> dict:
        action = body.get("action")
        if action not in ("pause", "resume", "stop", "seek", "volume", "speed"):
            raise MediaError("COMMAND_INVALID", "Unsupported phone command")
        value = body.get("positionMs") if action == "seek" else body.get("value")
        if action in ("seek", "volume", "speed") and (
                not isinstance(value, (int, float)) or isinstance(value, bool) or
                not (0 <= value if action == "seek" else
                     0 <= value <= 100 if action == "volume" else 0.25 <= value <= 4)):
            raise MediaError("COMMAND_INVALID", "Choose a valid playback setting")
        with self.lock:
            command_id = str(body.get("commandId", ""))
            if not command_id:
                raise MediaError("COMMAND_INVALID", "Command ID is required")
            if not self.phone or self.phone["leaseUntil"] < time.time():
                raise MediaError("PHONE_OFFLINE", "Open the player on the phone", 409)
            if (body.get("expectedSessionId") != self.phone["id"] or
                    body.get("expectedGeneration") != self.phone["generation"]):
                raise MediaError("SESSION_STALE", "Phone playback changed; refresh and retry", 409)
            if command_id in self.commands:
                command = self.commands[command_id]
                if command["sessionId"] != self.phone["id"] or command["generation"] != self.phone["generation"]:
                    raise MediaError("SESSION_STALE", "Command belongs to an older playback", 409)
                return dict(command)
            if body.get("expectedRevision") != self.phone["revision"]:
                raise MediaError("STATE_CHANGED", "Refresh phone state and retry", 409)
            result = {"commandId": command_id, "sessionId": self.phone["id"],
                      "generation": self.phone["generation"], "action": action,
                      "value": value,
                      "status": "queued", "expiresAt": time.time() + 10}
            self.commands[command_id] = result
            return dict(result)

    def pending_phone(self, session_id: str, generation: int) -> list[dict]:
        with self.lock:
            if self.phone.get("id") != session_id or self.phone.get("generation") != generation:
                raise MediaError("SESSION_STALE", "This phone session is no longer active", 409)
            now = time.time()
            for command in self.commands.values():
                if command["status"] == "queued" and command["expiresAt"] < now:
                    command["status"] = "expired"
            return [dict(c) for c in self.commands.values()
                    if c["sessionId"] == session_id and c["status"] == "queued"]

    def ack_phone(self, command_id: str, body: dict) -> dict:
        with self.lock:
            command = self.commands.get(command_id)
            if not command or command["sessionId"] != self.phone.get("id") or command["generation"] != self.phone.get("generation"):
                raise MediaError("COMMAND_UNKNOWN", "This command is no longer active", 404)
            if command["status"] != "queued":
                return dict(command)
            if command["expiresAt"] < time.time():
                command["status"] = "expired"
            elif body.get("sessionId") != command["sessionId"] or body.get("generation") != command["generation"]:
                raise MediaError("SESSION_STALE", "This phone session is no longer active", 409)
            elif body.get("status") not in ("applied", "rejected"):
                raise MediaError("COMMAND_INVALID", "Report applied or rejected")
            else:
                command["status"] = body["status"]
                command["observedState"] = body.get("state")
                if command["status"] == "applied":
                    self.phone["revision"] += 1
                    if body.get("state") in ("playing", "paused", "idle"):
                        self.phone["state"] = body["state"]
                    if isinstance(body.get("positionMs"), int) and body["positionMs"] >= 0:
                        self.phone["positionMs"] = body["positionMs"]
                    for key, low, high in (("volume", 0, 100), ("speed", 0.25, 4)):
                        value = body.get(key)
                        if isinstance(value, (int, float)) and not isinstance(value, bool) and low <= value <= high:
                            self.phone[key] = value
            return dict(command)


def handler_for(state: State, token: str):
    def diagnostics() -> dict:
        power = {"code": "POWER_UNKNOWN", "observed": None}
        try:
            reading = subprocess.run(["vcgencmd", "get_throttled"], capture_output=True,
                                     text=True, timeout=2, check=False).stdout.strip()
            bits = int(reading.split("=", 1)[1], 16)
            power = {"code": "UNDERVOLTAGE" if bits & 1 else "OK",
                     "observed": reading, "underVoltageNow": bool(bits & 1),
                     "throttledNow": bool(bits & 4), "underVoltageSinceBoot": bool(bits & (1 << 16)),
                     "throttledSinceBoot": bool(bits & (1 << 18)),
                     "fix": "Use a suitable Pi power supply or powered USB hub" if bits & 1 else None}
        except (OSError, ValueError, IndexError, subprocess.TimeoutExpired):
            pass
        displays = []
        for path in sorted(Path("/sys/class/drm").glob("card*-HDMI-*/status")):
            try:
                edid_bytes = len((path.parent / "edid").read_bytes())
                connector_state = path.read_text().strip()
                displays.append({"connector": path.parent.name, "state": connector_state,
                                 "enabled": (path.parent / "enabled").read_text().strip(),
                                 "edidBytes": edid_bytes,
                                 "code": "DISCONNECTED" if connector_state == "disconnected" else
                                         "NO_EDID" if edid_bytes == 0 else "OK",
                                 "fix": "Check display power/input and the Pi micro-HDMI cable" if
                                        connector_state == "connected" and edid_bytes == 0 else None})
            except OSError:
                continue
        log_path = state.database.parent / "mpv.log"
        player_errors = []
        try:
            with log_path.open("rb") as log:
                log.seek(max(0, log.seek(0, os.SEEK_END) - 65536))
                for raw in log:
                    line = raw.decode(errors="replace")
                    if any(marker in line.lower() for marker in ("error", "failed", "cannot")):
                        player_errors.append(line.strip()[-240:])
                        player_errors = player_errors[-10:]
        except OSError:
            pass
        return {"observedAt": int(time.time()), "drives": state.library.drive_status(),
                "piPlayer": state.pi_state(), "phonePlayer": state.phone_state(),
                "power": power, "displays": displays, "playerErrors": player_errors}

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt, *args):
            # Do not log URLs: a file name may be private. Never log auth headers.
            pass

        def _json(self, status: int, payload: dict | list):
            data = json.dumps(payload, separators=(",", ":")).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(data)

        def _error(self, error: MediaError):
            self._json(error.status, {"code": error.code, "message": str(error), "retryable": error.status >= 500})

        def _auth(self) -> bool:
            if secrets.compare_digest(self.headers.get("X-Csync-Token", ""), token):
                return True
            self._error(MediaError("AUTH_REQUIRED", "Connect to csync and try again", 401))
            return False

        def _apk(self):
            apk = state.database.parent / "csync-hub-update.apk"
            try:
                info = apk.lstat()
            except OSError:
                raise MediaError("UPDATE_UNAVAILABLE", "No app update is staged on the Pi", 404)
            if not stat.S_ISREG(info.st_mode) or info.st_size < 1024 or info.st_size > 100 * 1024 * 1024:
                raise MediaError("UPDATE_UNAVAILABLE", "The staged app update is invalid", 503)
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.android.package-archive")
            self.send_header("Content-Disposition", 'attachment; filename="csync-update.apk"')
            self.send_header("Content-Length", str(info.st_size))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if self.command != "HEAD":
                with apk.open("rb") as source:
                    while chunk := source.read(65536):
                        self.wfile.write(chunk)

        def _note_image(self, note_id: str, image_id: str):
            data = state.note_image_get(note_id, image_id)
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "private, no-store")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(data)

        def _note_file(self, note_id: str, file_id: str):
            meta, fd = state.note_file_open(note_id, file_id)
            try:
                length = os.fstat(fd).st_size
                ascii_name = re.sub(r"[^A-Za-z0-9._ -]", "_", meta["name"]) or "file"
                self.send_response(200)
                self.send_header("Content-Type", meta["mime"])
                self.send_header("Content-Length", str(length))
                self.send_header("Content-Disposition", f'attachment; filename="{ascii_name}"; '
                                 f"filename*=UTF-8''{quote(meta['name'], safe='')}")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Cache-Control", "private, no-store")
                self.end_headers()
                if self.command != "HEAD":
                    while chunk := os.read(fd, 65536):
                        self.wfile.write(chunk)
            finally:
                os.close(fd)

        def _bootstrap(self, provided: str) -> bool:
            marker = state.database.parent / "app-bootstrap-token"
            try:
                info = marker.lstat()
                if not stat.S_ISREG(info.st_mode) or time.time() - info.st_mtime > 7 * 86400:
                    return False
                expected = marker.read_text().strip()
            except OSError:
                return False
            return len(expected) >= 32 and secrets.compare_digest(expected, provided)

        def _body(self, max_length: int = 16384) -> dict:
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= max_length:
                    raise ValueError()
                value = json.loads(self.rfile.read(length))
                if not isinstance(value, dict):
                    raise ValueError()
                return value
            except (ValueError, json.JSONDecodeError):
                raise MediaError("BODY_INVALID", "Send a small JSON object")

        def do_HEAD(self):
            self._dispatch()

        def do_GET(self):
            self._dispatch()

        def do_POST(self):
            self._dispatch()

        def do_PUT(self):
            self._dispatch()

        def do_DELETE(self):
            self._dispatch()

        def _dispatch(self):
            parsed = urlsplit(self.path)
            if self.command in ("GET", "HEAD") and parsed.path.startswith("/v1/app/bootstrap/"):
                try:
                    if not self._bootstrap(parsed.path.removeprefix("/v1/app/bootstrap/")):
                        raise MediaError("UPDATE_UNAVAILABLE", "App update link is unavailable", 404)
                    return self._apk()
                except MediaError as error:
                    return self._error(error)
                except (BrokenPipeError, ConnectionResetError):
                    return
            if not self._auth():
                return
            try:
                self._route()
            except MediaError as error:
                self._error(error)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def _route(self):
            parsed = urlsplit(self.path)
            path = parsed.path
            parts = path.split("/")
            query = parse_qs(parsed.query)
            def number(name: str, default: int) -> int:
                try:
                    return int(query.get(name, [str(default)])[0])
                except ValueError:
                    raise MediaError("PAGE_INVALID", "Invalid page or session number")
            if self.command in ("GET", "HEAD"):
                if path == "/v1/health":
                    return self._json(200, {"ok": True, "drives": state.library.drive_status()})
                if path == "/v1/drives":
                    return self._json(200, {"drives": state.library.drive_status()})
                if path == "/v1/items":
                    return self._json(200, state.library.folder(query.get("driveId", [""])[0],
                        query.get("path", [""])[0], number("offset", 0)))
                if path == "/v1/videos":
                    return self._json(200, state.library.videos(number("offset", 0)))
                if path == "/v1/search":
                    return self._json(200, state.library.search(query.get("q", [""])[0]))
                if path.startswith("/v1/items/") and path.endswith("/stream"):
                    return self._stream(path[len("/v1/items/"):-len("/stream")])
                if path == "/v1/history":
                    return self._json(200, {"entries": state.history()})
                if path == "/v1/notes":
                    return self._json(200, {"notes": state.notes_list(query.get("q", [""])[0])})
                if path == "/v1/pins":
                    return self._json(200, {"pins": state.pins_list()})
                if path.startswith("/v1/pins/"):
                    return self._json(200, {"pin": state.pin_get(path.removeprefix("/v1/pins/"))})
                if len(parts) == 6 and parts[1:3] == ["v1", "notes"] and parts[4] == "images":
                    return self._note_image(parts[3], parts[5])
                if len(parts) == 5 and parts[1:3] == ["v1", "notes"] and parts[4] == "images":
                    return self._json(200, {"images": state.note_images(parts[3])})
                if len(parts) == 6 and parts[1:3] == ["v1", "notes"] and parts[4] == "files":
                    return self._note_file(parts[3], parts[5])
                if len(parts) == 5 and parts[1:3] == ["v1", "notes"] and parts[4] == "files":
                    return self._json(200, {"files": state.note_files(parts[3])})
                if path.startswith("/v1/notes/"):
                    return self._json(200, {"note": state.note_get(path.removeprefix("/v1/notes/"))})
                if path == "/v1/player/pi":
                    return self._json(200, state.pi_state())
                if path == "/v1/player/phone":
                    return self._json(200, state.phone_state())
                if path == "/v1/phone/commands":
                    return self._json(200, {"commands": state.pending_phone(query.get("sessionId", [""])[0],
                        number("generation", -1))})
                if path == "/v1/diagnostics":
                    return self._json(200, diagnostics())
                if path == "/v1/display/wallpaper":
                    return self._json(200, {"stored": state.wallpaper.is_file()})
                if path == "/v1/app/apk":
                    return self._apk()
                if path == "/v1/camera/status" and state.camera:
                    return self._json(200, state.camera.status())
                if path == "/v1/camera/stream" and state.camera:
                    return self._camera_stream()
                if path == "/v1/camera/captures" and state.camera:
                    return self._json(200, {"captures": state.camera.list_captures()})
                if path.startswith("/v1/camera/captures/") and state.camera:
                    return self._capture(path.rsplit("/", 1)[-1])
            elif self.command == "POST":
                if path == "/v1/notes":
                    return self._json(201, {"note": state.note_create(self._body(320 * 1024))})
                if path == "/v1/pins":
                    return self._json(201, {"pin": state.pin_create(self._body(8 * 1024))})
                if len(parts) == 5 and parts[1:3] == ["v1", "notes"] and parts[4] == "images":
                    try:
                        length = int(self.headers.get("Content-Length", "0"))
                    except ValueError:
                        length = 0
                    if not 8 <= length <= 1024 * 1024:
                        raise MediaError("IMAGE_INVALID", "Choose a PNG image under 1 MB")
                    return self._json(201, {"image": state.note_image_add(parts[3], self.rfile.read(length))})
                if len(parts) == 5 and parts[1:3] == ["v1", "notes"] and parts[4] == "files":
                    try:
                        length = int(self.headers.get("Content-Length", "0"))
                    except ValueError:
                        length = 0
                    self.connection.settimeout(30)
                    return self._json(201, {"file": state.note_file_add(
                        parts[3], query.get("name", [""])[0], self.headers.get("Content-Type", ""),
                        length, self.rfile)})
                if path == "/v1/cast/file":
                    try:
                        length = int(self.headers.get("Content-Length", "0"))
                    except ValueError:
                        length = 0
                    self.connection.settimeout(30)
                    return self._json(201, {"item": state.library.import_media(
                        query.get("driveId", [""])[0], query.get("name", [""])[0],
                        length, self.rfile)})
                if path == "/v1/display/wallpaper":
                    try:
                        length = int(self.headers.get("Content-Length", "0"))
                    except ValueError:
                        length = 0
                    if length < 100 or length > 10 * 1024 * 1024:
                        raise MediaError("IMAGE_INVALID", "Choose a JPEG image under 10 MB", 400)
                    return self._json(200, state.set_wallpaper(self.rfile.read(length)))
                body = self._body()
                if path == "/v1/cast/youtube":
                    return self._json(200, state.cast_youtube(body.get("url", "")))
                if path == "/v1/progress":
                    return self._json(200, state.save_progress(body))
                if path == "/v1/player/pi/commands":
                    return self._json(200, state.command_pi(body))
                if path == "/v1/player/pi/immediate":
                    return self._json(200, state.immediate_pi(body))
                if path == "/v1/player/phone/commands":
                    return self._json(202, state.command_phone(body))
                if path == "/v1/phone/sessions":
                    return self._json(200, state.register_phone(body))
                if path == "/v1/phone/heartbeat":
                    return self._json(200, state.phone_heartbeat(body))
                if path.startswith("/v1/phone/commands/") and path.endswith("/result"):
                    return self._json(200, state.ack_phone(path.split("/")[4], body))
                if path == "/v1/camera/photo" and state.camera:
                    return self._json(200, state.camera.save_photo())
                if path == "/v1/camera/record/start" and state.camera:
                    return self._json(200, state.camera.start_recording())
                if path == "/v1/camera/record/stop" and state.camera:
                    return self._json(200, state.camera.stop_recording())
                if path == "/v1/camera/record/clip" and state.camera:
                    return self._json(200, state.camera.record_clip(body.get("durationSeconds", 5)))
            elif self.command in ("PUT", "DELETE") and path.startswith("/v1/pins/"):
                pin_id = path.removeprefix("/v1/pins/")
                body = self._body(8 * 1024)
                if self.command == "PUT":
                    return self._json(200, {"pin": state.pin_update(pin_id, body)})
                return self._json(200, state.pin_delete(pin_id, body))
            elif self.command == "DELETE" and len(parts) == 6 and parts[1:3] == ["v1", "notes"] and \
                    parts[4] == "files":
                return self._json(200, state.note_file_delete(parts[3], parts[5]))
            elif self.command in ("PUT", "DELETE") and path.startswith("/v1/notes/"):
                note_id = path.removeprefix("/v1/notes/")
                body = self._body(320 * 1024)
                if self.command == "PUT":
                    return self._json(200, {"note": state.note_update(note_id, body)})
                return self._json(200, state.note_delete(note_id, body))
            raise MediaError("ROUTE_UNKNOWN", "This media operation is unavailable", 404)

        def _camera_stream(self):
            listener = state.camera.subscribe()
            try:
                self.connection.settimeout(5)
                self.send_response(200)
                self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                if self.command == "HEAD":
                    return
                while True:
                    try:
                        frame = listener.get(timeout=10)
                    except queue.Empty:
                        break
                    try:
                        self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " +
                            str(len(frame)).encode() + b"\r\n\r\n" + frame + b"\r\n")
                        self.wfile.flush()
                    except (BrokenPipeError, ConnectionResetError, TimeoutError, OSError):
                        break
            finally:
                self.close_connection = True
                state.camera.unsubscribe(listener)

        def _capture(self, name: str):
            path = state.camera.capture(name)
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg" if path.suffix == ".jpg" else
                             "video/x-motion-jpeg" if path.suffix == ".mjpeg" else "video/mp4")
            self.send_header("Content-Length", str(path.stat().st_size))
            self.end_headers()
            if self.command != "HEAD":
                with path.open("rb") as source:
                    while chunk := source.read(65536):
                        self.wfile.write(chunk)

        def _stream(self, item_id: str):
            meta, fd = state.library.open_item(item_id)
            try:
                length = os.fstat(fd).st_size
                start, end = 0, length - 1
                range_header = self.headers.get("Range")
                if range_header and self.headers.get("If-Range", meta["version"]) == meta["version"]:
                    if not range_header.startswith("bytes=") or "," in range_header:
                        raise MediaError("RANGE_INVALID", "Use a single byte range", 416)
                    spec = range_header[6:]
                    try:
                        left, right = spec.split("-", 1)
                        if left:
                            start = int(left)
                            end = min(int(right), length - 1) if right else length - 1
                        else:
                            suffix = int(right)
                            start = max(0, length - suffix)
                    except (ValueError, TypeError):
                        raise MediaError("RANGE_INVALID", "Invalid byte range", 416)
                    if start < 0 or start >= length or end < start:
                        raise MediaError("RANGE_INVALID", "Byte range is outside this file", 416)
                partial = bool(range_header and self.headers.get("If-Range", meta["version"]) == meta["version"])
                self.send_response(206 if partial else 200)
                self.send_header("Content-Type", meta["mime"])
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("ETag", meta["version"])
                self.send_header("Content-Length", str(max(0, end - start + 1)))
                if partial:
                    self.send_header("Content-Range", f"bytes {start}-{end}/{length}")
                self.end_headers()
                if self.command == "HEAD":
                    return
                os.lseek(fd, start, os.SEEK_SET)
                remaining = end - start + 1
                while remaining > 0:
                    chunk = os.read(fd, min(65536, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
            finally:
                os.close(fd)

    return Handler


def load_config(path: Path) -> tuple[Library, str, Path, Path | None, list[str] | None, Path]:
    config = json.loads(path.read_text())
    token = Path(config["tokenFile"]).read_text().strip()
    if not token:
        raise ValueError("empty mesh token")
    drives = [Drive(d["id"], d["label"], Path(d["root"]), d["uuid"]) for d in config["drives"]]
    return (Library(drives, token), token, Path(config["database"]),
            Path(config["mpvSocket"]), config.get("playerCommand"),
            Path(config.get("capturesDir", str(path.parent / "captures"))))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--bind", default="tailscale", help="tailscale or a Tailscale IPv4 address")
    parser.add_argument("--port", type=int, default=8792)
    args = parser.parse_args()
    if args.bind == "tailscale":
        args.bind = subprocess.check_output(["tailscale", "ip", "-4"], text=True, timeout=5).strip()
    if args.bind in ("0.0.0.0", "::", "127.0.0.1") or not args.bind.startswith("100."):
        parser.error("bind to a Tailscale IPv4 address")
    library, token, database, mpv_socket, player_command, captures = load_config(Path(args.config))
    state = State(library, database, mpv_socket, player_command, Camera(captures))
    handler = handler_for(state, token)
    server = ThreadingHTTPServer((args.bind, args.port), handler)
    local_server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    threading.Thread(target=local_server.serve_forever, daemon=True).start()
    print(f"csync media listening on {args.bind}:{args.port} and 127.0.0.1:{args.port}", flush=True)
    # The first mount after a boot includes a disk check and can take longer than one
    # request waits, so the drives are woken here and are ready before the phone asks.
    threading.Thread(target=library.drive_status, daemon=True).start()
    if state.wallpaper.is_file():
        def restore_wallpaper():
            try:
                state.show_wallpaper()
            except MediaError as error:
                print(f"wallpaper display unavailable: {error.code}", flush=True)
        threading.Thread(target=restore_wallpaper, daemon=True).start()
    server.serve_forever()


if __name__ == "__main__":
    main()
