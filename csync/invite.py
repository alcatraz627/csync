"""Mint an invite: a key the target uses once, a relay line that lets it bind one port,
and the token that carries everything the bootstrap needs so it asks nothing."""

import base64
import re
import secrets
import socket
import subprocess
import time

from . import funnel, keys, paths, relay, state
from .errors import CsyncError, INVITE, PREREQ, USAGE

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,31}$")
TOKEN_ORDER = [
    "v", "id", "name", "route", "exp", "ttl", "lan", "funnel", "relay_user", "relay_hostkey",
    "port", "target_port", "console_pub", "console_name", "src", "gate_sha", "teardown_sha",
    "teardown_root_sha", "invite_key_b64",
]


def parse_duration(text):
    m = re.fullmatch(r"(\d+)([smhd]?)", str(text).strip())
    if not m:
        raise CsyncError(USAGE, f"bad duration {text!r}", fix="use 30m, 4h, 1d")
    n, unit = int(m.group(1)), m.group(2) or "s"
    return n * {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]


def build_token(fields):
    text = "".join(f"{k}={fields[k]}\n" for k in TOKEN_ORDER if k in fields)
    return base64.urlsafe_b64encode(text.encode()).decode()


def parse_token(token):
    text = base64.urlsafe_b64decode(token.encode() + b"=" * (-len(token) % 4)).decode()
    out = {}
    for line in text.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k] = v
    return out


def lan_ip():
    pinned = state.load_config().get("lan_ip")
    if pinned:
        return pinned
    for iface in ("en0", "en1", "en2"):
        r = subprocess.run(["ipconfig", "getifaddr", iface], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def source_base(override=None):
    """Where the target fetches bootstrap assets: a raw GitHub URL pinned to HEAD, or the
    local repo as file:// when the tree is not a pushed commit."""
    if override:
        return override, None
    cfg = state.load_config()
    if cfg.get("src"):
        return cfg["src"], None
    r = subprocess.run(["git", "-C", str(paths.REPO), "rev-parse", "HEAD"], capture_output=True, text=True)
    dirty = subprocess.run(["git", "-C", str(paths.REPO), "status", "--porcelain"], capture_output=True, text=True)
    if r.returncode == 0 and not dirty.stdout.strip():
        sha = r.stdout.strip()
        remote = subprocess.run(["git", "-C", str(paths.REPO), "remote", "get-url", "origin"], capture_output=True, text=True).stdout.strip()
        m = re.search(r"github\.com[:/]([^/]+)/([^/.]+)", remote)
        if m:
            return f"https://raw.githubusercontent.com/{m.group(1)}/{m.group(2)}/{sha}", None
    return f"file://{paths.REPO}", "source is the local working tree, so the paste only works on this machine or one that mounts it"


def allocate_port(cfg, hosts):
    lo, hi = cfg["port_range"]
    used = {h.get("port") for h in hosts.values() if h.get("status") != "gone"}
    for p in range(lo, hi + 1):
        if p not in used and not relay.listening(p):
            return p
    raise CsyncError(INVITE, "no free tunnel port left", fix="csync teardown <name> on a host you are done with")


def create(name, route="auto", ttl=None, expires=None, src=None, target_port=22, console_name=None):
    if not NAME_RE.match(name):
        raise CsyncError(USAGE, f"host name {name!r} must be 2-32 chars of a-z, 0-9, -", fix="csync invite rahul-mbp")
    if route not in ("auto", "lan", "funnel"):
        raise CsyncError(USAGE, f"route must be auto, lan, or funnel, not {route!r}")
    cfg = state.load_config()
    paths.ensure_dirs()
    if not paths.CONSOLE_KEY.exists() or not paths.RELAY_CFG.exists():
        raise CsyncError(PREREQ, "the console is not initialised", fix="csync init")
    if len(relay.open_invites()) >= 5:
        raise CsyncError(INVITE, "5 invites are already open", fix="csync ls   then   csync teardown <name>")
    with state.locked():
        hosts = state.load_hosts()
        existing = hosts.get(name)
        if existing and existing.get("status") != "gone":
            raise CsyncError(INVITE, f"{name!r} is already invited or connected", fix=f"csync teardown {name}   or pick another name")
        if existing and existing.get("status") == "gone":
            raise CsyncError(INVITE, f"{name!r} was used before; names are not reused until forgotten", fix=f"csync forget {name}")
        invite_id = secrets.token_hex(4)
        port = allocate_port(cfg, hosts)
        now = int(time.time())
        ttl_s = parse_duration(ttl or cfg["ttl"])
        exp_s = parse_duration(expires or cfg["expires"])
        key_path = keys.ensure_key(paths.INVITES / invite_id / "id_ed25519", f"csync-invite-{invite_id}")
        pub = keys.pubkey(key_path)
        relay.add_line(invite_id, relay.authorized_line(invite_id, port, pub))
        lan = f"{lan_ip()}:{cfg['relay_port']}"
        fun = ""
        if route in ("auto", "funnel"):
            try:
                if funnel.backend_state() == "Running" and funnel.funnel_ready(cfg["funnel_port"], cfg["relay_port"]):
                    fun = f"{funnel.dns_name()}:{cfg['funnel_port']}"
            except CsyncError:
                fun = ""
        if route == "funnel" and not fun:
            relay.remove_line(invite_id)
            raise CsyncError(PREREQ, "Funnel is not publishing the relay", fix="csync doctor --fix")
        base, warning = source_base(src)
        fields = {
            "v": 1,
            "id": invite_id,
            "name": name,
            "route": route,
            "exp": now + exp_s,
            "ttl": ttl_s,
            "lan": lan,
            "funnel": fun,
            "relay_user": relay.getpass.getuser(),
            "relay_hostkey": keys.pubkey(paths.RELAY_HOSTKEY),
            "port": port,
            "target_port": target_port,
            "console_pub": keys.pubkey(paths.CONSOLE_KEY),
            "console_name": console_name or cfg.get("console_name") or socket.gethostname(),
            "src": base,
            "gate_sha": keys.sha256_file(paths.REPO / "target" / "gate.sh"),
            "teardown_sha": keys.sha256_file(paths.REPO / "target" / "teardown.sh"),
            "teardown_root_sha": keys.sha256_file(paths.REPO / "target" / "teardown-root.sh"),
            "invite_key_b64": base64.b64encode(keys.read_private(key_path).encode()).decode(),
        }
        token = build_token(fields)
        hosts[name] = {
            "name": name,
            "id": invite_id,
            "status": "invited",
            "route": route,
            "port": port,
            "target_port": target_port,
            "created": now,
            "expires": now + exp_s,
            "ttl": ttl_s,
            "deadline": None,
            "lan": lan,
            "funnel": fun,
            "src": base,
        }
        state.save_hosts(hosts)
    paste = f"bash <(curl -fsSL {base}/bootstrap.sh) {token}"
    return {"name": name, "id": invite_id, "port": port, "paste": paste, "token": token, "expires": now + exp_s, "lan": lan, "funnel": fun, "warning": warning}
