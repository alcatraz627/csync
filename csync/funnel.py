"""Tailscale on the console: is it up, what is its name, and is Funnel publishing the relay."""

import json
import shutil
import subprocess

from .errors import CsyncError, PREREQ

CANDIDATES = ["tailscale", "/Applications/Tailscale.app/Contents/MacOS/Tailscale"]


def binary():
    for c in CANDIDATES:
        if shutil.which(c) or c.startswith("/") and shutil.os.path.exists(c):
            return shutil.which(c) or c
    return None


def _run(args, check=False):
    b = binary()
    if not b:
        raise CsyncError(PREREQ, "tailscale is not installed on this Mac", fix="brew install --cask tailscale-app")
    r = subprocess.run([b] + args, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise CsyncError(PREREQ, f"tailscale {' '.join(args)} failed: {(r.stderr or r.stdout).strip()}", fix=f"{b} {' '.join(args)}")
    return r


def status():
    r = _run(["status", "--json", "--peers=false"])
    try:
        return json.loads(r.stdout)
    except ValueError:
        return {"BackendState": "Unknown", "raw": r.stdout + r.stderr}


def backend_state():
    return status().get("BackendState", "Unknown")


def dns_name():
    s = status()
    return (s.get("Self") or {}).get("DNSName", "").rstrip(".")


def can_funnel():
    caps = (status().get("Self") or {}).get("Capabilities") or []
    return "funnel" in caps


def up():
    st = backend_state()
    if st == "Running":
        return "already running"
    if st == "NeedsLogin":
        raise CsyncError(PREREQ, "this Mac is logged out of Tailscale", fix="tailscale up   (opens a browser once)")
    _run(["up"], check=True)
    return "started"


def funnel_on(public_port, local_port):
    _run(["funnel", "--bg", f"--tls-terminated-tcp={public_port}", f"tcp://localhost:{local_port}"], check=True)


def funnel_off(public_port):
    _run(["funnel", f"--tls-terminated-tcp={public_port}", "off"])


def funnel_mapping():
    """{public_port: 'host:port'} for every TLS-terminated TCP funnel this node publishes."""
    r = _run(["serve", "status", "--json"])
    try:
        s = json.loads(r.stdout or "{}")
    except ValueError:
        return {}
    out = {}
    allow = s.get("AllowFunnel") or {}
    for port, spec in (s.get("TCP") or {}).items():
        fwd = spec.get("TCPForward")
        if fwd and any(k.endswith(f":{port}") and v for k, v in allow.items()):
            out[int(port)] = fwd
    return out


def funnel_ready(public_port, local_port):
    fwd = funnel_mapping().get(int(public_port))
    return bool(fwd) and fwd.endswith(f":{local_port}")
