#!/bin/bash
# Install pihub as a socket-activated service. Run with sudo on the Pi.
#
# systemd owns the listening socket, so port 8642 answers from boot with no
# process running. The first connection starts the service; the service exits
# itself after five idle minutes and the socket goes back to waiting.
set -euo pipefail

PORT="${PIHUB_PORT:-8642}"
APP_USER="${SUDO_USER:-$(id -un)}"
SRC="$(cd "$(dirname "$0")" && pwd)"
DEST=/opt/pihub

echo "installing from $SRC to $DEST, running as $APP_USER on port $PORT"

install -d -o "$APP_USER" -g "$APP_USER" "$DEST"
install -o "$APP_USER" -g "$APP_USER" -m 755 "$SRC/server.py"  "$DEST/server.py"
install -o "$APP_USER" -g "$APP_USER" -m 644 "$SRC/index.html" "$DEST/index.html"
[ -f "$SRC/tailwind.js" ] && install -o "$APP_USER" -g "$APP_USER" -m 644 "$SRC/tailwind.js" "$DEST/tailwind.js"

cat > /etc/systemd/system/pihub.socket <<EOF
[Unit]
Description=pihub listening socket

[Socket]
ListenStream=$PORT
# One service instance handles every connection, so the camera has a single owner.
Accept=no

[Install]
WantedBy=sockets.target
EOF

cat > /etc/systemd/system/pihub.service <<EOF
[Unit]
Description=pihub camera and system console
Requires=pihub.socket
After=pihub.socket

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
# video for the camera, and the user's own groups for everything else.
SupplementaryGroups=video
WorkingDirectory=$DEST
ExecStart=/usr/bin/python3 $DEST/server.py
# The process exits on its own when idle. That is success, not a crash, so do
# not restart it; the socket unit brings it back on the next request.
Restart=no
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl disable --now pihub.service 2>/dev/null || true
systemctl enable --now pihub.socket

echo
systemctl --no-pager --lines=0 status pihub.socket || true
echo
echo "http://$(hostname -I | awk '{print $1}'):$PORT"
