#!/bin/bash
# Cross-compile the csync mesh agent for every device family, into dist/.
# Zero external dependencies, so each target is a single static binary you can
# drop onto a Mac, a Raspberry Pi, a Linux box, or a remote server and just run.
set -euo pipefail

cd "$(dirname "$0")"
GO="${GO:-/opt/homebrew/bin/go}"
[ -x "$GO" ] || GO="$(command -v go)"
OUT="dist"
mkdir -p "$OUT"

# target triples: label GOOS GOARCH  (GOARM appended for arm/v6)
targets="
darwin-arm64 darwin arm64
darwin-amd64 darwin amd64
linux-arm64 linux arm64
linux-amd64 linux amd64
linux-armv6 linux arm
"

echo "$targets" | while read -r label goos goarch; do
  [ -z "$label" ] && continue
  bin="$OUT/csync-agent-$label"
  env_extra=""
  [ "$label" = "linux-armv6" ] && env_extra="GOARM=6"
  echo "building $bin"
  env CGO_ENABLED=0 GOOS="$goos" GOARCH="$goarch" $env_extra \
    "$GO" build -trimpath -ldflags "-s -w" -o "$bin" .
done

echo
echo "built:"
ls -lh "$OUT"
