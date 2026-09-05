#!/bin/bash
# csync teardown, root half. Runs every 15 s from a root launch unit that the bootstrap
# armed. It does nothing until the session deadline passes or the user half asks; then it
# removes the sshd drop-in, puts Remote Login back the way it was, and removes itself.
# This is the only thing on the machine that runs as root after setup, and it can only do this.

ID="${1:-}"
[ -n "$ID" ] || exit 0
if [ "$(uname -s)" = "Darwin" ]; then
  RD="/Library/Application Support/csync/$ID"
else
  RD="/etc/csync/$ID"
fi

if [ ! -f "$RD/state.env" ]; then
  if [ "$(uname -s)" = "Darwin" ]; then
    rm -f /Library/LaunchDaemons/sh.csync.ttl.plist
    exec launchctl bootout system/sh.csync.ttl
  fi
  exit 0
fi
# shellcheck source=/dev/null
. "$RD/state.env"

now=$(date +%s)
if [ ! -e "$cs/teardown.requested" ] && [ "$now" -lt "$deadline" ]; then
  exit 0
fi

if [ "$dropin_existed" = "0" ]; then
  rm -f /etc/ssh/sshd_config.d/000-csync.conf
fi

if [ "$os" = "darwin" ]; then
  if [ "$rl_before" != "on" ]; then
    systemsetup -setremotelogin -f off >/dev/null 2>&1 || {
      launchctl bootout system/com.openssh.sshd >/dev/null 2>&1
      launchctl disable system/com.openssh.sshd >/dev/null 2>&1
    }
  fi
else
  if [ "$ssh_active_before" != "active" ]; then
    systemctl stop ssh 2>/dev/null || systemctl stop sshd 2>/dev/null
  else
    systemctl reload ssh 2>/dev/null || systemctl reload sshd 2>/dev/null
  fi
  if [ "$ssh_enabled_before" != "enabled" ]; then
    systemctl disable ssh 2>/dev/null || systemctl disable sshd 2>/dev/null
  fi
fi

if [ ! -e "$cs/teardown.requested" ] && [ -f "$cs/teardown.sh" ]; then
  su "$user_name" -c "/bin/bash '$cs/teardown.sh' --from-root --ttl" >/dev/null 2>&1
fi

touch "$cs/root.done" 2>/dev/null
chown "$user_name" "$cs/root.done" 2>/dev/null

rm -rf "$RD"
if [ "$os" = "darwin" ]; then
  rm -f /Library/LaunchDaemons/sh.csync.ttl.plist
  exec launchctl bootout system/sh.csync.ttl
else
  systemctl stop "csync-ttl-$ID.timer" 2>/dev/null
  exit 0
fi
