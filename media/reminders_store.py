"""Timer and reminder templates and runs the Mac and the phone share, as the Pi serves them.

A run is one timer or reminder started on ONE chosen device. The records are small JSON files in
`.reminders/` inside the notes repository, so they travel between the Mac and the Pi the same way notes
do, and every file has exactly one writer so git never has two edits of one file to merge.
Contract: the day-lanes reminders spec (templates/, runs/<id>.json, runs/<id>.state.json,
runs/<id>.stop, devices/<name>.json).
"""
from __future__ import annotations

import json
import os
import re
import secrets
import threading
import time
from pathlib import Path
from typing import Callable

from .library import MediaError
from .notes_store import ID_RE, NotesFolder

STATUSES = ("running", "paused", "ringing", "done", "stopped", "missed", "rejected")
FINISHED = ("done", "stopped", "missed", "rejected")
KINDS = ("timer", "reminder")
DEVICES = ("mac", "phone")
TIMER_GRACE_MS = 2 * 60 * 1000
REMINDER_GRACE_MS = 60 * 60 * 1000
FINISHED_KEEP_MS = 24 * 60 * 60 * 1000
UNANSWERED_KEEP_MS = 7 * 24 * 60 * 60 * 1000
DEVICE_QUIET_MS = 10 * 60 * 1000
CLEANUP_EVERY_MS = 60 * 1000
MAX_LABEL = 80
MAX_TEMPLATES = 100
MAX_MINUTES = 7 * 24 * 60
MAX_TOTAL_MS = MAX_MINUTES * 60 * 1000
MAX_EPOCH_MS = 4_102_444_800_000   # year 2100


def _bad(message: str, field: str | None = None) -> MediaError:
    return MediaError("RUN_INVALID", message, 400, field)


def _int(value, field: str, low: int, high: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not low <= value <= high:
        raise _bad(f"{field} must be a whole number from {low} to {high}", field)
    return value


def _text(value, field: str, low: int = 1, high: int = MAX_LABEL) -> str:
    if not isinstance(value, str) or not low <= len(value.strip()) <= high:
        raise _bad(f"{field} must be {low} to {high} characters" if low else f"{field} must be up to {high} characters", field)
    return value.strip()


class RemindersFolder:
    """Reads and writes `.reminders/` inside the notes repository; every write is a commit."""

    def __init__(self, notes: NotesFolder, clock: Callable[[], int] | None = None):
        self.notes = notes
        self.root = notes.folder / ".reminders"
        self.clock = clock or (lambda: int(time.time() * 1000))
        self._lock = threading.Lock()
        self._last_cleanup = 0
        for sub in ("templates", "runs", "devices"):
            (self.root / sub).mkdir(parents=True, exist_ok=True)

    # ── files ──
    def _path(self, sub: str, name: str) -> Path:
        base = name.split(".", 1)[0]
        if not ID_RE.fullmatch(base):
            raise MediaError("RUN_NOT_FOUND", "This run is no longer available", 404)
        return self.root / sub / name

    @staticmethod
    def _read(p: Path) -> dict | None:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return data if isinstance(data, dict) else None

    @staticmethod
    def _write(p: Path, data: dict | None) -> None:
        """Atomic: a reader sees the old file or the new one, never half of it."""
        tmp = p.with_name("." + p.name + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True) if data is not None else "", encoding="utf-8")
        os.replace(tmp, p)

    def _new_id(self, prefix: str, sub: str, suffix: str) -> str:
        while True:
            rid = f"{prefix}-{self.clock() // 1000}-{secrets.token_hex(2)}"
            if not (self.root / sub / (rid + suffix)).exists():
                return rid

    # ── templates ──
    def _template_fields(self, body: dict) -> dict:
        color = body.get("color", "")
        if color not in ("",) + NotesFolder.COLORS:
            raise MediaError("RUN_INVALID", "That colour is not one of the eight", 400, "color")
        return {"label": _text(body.get("label"), "label"), "minutes": _int(body.get("minutes"), "minutes", 1, MAX_MINUTES),
                "color": color}

    def templates(self) -> list[dict]:
        out = []
        for p in (self.root / "templates").glob("*.json"):
            data = self._read(p)
            if data and ID_RE.fullmatch(p.stem):
                out.append(data)
        out.sort(key=lambda t: (-int(t.get("created", 0)), t.get("id", "")))
        return out

    def template_add(self, body: dict) -> tuple[dict, bool]:
        """(template, created). A body that names an id already stored returns the stored one untouched,
        so a phone that seeds its starter templates twice does not double them."""
        fields = self._template_fields(body)
        with self._lock:
            tid = body.get("id")
            if tid is not None:
                if not isinstance(tid, str) or not ID_RE.fullmatch(tid):
                    raise _bad("id must be letters, digits, - or _", "id")
                existing = self._read(self._path("templates", tid + ".json"))
                if existing:
                    return existing, False
            else:
                tid = self._new_id("t", "templates", ".json")
            if len(list((self.root / "templates").glob("*.json"))) >= MAX_TEMPLATES:
                raise MediaError("RUN_INVALID", f"Keep up to {MAX_TEMPLATES} templates", 400)
            template = {"id": tid, "kind": "timer", "created": self.clock(), **fields}
            self._write(self._path("templates", tid + ".json"), template)
            self.notes.commit("template: add")
            return template, True

    def template_update(self, tid: str, body: dict) -> dict:
        fields = self._template_fields(body)
        with self._lock:
            p = self._path("templates", tid + ".json")
            current = self._read(p)
            if current is None:
                raise MediaError("RUN_NOT_FOUND", "This template is no longer available", 404)
            current.update(fields)
            self._write(p, current)
            self.notes.commit("template: edit")
            return current

    def template_delete(self, tid: str) -> dict:
        with self._lock:
            p = self._path("templates", tid + ".json")
            if not p.exists():
                raise MediaError("RUN_NOT_FOUND", "This template is no longer available", 404)
            p.unlink()
            self.notes.commit("template: delete")
            return {"deleted": True, "id": tid}

    # ── runs ──
    def _request(self, rid: str) -> dict | None:
        return self._read(self._path("runs", rid + ".json"))

    def _state(self, rid: str) -> dict | None:
        return self._read(self._path("runs", rid + ".state.json"))

    @staticmethod
    def _grace(kind: str) -> int:
        return TIMER_GRACE_MS if kind == "timer" else REMINDER_GRACE_MS

    def run_add(self, body: dict) -> tuple[dict, bool]:
        """The phone asks for a run on `target`. (row, created): a body that names an id already stored
        returns that run untouched, so a request the phone's outbox sends twice starts one run."""
        kind = body.get("kind")
        if kind not in KINDS:
            raise _bad("kind is timer or reminder", "kind")
        target = body.get("target")
        if target not in DEVICES:
            raise _bad("target is mac or phone", "target")
        color = body.get("color", "")
        if color not in ("",) + NotesFolder.COLORS:
            raise MediaError("RUN_INVALID", "That colour is not one of the eight", 400, "color")
        label = _text(body.get("label"), "label")
        now = self.clock()
        fire_at = _int(body.get("fire_at"), "fire_at", 1, MAX_EPOCH_MS)
        total = _int(body.get("total_ms", 0 if kind == "reminder" else None), "total_ms",
                     1000 if kind == "timer" else 0, MAX_TOTAL_MS)
        template, note = body.get("template"), body.get("note")
        for field, value in (("template", template), ("note", note)):
            if value is not None and (not isinstance(value, str) or not ID_RE.fullmatch(value)):
                raise _bad(f"{field} must be an id or null", field)
        with self._lock:
            rid = body.get("id")
            if rid is not None:
                if not isinstance(rid, str) or not ID_RE.fullmatch(rid):
                    raise _bad("id must be letters, digits, - or _", "id")
                if self._request(rid):
                    return self._row(rid), False
            else:
                rid = self._new_id("r", "runs", ".json")
            request = {"id": rid, "kind": kind, "label": label, "color": color, "total_ms": total, "fire_at": fire_at,
                       "target": target, "from": "phone", "created_at": now, "template": template, "note": note}
            self._write(self._path("runs", rid + ".json"), request)
            self.notes.commit(f"run: request to {target}")
        return self._row(rid), True

    def run_state(self, rid: str, body: dict) -> dict:
        """The phone writes the truth about a run aimed at the phone. A request that reaches the phone
        long after its time is recorded as missed (a timer) or as ringing once, marked missed (a reminder)."""
        request = self._request(rid)
        if request is None:
            raise MediaError("RUN_NOT_FOUND", "This run is no longer available", 404)
        if request.get("target") != "phone":
            raise MediaError("RUN_NOT_YOURS", "Only the Mac writes the state of a run on the Mac", 403)
        status = body.get("status")
        if status not in STATUSES:
            raise _bad("status is one of " + ", ".join(STATUSES), "status")
        end_ms = body.get("end_ms")
        remain_ms = body.get("remain_ms")
        for field, value in (("end_ms", end_ms), ("remain_ms", remain_ms)):
            if value is not None:
                _int(value, field, 0, MAX_EPOCH_MS)
        note = body.get("note", "")
        note = _text(note, "note", 0, 200) if note else ""
        with self._lock:
            now = self.clock()
            current = self._state(rid)
            if current and current.get("status") in FINISHED:
                if current["status"] == status:
                    return self._row(rid)
                raise MediaError("RUN_FINISHED", "This run already ended", 409)
            if current is None and status in ("running", "paused", "ringing"):
                late = now - int(request.get("fire_at", now))
                if late > self._grace(request.get("kind", "timer")):
                    if request.get("kind") == "timer":
                        status, note = "missed", note or "Arrived after its time"
                    else:
                        status, note = "ringing", note or "missed"
            state = {"status": status, "updated_at": now, "end_ms": end_ms, "remain_ms": remain_ms, "note": note}
            self._write(self._path("runs", rid + ".state.json"), state)
            self.notes.commit(f"run: {status}")
        return self._row(rid)

    def run_stop(self, rid: str) -> dict:
        """Any device asks for a run to end. The target does the stopping on its next look."""
        with self._lock:
            if self._request(rid) is None:
                raise MediaError("RUN_NOT_FOUND", "This run is no longer available", 404)
            state = self._state(rid)
            stop = self._path("runs", rid + ".stop")
            if not (state and state.get("status") in FINISHED) and not stop.exists():
                self._write(stop, None)
                self.notes.commit("run: stop requested")
        return self._row(rid)

    def _row(self, rid: str) -> dict:
        request = self._request(rid) or {}
        state = self._state(rid)
        target = request.get("target")
        device = self._read(self._path("devices", target + ".json")) if target in DEVICES else None
        now = self.clock()
        signals = [s for s in ((state or {}).get("updated_at"), (device or {}).get("seen_at")) if isinstance(s, int)]
        row = {"id": rid, "kind": request.get("kind"), "label": request.get("label", ""), "color": request.get("color", ""),
               "totalMs": request.get("total_ms", 0), "fireAt": request.get("fire_at"), "target": target,
               "from": request.get("from"), "createdAt": request.get("created_at"), "template": request.get("template"),
               "note": request.get("note"),
               "status": state["status"] if state else "waiting",
               "endMs": (state or {}).get("end_ms"), "remainMs": (state or {}).get("remain_ms"),
               "stateNote": (state or {}).get("note", ""), "updatedAt": (state or {}).get("updated_at"),
               "stopRequested": self._path("runs", rid + ".stop").exists(),
               "waitingFor": target if state is None else None,
               "staleSeconds": (now - max(signals)) // 1000 if signals else None}
        return row

    def runs(self) -> dict:
        """Every run as one row, newest first, with what each device last said it was running."""
        self.cleanup()
        rows = []
        for p in (self.root / "runs").glob("*.json"):
            if p.name.endswith(".state.json") or not ID_RE.fullmatch(p.stem):
                continue
            if self._read(p) is not None:
                rows.append(self._row(p.stem))
        rows.sort(key=lambda r: (-(r["createdAt"] or 0), r["id"]))
        now = self.clock()
        devices = {}
        for name in DEVICES:
            data = self._read(self._path("devices", name + ".json"))
            if data:
                seen = data.get("seen_at")
                items = [{"run": i.get("run"), "label": i.get("label", ""), "endMs": i.get("end_ms")}
                         for i in data.get("running", []) if isinstance(i, dict)]
                devices[name] = {"seenAt": seen, "running": items,
                                 "staleSeconds": (now - seen) // 1000 if isinstance(seen, int) else None}
        return {"runs": rows, "devices": devices}

    def device_set(self, name: str, body: dict) -> dict:
        """The phone says what it is running. Said again unchanged within ten minutes, nothing is written,
        so an idle phone does not fill the history with heartbeats."""
        if name != "phone":
            raise MediaError("RUN_NOT_YOURS", "Only the Mac writes the Mac's device file", 403)
        running = body.get("running", [])
        if not isinstance(running, list) or len(running) > 20:
            raise _bad("running is a list of up to 20 runs", "running")
        clean = []
        for item in running:
            if not isinstance(item, dict) or not isinstance(item.get("run"), str) or not ID_RE.fullmatch(item["run"]):
                raise _bad("each running item needs a run id", "running")
            clean.append({"run": item["run"], "label": _text(item.get("label", "x"), "label"),
                          "end_ms": _int(item.get("end_ms"), "end_ms", 0, MAX_EPOCH_MS)})
        with self._lock:
            now = self.clock()
            p = self._path("devices", "phone.json")
            current = self._read(p)
            if current and current.get("running") == clean and now - int(current.get("seen_at", 0)) < DEVICE_QUIET_MS:
                return {"device": "phone", "seenAt": current["seen_at"], "running": clean, "written": False}
            self._write(p, {"seen_at": now, "running": clean})
            self.notes.commit("device: phone")
        return {"device": "phone", "seenAt": now, "running": clean, "written": True}

    # ── cleanup ──
    def cleanup(self, force: bool = False) -> list[str]:
        """Removes what this side owns once it is stale: runs aimed at the phone, 24 hours after they
        ended; runs the phone started that nobody ever picked up, after 7 days; and loose state or stop
        files whose request is gone. The Mac removes its own the same way. Returns the removed names."""
        now = self.clock()
        if not force and now - self._last_cleanup < CLEANUP_EVERY_MS:
            return []
        self._last_cleanup = now
        removed: list[str] = []
        with self._lock:
            runs = self.root / "runs"
            for p in sorted(runs.iterdir()):
                if p.name.startswith("."):
                    continue
                rid = p.name.split(".", 1)[0]
                request = self._request(rid)
                if request is None:
                    if not p.name.endswith(".json") or p.name.endswith(".state.json"):
                        removed.append(p.name)
                        p.unlink(missing_ok=True)
                    continue
                if p.name != rid + ".json":
                    continue
                state = self._state(rid)
                if state and request.get("target") == "phone" and state.get("status") in FINISHED \
                        and now - int(state.get("updated_at", now)) > FINISHED_KEEP_MS:
                    gone = True
                elif state is None and request.get("from") == "phone" \
                        and now - int(request.get("created_at", now)) > UNANSWERED_KEEP_MS:
                    gone = True
                else:
                    gone = False
                if gone:
                    for suffix in (".json", ".state.json", ".stop"):
                        if (runs / (rid + suffix)).exists():
                            (runs / (rid + suffix)).unlink()
                            removed.append(rid + suffix)
            if removed:
                self.notes.commit("runs: cleanup")
        return removed
