#!/bin/bash
# csync gate: every SSH session the console opens on this laptop passes through here first.
# It writes the command down, refuses the handful that would wreck the machine, then runs it.
# It sits in the authorized_keys line, so it holds even when the console is bypassed.
# The bare command "true" is the console's liveness probe and is not written down.

CS="$(cd "$(dirname "$0")" && pwd)"
LOG="$CS/session.log"
cmd="${SSH_ORIGINAL_COMMAND:-}"
ts="$(date '+%Y-%m-%d %H:%M:%S')"
force=0
case "$cmd" in
  "CSYNC_FORCE=1 "*) force=1; cmd="${cmd#CSYNC_FORCE=1 }" ;;
esac

if [ "$cmd" = "true" ]; then
  exec /usr/bin/true
elif [ $force -eq 1 ]; then
  printf '%s\t%s\t[force]\n' "$ts" "$cmd" >> "$LOG"
else
  printf '%s\t%s\n' "$ts" "${cmd:-<interactive shell>}" >> "$LOG"
fi

refuse() {
  printf '%s\trefused: %s\n' "$ts" "$1" >> "$LOG"
  printf 'csync gate: refused: %s\n' "$1" >&2
  exit 126
}

if [ $force -eq 0 ] && [ -n "$cmd" ]; then
  printf '%s\n' "$cmd" | grep -Eq '(^|[;&|][[:space:]]*)(sudo[[:space:]]+)?rm[[:space:]]+(-[a-zA-Z]*r[a-zA-Z]*[[:space:]]+)+(-[a-zA-Z]+[[:space:]]+)*(/|~|\$HOME|"\$HOME"|\*|~/\*|/\*)([[:space:]]|$)' && refuse "rm -r aimed at / or ~"
  printf '%s\n' "$cmd" | grep -Eq '(^|[;&|][[:space:]]*)(sudo[[:space:]]+)?mkfs' && refuse "mkfs"
  printf '%s\n' "$cmd" | grep -Eq '(^|[;&|][[:space:]]*)(sudo[[:space:]]+)?diskutil[[:space:]]+(erase|reformat|partition|apfs[[:space:]]+delete)' && refuse "diskutil erase"
  printf '%s\n' "$cmd" | grep -Eq '(^|[;&|][[:space:]]*)(sudo[[:space:]]+)?dd[[:space:]]+.*of=/dev/' && refuse "dd onto a device"
  printf '%s\n' "$cmd" | grep -Eq '(^|[;&|][[:space:]]*)(sudo[[:space:]]+)?(shutdown|reboot|halt)([[:space:]]|$)' && refuse "shutdown or reboot"
  printf '%s\n' "$cmd" | grep -Eq 'launchctl[[:space:]]+bootout[[:space:]]+system' && refuse "launchctl bootout system"
  printf '%s\n' "$cmd" | grep -Eq '(>[[:space:]]*|rm[[:space:]]+.*[[:space:]])/System/' && refuse "writes under /System"
fi

case "$cmd" in
  "")
    stamp="$(date +%Y%m%d-%H%M%S)"
    if [ "$(uname -s)" = "Darwin" ]; then
      exec /usr/bin/script -q "$CS/shell-$stamp.log" "${SHELL:-/bin/zsh}" -l
    elif command -v script >/dev/null 2>&1; then
      exec script -q -c "${SHELL:-/bin/bash} -l" "$CS/shell-$stamp.log"
    else
      # Termux ships no script(1) unless util-linux is installed; say so rather
      # than pretending the shell was recorded.
      printf '%s\tinteractive shell NOT recorded (no script command)\n' "$ts" >> "$LOG"
      exec "${SHELL:-sh}" -l
    fi
    ;;
  sftp|internal-sftp)
    for s in "${PREFIX:-/usr}/libexec/sftp-server" /usr/libexec/sftp-server /usr/lib/openssh/sftp-server /usr/libexec/openssh/sftp-server /usr/lib/ssh/sftp-server; do
      [ -x "$s" ] && exec "$s"
    done
    refuse "no sftp server on this machine"
    ;;
  *)
    exec "${SHELL:-sh}" -c "$cmd"
    ;;
esac
