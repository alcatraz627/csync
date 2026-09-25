"""On-demand Pi camera preview and captures."""

from __future__ import annotations

import queue
import shutil
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from .library import MediaError


class Camera:
    MIN_FREE_BYTES = 512 * 1024 * 1024
    MAX_RAW_BYTES = 512 * 1024 * 1024
    MAX_RECORD_SECONDS = 30 * 60

    def __init__(self, captures: Path):
        self.captures = captures
        self.captures.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.listeners: set[queue.Queue] = set()
        self.process: subprocess.Popen | None = None
        self.last_frame: bytes | None = None
        self.last_at = 0.0
        self.record_file = None
        self.record_path: Path | None = None
        self.record_error: str | None = None
        self.record_started = 0.0
        self.record_bytes = 0

    def _start(self):
        if self.process and self.process.poll() is None:
            return
        self.last_frame = None
        try:
            self.process = subprocess.Popen([
                "rpicam-vid", "--nopreview", "--timeout", "0", "--width", "640",
                "--height", "480", "--framerate", "10", "--codec", "mjpeg",
                "--output", "-",
            ], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
        except OSError as error:
            raise MediaError("CAMERA_UNAVAILABLE", f"Camera could not start: {error}", 503)
        threading.Thread(target=self._read, daemon=True, name="camera-frames").start()

    def _read(self):
        pending = bytearray()
        process = self.process
        try:
            while process and process.poll() is None:
                chunk = process.stdout.read(65536)
                if not chunk:
                    break
                pending.extend(chunk)
                while True:
                    begin = pending.find(b"\xff\xd8")
                    if begin < 0:
                        pending.clear()
                        break
                    end = pending.find(b"\xff\xd9", begin + 2)
                    if end < 0:
                        if begin:
                            del pending[:begin]
                        if len(pending) > 4_000_000:
                            pending.clear()
                        break
                    frame = bytes(pending[begin:end + 2])
                    del pending[:end + 2]
                    with self.lock:
                        self.last_frame = frame
                        self.last_at = time.time()
                        if self.record_file:
                            try:
                                if (self.record_bytes + len(frame) > self.MAX_RAW_BYTES or
                                        time.monotonic() - self.record_started > self.MAX_RECORD_SECONDS or
                                        shutil.disk_usage(self.captures).free < self.MIN_FREE_BYTES):
                                    raise OSError(28, "Recording limit or free-space reserve reached")
                                self.record_file.write(frame)
                                self.record_bytes += len(frame)
                            except OSError as error:
                                self.record_error = f"Recording stopped: {error.strerror or error}"
                                try:
                                    self.record_file.close()
                                except OSError:
                                    pass
                                self.record_file = None
                                self.record_path = None
                        for listener in self.listeners:
                            try:
                                listener.put_nowait(frame)
                            except queue.Full:
                                pass
        finally:
            with self.lock:
                if self.process is process:
                    self.process = None
                    if self.record_file:
                        try:
                            self.record_file.close()
                        except OSError:
                            pass
                        self.record_file = None
                        self.record_path = None
                        self.record_error = "Recording stopped because the camera process ended"

    def subscribe(self) -> queue.Queue:
        with self.lock:
            self._start()
            listener = queue.Queue(maxsize=2)
            self.listeners.add(listener)
            if self.last_frame:
                listener.put_nowait(self.last_frame)
            return listener

    def unsubscribe(self, listener: queue.Queue):
        with self.lock:
            self.listeners.discard(listener)
            if not self.listeners and self.record_file:
                threading.Thread(target=self._finish_if_idle, daemon=True).start()
            self._stop_if_idle()

    def _finish_if_idle(self):
        with self.lock:
            if self.listeners or not self.record_file:
                return
        try:
            self.stop_recording()
        except MediaError:
            pass

    def _stop_if_idle(self):
        if not self.listeners and not self.record_file and self.process:
            process = self.process
            self.process = None
            process.terminate()

    def photo(self) -> bytes:
        listener = self.subscribe()
        try:
            frame = listener.get(timeout=8)
            settle_until = time.monotonic() + 2
            while time.monotonic() < settle_until:
                try:
                    frame = listener.get(timeout=settle_until - time.monotonic())
                except queue.Empty:
                    break
            return frame
        except queue.Empty:
            raise MediaError("CAMERA_TIMEOUT", "Camera did not deliver a frame", 503)
        finally:
            self.unsubscribe(listener)

    def save_photo(self) -> dict:
        frame = self.photo()
        name = datetime.now(timezone.utc).strftime("photo-%Y%m%d-%H%M%S-%f.jpg")
        (self.captures / name).write_bytes(frame)
        return {"name": name, "bytes": len(frame), "path": str(self.captures / name)}

    def start_recording(self) -> dict:
        with self.lock:
            if not self.listeners:
                raise MediaError("CAMERA_NOT_VIEWED", "Open Camera before recording", 409)
            if self.record_file:
                raise MediaError("RECORDING_ACTIVE", "Recording is already running", 409)
            if shutil.disk_usage(self.captures).free < self.MIN_FREE_BYTES:
                raise MediaError("RECORDING_SPACE_LOW", "Free at least 512 MB before recording", 507)
            self._start()
            self.record_error = None
            self.record_started = time.monotonic()
            self.record_bytes = 0
            name = datetime.now(timezone.utc).strftime("video-%Y%m%d-%H%M%S-%f.mjpeg")
            self.record_path = self.captures / name
            self.record_file = self.record_path.open("wb")
            return {"recording": True, "name": name}

    def stop_recording(self) -> dict:
        with self.lock:
            if not self.record_file or not self.record_path:
                if self.record_error:
                    raise MediaError("RECORDING_WRITE_FAILED", self.record_error, 507)
                raise MediaError("RECORDING_IDLE", "No recording is running", 409)
            try:
                self.record_file.close()
            except OSError as error:
                self.record_error = f"Recording stopped: {error.strerror or error}"
                self.record_file = None
                self.record_path = None
                raise MediaError("RECORDING_WRITE_FAILED", self.record_error, 507)
            raw = self.record_path
            self.record_file = None
            self.record_path = None
            self._stop_if_idle()
        output = raw.with_suffix(".mp4")
        try:
            subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "mjpeg",
                "-framerate", "10", "-i", str(raw), "-an", "-c:v", "libx264",
                "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                str(output),
            ], check=True, timeout=120)
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            raise MediaError("RECORDING_CONVERT_FAILED", f"Raw capture kept as {raw.name}", 500)
        raw.unlink()
        return {"recording": False, "name": output.name, "bytes": output.stat().st_size,
                "path": str(output)}

    def record_clip(self, seconds: int) -> dict:
        if not isinstance(seconds, int) or not 1 <= seconds <= 120:
            raise MediaError("DURATION_INVALID", "Choose 1 to 120 seconds")
        listener = self.subscribe()
        try:
            self.start_recording()
            time.sleep(seconds)
            return self.stop_recording()
        finally:
            self.unsubscribe(listener)

    def status(self) -> dict:
        with self.lock:
            return {"streaming": bool(self.listeners), "viewers": len(self.listeners),
                    "recording": bool(self.record_file), "lastFrameAt": self.last_at,
                    "recordingError": self.record_error}

    def list_captures(self) -> list[dict]:
        return [{"name": p.name, "bytes": p.stat().st_size}
                for p in sorted(self.captures.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
                if p.is_file() and p.suffix in (".jpg", ".mp4", ".mjpeg")][:100]

    def capture(self, name: str) -> Path:
        if not name or Path(name).name != name or not name.endswith((".jpg", ".mp4", ".mjpeg")):
            raise MediaError("CAPTURE_UNKNOWN", "Capture not found", 404)
        path = self.captures / name
        if not path.is_file() or path.is_symlink():
            raise MediaError("CAPTURE_UNKNOWN", "Capture not found", 404)
        return path
