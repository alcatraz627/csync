#!/bin/bash
# Shows a notification on the target's screen.
text="${1:-}"
[ -n "$text" ] || { echo "nothing to say" >&2; exit 2; }
esc="$(printf '%s' "$text" | sed 's/\\/\\\\/g; s/"/\\"/g')"
if [ "$(uname -s)" = "Darwin" ]; then
  osascript -e "display notification \"$esc\" with title \"csync\""
elif command -v notify-send >/dev/null 2>&1; then
  notify-send "csync" "$text"
else
  echo "no notification tool" >&2; exit 1
fi
