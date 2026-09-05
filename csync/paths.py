"""Where csync keeps things on the console. Three roots, each overridable for tests."""

import os
import sys
from pathlib import Path

from .envcfg import env

REPO = Path(__file__).resolve().parent.parent
BIN = REPO / "bin" / "csync"
PYTHON = sys.executable

HOME = Path(env("CSYNC_HOME") or Path.home() / ".config" / "csync")
STATE = Path(env("CSYNC_STATE") or Path.home() / ".local" / "state" / "csync")
DATA = Path(env("CSYNC_DATA") or Path.home() / "csync")

CONFIG = HOME / "config.json"
HOSTS = HOME / "hosts.json"
LOCK = HOME / ".lock"
SSH_CONFIG = HOME / "ssh_config"
KNOWN_HOSTS = HOME / "known_hosts"
CONSOLE_KEY = HOME / "id_ed25519"
INVITES = HOME / "invites"

RELAY = HOME / "relay"
RELAY_CFG = RELAY / "sshd_config"
RELAY_HOSTKEY = RELAY / "ssh_host_ed25519_key"
RELAY_AK = RELAY / "authorized_keys"
RELAY_PID = RELAY / "sshd.pid"
RELAY_LOG = RELAY / "sshd.log"

AUDIT = STATE / "audit.jsonl"
LAUNCH_AGENT = Path.home() / "Library" / "LaunchAgents" / "sh.csync.relay.plist"
LAUNCH_LABEL = "sh.csync.relay"


def host_dir(name):
    return DATA / name


def env_overrides():
    """The env pairs a forced command needs so it lands in the same roots as the CLI."""
    out = {}
    for var in ("CSYNC_HOME", "CSYNC_STATE", "CSYNC_DATA"):
        if env(var):
            out[var] = env(var)
    return out


def ensure_dirs():
    for d in (HOME, STATE, DATA, RELAY, INVITES):
        d.mkdir(parents=True, exist_ok=True)
    os.chmod(HOME, 0o700)
    os.chmod(RELAY, 0o700)
    os.chmod(INVITES, 0o700)
