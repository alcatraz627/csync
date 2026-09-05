"""ed25519 keys via ssh-keygen: the console key, the relay host key, one key per invite."""

import hashlib
import os
import subprocess
from pathlib import Path

from .errors import CsyncError, PREREQ


def ensure_key(path, comment):
    path = Path(path)
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", comment, "-f", str(path)],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        raise CsyncError(PREREQ, f"ssh-keygen failed: {r.stderr.strip()}", fix="xcode-select --install")
    os.chmod(path, 0o600)
    return path


def pubkey(path):
    """The public line without its comment: 'ssh-ed25519 AAAA...'."""
    text = Path(str(path) + ".pub").read_text().strip()
    parts = text.split()
    return " ".join(parts[:2])


def read_private(path):
    return Path(path).read_text()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
