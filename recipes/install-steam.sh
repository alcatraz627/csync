#!/bin/bash
# csync-recipe: install-steam
# os: darwin
# summary: downloads Steam and puts it in ~/Applications, no admin rights needed
set -e
dl="$HOME/Downloads/csync"
mkdir -p "$dl" "$HOME/Applications"
if [ -d "$HOME/Applications/Steam.app" ] || [ -d "/Applications/Steam.app" ]; then
  echo "Steam is already installed"
  exit 0
fi
echo "downloading steam.dmg"
curl -fsSL -o "$dl/steam.dmg" "https://cdn.fastly.steamstatic.com/client/installer/steam.dmg"
mnt="$(hdiutil attach -nobrowse -readonly "$dl/steam.dmg" | awk -F'\t' '/\/Volumes\//{print $NF; exit}')"
cp -R "$mnt/Steam.app" "$HOME/Applications/Steam.app"
hdiutil detach "$mnt" -quiet
rm -f "$dl/steam.dmg"
echo "Steam is in ~/Applications; first launch downloads its updates"
