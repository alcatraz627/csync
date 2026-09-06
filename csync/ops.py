"""The verbs that act on a connected host. Each one streams a script or a command over
the tunnel and returns a dict; cli.py decides how it is shown."""

import os
import re
import shlex
import subprocess
import sys
import time

from . import paths, state, tunnel
from .errors import CsyncError, REMOTE_FAILED, USAGE

OPS = paths.REPO / "ops"
DENY = [
    (r"(^|[;&|]\s*)(sudo\s+)?rm\s+(-[a-zA-Z]*r[a-zA-Z]*\s+)+(-[a-zA-Z]+\s+)*(/|~|\$HOME|\"\$HOME\"|\*|~/\*|/\*)(\s|$)", "rm -r aimed at / or ~"),
    (r"(^|[;&|]\s*)(sudo\s+)?mkfs", "mkfs"),
    (r"(^|[;&|]\s*)(sudo\s+)?diskutil\s+(erase|reformat|partition|apfs\s+delete)", "diskutil erase"),
    (r"(^|[;&|]\s*)(sudo\s+)?dd\s+.*of=/dev/", "dd onto a device"),
    (r"(^|[;&|]\s*)(sudo\s+)?(shutdown|reboot|halt)(\s|$)", "shutdown or reboot"),
    (r"launchctl\s+bootout\s+system", "launchctl bootout system"),
    (r"(>\s*|rm\s+.*\s)/System/", "writes under /System"),
]


def deny_reason(cmd):
    for pat, why in DENY:
        if re.search(pat, cmd):
            return why
    return None


def _ts():
    return time.strftime("%Y%m%d-%H%M%S")


def _dir(h, sub):
    d = paths.host_dir(h["name"]) / sub
    d.mkdir(parents=True, exist_ok=True)
    return d


def stream_script(h, script, args=(), capture=True, stdin_extra=None):
    """Run ops/<script> on the target through 'bash -s', never storing it there."""
    path = OPS / script
    argv = tunnel.ssh_base(h) + ["bash", "-s", "--"] + [shlex.quote(a) for a in args]
    with open(path, "rb") as fh:
        body = fh.read()
    r = subprocess.run(argv, input=body, capture_output=capture)
    out = r.stdout.decode(errors="replace") if capture else ""
    err = r.stderr.decode(errors="replace") if capture else ""
    if r.returncode == 255:
        raise CsyncError(REMOTE_FAILED, f"could not reach {h['name']}: {err.strip()}", fix=f"csync wait {h['name']}")
    return r.returncode, out, err


def run(h, cmd, force=False, full=False, json_mode=False, timeout=None):
    if not cmd:
        raise CsyncError(USAGE, "nothing to run", fix=f"csync run {h['name']} -- uname -a")
    text = " ".join(cmd) if len(cmd) == 1 else shlex.join(cmd)
    why = deny_reason(text)
    if why and not force:
        raise CsyncError(REMOTE_FAILED, f"refused before it ran: {why}", fix=f"csync run {h['name']} --force -- {text}   (needs a terminal)")
    remote = ("CSYNC_FORCE=1 " if force else "") + text
    argv = tunnel.ssh_base(h) + [remote]
    logdir = _dir(h, "runs")
    logfile = logdir / f"{_ts()}.log"
    p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
    lines = []
    shown = 0
    limit = None if (full or json_mode) else 200
    truncated = False
    with open(logfile, "w") as lf:
        for line in p.stdout:
            lf.write(line)
            lines.append(line)
            if json_mode:
                continue
            if limit is None or shown < limit:
                sys.stdout.write(line)
                sys.stdout.flush()
                shown += 1
            elif not truncated:
                truncated = True
                sys.stdout.write(f"… output continues in {logfile} (--full to see it all)\n")
    rc = p.wait(timeout=timeout)
    if rc == 126 and any("csync gate: refused" in l for l in lines):
        raise CsyncError(REMOTE_FAILED, "the target's gate refused it: " + lines[-1].strip(), fix=f"csync run {h['name']} --force -- {text}   (needs a terminal)")
    return {"exit": rc, "lines": len(lines), "log": str(logfile), "output": "".join(lines) if json_mode else None, "truncated": truncated}


def _remote_exists(h, path):
    r = subprocess.run(tunnel.ssh_base(h) + [f"test -e {shlex.quote(path)}"], capture_output=True)
    return r.returncode == 0


def _rsync_progress():
    """macOS ships openrsync, which speaks the protocol but not GNU rsync's --info flags."""
    r = subprocess.run(["rsync", "--version"], capture_output=True, text=True)
    return ["--info=progress2"] if "version 3." in r.stdout else []


def _rsync(h, args, capture):
    ssh_cmd = " ".join(shlex.quote(a) for a in tunnel.ssh_base(h)[:-1])
    argv = ["rsync", "-a"] + ([] if capture else _rsync_progress()) + ["-e", ssh_cmd] + args
    r = subprocess.run(argv, capture_output=capture, text=True)
    if r.returncode != 0:
        err = (r.stderr or "").strip() if capture else ""
        raise CsyncError(REMOTE_FAILED, f"rsync exited {r.returncode} {err}".strip(), fix=f"csync wait {h['name']}")
    return r


def push(h, srcs, dst=None, overwrite=False, dry_run=False, json_mode=False):
    dst = dst or "~/Downloads/csync/"
    if not dst.endswith("/") and len(srcs) > 1:
        dst += "/"
    subprocess.run(tunnel.ssh_base(h) + [f"mkdir -p {shlex.quote(dst if dst.endswith('/') else os.path.dirname(dst) or '.')}"], capture_output=True)
    landed = []
    for s in srcs:
        if not os.path.exists(s):
            raise CsyncError(USAGE, f"no such local file {s}")
        target = dst + os.path.basename(s.rstrip("/")) if dst.endswith("/") else dst
        if not overwrite and _remote_exists(h, target):
            raise CsyncError(USAGE, f"{target} already exists on {h['name']}", fix=f"csync push {h['name']} {s} {dst} --overwrite")
        landed.append(target)
    args = (["-n"] if dry_run else []) + list(srcs) + [f"csync-{h['name']}:{dst}"]
    _rsync(h, args, capture=json_mode)
    return {"landed": landed, "dry_run": dry_run}


def pull(h, srcs, dst=None, json_mode=False):
    dst = dst or str(_dir(h, "inbox")) + "/"
    os.makedirs(dst if dst.endswith("/") else os.path.dirname(dst) or ".", exist_ok=True)
    args = [f"csync-{h['name']}:{s}" for s in srcs] + [dst]
    _rsync(h, args, capture=json_mode)
    got = [os.path.join(dst, os.path.basename(s.rstrip("/"))) if dst.endswith("/") else dst for s in srcs]
    return {"got": got}


def shot(h, display=1, open_after=False, json_mode=False):
    rc, out, err = stream_script(h, "shot.sh", [str(display)])
    if rc != 0:
        raise CsyncError(REMOTE_FAILED, f"screenshot failed on {h['name']}: {(err or out).strip()}", fix="csync info " + h["name"] + " displays")
    remote = out.strip().splitlines()[-1]
    local = _dir(h, "shots") / f"{_ts()}.png"
    _rsync(h, [f"csync-{h['name']}:{remote}", str(local)], capture=True)
    subprocess.run(tunnel.ssh_base(h) + [f"rm -f {shlex.quote(remote)}"], capture_output=True)
    size = local.stat().st_size
    if size < 5000:
        raise CsyncError(
            REMOTE_FAILED,
            f"the capture came back empty ({size} bytes), which is macOS refusing screen access",
            fix=f"on {h['name']}: System Settings › Privacy & Security › Screen Recording › enable sshd-keygen-wrapper, then run csync shot {h['name']} again",
            data={"path": str(local), "bytes": size},
        )
    if open_after:
        subprocess.run(["open", str(local)])
    return {"path": str(local), "bytes": size}


SECTIONS = ["system", "cpu", "memory", "disk", "battery", "displays", "usb", "bluetooth", "network", "audio", "camera"]
ANDROID_SECTIONS = ["telephony", "location", "sensors"]


def sections_for(h):
    return SECTIONS + (ANDROID_SECTIONS if h.get("os") == "android" else [])


def info(h, sections=()):
    allowed = sections_for(h)
    bad = [s for s in sections if s not in allowed]
    if bad:
        raise CsyncError(USAGE, f"unknown section {bad[0]!r}", fix="sections: " + " ".join(allowed))
    rc, out, err = stream_script(h, "info.sh", list(sections) or allowed)
    parsed = {}
    current = None
    for line in out.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            parsed[current] = []
        elif current is not None:
            parsed[current].append(line)
    full = _dir(h, "info") / f"{_ts()}.txt"
    full.write_text(out)
    return {"sections": parsed, "file": str(full), "exit": rc, "stderr": err.strip()}


def logs(h, since="1h", app=None, crash=False, json_mode=False):
    args = ["--since", since] + (["--app", app] if app else []) + (["--crash"] if crash else [])
    rc, out, err = stream_script(h, "logs.sh", args)
    bundle = None
    digest = []
    for line in out.splitlines():
        if line.startswith("BUNDLE="):
            bundle = line.split("=", 1)[1].strip()
        else:
            digest.append(line)
    if rc != 0 or not bundle:
        raise CsyncError(REMOTE_FAILED, f"log collection failed on {h['name']}: {(err or out).strip()[:300]}", fix=f"csync run {h['name']} -- log show --last 5m")
    local = _dir(h, "logs") / f"{_ts()}.tar.gz"
    _rsync(h, [f"csync-{h['name']}:{bundle}", str(local)], capture=True)
    subprocess.run(tunnel.ssh_base(h) + [f"rm -f {shlex.quote(bundle)}"], capture_output=True)
    return {"bundle": str(local), "bytes": local.stat().st_size, "digest": digest[:40]}


def open_(h, target):
    rc, out, err = stream_script(h, "open.sh", [target])
    if rc != 0:
        raise CsyncError(REMOTE_FAILED, f"open failed on {h['name']}: {(err or out).strip()}")
    return {"opened": target}


def say(h, text):
    rc, out, err = stream_script(h, "say.sh", [text])
    if rc != 0:
        raise CsyncError(REMOTE_FAILED, f"notification failed on {h['name']}: {(err or out).strip()}")
    return {"said": text}


def persist(h, action):
    """Turn the target's always-on behaviour on or off without ending the session."""
    if action not in ("on", "off", "status"):
        raise CsyncError(USAGE, "persist takes on, off, or status")
    rc, out, err = stream_script(h, "persist.sh", [action])
    if rc != 0:
        raise CsyncError(REMOTE_FAILED, f"persist {action} failed on {h['name']}: {(err or out).strip()}", fix=f"csync run {h['name']} -- ~/.csync/teardown.sh")
    return {"action": action, "lines": out.strip().splitlines()}
