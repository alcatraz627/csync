"""The relay sshd on the console: its config, its LaunchAgent, its authorized keys,
and the forced command that greets each tunnel."""

import getpass
import os
import plistlib
import signal
import socket
import subprocess
import sys
import time

from . import emit, keys, paths, state
from .envcfg import env
from .errors import CsyncError, PREREQ

SSHD = "/usr/sbin/sshd"


def config_text(cfg):
    user = getpass.getuser()
    return "\n".join(
        [
            f"Port {cfg['relay_port']}",
            f"ListenAddress {cfg['relay_bind']}",
            f"HostKey {paths.RELAY_HOSTKEY}",
            f"AuthorizedKeysFile {paths.RELAY_AK}",
            f"PidFile {paths.RELAY_PID}",
            "PubkeyAuthentication yes",
            "PasswordAuthentication no",
            "KbdInteractiveAuthentication no",
            "UsePAM no",
            "PermitRootLogin no",
            f"AllowUsers {user}",
            "AllowTcpForwarding remote",
            "GatewayPorts no",
            "X11Forwarding no",
            "AllowAgentForwarding no",
            "PermitTTY no",
            "ClientAliveInterval 30",
            "ClientAliveCountMax 3",
            "LogLevel VERBOSE",
            "StrictModes yes",
            "",
        ]
    )


def write_config(cfg):
    paths.ensure_dirs()
    keys.ensure_key(paths.RELAY_HOSTKEY, "csync-relay-host")
    paths.RELAY_CFG.write_text(config_text(cfg))
    os.chmod(paths.RELAY_CFG, 0o600)
    if not paths.RELAY_AK.exists():
        paths.RELAY_AK.write_text("")
    os.chmod(paths.RELAY_AK, 0o600)


def hello_command(invite_id):
    env = paths.env_overrides()
    prefix = ""
    if env:
        prefix = "env " + " ".join(f"{k}={v}" for k, v in env.items()) + " "
    return f"{prefix}{paths.PYTHON} {paths.BIN} relay-hello {invite_id}"


def authorized_line(invite_id, port, pub):
    opts = ",".join(
        [
            "restrict",
            "port-forwarding",
            f'permitlisten="127.0.0.1:{port}"',
            f'command="{hello_command(invite_id)}"',
        ]
    )
    return f"{opts} {pub} csync-invite:{invite_id}"


def add_line(invite_id, line):
    remove_line(invite_id)
    with open(paths.RELAY_AK, "a") as fh:
        fh.write(line + "\n")
    os.chmod(paths.RELAY_AK, 0o600)


def remove_line(invite_id):
    if not paths.RELAY_AK.exists():
        return False
    marker = f"csync-invite:{invite_id}"
    lines = paths.RELAY_AK.read_text().splitlines()
    kept = [l for l in lines if not l.rstrip().endswith(marker)]
    removed = len(kept) != len(lines)
    tmp = paths.RELAY_AK.with_suffix(".tmp")
    tmp.write_text("".join(l + "\n" for l in kept))
    os.chmod(tmp, 0o600)
    os.replace(tmp, paths.RELAY_AK)
    return removed


def open_invites():
    if not paths.RELAY_AK.exists():
        return []
    out = []
    for l in paths.RELAY_AK.read_text().splitlines():
        if "csync-invite:" in l:
            out.append(l.rsplit("csync-invite:", 1)[1].strip())
    return out


def listening(port, host="127.0.0.1"):
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def pid_alive():
    try:
        pid = int(paths.RELAY_PID.read_text().strip())
        os.kill(pid, 0)
        return pid
    except (OSError, ValueError):
        return None


def plist():
    return {
        "Label": paths.LAUNCH_LABEL,
        "ProgramArguments": [SSHD, "-D", "-e", "-f", str(paths.RELAY_CFG)],
        "RunAtLoad": True,
        "KeepAlive": True,
        "StandardErrorPath": str(paths.RELAY_LOG),
        "StandardOutPath": str(paths.RELAY_LOG),
    }


def install_agent():
    paths.LAUNCH_AGENT.parent.mkdir(parents=True, exist_ok=True)
    with open(paths.LAUNCH_AGENT, "wb") as fh:
        plistlib.dump(plist(), fh)
    domain = f"gui/{os.getuid()}"
    subprocess.run(["launchctl", "bootout", f"{domain}/{paths.LAUNCH_LABEL}"], capture_output=True)
    r = subprocess.run(["launchctl", "bootstrap", domain, str(paths.LAUNCH_AGENT)], capture_output=True, text=True)
    if r.returncode != 0:
        raise CsyncError(PREREQ, f"launchctl bootstrap failed: {r.stderr.strip()}", fix=f"launchctl bootstrap {domain} {paths.LAUNCH_AGENT}")


def agent_loaded():
    r = subprocess.run(["launchctl", "print", f"gui/{os.getuid()}/{paths.LAUNCH_LABEL}"], capture_output=True)
    return r.returncode == 0


def start_daemon():
    """Start the relay without launchd: sshd forks itself into the background and writes its pid."""
    r = subprocess.run([SSHD, "-f", str(paths.RELAY_CFG), "-E", str(paths.RELAY_LOG)], capture_output=True, text=True)
    if r.returncode != 0:
        raise CsyncError(PREREQ, f"sshd failed to start: {r.stderr.strip()}", fix=f"{SSHD} -t -f {paths.RELAY_CFG}")
    for _ in range(20):
        if pid_alive():
            return pid_alive()
        time.sleep(0.1)
    raise CsyncError(PREREQ, "relay sshd did not come up", fix=f"tail {paths.RELAY_LOG}")


def stop_daemon():
    pid = pid_alive()
    if pid:
        os.kill(pid, signal.SIGTERM)


def parse_hello(text):
    parts = text.strip().split()
    if not parts or parts[0] != "hello":
        return None
    fields = {}
    for p in parts[1:]:
        if "=" in p:
            k, v = p.split("=", 1)
            fields[k] = v
    return fields


def hello_main(invite_id):
    """Forced command for one invite key. Records the target's hello, keeps the session
    open so the reverse listener stays up, and marks the host offline when it drops."""
    fields = parse_hello(env("SSH_ORIGINAL_COMMAND") or "")
    if not fields or fields.get("id") != invite_id:
        sys.stderr.write("csync relay: this key only carries a hello\n")
        return 1
    cfg = state.load_config()
    with state.locked():
        hosts = state.load_hosts()
        name = None
        for n, h in hosts.items():
            if h.get("id") == invite_id:
                name = n
                break
        if not name:
            sys.stderr.write("csync relay: unknown invite\n")
            return 1
        h = hosts[name]
        now = time.time()
        if h.get("expires") and h.get("status") == "invited" and now > h["expires"]:
            sys.stderr.write("csync relay: invite expired\n")
            return 1
        hostkey = fields.get("sshd_hostkey", "").replace(":", " ", 1)
        h.update(
            {
                "status": "online",
                "user": fields.get("user"),
                "host": fields.get("host"),
                "os": fields.get("os"),
                "os_label": {"darwin": "macOS", "linux": "Linux"}.get(fields.get("os"), fields.get("os")),
                "osver": fields.get("osver"),
                "arch": fields.get("arch"),
                "route_used": fields.get("route"),
                "cs": fields.get("cs") or h.get("cs"),
                "hostkey": hostkey or h.get("hostkey"),
                "deadline": int(fields["deadline"]) if fields.get("deadline", "").isdigit() else h.get("deadline"),
                "last_hello": now,
                "hello_pid": os.getpid(),
            }
        )
        save_hosts(hosts)
        from . import tunnel

        if hostkey:
            tunnel.known_hosts_set(h["port"], hostkey)
        tunnel.rewrite_ssh_config(hosts)
    state.audit({"host": name, "verb": "hello", "actor": "target", "exit": 0, "route": fields.get("route")})
    emit.notify("csync", f"{name} connected ({fields.get('route', '?')})", cfg.get("notify", True))

    def bye(signum, frame):
        try:
            with state.locked():
                hosts2 = state.load_hosts()
                if name in hosts2 and hosts2[name].get("hello_pid") == os.getpid():
                    hosts2[name]["status"] = "offline"
                    hosts2[name]["hello_pid"] = None
                    state.save_hosts(hosts2)
            state.audit({"host": name, "verb": "bye", "actor": "target", "exit": 0})
            emit.notify("csync", f"{name} dropped, waiting for it to reconnect", cfg.get("notify", True))
        finally:
            os._exit(0)

    for s in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT, signal.SIGPIPE):
        signal.signal(s, bye)
    while True:
        time.sleep(3600)


def save_hosts(hosts):
    state.save_hosts(hosts)
