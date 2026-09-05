"""Every environment read in csync goes through here, so the names are declared once."""

import os

KNOWN = {
    "CSYNC_HOME": "console config root, default ~/.config/csync",
    "CSYNC_STATE": "audit journal root, default ~/.local/state/csync",
    "CSYNC_DATA": "pulled files root, default ~/csync",
    "CSYNC_ACTOR": "force the actor: human or agent",
    "CLAUDECODE": "set by Claude Code; marks the actor as an agent",
    "SSH_ORIGINAL_COMMAND": "set by sshd for the relay's forced command",
    "NO_COLOR": "any value disables colour",
    "TERM": "dumb disables colour",
    "PATH": "where optional tools are looked up",
}


def env(name, default=None):
    if name not in KNOWN:
        raise KeyError(f"{name} is not a declared environment variable; add it to csync/envcfg.py")
    return os.environ.get(name, default)
