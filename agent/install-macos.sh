#!/bin/bash
# Install the csync mesh agent on this Mac and keep it running as a LaunchAgent,
# so the machine always receives shares over the tailnet.
set -euo pipefail

cd "$(dirname "$0")"
GO="${GO:-/opt/homebrew/bin/go}"
[ -x "$GO" ] || GO="$(command -v go)"

BIN_DIR="$HOME/.local/bin"
BIN="$BIN_DIR/csync-agent"
PLIST="$HOME/Library/LaunchAgents/com.csync.agent.plist"
LABEL="com.csync.agent"

mkdir -p "$BIN_DIR"
echo "building host binary -> $BIN"
env CGO_ENABLED=0 "$GO" build -trimpath -ldflags "-s -w" -o "$BIN" .

# Mint the token now so the service starts with one already in place.
"$BIN" token >/dev/null

mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<PLISTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$BIN</string>
    <string>serve</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/csync-agent.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/csync-agent.log</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key><string>$HOME/.local/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin</string>
  </dict>
</dict>
</plist>
PLISTEOF

# Reload cleanly: a bootout of an unloaded label is not an error here.
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
launchctl kickstart -k "gui/$(id -u)/$LABEL"

echo "installed and started $LABEL"
echo "log: $HOME/Library/Logs/csync-agent.log"
