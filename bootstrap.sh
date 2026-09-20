#!/bin/bash
# csync bootstrap: makes this laptop reachable by one console over a tunnel this laptop opens
# itself, writes down every change it makes, and installs the script that undoes them.
#
#   bash <(curl -fsSL <src>/bootstrap.sh) <token>
#
# Needs bash 3.2, curl, ssh, and openssl (only for the Funnel route). Asks for your password
# once, on macOS and Linux alike, to turn on the SSH service and arm the timed cleanup.

set -u

TOKEN=""
NO_ROOT=0
NO_LAUNCHD=0
DEV_HOME=""
DEV_HOSTKEY=""
while [ $# -gt 0 ]; do
  case "$1" in
    --no-root) NO_ROOT=1 ;;
    --no-launchd) NO_LAUNCHD=1 ;;
    --home) shift; DEV_HOME="$1" ;;
    --hostkey) shift; DEV_HOSTKEY="$1" ;;
    -h|--help) sed -n '2,8p' "$0" 2>/dev/null; exit 0 ;;
    *) TOKEN="$1" ;;
  esac
  shift
done

say()  { printf '%s\n' "$*"; }
step() { printf '\033[1m→\033[0m %s\n' "$*"; }
die()  { printf 'csync: %s\n' "$*" >&2; exit 1; }

[ -n "$TOKEN" ] || die "usage: bash <(curl -fsSL <src>/bootstrap.sh) <token>"

TMP="$(mktemp -d "${TMPDIR:-/tmp}/csync-boot.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

b64d() {
  # macOS/BSD decode is -D, GNU is --decode; bare -d is ambiguous and on some
  # macOS builds succeeds with WRONG output, so try the unambiguous ones first.
  base64 -D < "$1" > "$2" 2>/dev/null && [ -s "$2" ] && return 0
  base64 --decode < "$1" > "$2" 2>/dev/null && [ -s "$2" ] && return 0
  base64 -d < "$1" > "$2" 2>/dev/null && [ -s "$2" ] && return 0
  openssl base64 -d -A < "$1" > "$2" 2>/dev/null && [ -s "$2" ]
}

printf '%s' "$TOKEN" | tr -- '-_' '+/' > "$TMP/tok.b64"
pad=$(( (4 - $(wc -c < "$TMP/tok.b64") % 4) % 4 ))
[ $pad -gt 0 ] && printf '%*s' "$pad" '' | tr ' ' '=' >> "$TMP/tok.b64"
b64d "$TMP/tok.b64" "$TMP/tok.txt" || die "that token does not decode"
tok() { sed -n "s/^$1=//p" "$TMP/tok.txt" | head -n 1; }

V="$(tok v)"; [ "$V" = "1" ] || die "token version $V is not one this script reads"
ID="$(tok id)"; NAME="$(tok name)"; ROUTE="$(tok route)"; EXP="$(tok exp)"; TTL="$(tok ttl)"
LAN="$(tok lan)"; FUNNEL="$(tok funnel)"; RELAY_USER="$(tok relay_user)"; RELAY_HOSTKEY="$(tok relay_hostkey)"
PORT="$(tok port)"; TARGET_PORT="$(tok target_port)"; CONSOLE_PUB="$(tok console_pub)"
CONSOLE_NAME="$(tok console_name)"; SRC="$(tok src)"
GATE_SHA="$(tok gate_sha)"; TEARDOWN_SHA="$(tok teardown_sha)"; TEARDOWN_ROOT_SHA="$(tok teardown_root_sha)"
INVITE_KEY_B64="$(tok invite_key_b64)"
[ -n "$ID" ] && [ -n "$PORT" ] && [ -n "$CONSOLE_PUB" ] && [ -n "$INVITE_KEY_B64" ] || die "token is missing fields"

NOW=$(date +%s)
[ "$NOW" -lt "$EXP" ] || die "this invite expired; ask for a new line"

OS="$(uname -s)"
case "$OS" in
  Darwin) OS=darwin; OSVER="$(sw_vers -productVersion 2>/dev/null)" ;;
  Linux)
    if [ -n "${PREFIX:-}" ] && [ -d "${PREFIX}/bin" ] && case "${PREFIX}" in *com.termux*) true ;; *) false ;; esac; then
      OS=android; OSVER="$(getprop ro.build.version.release 2>/dev/null)"
    else
      OS=linux; OSVER="$( . /etc/os-release 2>/dev/null; printf '%s %s' "${ID:-linux}" "${VERSION_ID:-}")"
    fi ;;
  *) die "this runs on macOS, Linux, and Android under Termux; Windows support is planned, not built" ;;
esac
ARCH="$(uname -m)"

# Termux has no /bin/bash and no privileged anything: resolve the interpreter and
# force the no-root path before any step assumes a system service exists.
BASH_BIN="$(command -v bash)"
[ -n "$BASH_BIN" ] || die "bash is missing"
if [ "$OS" = android ]; then
  NO_ROOT=1
  NO_LAUNCHD=1
  TARGET_PORT=8022
  ETC_SSH="$PREFIX/etc/ssh"
  command -v pkg >/dev/null 2>&1 || die "this is Termux-shaped but has no pkg; install Termux from F-Droid, not the Play Store"
else
  ETC_SSH="/etc/ssh"
fi

for t in curl ssh; do command -v "$t" >/dev/null 2>&1 || die "$t is missing"; done

H="${DEV_HOME:-$HOME}"
CS="$H/.csync"
[ -e "$CS" ] && die "a csync session already exists here; run $CS/teardown.sh first"
mkdir -p "$CS"
chmod 700 "$CS"
ME="$(id -un)"
CREATED_H="$(date '+%Y-%m-%d %H:%M:%S')"
DEADLINE=$(( NOW + TTL ))

st() { printf "%s='%s'\n" "$1" "$(printf '%s' "$2" | sed "s/'/'\\\\''/g")" >> "$CS/state.env"; }
changed() { printf '%s  %s\n' "$(date '+%H:%M:%S')" "$*" >> "$CS/changes.log"; }

st v 1; st id "$ID"; st name "$NAME"; st h "$H"; st cs "$CS"; st os "$OS"; st osver "$OSVER"
st user_name "$ME"; st uid "$(id -u)"; st route "$ROUTE"; st port "$PORT"; st target_port "$TARGET_PORT"
st console_name "$CONSOLE_NAME"; st created "$NOW"; st created_h "$CREATED_H"; st deadline "$DEADLINE"
st no_root "$NO_ROOT"; st bash_bin "$BASH_BIN"; st etc_ssh "$ETC_SSH"

step "csync $NAME: setting this machine up for $CONSOLE_NAME (until $(date -r "$DEADLINE" '+%H:%M' 2>/dev/null || date -d "@$DEADLINE" '+%H:%M'))"

sha256() {
  if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | awk '{print $1}'; else sha256sum "$1" | awk '{print $1}'; fi
}
fetch() {
  curl -fsSL "$SRC/$1" -o "$2" || die "could not fetch $1 from $SRC"
  got="$(sha256 "$2")"
  [ "$got" = "$3" ] || die "$1 does not match the hash in the invite (got $got)"
  chmod 700 "$2"
}
fetch target/gate.sh "$CS/gate.sh" "$GATE_SHA"
fetch target/teardown.sh "$CS/teardown.sh" "$TEARDOWN_SHA"
fetch target/teardown-root.sh "$CS/teardown-root.sh" "$TEARDOWN_ROOT_SHA"
say "  fetched gate, teardown, and root teardown; hashes match the invite"

printf '%s' "$INVITE_KEY_B64" > "$TMP/ik.b64"
b64d "$TMP/ik.b64" "$CS/invite_key" || die "invite key does not decode"
chmod 600 "$CS/invite_key"
# The private half must SIGN, not merely parse. If the decode mangled it, retry
# with openssl (deterministic on LibreSSL and OpenSSL) before giving up.
if ! ssh-keygen -y -f "$CS/invite_key" >/dev/null 2>&1; then
  openssl base64 -d -A < "$TMP/ik.b64" > "$CS/invite_key" 2>/dev/null
  chmod 600 "$CS/invite_key"
  ssh-keygen -y -f "$CS/invite_key" >/dev/null 2>&1 || die "invite key did not install cleanly (base64 decode produced a bad key); this is a csync bug, do not retry the paste, tell the operator"
fi
printf 'csync-relay %s\n' "$RELAY_HOSTKEY" > "$CS/known_hosts"
chmod 600 "$CS/known_hosts"

AK="$H/.ssh/authorized_keys"
AK_EXISTED=0
if [ -e "$AK" ]; then AK_EXISTED=1; cp -f "$AK" "$CS/authorized_keys.before"; fi
mkdir -p "$H/.ssh"
chmod 700 "$H/.ssh"
printf 'restrict,pty,from="127.0.0.1,::1",command="%s/gate.sh" %s # csync:%s\n' "$CS" "$CONSOLE_PUB" "$ID" >> "$AK"
chmod 600 "$AK"
st ak_existed "$AK_EXISTED"
changed "added one line to ~/.ssh/authorized_keys (console key, loopback only, behind the gate)"
say "  console key installed behind the gate"

probe() {
  if command -v nc >/dev/null 2>&1; then
    nc -z -w 2 "$1" "$2" >/dev/null 2>&1
  else
    ( exec 3<>"/dev/tcp/$1/$2" ) 2>/dev/null
  fi
}
LAN_HOST="${LAN%:*}"; LAN_PORT="${LAN##*:}"
FUN_HOST="${FUNNEL%:*}"; FUN_PORT="${FUNNEL##*:}"
USE=""
case "$ROUTE" in
  lan) probe "$LAN_HOST" "$LAN_PORT" && USE=lan ;;
  funnel) [ -n "$FUNNEL" ] && USE=funnel ;;
  auto)
    if probe "$LAN_HOST" "$LAN_PORT"; then USE=lan; elif [ -n "$FUNNEL" ]; then USE=funnel; fi ;;
esac
[ -n "$USE" ] || die "cannot reach the console: LAN $LAN did not answer and no Funnel address was offered"
[ "$USE" = "funnel" ] && { command -v openssl >/dev/null 2>&1 || die "openssl is needed for the Funnel route"; }
st route_used "$USE"
say "  route: $USE"

if [ "$OS" = android ]; then
  step "installing openssh, rsync and termux-api (no root, nothing outside Termux)"
  pkg install -y openssh rsync termux-api >/dev/null 2>&1 || die "pkg install failed; open Termux and run: pkg update"
  changed "installed openssh, rsync, termux-api inside Termux"
  [ -f "$ETC_SSH/ssh_host_ed25519_key" ] || ssh-keygen -A >/dev/null 2>&1
  if pgrep -x sshd >/dev/null 2>&1; then
    st sshd_was_running 1
    say "  Termux sshd was already running on 8022, leaving it alone"
  else
    st sshd_was_running 0
    sshd
    changed "started Termux sshd on port 8022 (no root, keys only)"
    say "  Termux sshd listening on 8022"
  fi
fi

HK=""
if [ -n "$DEV_HOSTKEY" ]; then
  HK="$(awk '{print $1":"$2}' "$DEV_HOSTKEY.pub" 2>/dev/null)"
else
  for f in "$ETC_SSH/ssh_host_ed25519_key.pub" "$ETC_SSH/ssh_host_ecdsa_key.pub" "$ETC_SSH/ssh_host_rsa_key.pub"; do
    [ -r "$f" ] && { HK="$(awk '{print $1":"$2}' "$f")"; break; }
  done
fi

if [ "$OS" = android ]; then
  HOSTLABEL="$(getprop ro.product.model 2>/dev/null | tr ' ' '-')"
fi
[ -n "${HOSTLABEL:-}" ] || HOSTLABEL="$(hostname -s 2>/dev/null || hostname 2>/dev/null || echo device)"

HELLO="hello v=1 id=$ID user=$ME host=$HOSTLABEL os=$OS osver=$(printf '%s' "$OSVER" | tr ' ' '_') arch=$ARCH route=$USE sshd_hostkey=$HK deadline=$DEADLINE cs=$CS"
if [ "$USE" = "lan" ]; then
  DEST="$RELAY_USER@$LAN_HOST"; PORTOPT="-p $LAN_PORT"; PROXY=""
else
  DEST="$RELAY_USER@$FUN_HOST"; PORTOPT=""
  PROXY="-o ProxyCommand=openssl s_client -quiet -connect $FUN_HOST:$FUN_PORT -servername $FUN_HOST"
fi

cat > "$CS/tunnel.sh" <<EOF
#!$BASH_BIN
# keeps the reverse tunnel to $CONSOLE_NAME alive, and hands over to teardown at the deadline
CS="$CS"
while :; do
  now=\$(date +%s)
  if [ "\$now" -ge "$DEADLINE" ]; then exec "$BASH_BIN" "\$CS/teardown.sh" --ttl; fi
  ssh -F none -T -i "\$CS/invite_key" -o IdentitiesOnly=yes -o UserKnownHostsFile="\$CS/known_hosts" \\
      -o StrictHostKeyChecking=yes -o HostKeyAlias=csync-relay -o ExitOnForwardFailure=yes \\
      -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -o BatchMode=yes -o ConnectTimeout=15 \\
      $( [ -n "$PROXY" ] && printf '"%s"' "$PROXY" ) $PORTOPT \\
      -R 127.0.0.1:$PORT:localhost:$TARGET_PORT "$DEST" "$HELLO" </dev/null
  sleep 5
done
EOF
chmod 700 "$CS/tunnel.sh"

if [ "$OS" = android ]; then
  # Doze suspends background processes, so hold a wake-lock and re-arm on boot.
  # Both are removed by teardown, and neither survives it.
  termux-wake-lock >/dev/null 2>&1 && changed "held a Termux wake-lock (released at teardown)"
  nohup "$BASH_BIN" "$CS/tunnel.sh" > "$CS/tunnel.log" 2>&1 &
  st tunnel_pid "$!"
  st supervisor "termux"
  if [ -d "$H/.termux/boot" ] || mkdir -p "$H/.termux/boot" 2>/dev/null; then
    printf '#!%s\ntermux-wake-lock\nexec %s "%s/tunnel.sh"\n' "$BASH_BIN" "$BASH_BIN" "$CS" > "$H/.termux/boot/csync-$ID.sh"
    chmod 700 "$H/.termux/boot/csync-$ID.sh"
    st boot_script "$H/.termux/boot/csync-$ID.sh"
    changed "added ~/.termux/boot/csync-$ID.sh so the tunnel returns after a reboot (needs the Termux:Boot app; removed at teardown)"
  fi
elif [ $NO_LAUNCHD -eq 1 ]; then
  nohup "$BASH_BIN" "$CS/tunnel.sh" > "$CS/tunnel.log" 2>&1 &
  st tunnel_pid "$!"
  st supervisor "pid"
elif [ "$OS" = "darwin" ]; then
  PL="$H/Library/LaunchAgents/sh.csync.tunnel.plist"
  mkdir -p "$H/Library/LaunchAgents"
  cat > "$PL" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>sh.csync.tunnel</string>
  <key>ProgramArguments</key><array><string>/bin/bash</string><string>$CS/tunnel.sh</string></array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$CS/tunnel.log</string>
  <key>StandardErrorPath</key><string>$CS/tunnel.log</string>
</dict></plist>
EOF
  launchctl bootout "gui/$(id -u)/sh.csync.tunnel" >/dev/null 2>&1
  launchctl bootstrap "gui/$(id -u)" "$PL" || die "could not start the tunnel agent"
  st supervisor "launchd"
  changed "added ~/Library/LaunchAgents/sh.csync.tunnel.plist (the tunnel keeper)"
else
  if command -v systemd-run >/dev/null 2>&1; then
    systemd-run --user --unit=csync-tunnel --collect /bin/bash "$CS/tunnel.sh" >/dev/null 2>&1 || die "could not start the tunnel unit"
    st supervisor "systemd"
    changed "started user unit csync-tunnel.service (the tunnel keeper)"
  else
    nohup /bin/bash "$CS/tunnel.sh" > "$CS/tunnel.log" 2>&1 &
    st tunnel_pid "$!"
    st supervisor "pid"
  fi
fi
say "  tunnel keeper started"

if [ $NO_ROOT -eq 0 ]; then
  cat > "$CS/root-setup.sh" <<EOF
#!/bin/bash
set -u
ID="$ID"; USER_NAME="$ME"; CS="$CS"; DEADLINE="$DEADLINE"; OS="$OS"
DROPIN=/etc/ssh/sshd_config.d/000-csync.conf
if [ "\$OS" = darwin ]; then RD="/Library/Application Support/csync/\$ID"; else RD="/etc/csync/\$ID"; fi
mkdir -p "\$RD"; chmod 700 "\$RD"
DROPIN_EXISTED=0; [ -e "\$DROPIN" ] && DROPIN_EXISTED=1
if [ "\$OS" = darwin ]; then
  RL_BEFORE="\$(systemsetup -getremotelogin 2>/dev/null | awk '{print tolower(\$NF)}')"
  [ -n "\$RL_BEFORE" ] || RL_BEFORE=unknown
  printf "cs='%s'\nuser_name='%s'\ndeadline='%s'\nos='%s'\nrl_before='%s'\ndropin_existed='%s'\n" "\$CS" "\$USER_NAME" "\$DEADLINE" "\$OS" "\$RL_BEFORE" "\$DROPIN_EXISTED" > "\$RD/state.env"
  if [ "\$RL_BEFORE" != on ]; then
    systemsetup -setremotelogin on >/dev/null 2>&1 || { launchctl enable system/com.openssh.sshd; launchctl bootstrap system /System/Library/LaunchDaemons/ssh.plist; }
    echo "CHANGED: Remote Login turned on (was \$RL_BEFORE)"
  else
    echo "KEPT: Remote Login was already on"
  fi
  mkdir -p /etc/ssh/sshd_config.d
  printf 'PasswordAuthentication no\nKbdInteractiveAuthentication no\nAllowUsers %s\n' "\$USER_NAME" > "\$DROPIN"
  chmod 644 "\$DROPIN"
  echo "CHANGED: sshd drop-in \$DROPIN (keys only, one user)"
  cp -f "\$CS/teardown-root.sh" "\$RD/teardown-root.sh"; chmod 700 "\$RD/teardown-root.sh"; chown -R root:wheel "\$RD"
  cat > /Library/LaunchDaemons/sh.csync.ttl.plist <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>sh.csync.ttl</string>
  <key>ProgramArguments</key><array><string>/bin/bash</string><string>\$RD/teardown-root.sh</string><string>\$ID</string></array>
  <key>RunAtLoad</key><true/>
  <key>StartInterval</key><integer>15</integer>
</dict></plist>
PL
  chown root:wheel /Library/LaunchDaemons/sh.csync.ttl.plist; chmod 644 /Library/LaunchDaemons/sh.csync.ttl.plist
  launchctl bootout system/sh.csync.ttl >/dev/null 2>&1
  launchctl bootstrap system /Library/LaunchDaemons/sh.csync.ttl.plist
  echo "CHANGED: timed cleanup armed for \$(date -r "\$DEADLINE" '+%H:%M')"
else
  if ! command -v sshd >/dev/null 2>&1 && [ ! -x /usr/sbin/sshd ]; then
    if command -v apt-get >/dev/null 2>&1; then apt-get install -y -q openssh-server; elif command -v dnf >/dev/null 2>&1; then dnf install -y -q openssh-server; elif command -v pacman >/dev/null 2>&1; then pacman -S --noconfirm --quiet openssh; fi
    echo "CHANGED: installed openssh-server"
  fi
  SVC=ssh; systemctl list-unit-files sshd.service >/dev/null 2>&1 && SVC=sshd
  EN_BEFORE="\$(systemctl is-enabled \$SVC 2>/dev/null)"; AC_BEFORE="\$(systemctl is-active \$SVC 2>/dev/null)"
  LINGER_BEFORE="\$(loginctl show-user "\$USER_NAME" -p Linger --value 2>/dev/null)"
  printf "cs='%s'\nuser_name='%s'\ndeadline='%s'\nos='%s'\nssh_enabled_before='%s'\nssh_active_before='%s'\ndropin_existed='%s'\nlinger_before='%s'\n" "\$CS" "\$USER_NAME" "\$DEADLINE" "\$OS" "\$EN_BEFORE" "\$AC_BEFORE" "\$DROPIN_EXISTED" "\$LINGER_BEFORE" > "\$RD/state.env"
  mkdir -p /etc/ssh/sshd_config.d
  printf 'ListenAddress 127.0.0.1\nPasswordAuthentication no\nKbdInteractiveAuthentication no\nAllowUsers %s\n' "\$USER_NAME" > "\$DROPIN"
  chmod 644 "\$DROPIN"
  systemctl enable --now \$SVC >/dev/null 2>&1; systemctl reload \$SVC >/dev/null 2>&1
  echo "CHANGED: sshd on, loopback only, keys only, one user (was enabled=\$EN_BEFORE active=\$AC_BEFORE)"
  # Without lingering there is no user manager while nobody is logged in, so the
  # tunnel started by systemd-run --user dies with the session that started it.
  # On a headless machine that is every session. Teardown puts this back.
  if [ "\$LINGER_BEFORE" != "yes" ]; then
    loginctl enable-linger "\$USER_NAME" >/dev/null 2>&1 && echo "CHANGED: enabled lingering for \$USER_NAME so the tunnel outlives the login session"
  else
    echo "KEPT: lingering for \$USER_NAME was already on"
  fi
  cp -f "\$CS/teardown-root.sh" "\$RD/teardown-root.sh"; chmod 700 "\$RD/teardown-root.sh"
  systemd-run --unit="csync-ttl-\$ID" --on-active=15 --on-unit-active=15 /bin/bash "\$RD/teardown-root.sh" "\$ID" >/dev/null 2>&1
  echo "CHANGED: timed cleanup armed"
fi
EOF
  chmod 700 "$CS/root-setup.sh"
  say "  your password now, once: it turns on the SSH service for you only, keys only, and arms the cleanup"
  sudo -p "  password for $ME: " /bin/bash "$CS/root-setup.sh" > "$TMP/root.out" 2>&1 || { cat "$TMP/root.out" >&2; die "the root step failed; nothing else was left running: run $CS/teardown.sh"; }
  sed -n 's/^\(CHANGED\|KEPT\): //p' "$TMP/root.out" | while IFS= read -r line; do changed "$line"; done
  sed 's/^/  /' "$TMP/root.out"
  rm -f "$CS/root-setup.sh"
elif [ "$OS" = android ]; then
  changed "no root steps on Android: nothing outside Termux was touched"
else
  changed "root steps skipped (--no-root): the SSH service and the timed cleanup were not touched"
fi

ENDS_AT="$(date -r "$DEADLINE" '+%H:%M' 2>/dev/null || date -d "@$DEADLINE" '+%H:%M')"
if [ "$OS" = "darwin" ]; then
  osascript -e "display notification \"$CONSOLE_NAME can now reach this Mac until $ENDS_AT. Details in Terminal.\" with title \"csync\"" >/dev/null 2>&1
elif [ "$OS" = android ]; then
  termux-notification --title csync --content "$CONSOLE_NAME can reach this phone until $ENDS_AT" >/dev/null 2>&1
elif command -v notify-send >/dev/null 2>&1; then
  notify-send "csync" "$CONSOLE_NAME can now reach this machine. Details in the terminal." >/dev/null 2>&1
fi

say ""
say "  Connected to $CONSOLE_NAME as $ME, until $ENDS_AT"
if [ "$OS" = android ]; then
  say "  They can: run commands in Termux, copy files both ways, read device info, take a CAMERA photo."
  say "  They cannot: see your screen, use root, read other apps' data, or see your passwords."
  say "  Every command they run is written to $CS/session.log"
  say "  To end it now, at any time:  $CS/teardown.sh"
  say "  That also releases the wake-lock and removes the boot script."
else
  say "  They can: run commands as you, copy files both ways, take screenshots, read device info."
  say "  They cannot: use admin rights, or see your passwords."
  say "  Every command they run is written to $CS/session.log"
  say "  To end it now, at any time:  $CS/teardown.sh"
  say "  A receipt lands on your Desktop when it ends."
fi
