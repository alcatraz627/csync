#!/usr/bin/env python3
"""A small web console for a Raspberry Pi: camera preview, stills, and system info.

It is meant to cost nothing while nobody is looking at it. systemd holds the
listening socket, this process only exists once someone connects, and it exits
itself after IDLE_EXIT seconds with no traffic. The next request starts it again.

Run standalone for development:  python3 server.py --port 8642
"""

import io
import json
import os
import platform
import socket
import socketserver
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
PHOTO_DIR = os.path.expanduser("~/pihub-photos")
IDLE_EXIT = 300          # seconds of no traffic before the process stands down
BOOT = time.time()

_last_seen = time.time()
_lock = threading.Lock()


def touch():
    """Mark the service as in use. A streamed frame counts, so watching keeps it warm."""
    global _last_seen
    with _lock:
        _last_seen = time.time()


def idle_for():
    with _lock:
        return time.time() - _last_seen



class LatestFrame(io.BufferedIOBase):
    """The JPEG encoder writes here; every viewer reads the most recent frame.

    One producer and any number of consumers is the whole point. Grabbing a frame
    per request instead makes viewers queue behind each other on the camera, and
    the second one starves.
    """

    def __init__(self):
        self.frame = None
        self.cond = threading.Condition()

    def write(self, buf):
        with self.cond:
            self.frame = buf
            self.cond.notify_all()
        return len(buf)

    def wait(self, timeout=5.0):
        with self.cond:
            if self.cond.wait_for(lambda: self.frame is not None, timeout):
                return self.frame
        return None


class Camera:
    """Wraps picamera2 and keeps every failure reportable instead of fatal.

    The page must be able to say why there is no picture, so nothing here raises
    into the request handler; callers check the returned reason.
    """

    def __init__(self):
        self.error = None
        self.picam = None
        self.out = None
        self._lock = threading.Lock()

    def _ensure(self):
        if self.picam is not None:
            return True
        try:
            from picamera2 import Picamera2
            from picamera2.encoders import JpegEncoder
            from picamera2.outputs import FileOutput
            cam = Picamera2()
            cam.configure(cam.create_video_configuration(main={"size": (1280, 960)}))
            out = LatestFrame()
            cam.start_recording(JpegEncoder(q=80), FileOutput(out))
            self.picam, self.out = cam, out
            self.error = None
            return True
        except Exception as exc:
            self.error = "%s: %s" % (type(exc).__name__, exc)
            self._drop()
            return False

    def _drop(self):
        if self.picam is not None:
            try:
                self.picam.stop_recording()
            except Exception:
                pass
            try:
                self.picam.close()
            except Exception:
                pass
        self.picam, self.out = None, None

    def frame(self, timeout=5.0):
        """The most recent JPEG, or (None, reason). Never blocks another viewer."""
        with self._lock:
            if not self._ensure():
                return None, self.error
            out = self.out
        jpeg = out.wait(timeout)
        if jpeg is None:
            with self._lock:
                self.error = "the camera produced no frame within %.0fs" % timeout
                self._drop()          # re-open on the next try rather than stay wedged
            return None, self.error
        return jpeg, None

    def release(self):
        """Hand the camera back; a process that dies holding it blocks the next start."""
        with self._lock:
            self._drop()

    def status(self):
        cams = run(["rpicam-hello", "--list-cameras"])
        return {
            "ok": self.error is None and self.picam is not None,
            "error": self.error,
            "detected": "Available cameras" in cams and "ov5647" in cams.lower() or "0 :" in cams,
            "listing": cams.strip() or "rpicam-hello produced no output",
        }


CAM = Camera()



def run(cmd):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=6)
        return (p.stdout or p.stderr or "").strip()
    except FileNotFoundError:
        return "%s is not installed" % cmd[0]
    except Exception as exc:
        return "%s: %s" % (type(exc).__name__, exc)


def read(path, default=""):
    try:
        with open(path) as fh:
            return fh.read().strip()
    except Exception:
        return default


def sysinfo():
    mem = {}
    for line in read("/proc/meminfo").splitlines():
        k, _, v = line.partition(":")
        mem[k.strip()] = v.strip()

    temp = read("/sys/class/thermal/thermal_zone0/temp")
    temp_c = "%.1f °C" % (int(temp) / 1000.0) if temp.isdigit() else "unavailable"

    up = read("/proc/uptime", "0").split()[0]
    try:
        secs = int(float(up))
        uptime = "%dd %dh %dm" % (secs // 86400, secs % 86400 // 3600, secs % 3600 // 60)
    except Exception:
        uptime = "unavailable"

    model = read("/proc/device-tree/model", "unknown").replace("\x00", "")
    throttled = run(["vcgencmd", "get_throttled"])

    return {
        "model": model,
        "hostname": socket.gethostname(),
        "os": read("/etc/os-release").splitlines()[0].split("=", 1)[-1].strip('"'),
        "kernel": platform.release(),
        "arch": platform.machine(),
        "python": platform.python_version(),
        "uptime": uptime,
        "temperature": temp_c,
        "throttled": throttled or "vcgencmd unavailable",
        "loadavg": read("/proc/loadavg", "unavailable").split(" up ")[0],
        "mem_total": mem.get("MemTotal", "unavailable"),
        "mem_available": mem.get("MemAvailable", "unavailable"),
        "swap_total": mem.get("SwapTotal", "unavailable"),
        "disks": run(["df", "-h", "--output=source,size,used,avail,pcent,target", "-x", "tmpfs", "-x", "devtmpfs"]),
        "service_uptime": "%d s" % int(time.time() - BOOT),
        "idle_for": "%d s" % int(idle_for()),
        "stands_down_in": "%d s" % max(0, int(IDLE_EXIT - idle_for())),
    }



class Handler(BaseHTTPRequestHandler):
    server_version = "pihub"

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))

    def _send(self, code, ctype, body, extra=None):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, "application/json", json.dumps(obj, indent=1))

    def do_GET(self):
        touch()
        path = self.path.split("?", 1)[0]

        if path == "/":
            try:
                with open(os.path.join(HERE, "index.html"), "rb") as fh:
                    self._send(200, "text/html; charset=utf-8", fh.read())
            except FileNotFoundError:
                self._send(500, "text/plain", "index.html is missing next to server.py")

        elif path == "/tailwind.js":
            try:
                with open(os.path.join(HERE, "tailwind.js"), "rb") as fh:
                    self._send(200, "application/javascript", fh.read())
            except FileNotFoundError:
                # Styling is optional; the page must still work unstyled.
                self._send(404, "text/plain", "not vendored")

        elif path == "/api/sysinfo":
            self._json(sysinfo())

        elif path == "/api/camera":
            self._json(CAM.status())

        elif path == "/api/frame":
            jpeg, err = CAM.frame()
            if err:
                self._json({"error": err}, code=503)
            else:
                self._send(200, "image/jpeg", jpeg)

        elif path == "/api/stream":
            self.stream()

        elif path == "/api/photos":
            self._json({"photos": photo_list()})

        elif path.startswith("/photos/"):
            name = os.path.basename(path[len("/photos/"):])
            full = os.path.join(PHOTO_DIR, name)
            if os.path.isfile(full):
                with open(full, "rb") as fh:
                    self._send(200, "image/jpeg", fh.read())
            else:
                self._send(404, "text/plain", "no such photo")

        else:
            self._send(404, "text/plain", "not found")

    def do_POST(self):
        touch()
        if self.path.split("?", 1)[0] == "/api/capture":
            jpeg, err = CAM.frame()
            if err:
                self._json({"error": err}, code=503)
                return
            os.makedirs(PHOTO_DIR, exist_ok=True)
            name = time.strftime("%Y%m%d-%H%M%S") + ".jpg"
            with open(os.path.join(PHOTO_DIR, name), "wb") as fh:
                fh.write(jpeg)
            self._json({"saved": name, "url": "/photos/" + name, "dir": PHOTO_DIR})
        else:
            self._send(404, "text/plain", "not found")

    def stream(self):
        """multipart/x-mixed-replace, the format an <img> tag renders natively."""
        jpeg, err = CAM.frame()
        if err:
            self._json({"error": err}, code=503)
            return
        boundary = "pihubframe"
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=%s" % boundary)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            while True:
                touch()          # a watched stream is use, so it holds the process open
                if jpeg:
                    self.wfile.write(b"--" + boundary.encode() + b"\r\n")
                    self.wfile.write(b"Content-Type: image/jpeg\r\n")
                    self.wfile.write(b"Content-Length: %d\r\n\r\n" % len(jpeg))
                    self.wfile.write(jpeg)
                    self.wfile.write(b"\r\n")
                time.sleep(0.12)
                jpeg, err = CAM.frame()
                if err:
                    break
        except (BrokenPipeError, ConnectionResetError):
            pass          # the tab was closed, which is the normal way this ends


def photo_list():
    if not os.path.isdir(PHOTO_DIR):
        return []
    names = sorted((n for n in os.listdir(PHOTO_DIR) if n.endswith(".jpg")), reverse=True)
    return [{"name": n, "url": "/photos/" + n} for n in names[:24]]


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    inherited = None

    def server_bind(self):
        if self.inherited is None:
            return super().server_bind()
        # systemd already bound and listened; adopt its socket instead.
        self.socket.close()
        self.socket = self.inherited
        self.server_address = self.socket.getsockname()

    def server_activate(self):
        if self.inherited is None:
            return super().server_activate()


def watchdog(server):
    while True:
        time.sleep(10)
        if idle_for() > IDLE_EXIT:
            sys.stderr.write("idle %ds, standing down; the socket unit will start me again\n"
                             % int(idle_for()))
            server.shutdown()
            return


def main():
    port = 8642
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])

    inherited = None
    # systemd socket activation hands the listening socket in as fd 3.
    if os.environ.get("LISTEN_FDS") == "1" and os.environ.get("LISTEN_PID") == str(os.getpid()):
        inherited = socket.socket(fileno=3, family=socket.AF_INET, type=socket.SOCK_STREAM)

    Server.inherited = inherited
    server = Server(("0.0.0.0", port), Handler)
    where = server.server_address
    sys.stderr.write("pihub on %s:%d (%s), idle stand-down after %ds\n"
                     % (where[0], where[1],
                        "socket-activated" if inherited else "standalone", IDLE_EXIT))
    threading.Thread(target=watchdog, args=(server,), daemon=True).start()
    try:
        server.serve_forever()
    finally:
        CAM.release()
    sys.stderr.write("stopped\n")


if __name__ == "__main__":
    main()
