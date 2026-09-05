#!/bin/bash
# Opens a URL, an app by name, or a path on the target's screen.
t="${1:-}"
[ -n "$t" ] || { echo "nothing to open" >&2; exit 2; }
if [ "$(uname -s)" = "Darwin" ]; then
  case "$t" in
    http://*|https://*|file://*|/*|~*) open "$t" ;;
    *) open -a "$t" 2>/dev/null || open "$t" ;;
  esac
else
  export DISPLAY="${DISPLAY:-:0}"
  xdg-open "$t" >/dev/null 2>&1 &
fi
