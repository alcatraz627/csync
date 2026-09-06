#!/bin/bash
# Shows a notification on the target's screen.
text="${1:-}"
[ -n "$text" ] || { echo "nothing to say" >&2; exit 2; }
os="$(uname -s)"
if [ -n "${PREFIX:-}" ] && [ -d "$PREFIX/bin" ]; then
  case "$PREFIX" in *com.termux*) os=Android ;; esac
fi
esc="$(printf '%s' "$text" | sed 's/\\/\\\\/g; s/"/\\"/g')"
if [ "$os" = "Darwin" ]; then
  osascript -e "display notification \"$esc\" with title \"csync\""
elif [ "$os" = "Android" ]; then
  command -v termux-notification >/dev/null 2>&1 || { echo "termux-api is not installed" >&2; exit 1; }
  termux-notification --title csync --content "$text"
elif command -v notify-send >/dev/null 2>&1; then
  notify-send "csync" "$text"
else
  echo "no notification tool" >&2; exit 1
fi
