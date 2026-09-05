"""Human output: the host row, tables, colour, notifications. JSON is assembled in cli.py."""

import os
import platform
import subprocess
import sys
import time

from .envcfg import env


def color_on():
    return sys.stdout.isatty() and not env("NO_COLOR") and env("TERM") != "dumb"


def c(code, s):
    return f"\x1b[{code}m{s}\x1b[0m" if color_on() else str(s)


def bold(s):
    return c("1", s)


def dim(s):
    return c("2", s)


def cyan(s):
    return c("36", s)


def green(s):
    return c("32", s)


def yellow(s):
    return c("33", s)


def red(s):
    return c("31", s)


def fmt_duration(seconds):
    seconds = int(seconds)
    if seconds < 0:
        return "0m"
    h, rem = divmod(seconds, 3600)
    m = rem // 60
    if h >= 48:
        return f"{h // 24}d"
    if h:
        return f"{h}h{m:02d}m"
    return f"{m}m"


def state_glyph(h):
    st = h.get("status")
    return {"online": "🟢", "offline": "🟡", "invited": "⏳", "gone": "🔴"}.get(st, "⚪")


def host_row(h, now=None):
    now = now or time.time()
    who = f"{h.get('user') or '?'}@{h.get('host') or '?'}"
    osv = " ".join(x for x in (h.get("os_label") or h.get("os"), h.get("osver")) if x)
    parts = [bold(h["name"]), who, osv or "os ?", h.get("route_used") or h.get("route") or "route ?"]
    st = h.get("status")
    if st == "online" and h.get("last_hello"):
        parts.append(green(f"online {fmt_duration(now - h['last_hello'])}"))
    elif st == "offline":
        parts.append(yellow("reconnecting"))
    elif st == "invited":
        parts.append(dim("waiting for the paste"))
    elif st == "gone":
        parts.append(red("gone"))
    if h.get("deadline"):
        parts.append(f"ends in {fmt_duration(h['deadline'] - now)}")
    elif h.get("expires") and st == "invited":
        parts.append(f"invite expires in {fmt_duration(h['expires'] - now)}")
    return f"{state_glyph(h)} " + dim(" · ").join(parts)


def table(rows, headers):
    if not rows:
        return ""
    widths = [len(h) for h in headers]
    for r in rows:
        for i, cell in enumerate(r):
            widths[i] = max(widths[i], len(str(cell)))
    line = "  ".join(bold(h.ljust(widths[i])) for i, h in enumerate(headers))
    out = [line]
    for r in rows:
        out.append("  ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(r)))
    return "\n".join(out)


def notify(title, message, enabled=True):
    if not enabled:
        return
    if platform.system() == "Darwin":
        script = f'display notification "{_esc(message)}" with title "{_esc(title)}"'
        subprocess.run(["osascript", "-e", script], capture_output=True)
    elif _which("notify-send"):
        subprocess.run(["notify-send", title, message], capture_output=True)


def _esc(s):
    return str(s).replace("\\", "\\\\").replace('"', '\\"')


def _which(name):
    for p in (env("PATH") or "").split(os.pathsep):
        if os.access(os.path.join(p, name), os.X_OK):
            return True
    return False


def set_title(text):
    if sys.stdout.isatty():
        sys.stdout.write(f"\x1b]0;{text}\x07")
        sys.stdout.flush()
