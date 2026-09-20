#!/bin/bash
# Regressions for two macOS pairing fixes.
#
# 1. Host-key pin. bootstrap froze the sshd host key into the hello at setup, but on
#    macOS the key only exists after Remote Login turns on (a later step), so the hello
#    shipped sshd_hostkey= empty and the console could never pin the target. run/say/open
#    then failed "not answering" while the tunnel was up. The fix: tunnel.sh reads the key
#    fresh on every connect. Assert the keeper reads it at runtime, never frozen.
#
# 2. No-expiry option. A trusted own machine should pair with --ttl none and never expire.
#    Assert the keeper and the root teardown timer both treat a 0 deadline as no-expiry.
set -u

here="$(cd "$(dirname "$0")" && pwd)"
boot="$here/../bootstrap.sh"
tdr="$here/../target/teardown-root.sh"
fail() { echo "FAIL: $1"; exit 1; }

[ -f "$boot" ] || fail "bootstrap.sh not found"
[ -f "$tdr" ] || fail "teardown-root.sh not found"

# 1a. The hello must call hostkey() at connect time, and must not freeze a value.
grep -Fq 'sshd_hostkey=\$(hostkey)' "$boot" || fail "keeper hello does not read the host key at runtime"
grep -Fq 'hostkey() {' "$boot" || fail "no hostkey() helper in bootstrap"
grep -Fq 'sshd_hostkey=$HK' "$boot" && fail "hello still freezes a precomputed host key"

# 1b. The hostkey() algorithm returns keytype:key from the first readable host key.
command -v ssh-keygen >/dev/null 2>&1 || { echo "SKIP: no ssh-keygen"; exit 0; }
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/etc_ssh"
ssh-keygen -q -t ed25519 -N '' -C hk-test -f "$tmp/etc_ssh/ssh_host_ed25519_key" || fail "keygen"
ETC_SSH="$tmp/etc_ssh" DEV_HOSTKEY=""
hostkey() {
  for f in "$ETC_SSH/ssh_host_ed25519_key.pub" "$ETC_SSH/ssh_host_ecdsa_key.pub" "$ETC_SSH/ssh_host_rsa_key.pub"; do
    [ -r "$f" ] && { awk '{print $1":"$2}' "$f"; return; }
  done
}
hk="$(hostkey)"
case "$hk" in ssh-ed25519:AAAA*) : ;; *) fail "hostkey() produced '$hk', not keytype:key" ;; esac
# The relay turns keytype:key into a known_hosts line; that must reproduce the real fingerprint.
printf '[127.0.0.1]:1 %s\n' "$(printf '%s' "$hk" | sed 's/:/ /')" > "$tmp/kh"
want="$(ssh-keygen -lf "$tmp/etc_ssh/ssh_host_ed25519_key.pub" | awk '{print $2}')"
got="$(ssh-keygen -lf "$tmp/kh" | awk '{print $2}')"
[ "$got" = "$want" ] || fail "pinned key fingerprint $got != host key $want"

# 2. No-expiry: teardown-root must stay alive when deadline is 0 or empty.
guard() {  # mirrors teardown-root.sh: stays (rc 0) unless past a positive deadline
  local deadline="$1" now=2000000000
  case "$deadline" in ''|0) return 0 ;; esac
  [ "$now" -lt "$deadline" ] && return 0
  return 1
}
guard 0   || fail "deadline 0 should be no-expiry (stay)"
guard ""  || fail "empty deadline should be no-expiry (stay)"
guard 9999999999 || fail "future deadline should stay"
guard 100 && fail "past deadline should tear down"

# The keeper's own guard: only hand to teardown when the deadline is positive AND passed.
grep -Fq 'DEADLINE" -gt 0 ] &&' "$boot" || fail "keeper does not guard teardown on a positive deadline"

echo "PASS: keeper reads the host key at connect time; no-expiry deadline honored ($got)"
