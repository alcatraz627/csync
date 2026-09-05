"""Config, host records, and the audit journal. Every write is atomic and under one lock."""

import fcntl
import json
import os
import time
from contextlib import contextmanager

from . import paths
from .errors import CsyncError, UNKNOWN_HOST

DEFAULTS = {
    "relay_port": 5122,
    "relay_bind": "0.0.0.0",
    "funnel_port": 10000,
    "port_range": [5200, 5299],
    "ttl": "4h",
    "expires": "1h",
    "notify": True,
    "console_name": "",
    "src": "",
}


@contextmanager
def locked():
    paths.HOME.mkdir(parents=True, exist_ok=True)
    with open(paths.LOCK, "w") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def _read(path, default):
    try:
        with open(path) as fh:
            return json.load(fh)
    except FileNotFoundError:
        return default


def save_json(path, obj, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w") as fh:
        json.dump(obj, fh, indent=2, sort_keys=True)
        fh.write("\n")
    os.chmod(tmp, mode)
    os.replace(tmp, path)


def load_config():
    cfg = dict(DEFAULTS)
    cfg.update(_read(paths.CONFIG, {}))
    return cfg


def save_config(cfg):
    save_json(paths.CONFIG, cfg)


def load_hosts():
    return _read(paths.HOSTS, {})


def save_hosts(hosts):
    save_json(paths.HOSTS, hosts)


def host_get(name, hosts=None):
    hosts = load_hosts() if hosts is None else hosts
    h = hosts.get(name)
    if not h or h.get("status") == "gone":
        raise CsyncError(UNKNOWN_HOST, f"no host named {name!r}", fix="csync ls")
    return h


def host_update(name, **fields):
    with locked():
        hosts = load_hosts()
        h = hosts.setdefault(name, {"name": name})
        h.update(fields)
        save_hosts(hosts)
        return h


def audit(entry):
    entry = dict(entry)
    entry.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%S%z"))
    paths.STATE.mkdir(parents=True, exist_ok=True)
    with open(paths.AUDIT, "a") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")


def audit_tail(n=20, host=None):
    try:
        with open(paths.AUDIT) as fh:
            lines = fh.readlines()
    except FileNotFoundError:
        return []
    out = []
    for line in lines:
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if host and e.get("host") != host:
            continue
        out.append(e)
    return out[-n:]
