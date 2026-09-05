"""Console readiness: each check names what it looked at and the command that fixes it."""

import shutil
import sys

from . import funnel, paths, relay, state
from .errors import CsyncError


def checks(cfg, fix=False):
    rows = []

    def add(name, ok, detail, fixcmd=None, fixer=None):
        if not ok and fix and fixer:
            try:
                fixer()
                ok, detail = True, detail + " → fixed"
            except CsyncError as e:
                detail = f"{detail} → fix failed: {e.message}"
        rows.append({"check": name, "ok": bool(ok), "detail": detail, "fix": None if ok else fixcmd})

    add("python", sys.version_info >= (3, 12), sys.version.split()[0], "brew install python")
    for tool in ("ssh", "rsync", "ssh-keygen"):
        add(tool, bool(shutil.which(tool)), shutil.which(tool) or "missing", "xcode-select --install")
    add("console key", paths.CONSOLE_KEY.exists(), str(paths.CONSOLE_KEY), "csync init")
    add("relay config", paths.RELAY_CFG.exists(), str(paths.RELAY_CFG), "csync init", lambda: relay.write_config(cfg))
    add("relay host key", paths.RELAY_HOSTKEY.exists(), str(paths.RELAY_HOSTKEY), "csync init")
    port = cfg["relay_port"]
    if paths.LAUNCH_AGENT.exists():
        add("relay agent", relay.agent_loaded(), paths.LAUNCH_LABEL, f"launchctl bootstrap gui/$(id -u) {paths.LAUNCH_AGENT}", relay.install_agent)
    else:
        add("relay process", bool(relay.pid_alive()), f"pid {relay.pid_alive() or '-'} (no LaunchAgent)", "csync init", relay.start_daemon)
    add("relay listening", relay.listening(port), f"127.0.0.1:{port}", "csync doctor --fix")
    try:
        st = funnel.backend_state()
        add("tailscale", st == "Running", st, "tailscale up", funnel.up)
        if st == "Running" or fix:
            st = funnel.backend_state()
        if st == "Running":
            add("funnel capability", funnel.can_funnel(), "node may use Funnel", "enable Funnel for this node in the Tailscale admin console")
            ready = funnel.funnel_ready(cfg["funnel_port"], port)
            add("funnel publishing relay", ready, f"{funnel.dns_name()}:{cfg['funnel_port']} → localhost:{port}", f"tailscale funnel --bg --tls-terminated-tcp={cfg['funnel_port']} tcp://localhost:{port}", lambda: funnel.funnel_on(cfg["funnel_port"], port))
    except CsyncError as e:
        add("tailscale", False, e.message, e.fix)
    return rows
