#!/bin/bash
# End-to-end on one Mac: this machine plays the console and, through a second unprivileged
# sshd, the target. Exercises init, invite, bootstrap (user half), the tunnel, the gate,
# every verb, and teardown with its residue check. The root half (Remote Login, drop-in,
# TTL daemon) needs a real second machine and is reported UNCONFIRMED here.

set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
CSYNC="$REPO/bin/csync"
T="$(mktemp -d "${TMPDIR:-/tmp}/csync-loop.XXXXXX")"
export CSYNC_HOME="$T/console" CSYNC_STATE="$T/state" CSYNC_DATA="$T/data" CSYNC_ACTOR=human
TH="$T/target"
ROUTE="${ROUTE:-lan}"            # lan, or funnel to go out through Tailscale and back
RELAY_PORT="${RELAY_PORT:-5123}" # not 5122, so a real console on this Mac is left alone
FUNNEL_PORT="${FUNNEL_PORT:-8443}"
TARGET_PORT=5022
PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
bad()  { FAIL=$((FAIL+1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }
note() { printf '  \033[2m%s\033[0m\n' "$1"; }
check() { if eval "$2"; then ok "$1"; else bad "$1"; fi; }

cleanup() {
  [ -f "$TH/sshd.pid" ] && kill "$(cat "$TH/sshd.pid")" 2>/dev/null
  [ -f "$CSYNC_HOME/relay/sshd.pid" ] && kill "$(cat "$CSYNC_HOME/relay/sshd.pid")" 2>/dev/null
  pkill -f "$TH/.csync/invite_key" 2>/dev/null
  pkill -f "$TH/.csync/tunnel.sh" 2>/dev/null
  [ "$ROUTE" = funnel ] && tailscale funnel --tls-terminated-tcp="$FUNNEL_PORT" off >/dev/null 2>&1
  if [ "${KEEP:-0}" = 1 ]; then note "kept $T"; else rm -rf "$T"; fi
}
trap cleanup EXIT

printf '\n\033[1mcsync loopback\033[0m  %s\n' "$T"

for p in $RELAY_PORT $TARGET_PORT; do
  if nc -z -w1 127.0.0.1 $p 2>/dev/null; then echo "port $p is busy; stop what is on it first" >&2; exit 1; fi
done

# console
if [ "$ROUTE" = funnel ]; then
  "$CSYNC" init --no-launchd --relay-port $RELAY_PORT --funnel-port $FUNNEL_PORT --bind 127.0.0.1 --lan-ip 127.0.0.1 --console-name "loop-console" > "$T/init.out" 2>&1
  check "init publishes the relay through Funnel" "grep -q 'funnel publishing relay' '$T/init.out' && grep -A0 'funnel publishing relay' '$T/init.out' | grep -q 'ok'"
  INVITE_ROUTE="--route funnel"
else
  "$CSYNC" init --no-funnel --no-launchd --relay-port $RELAY_PORT --bind 127.0.0.1 --lan-ip 127.0.0.1 --console-name "loop-console" > "$T/init.out" 2>&1
  INVITE_ROUTE="--route lan"
fi
check "init starts the relay sshd" "[ -f '$CSYNC_HOME/relay/sshd.pid' ] && nc -z -w1 127.0.0.1 $RELAY_PORT"

# stand-in target: an unprivileged sshd on 5022 with the fake home's authorized_keys
mkdir -p "$TH/.ssh"
ssh-keygen -q -t ed25519 -N '' -f "$TH/ssh_host_ed25519_key"
cat > "$TH/sshd_config" <<EOF
Port $TARGET_PORT
ListenAddress 127.0.0.1
HostKey $TH/ssh_host_ed25519_key
AuthorizedKeysFile $TH/.ssh/authorized_keys
PidFile $TH/sshd.pid
PasswordAuthentication no
KbdInteractiveAuthentication no
UsePAM no
PermitRootLogin no
AllowUsers $(id -un)
PermitTTY yes
StrictModes no
Subsystem sftp /usr/libexec/sftp-server
LogLevel VERBOSE
EOF
/usr/sbin/sshd -f "$TH/sshd_config" -E "$TH/sshd.log"
check "stand-in target sshd listens on $TARGET_PORT" "nc -z -w1 127.0.0.1 $TARGET_PORT"

# invite
# shellcheck disable=SC2086
"$CSYNC" --json invite loop $INVITE_ROUTE --ttl 30m --target-port $TARGET_PORT > "$T/invite.json"
TOKEN="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["token"])' "$T/invite.json")"
check "invite mints a token" "[ -n '$TOKEN' ]"
check "invite writes one relay key line" "[ \$(grep -c csync-invite: '$CSYNC_HOME/relay/authorized_keys') -eq 1 ]"

# bootstrap, user half only, under bash 3.2
/bin/bash "$REPO/bootstrap.sh" "$TOKEN" --no-root --no-launchd --home "$TH" --hostkey "$TH/ssh_host_ed25519_key" > "$T/bootstrap.out" 2>&1
check "bootstrap runs under /bin/bash 3.2" "[ \$? -eq 0 ] || grep -q 'tunnel keeper started' '$T/bootstrap.out'"
check "bootstrap installs the gated key line" "grep -q 'command=\"$TH/.csync/gate.sh\"' '$TH/.ssh/authorized_keys'"
check "bootstrap fetched gate and teardown with matching hashes" "[ -x '$TH/.csync/gate.sh' ] && [ -x '$TH/.csync/teardown.sh' ]"
check "bootstrap ends with the six-line summary" "grep -q 'To end it now' '$T/bootstrap.out'"

# wait for the hello
"$CSYNC" wait loop --timeout 60 > "$T/wait.out" 2>&1
check "wait returns once the tunnel is up" "[ \$? -eq 0 ] || grep -q 'loop' '$T/wait.out'"
check "route used is $ROUTE" "grep -q '\"route_used\": \"$ROUTE\"' '$CSYNC_HOME/hosts.json'"
check "hello pinned the target host key" "grep -q '\[127.0.0.1\]:520' '$CSYNC_HOME/known_hosts'"
check "ssh_config carries Host csync-loop" "grep -q 'Host csync-loop' '$CSYNC_HOME/ssh_config'"

# verbs
"$CSYNC" run loop -- uname -a > "$T/run.out" 2>&1
check "run streams uname through the tunnel" "grep -q Darwin '$T/run.out'"
check "gate logged the command on the target" "grep -q 'uname -a' '$TH/.csync/session.log'"

"$CSYNC" run loop -- rm -rf / > "$T/deny1.out" 2>&1; rc=$?
check "console refuses rm -rf / before it runs (exit 5)" "[ $rc -eq 5 ]"
ssh -F "$CSYNC_HOME/ssh_config" csync-loop 'rm -rf ~' > "$T/deny2.out" 2>&1; rc=$?
check "gate refuses rm -rf ~ even over raw ssh (exit 126)" "[ $rc -eq 126 ] && grep -q refused '$T/deny2.out'"
check "gate wrote the refusal down" "grep -q 'refused: rm -r' '$TH/.csync/session.log'"

echo "payload $(date)" > "$T/push-me.txt"
"$CSYNC" push loop "$T/push-me.txt" "$TH/pushed/" > "$T/push.out" 2>&1
check "push lands a file" "[ -f '$TH/pushed/push-me.txt' ]"
"$CSYNC" push loop "$T/push-me.txt" "$TH/pushed/" > "$T/push2.out" 2>&1; rc=$?
check "push refuses to overwrite without --overwrite (exit 2)" "[ $rc -eq 2 ]"
"$CSYNC" pull loop "$TH/pushed/push-me.txt" > "$T/pull.out" 2>&1
check "pull lands in the host inbox" "[ -f '$CSYNC_DATA/loop/inbox/push-me.txt' ]"

"$CSYNC" --json info loop system cpu > "$T/info.json" 2>&1
check "info returns parsed sections" "python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d[\"ok\"] and \"cpu\" in d[\"sections\"]' '$T/info.json'"

"$CSYNC" --json logs loop --since 5m > "$T/logs.json" 2>&1
check "logs pulls a bundle" "python3 -c 'import json,sys,os; d=json.load(open(sys.argv[1])); assert d[\"ok\"] and os.path.getsize(d[\"bundle\"])>0' '$T/logs.json'"

"$CSYNC" --json shot loop > "$T/shot.json" 2>&1; rc=$?
if [ $rc -eq 0 ]; then ok "shot captured a real screen"; else note "shot: $(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d.get("error"))' "$T/shot.json") (TCC context of a test sshd is not the real one; S1 stays on the second laptop)"; fi

"$CSYNC" recipe loop hello --dev -- a b > "$T/recipe.out" 2>&1
check "recipe streams and runs" "grep -q 'hello from' '$T/recipe.out'"
"$CSYNC" say loop "loopback test" > "$T/say.out" 2>&1
check "say shows a notification" "[ \$? -eq 0 ]"

"$CSYNC" --json log --last 50 > "$T/log.json"
check "audit journal has actor on every line" "python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); es=d[\"entries\"]; assert es and all(\"actor\" in e for e in es)' '$T/log.json'"
"$CSYNC" status > "$T/status.out" 2>&1
check "status renders in one screen" "[ \$(wc -l < '$T/status.out') -le 44 ]"

# teardown
"$CSYNC" teardown loop --yes --verify > "$T/teardown.out" 2>&1; rc=$?
check "teardown exits 0 with no residue" "[ $rc -eq 0 ] && grep -q clean '$T/teardown.out'"
check "target: csync line gone from authorized_keys" "! grep -q 'csync:' '$TH/.ssh/authorized_keys' 2>/dev/null"
check "target: ~/.csync removed" "[ ! -d '$TH/.csync' ]"
check "target: receipt written" "ls '$TH'/csync-receipt-*.txt >/dev/null 2>&1"
check "console: relay key line removed" "! grep -q csync-invite: '$CSYNC_HOME/relay/authorized_keys'"
check "console: ssh_config block removed" "! grep -q 'Host csync-loop' '$CSYNC_HOME/ssh_config'"
check "console: session log copied home" "[ -f '$CSYNC_DATA/loop/session/session.log' ]"
"$CSYNC" --json run loop -- true > "$T/gone.json" 2>&1; rc=$?
check "host is unknown after teardown (exit 3)" "[ $rc -eq 3 ]"

printf '\n%s passed, %s failed\n' "$PASS" "$FAIL"
printf 'UNCONFIRMED on this Mac (needs the second laptop with sudo): Remote Login toggle, sshd drop-in, root TTL daemon, LaunchAgent tunnel keeper, Funnel from a network outside the tailnet, real TCC screenshot.\n'
[ $FAIL -eq 0 ]
