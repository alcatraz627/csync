"""The console's view of a tunnel: the ssh_config block, the pinned host key, and the wait."""

import os
import subprocess
import time

from . import paths, state
from .errors import CsyncError, OFFLINE


def block(h):
    return "\n".join(
        [
            f"Host csync-{h['name']}",
            "  HostName 127.0.0.1",
            f"  Port {h['port']}",
            f"  User {h.get('user') or 'nobody'}",
            f"  IdentityFile {paths.CONSOLE_KEY}",
            "  IdentitiesOnly yes",
            f"  UserKnownHostsFile {paths.KNOWN_HOSTS}",
            "  StrictHostKeyChecking yes",
            "  BatchMode yes",
            "  ConnectTimeout 5",
            "  ServerAliveInterval 15",
            "  LogLevel ERROR",
            "",
        ]
    )


def rewrite_ssh_config(hosts):
    parts = ["# written by csync; edit ~/.ssh/config for your own hosts", ""]
    for h in hosts.values():
        if h.get("status") in ("online", "offline") and h.get("user"):
            parts.append(block(h))
    paths.SSH_CONFIG.write_text("\n".join(parts))
    os.chmod(paths.SSH_CONFIG, 0o600)


def known_hosts_set(port, key):
    prefix = f"[127.0.0.1]:{port} "
    lines = []
    if paths.KNOWN_HOSTS.exists():
        lines = [l for l in paths.KNOWN_HOSTS.read_text().splitlines() if not l.startswith(prefix)]
    lines.append(prefix + key)
    paths.KNOWN_HOSTS.write_text("".join(l + "\n" for l in lines))
    os.chmod(paths.KNOWN_HOSTS, 0o600)


def known_hosts_drop(port):
    if not paths.KNOWN_HOSTS.exists():
        return
    prefix = f"[127.0.0.1]:{port} "
    lines = [l for l in paths.KNOWN_HOSTS.read_text().splitlines() if not l.startswith(prefix)]
    paths.KNOWN_HOSTS.write_text("".join(l + "\n" for l in lines))


def ssh_base(h):
    return ["ssh", "-F", str(paths.SSH_CONFIG), f"csync-{h['name']}"]


def hello_alive(h):
    pid = h.get("hello_pid")
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def reachable(h):
    if not h.get("user"):
        return False
    r = subprocess.run(ssh_base(h) + ["true"], capture_output=True, text=True)
    return r.returncode == 0


def require_online(h, timeout=0):
    """Raise OFFLINE unless the host answers; wait up to timeout seconds for a reconnect."""
    deadline = time.time() + timeout
    while True:
        if reachable(h):
            return
        if time.time() >= deadline:
            break
        time.sleep(2)
        h = state.host_get(h["name"])
    status = "waiting for the paste" if h.get("status") == "invited" else "not answering"
    raise CsyncError(OFFLINE, f"{h['name']} is {status}", fix=f"csync wait {h['name']}")


def wait(name, timeout=600):
    start = time.time()
    while time.time() - start < timeout:
        h = state.host_get(name)
        if h.get("status") == "online" and hello_alive(h) and reachable(h):
            return h
        time.sleep(2)
    h = state.host_get(name)
    raise CsyncError(OFFLINE, f"{name} did not connect within {int(timeout)}s", fix=f"on {name}, paste the invite line again, or csync invite {name} after csync forget {name}")
