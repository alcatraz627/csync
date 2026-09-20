#!/bin/bash
# Screenshot of display N to a temp file. Prints its size, then the path as the last line.
# On Android without root there is no screen capture, so this takes a CAMERA frame and
# says so; a real screen shot needs the ADB mode.
display="${1:-1}"
os="$(uname -s)"
if [ -n "${PREFIX:-}" ] && [ -d "$PREFIX/bin" ]; then
  case "$PREFIX" in *com.termux*) os=Android ;; esac
fi
f="$(mktemp "${TMPDIR:-/tmp}/csync-shot.XXXXXX")"
mv -f "$f" "$f.png"
f="$f.png"

if [ "$os" = "Darwin" ]; then
  err="$(screencapture -x -D "$display" "$f" 2>&1)"
  [ -s "$f" ] || err="$(screencapture -x "$f" 2>&1)"
  # macOS returns this exact phrase, non-zero, when Screen Recording is not granted
  # to the SSH daemon; surface it as a distinct signal so the console names the real fix.
  if [ ! -s "$f" ]; then
    case "$err" in
      *"could not create image"*|*[Nn]ot\ authorized*|*[Dd]enied*)
        echo "screen-recording-denied" >&2; exit 3 ;;
    esac
  fi
elif [ "$os" = "Android" ]; then
  if command -v termux-camera-photo >/dev/null 2>&1; then
    # display doubles as the camera id here: 0 is usually the back camera, 1 the front
    cam="$display"; [ "$cam" = "1" ] && cam=0
    j="${f%.png}.jpg"
    termux-camera-photo -c "$cam" "$j" 2>/dev/null
    if [ -s "$j" ]; then
      mv -f "$j" "$f"
      printf 'note=camera frame from camera %s; screen capture needs root or the ADB mode\n' "$cam"
    else
      echo "camera capture failed: grant Termux the camera permission, or the camera is in use" >&2
      exit 1
    fi
  else
    echo "termux-api is not installed, so no camera frame is available" >&2
    exit 1
  fi
else
  export DISPLAY="${DISPLAY:-:0}"
  export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"
  export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
  export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
  if command -v grim >/dev/null 2>&1; then grim "$f"
  elif command -v gnome-screenshot >/dev/null 2>&1; then gnome-screenshot -f "$f"
  elif command -v import >/dev/null 2>&1; then import -window root "$f"
  elif command -v scrot >/dev/null 2>&1; then scrot "$f"
  else echo "no screenshot tool (grim, gnome-screenshot, import, scrot)" >&2; exit 1
  fi
fi
[ -s "$f" ] || { echo "capture produced no file" >&2; exit 1; }
printf 'bytes=%s\n' "$(wc -c < "$f" | tr -d ' ')"
printf '%s\n' "$f"
