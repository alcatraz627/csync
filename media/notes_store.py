"""The notes folder the Mac, the Pi and the phone share, as the Pi serves it.

One markdown file per note with the same frontmatter Switchboard writes, kept in
a git repository so every save is a version and the Mac can push and pull. A
pin is a note with a `url:` line. A save that arrives on top of an edit it never
saw is not refused: both sides land in the file with git's markers, so nothing
is ever lost and nobody waits. Contract:
switchboard-mac/docs/plans/20261010-notes-contract.md
"""
from __future__ import annotations

import json
import re
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .library import MediaError

ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")
# Frontmatter keys in the order Switchboard writes them; unknown keys are kept after these.
KEY_ORDER = ("title", "created", "tags", "expires", "remind_at", "remind_repeat", "reminder_id",
             "pinned", "color", "agent", "source", "url")
QUOTED = {"title", "tags", "reminder_id", "agent", "source", "url"}


def _quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _unquote(value: str) -> str:
    if value.startswith('"'):
        try:
            return json.loads(value)
        except ValueError:
            return value
    # YAML single quotes, as other editors write them: '' is a literal quote
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    return value


def parse(text: str) -> tuple[dict, str]:
    """Frontmatter fields and the body, the way Notes.swift reads them."""
    fields: dict[str, str] = {}
    body = text
    if text.startswith("---\n"):
        # from 3, so an empty block ("---" then "---") closes too
        end = text.find("\n---\n", 3)
        if end >= 0:
            for line in text[4:end].split("\n"):
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                fields[key.strip()] = _unquote(value.strip())
            body = text[end + 5:]
    body = body.strip("\n")
    if "title" in fields:
        fields["title"] = fields["title"].strip()
    if not fields.get("title") and body:
        first, _, rest = body.partition("\n")
        fields["title"] = first.lstrip("#").strip()
        body = rest.strip("\n")
    return fields, body


def render(fields: dict, body: str) -> str:
    lines = ["---"]
    for key in list(KEY_ORDER) + [k for k in fields if k not in KEY_ORDER]:
        value = fields.get(key)
        # the title is always written, empty or not: a file without one reads its first body line as the title
        if value in (None, "", False) and key != "title":
            continue
        if key == "title" and value is None:
            value = ""
        if key == "pinned":
            lines.append("pinned: true")
        elif key in QUOTED:
            lines.append(f"{key}: {_quote(str(value))}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n" + body + ("\n" if body else "")


def conflicted(body: str) -> bool:
    return body.startswith("<<<<<<< ") or "\n<<<<<<< " in body


class NotesFolder:
    """Reads and writes the folder; every write is a commit."""

    def __init__(self, folder: Path, author: str = "csync-pi"):
        self.folder = Path(folder)
        self.author = author
        self.folder.mkdir(parents=True, exist_ok=True)
        if not (self.folder / ".git").exists():
            self._git("init", "-q", "-b", "main")
            self._git("config", "user.name", author)
            self._git("config", "user.email", author + "@local")
            # the Mac pushes straight into this working tree
            self._git("config", "receive.denyCurrentBranch", "updateInstead")
            (self.folder / ".gitignore").write_text("order.json\n.DS_Store\n.import/\n.trash/\n")
            self._git("add", "-A")
            self._git("commit", "-q", "-m", "notes folder")

    # ── git ──
    def _git(self, *args: str) -> subprocess.CompletedProcess:
        # local only: the Mac pushes here, this side never reaches out, so nothing can prompt
        return subprocess.run(["git", *args], cwd=self.folder, capture_output=True, text=True, timeout=20)

    def commit(self, reason: str) -> None:
        self._git("add", "-A")
        self._git("commit", "-q", "-m", reason)
        self._counts = None

    _counts: tuple[str, dict[str, int], dict[str, int]] | None = None

    def _head_stamp(self) -> str:
        """Changes whenever HEAD moves, here or by a push, without running git."""
        for name in ("refs/heads/main", "packed-refs", "HEAD"):
            try:
                st = (self.folder / ".git" / name).stat()
                return f"{name}:{st.st_mtime_ns}:{st.st_size}"
            except OSError:
                continue
        return ""

    def _commit_counts(self) -> dict[str, int]:
        """Commits per file, from one git call, kept until HEAD moves (a 500-note list is one pass)."""
        head = self._head_stamp()
        if self._counts and self._counts[0] == head:
            return self._counts[1]
        counts: dict[str, int] = {}
        latest: dict[str, int] = {}
        when = 0
        # newest first, so the first time a file appears is its last edit
        for line in self._git("log", "--format=@%ct", "--name-only", "--", "*.md").stdout.splitlines():
            if line.startswith("@") and line[1:].isdigit():
                when = int(line[1:])
            elif line.endswith(".md"):
                counts[line[:-3]] = counts.get(line[:-3], 0) + 1
                latest.setdefault(line[:-3], when)
        # one assignment, so a request thread never reads counts from one HEAD and times from another
        self._counts = (head, counts, latest)
        return counts

    def edited_at(self, note_id: str, p: Path, created: int | None = None) -> int:
        """When the note was last edited: its last commit, else the file's time.
        The file time alone lies after a sync or checkout touches every file, and a
        note with one commit was only imported, so its own created time is truer.
        A note no commit has seen yet (just written) keeps its file time."""
        self._commit_counts()
        snap = self._counts   # one read: counts and times from the same HEAD
        n = snap[1].get(note_id, 0) if snap else 0
        latest = snap[2] if snap else {}
        if n == 1 and created:
            return created
        return latest.get(note_id) or int(p.stat().st_mtime)

    def revision(self, note_id: str) -> int:
        """How many commits have touched the note: 1 for a fresh one, 0 for a file git never saw."""
        return self._commit_counts().get(note_id, 0)

    def history(self, note_id: str) -> list[dict]:
        out = self._git("log", "--format=%h%x09%ct%x09%s", "--", note_id + ".md").stdout
        rows = []
        for line in out.splitlines():
            parts = line.split("\t", 2)
            if len(parts) == 3 and parts[1].isdigit():
                rows.append({"sha": parts[0], "at": int(parts[1]), "reason": parts[2]})
        return rows

    # ── files ──
    def path(self, note_id: str) -> Path:
        if not ID_RE.fullmatch(note_id):
            raise MediaError("NOTE_NOT_FOUND", "This note is no longer available", 404)
        return self.folder / (note_id + ".md")

    def read(self, note_id: str) -> dict:
        p = self.path(note_id)
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            raise MediaError("NOTE_NOT_FOUND", "This note is no longer available", 404)
        fields, body = parse(text)
        return self._shape(note_id, fields, body, p)

    def _shape(self, note_id: str, fields: dict, body: str, p: Path) -> dict:
        st = p.stat()
        created = fields.get("created")
        try:
            created_at = int(datetime.fromisoformat(created.replace("Z", "+00:00")).timestamp()) if created else int(st.st_mtime)
        except ValueError:
            created_at = int(st.st_mtime)
        tags = [t.strip() for t in fields.get("tags", "").split(",") if t.strip()]
        note = {"id": note_id, "title": fields.get("title", ""), "body": body,
                "revision": self.revision(note_id), "createdAt": created_at, "updatedAt": self.edited_at(note_id, p, created_at if created else None),
                "tags": tags, "conflicted": conflicted(body)}
        for key in ("agent", "source", "url", "color"):
            if fields.get(key):
                note[key] = fields[key]
        if fields.get("pinned") == "true":
            note["pinned"] = True
        return note

    def _write(self, note_id: str, fields: dict, body: str, reason: str) -> None:
        self.path(note_id).write_text(render(fields, body), encoding="utf-8")
        self.commit(reason)

    def all(self) -> list[dict]:
        out = []
        for p in self.folder.glob("*.md"):
            try:
                fields, body = parse(p.read_text(encoding="utf-8"))
            except OSError:
                continue
            out.append(self._shape(p.stem, fields, body, p))
        out.sort(key=lambda n: (-n["updatedAt"], n["id"]))
        return out

    @staticmethod
    def new_id() -> str:
        return time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:4]

    # ── notes ──
    def create(self, title: str, body: str, agent: str | None = None, url: str = "", tags: list[str] | None = None,
               source: str = "") -> dict:
        note_id = self.new_id()
        while self.path(note_id).exists():
            note_id += "x"
        fields = {"title": title, "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
        if tags:
            fields["tags"] = ", ".join(tags)
        if agent:
            fields["agent"] = agent
        if url:
            fields["url"] = url
        if source:
            fields["source"] = source
        self._write(note_id, fields, body, f"save ({agent or self.author})")
        return self.read(note_id)

    def update(self, note_id: str, title: str, body: str, expected: int, agent: str | None = None,
               url: str | None = None, tags: list[str] | None = None) -> dict:
        """A stale save keeps both sides in the body, marked; the caller sees `conflicted`."""
        fields, current = parse(self.path(note_id).read_text(encoding="utf-8")) if self.path(note_id).exists() else (None, "")
        if fields is None:
            raise MediaError("NOTE_NOT_FOUND", "This note is no longer available", 404)
        who = agent or "phone"
        if self.revision(note_id) != expected and body != current:
            body = f"<<<<<<< {who}\n{body}\n=======\n{current}\n>>>>>>> {self.author}\n"
            reason = f"merge: both sides kept ({who})"
        else:
            reason = f"save ({who})"
        fields["title"] = title
        if agent:
            fields["agent"] = agent
        if url is not None:
            fields["url"] = url
        if tags is not None:
            fields["tags"] = ", ".join(tags)
        self._write(note_id, fields, body, reason)
        return self.read(note_id)

    COLORS = ("red", "orange", "yellow", "green", "teal", "blue", "purple", "pink")

    def set_meta(self, note_id: str, color: str | None = None, pinned: bool | None = None) -> dict:
        """Colour and pin only: no revision check, since neither can lose anyone's writing.
        color "" clears it; None leaves it as it is."""
        p = self.path(note_id)
        if not p.exists():
            raise MediaError("NOTE_NOT_FOUND", "This note is no longer available", 404)
        fields, body = parse(p.read_text(encoding="utf-8"))
        if color is not None:
            if color == "":
                fields.pop("color", None)
            elif color in self.COLORS:
                fields["color"] = color
            else:
                raise MediaError("NOTE_COLOR", "That colour is not one of the eight", 400)
        if pinned is not None:
            if pinned:
                fields["pinned"] = "true"
            else:
                fields.pop("pinned", None)
        self._write(note_id, fields, body, "pin" if pinned is not None else "colour")
        return self.read(note_id)

    def delete(self, note_id: str, expected: int, code: str = "NOTE_CONFLICT") -> dict:
        """Deleting over an edit never seen would lose it, so that one is refused."""
        p = self.path(note_id)
        if not p.exists():
            raise MediaError("NOTE_NOT_FOUND", "This note is no longer available", 404)
        if self.revision(note_id) != expected:
            raise MediaError(code, "This note changed elsewhere. Reload it before deleting", 409)
        p.unlink()
        self.commit("delete")
        return {"deleted": True, "id": note_id}
