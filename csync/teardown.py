"""Undo a session on both ends and prove it: the target restores its snapshot, the console
forgets the tunnel, and whatever is left is named."""

import os
import shlex
import shutil
import subprocess

from . import paths, relay, state, tunnel
from .errors import CsyncError, RESIDUE


def _cs(h):
    # Home-relative fallback, never "~/...": these paths are shell-quoted.
    return h.get("cs") or ".csync"


def plan(h):
    return {
        "target": [
            "the csync line in ~/.ssh/authorized_keys",
            "/etc/ssh/sshd_config.d/csync.conf, Remote Login and its access group restored (root part)",
            "the tunnel launch unit and the TTL unit",
            "~/.csync/ after its logs are copied home",
        ],
        "console": [
            f"relay key line csync-invite:{h.get('id')}",
            f"Host csync-{h['name']} in {paths.SSH_CONFIG}",
            f"known_hosts entry for 127.0.0.1:{h.get('port')}",
            f"invite key {paths.INVITES / str(h.get('id'))}",
        ],
        "kept": [str(paths.host_dir(h["name"]))],
    }


def _copy_logs(h):
    """Pull the target's session log and shell recordings as one tar stream."""
    dst = paths.host_dir(h["name"]) / "session"
    dst.mkdir(parents=True, exist_ok=True)
    remote = f"bash -c 'cd {shlex.quote(_cs(h))} && shopt -s nullglob && tar czf - session.log shell-*.log'"
    r = subprocess.run(tunnel.ssh_base(h) + [remote], capture_output=True)
    if r.returncode != 0 or not r.stdout:
        return False
    import io
    import tarfile

    try:
        with tarfile.open(fileobj=io.BytesIO(r.stdout), mode="r:gz") as tf:
            tf.extractall(dst, filter="data")
    except (tarfile.TarError, OSError):
        return False
    return True


def run(h, receipt=True, verify=True, dry_run=False):
    if dry_run:
        return {"plan": plan(h), "dry_run": True}
    residue = []
    target_out = ""
    reached = tunnel.reachable(h)
    if reached:
        _copy_logs(h)
        remote = f"{_cs(h)}/teardown.sh" + ("" if receipt else " --no-receipt")
        r = subprocess.run(tunnel.ssh_base(h) + [remote], capture_output=True, text=True)
        target_out = r.stdout + r.stderr
        for line in target_out.splitlines():
            if line.startswith("RESIDUE:"):
                residue.append(("target", line[len("RESIDUE:"):].strip()))
    else:
        residue.append(("target", f"unreachable, so nothing was removed there; its TTL cleans up at the deadline, or the friend runs ~/.csync/teardown.sh"))
    with state.locked():
        hosts = state.load_hosts()
        relay.remove_line(h["id"])
        tunnel.known_hosts_drop(h["port"])
        if h["name"] in hosts:
            hosts[h["name"]]["status"] = "gone"
            hosts[h["name"]]["hello_pid"] = None
        tunnel.rewrite_ssh_config(hosts)
        state.save_hosts(hosts)
    pid = h.get("hello_pid")
    if pid:
        try:
            os.kill(pid, 15)
        except OSError:
            pass
    inv = paths.INVITES / str(h["id"])
    if inv.exists():
        shutil.rmtree(inv)
    if verify:
        if h["id"] in relay.open_invites():
            residue.append(("console", f"relay line csync-invite:{h['id']} still present"))
        if paths.SSH_CONFIG.exists() and f"Host csync-{h['name']}\n" in paths.SSH_CONFIG.read_text():
            residue.append(("console", f"ssh_config still has Host csync-{h['name']}"))
        if paths.KNOWN_HOSTS.exists() and f"[127.0.0.1]:{h['port']} " in paths.KNOWN_HOSTS.read_text():
            residue.append(("console", "known_hosts entry still present"))
        if inv.exists():
            residue.append(("console", f"invite key still at {inv}"))
    result = {"residue": [{"where": w, "what": x} for w, x in residue], "target_output": target_out, "kept": str(paths.host_dir(h["name"]))}
    if residue:
        raise CsyncError(RESIDUE, f"{len(residue)} item(s) left after teardown", fix="see the residue table", data=result)
    return result
