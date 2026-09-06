#!/bin/bash
# csync teardown, user half: removes the console's key, writes the receipt, asks the root
# half to restore Remote Login and the sshd drop-in, reports what is left, then stops the
# tunnel and deletes itself. The friend can run this at any time to end the session.

CS="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=/dev/null
. "$CS/state.env"
trap '' HUP PIPE

MODE=normal
RECEIPT=1
for a in "$@"; do
  case "$a" in
    --no-receipt) RECEIPT=0 ;;
    --ttl) MODE=ttl ;;
    --from-root) MODE=fromroot ;;
  esac
done

say() { printf '%s\n' "$*"; }
now_h() { date '+%Y-%m-%d %H:%M:%S'; }

AK="$h/.ssh/authorized_keys"
if [ -e "$AK" ]; then
  grep -v "# csync:$id\$" "$AK" > "$AK.csync-tmp" 2>/dev/null
  mv -f "$AK.csync-tmp" "$AK"
  chmod 600 "$AK"
  if [ "$ak_existed" = "0" ] && [ ! -s "$AK" ]; then
    rm -f "$AK"
  fi
  say "removed the console's key"
fi

if [ "${os:-}" = android ]; then
  termux-wake-unlock >/dev/null 2>&1 && say "released the wake-lock"
  [ -n "${boot_script:-}" ] && rm -f "$boot_script" && say "removed the boot script"
  pkill -x sshd >/dev/null 2>&1 && say "stopped the Termux sshd"
fi

ROOT_NOTE=""
if [ "${os:-}" = android ]; then
  ROOT_NOTE="Android: nothing outside Termux was ever changed, so nothing needed restoring"
elif [ "$no_root" = "1" ]; then
  ROOT_NOTE="root steps were skipped at setup, nothing to restore"
elif [ "$MODE" = "fromroot" ]; then
  ROOT_NOTE="root half already running"
else
  touch "$CS/teardown.requested"
  i=0
  while [ $i -lt 45 ] && [ ! -e "$CS/root.done" ]; do
    sleep 1
    i=$((i + 1))
  done
  if [ -e "$CS/root.done" ]; then
    ROOT_NOTE="Remote Login and sshd settings restored"
  else
    ROOT_NOTE="root half did not report within 45 s"
  fi
fi

RES=0
residue() { say "RESIDUE: $1"; RES=1; }
grep -q "# csync:$id\$" "$AK" 2>/dev/null && residue "authorized_keys still carries the csync line"
if [ "${os:-}" = android ]; then
  [ -n "${boot_script:-}" ] && [ -e "${boot_script:-}" ] && residue "boot script still at $boot_script"
elif [ "$no_root" != "1" ]; then
  [ -e /etc/ssh/sshd_config.d/000-csync.conf ] && residue "/etc/ssh/sshd_config.d/000-csync.conf still present"
  if [ "$MODE" != "fromroot" ] && [ ! -e "$CS/root.done" ]; then
    residue "root cleanup did not report back, Remote Login may still be on"
  fi
  [ "$os" = "darwin" ] && [ -e /Library/LaunchDaemons/sh.csync.ttl.plist ] && residue "TTL daemon plist still present"
fi

if [ $RECEIPT -eq 1 ]; then
  dest="$h"
  [ -d "$h/Desktop" ] && dest="$h/Desktop"
  R="$dest/csync-receipt-$(date +%Y%m%d-%H%M).txt"
  {
    say "csync session receipt"
    say "====================="
    say "session   $name ($id)"
    say "console   $console_name"
    say "started   $created_h"
    say "ended     $(now_h)"
    say "route     $route"
    say ""
    say "What was changed on this machine at setup"
    say "-----------------------------------------"
    [ -f "$CS/changes.log" ] && cat "$CS/changes.log"
    say ""
    say "Every command the console ran here"
    say "----------------------------------"
    [ -f "$CS/session.log" ] && cat "$CS/session.log"
    for f in "$CS"/shell-*.log; do
      [ -e "$f" ] && say "interactive shell recorded: $(basename "$f") ($(wc -c < "$f" | tr -d ' ') bytes)"
    done
    say ""
    say "Cleanup"
    say "-------"
    say "console key removed from ~/.ssh/authorized_keys"
    say "$ROOT_NOTE"
    if [ $RES -eq 0 ]; then say "nothing else left behind"; else say "some items were left, see above"; fi
  } > "$R"
  say "receipt at $R"
fi

if [ "$os" = "darwin" ]; then
  osascript -e 'display notification "Session ended. Everything csync set up has been removed." with title "csync"' >/dev/null 2>&1
elif [ "$os" = android ]; then
  termux-notification --title csync --content "Session ended. Everything csync set up has been removed." >/dev/null 2>&1
elif command -v notify-send >/dev/null 2>&1; then
  notify-send "csync" "Session ended. Everything csync set up has been removed." >/dev/null 2>&1
fi

say "RESIDUE-CHECK: $RES"
say "DONE"
sleep 1

stop_tunnel() {
  if [ -n "${tunnel_pid:-}" ]; then
    kill "$tunnel_pid" 2>/dev/null
    pkill -f "$CS/invite_key" 2>/dev/null
  fi
  if [ "${supervisor:-}" = "launchd" ]; then
    launchctl bootout "gui/$(id -u)/sh.csync.tunnel" 2>/dev/null
    rm -f "$h/Library/LaunchAgents/sh.csync.tunnel.plist"
  elif [ "${supervisor:-}" = "systemd" ]; then
    systemctl --user stop csync-tunnel.service 2>/dev/null
  elif [ "${supervisor:-}" = "termux" ]; then
    pkill -f "$CS/tunnel.sh" 2>/dev/null
  fi
}

( sleep 1; stop_tunnel ) >/dev/null 2>&1 &
rm -rf "$CS"
exit 0
