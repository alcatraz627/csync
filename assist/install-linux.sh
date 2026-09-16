#!/bin/bash
# Install csync-assist on a Linux home server (the Pi) as a per-user systemd
# service. Run ON the target after copying the right dist/ binary there. The
# Gemini key must exist at ~/.config/csync/gemini.key before it will serve.
set -euo pipefail

BIN_SRC="${1:-}"
if [ -z "$BIN_SRC" ] || [ ! -x "$BIN_SRC" ]; then
  echo "usage: install-linux.sh <path-to-csync-assist-binary>" >&2
  exit 2
fi

BIN_DIR="$HOME/.local/bin"
BIN="$BIN_DIR/csync-assist"
UNIT_DIR="$HOME/.config/systemd/user"
UNIT="$UNIT_DIR/csync-assist.service"

mkdir -p "$BIN_DIR" "$UNIT_DIR"
install -m 0755 "$BIN_SRC" "$BIN"

cat > "$UNIT" <<UNITEOF
[Unit]
Description=csync assistant (Gemini over the tailnet)
After=network-online.target tailscaled.service
Wants=network-online.target

[Service]
ExecStart=$BIN serve
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
UNITEOF

systemctl --user daemon-reload
systemctl --user enable --now csync-assist.service 2>&1 || true
loginctl enable-linger "$(id -un)" 2>/dev/null || true

echo "installed csync-assist.service"
echo "it will not serve until ~/.config/csync/gemini.key exists; then: systemctl --user restart csync-assist"
