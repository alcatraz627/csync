#!/bin/bash
# Screenshot of display N to a temp file. Prints its size, then the path as the last line.
display="${1:-1}"
f="$(mktemp "${TMPDIR:-/tmp}/csync-shot.XXXXXX")"
mv -f "$f" "$f.png"
f="$f.png"
if [ "$(uname -s)" = "Darwin" ]; then
  screencapture -x -D "$display" "$f" 2>/dev/null || screencapture -x "$f"
else
  export DISPLAY="${DISPLAY:-:0}"
  export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"
  export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
  export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
  if command -v grim >/dev/null 2>&1; then grim "$f"
  elif command -v gnome-screenshot >/dev/null 2>&1; then gnome-screenshot -f "$f"
  elif command -v import >/dev/null 2>&1; then import -window root "$f"
  elif command -v scrot >/dev/null 2>&1; then scrot "$f"
  else echo "no screenshot tool (grim, gnome-screenshot, import, scrot)" >&2; exit 1
  fi
fi
[ -s "$f" ] || { echo "capture produced no file" >&2; exit 1; }
printf 'bytes=%s\n' "$(wc -c < "$f" | tr -d ' ')"
printf '%s\n' "$f"
