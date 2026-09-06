#!/bin/bash
# Opens a URL, an app by name, or a path on the target's screen.
t="${1:-}"
[ -n "$t" ] || { echo "nothing to open" >&2; exit 2; }
os="$(uname -s)"
if [ -n "${PREFIX:-}" ] && [ -d "$PREFIX/bin" ]; then
  case "$PREFIX" in *com.termux*) os=Android ;; esac
fi
if [ "$os" = "Darwin" ]; then
  case "$t" in
    http://*|https://*|file://*|/*|~*) open "$t" ;;
    *) open -a "$t" 2>/dev/null || open "$t" ;;
  esac
elif [ "$os" = "Android" ]; then
  case "$t" in
    http://*|https://*)
      if command -v termux-open-url >/dev/null 2>&1; then termux-open-url "$t"
      else am start -a android.intent.action.VIEW -d "$t" >/dev/null; fi ;;
    *.*.*)  am start -n "$t" >/dev/null 2>&1 || am start -a android.intent.action.MAIN -p "$t" >/dev/null ;;
    *)      command -v termux-open >/dev/null 2>&1 && termux-open "$t" || am start -a android.intent.action.VIEW -d "file://$t" >/dev/null ;;
  esac
else
  export DISPLAY="${DISPLAY:-:0}"
  xdg-open "$t" >/dev/null 2>&1 &
fi
