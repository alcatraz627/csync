#!/bin/bash
# Cross-compile csync-assist for the devices that would host it (a home server:
# a Pi or a Linux/macOS box). Zero dependencies, one static binary per target.
set -euo pipefail

cd "$(dirname "$0")"
GO="${GO:-/opt/homebrew/bin/go}"
[ -x "$GO" ] || GO="$(command -v go)"
OUT="dist"
mkdir -p "$OUT"

targets="
darwin-arm64 darwin arm64
linux-arm64 linux arm64
linux-amd64 linux amd64
"

echo "$targets" | while read -r label goos goarch; do
  [ -z "$label" ] && continue
  bin="$OUT/csync-assist-$label"
  echo "building $bin"
  env CGO_ENABLED=0 GOOS="$goos" GOARCH="$goarch" \
    "$GO" build -trimpath -ldflags "-s -w" -o "$bin" .
done

echo
ls -lh "$OUT"
