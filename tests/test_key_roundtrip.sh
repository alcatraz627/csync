#!/bin/bash
# Regression for the macOS invite-key corruption. The bug: bootstrap decoded the
# invite private key with the ambiguous `base64 -d`, which on macOS/BSD can
# succeed with WRONG bytes, mangling the private half while leaving the public
# blob intact, so the key parsed and offered but could not sign. The loopback
# test never caught it because it ran on one machine. This exercises the exact
# encode (as invite.py) and decode (as bootstrap's b64d) and asserts the private
# half still SIGNS by deriving its public with `ssh-keygen -y`.
set -u

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

command -v ssh-keygen >/dev/null 2>&1 || { echo "SKIP: no ssh-keygen"; exit 0; }
ssh-keygen -q -t ed25519 -N '' -C roundtrip-test -f "$tmp/k" || { echo "FAIL: keygen"; exit 1; }
want="$(ssh-keygen -lf "$tmp/k" | awk '{print $2}')"

# Encode exactly as csync/invite.py does: base64 of the private key text, one line.
python3 - "$tmp/k" "$tmp/k.b64" <<'PY'
import base64, sys, pathlib
text = pathlib.Path(sys.argv[1]).read_text()
pathlib.Path(sys.argv[2]).write_text(base64.b64encode(text.encode()).decode())
PY

# The exact b64d from bootstrap.sh: unambiguous decoders first, then a fallback.
b64d() {
  base64 -D < "$1" > "$2" 2>/dev/null && [ -s "$2" ] && return 0
  base64 --decode < "$1" > "$2" 2>/dev/null && [ -s "$2" ] && return 0
  base64 -d < "$1" > "$2" 2>/dev/null && [ -s "$2" ] && return 0
  openssl base64 -d -A < "$1" > "$2" 2>/dev/null && [ -s "$2" ]
}
b64d "$tmp/k.b64" "$tmp/k.out" || { echo "FAIL: decode"; exit 1; }
chmod 600 "$tmp/k.out"

# The private half must sign: -y derives the public FROM the private scalar.
ssh-keygen -yf "$tmp/k.out" > "$tmp/k.derived.pub" 2>/dev/null || { echo "FAIL: private half unusable after decode"; exit 1; }
got="$(ssh-keygen -lf "$tmp/k.derived.pub" | awk '{print $2}')"
if [ "$got" = "$want" ]; then
  echo "PASS: invite-key round-trip signs on $(uname -s), $got"
  exit 0
fi
echo "FAIL: decoded key fingerprint $got != original $want"
exit 1
