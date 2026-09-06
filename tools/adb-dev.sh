#!/bin/bash
# The development channel to a phone over ADB, so csync can be built and tested against
# a real Android without asking a human for anything after the first setup.
#
# This is NOT the csync ADB mode. It is scaffolding: adb carries a port forward so the
# Mac can reach the phone's Termux sshd at localhost, and everything after that is
# ordinary ssh. The phone side is three lines, pasted once.
#
#   tools/adb-dev.sh keygen      make the dev keypair on this Mac
#   tools/adb-dev.sh phone-lines print the three lines to paste into Termux
#   tools/adb-dev.sh connect     push the key, forward the port, verify ssh
#   tools/adb-dev.sh sh          shell on the phone
#   tools/adb-dev.sh run <cmd>   one command on the phone
#   tools/adb-dev.sh status      what adb and the forward think right now
#   tools/adb-dev.sh off         drop the forward (the phone keeps running)

set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
KEY="${CSYNC_DEV_KEY:-$HOME/.config/csync/dev/id_ed25519}"
PORT="${CSYNC_DEV_PORT:-8022}"
SDCARD=/sdcard/Download
PUBNAME=csync-dev.pub

say()  { printf '%s\n' "$*"; }
die()  { printf 'adb-dev: %s\n' "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

have adb || die "adb is missing: brew install --cask android-platform-tools"

keygen() {
  mkdir -p "$(dirname "$KEY")"
  chmod 700 "$(dirname "$KEY")"
  [ -f "$KEY" ] && { say "dev key already at $KEY"; return 0; }
  ssh-keygen -q -t ed25519 -N '' -C csync-dev -f "$KEY"
  say "made $KEY"
}

devices() { adb devices | sed -n '2,$p' | grep -c 'device$'; }

phone_lines() {
  keygen >/dev/null
  cat <<EOF

Paste these three lines into Termux on the phone, once:

  pkg install -y openssh rsync termux-api
  mkdir -p ~/.ssh && cat $SDCARD/$PUBNAME >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys
  sshd

The first installs what csync needs. The second trusts this Mac's dev key, which
'connect' will have already pushed to $SDCARD. The third starts Termux's ssh
server on port $PORT. Nothing here needs root.

EOF
}

connect() {
  keygen >/dev/null
  [ "$(devices)" -ge 1 ] || die "no device in 'adb devices'. Plug in USB and accept the debugging prompt, or run: adb pair <host:port>"
  adb push "$KEY.pub" "$SDCARD/$PUBNAME" >/dev/null || die "could not push the key; is USB file access allowed?"
  say "pushed the dev key to $SDCARD/$PUBNAME"
  adb forward --remove tcp:$PORT >/dev/null 2>&1
  adb forward tcp:$PORT tcp:$PORT >/dev/null || die "adb forward failed"
  say "forwarded localhost:$PORT to the phone's $PORT"
  if ssh_ok; then
    say "ssh works: $(ssh_run 'getprop ro.product.model' 2>/dev/null)"
    say "→ tools/adb-dev.sh sh   or   tools/adb-dev.sh run '<cmd>'"
  else
    say "ssh not answering yet. If you have not pasted the three lines into Termux, do that now:"
    phone_lines
    say "then re-run: tools/adb-dev.sh connect"
    return 1
  fi
}

ssh_args() {
  printf '%s\n' -i "$KEY" -p "$PORT" -o IdentitiesOnly=yes -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -o ConnectTimeout=8
}

ssh_run() {
  # shellcheck disable=SC2046
  ssh $(ssh_args) -o BatchMode=yes localhost "$@"
}

ssh_ok() { ssh_run true >/dev/null 2>&1; }

case "${1:-connect}" in
  keygen)      keygen ;;
  phone-lines) phone_lines ;;
  connect)     connect ;;
  sh)          shift; exec ssh $(ssh_args) -t localhost ;;
  run)         shift; [ $# -gt 0 ] || die "run needs a command"; ssh_run "$@" ;;
  status)
    say "adb devices:"; adb devices | sed -n '2,$p' | sed 's/^/  /'
    say "forwards:";    adb forward --list | sed 's/^/  /'
    if ssh_ok; then say "ssh: up ($(ssh_run 'echo $PREFIX' 2>/dev/null))"; else say "ssh: not answering on localhost:$PORT"; fi ;;
  off)
    adb forward --remove tcp:$PORT >/dev/null 2>&1
    say "forward dropped; Termux and its sshd are untouched" ;;
  *) sed -n '2,20p' "$0" ;;
esac
