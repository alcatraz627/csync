"""Recipes: reviewed shell files in the repo, streamed to a target, never stored there."""

import re
import shlex
import subprocess

from . import paths, tunnel
from .errors import CsyncError, REMOTE_FAILED, USAGE

RECIPES = paths.REPO / "recipes"
HEADER = re.compile(r"^#\s*(csync-recipe|os|summary):\s*(.*)$")


def parse_header(path):
    meta = {"name": path.stem, "os": "darwin,linux", "summary": ""}
    with open(path) as fh:
        for i, line in enumerate(fh):
            if i > 8:
                break
            m = HEADER.match(line.strip())
            if m:
                key = {"csync-recipe": "name"}.get(m.group(1), m.group(1))
                meta[key] = m.group(2).strip()
    return meta


def listing():
    out = []
    for p in sorted(RECIPES.glob("*.sh")):
        out.append(parse_header(p))
    return out


def path_for(name):
    p = RECIPES / f"{name}.sh"
    if not p.exists():
        raise CsyncError(USAGE, f"no recipe named {name!r}", fix="csync recipes")
    return p


def tree_is_clean(path):
    r = subprocess.run(["git", "-C", str(paths.REPO), "status", "--porcelain", "--", str(path)], capture_output=True, text=True)
    if r.returncode != 0:
        return False
    return not r.stdout.strip()


def run(h, name, args=(), dry_run=False, dev=False, json_mode=False):
    p = path_for(name)
    meta = parse_header(p)
    if dry_run:
        return {"recipe": meta, "script": p.read_text(), "dry_run": True}
    if h.get("os") and h["os"] not in meta["os"].split(","):
        raise CsyncError(USAGE, f"recipe {name} is for {meta['os']}, and {h['name']} runs {h['os']}")
    if not dev and not tree_is_clean(p):
        raise CsyncError(USAGE, f"recipes/{name}.sh is not a committed version", fix=f"commit it, or csync recipe {h['name']} {name} --dev")
    argv = tunnel.ssh_base(h) + ["bash", "-s", "--"] + [shlex.quote(a) for a in args]
    r = subprocess.run(argv, input=p.read_bytes(), capture_output=json_mode)
    if r.returncode == 255:
        raise CsyncError(REMOTE_FAILED, f"could not reach {h['name']}", fix=f"csync wait {h['name']}")
    return {"recipe": meta, "exit": r.returncode, "output": r.stdout.decode(errors="replace") if json_mode else None}
