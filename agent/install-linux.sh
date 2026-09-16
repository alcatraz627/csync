#!/bin/bash
# Install the csync mesh agent on a Linux device (Raspberry Pi, server, laptop)
# as a per-user systemd service. Run this ON the target after copying the right
# dist/ binary there (e.g. csync-agent-linux-arm64 for a Pi).
#   csync push raspberrypi dist/csync-agent-linux-arm64
#   ssh raspberrypi 'bash -s' < install-linux.sh   # or run it there directly
set -euo pipefail

BIN_SRC="${1:-}"
if [ -z "$BIN_SRC" ] || [ ! -x "$BIN_SRC" ]; then
  echo "usage: install-linux.sh <path-to-csync-agent-binary>" >&2
  exit 2
fi

BIN_DIR="$HOME/.local/bin"
BIN="$BIN_DIR/csync-agent"
UNIT_DIR="$HOME/.config/systemd/user"
UNIT="$UNIT_DIR/csync-agent.service"

mkdir -p "$BIN_DIR" "$UNIT_DIR"
install -m 0755 "$BIN_SRC" "$BIN"
"$BIN" token >/dev/null

cat > "$UNIT" <<UNITEOF
[Unit]
Description=csync mesh agent
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
systemctl --user enable --now csync-agent.service
# Keep the service alive after logout so the device always receives.
loginctl enable-linger "$(id -un)" 2>/dev/null || true

echo "installed and started csync-agent.service"
echo "status: systemctl --user status csync-agent.service"
