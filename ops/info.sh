#!/bin/bash
# Hardware and device summary. Args are section names; prints "## section" then its lines.
os="$(uname -s)"
cap() { head -n 60; }
sec() { printf '## %s\n' "$1"; }
have() { command -v "$1" >/dev/null 2>&1; }

for s in "$@"; do
  sec "$s"
  if [ "$os" = "Darwin" ]; then
    case "$s" in
      system)    sw_vers; sysctl -n kern.hostname; system_profiler SPHardwareDataType 2>/dev/null | sed -n '/Model Name/,/Serial/p' | sed 's/^ *//' | cap ;;
      cpu)       sysctl -n machdep.cpu.brand_string; printf 'cores %s\n' "$(sysctl -n hw.ncpu)"; uptime ;;
      memory)    printf '%s GB installed\n' "$(( $(sysctl -n hw.memsize) / 1073741824 ))"; vm_stat | head -n 8 ;;
      disk)      df -h / /System/Volumes/Data 2>/dev/null | cap ;;
      battery)   pmset -g batt | cap ;;
      displays)  system_profiler SPDisplaysDataType 2>/dev/null | sed 's/^ *//' | grep -Ei 'Chipset|Resolution|Display Type|Main Display|Connection|^[A-Z].*:$' | cap ;;
      usb)       system_profiler SPUSBDataType 2>/dev/null | sed 's/^ *//' | grep -Ei '^[^:]+:$|Product ID|Vendor ID|Manufacturer' | cap ;;
      bluetooth) system_profiler SPBluetoothDataType 2>/dev/null | sed 's/^ *//' | grep -Ei 'State|Connected|Address|^[^:]+:$' | cap ;;
      network)   for i in en0 en1; do ip="$(ipconfig getifaddr $i 2>/dev/null)"; [ -n "$ip" ] && printf '%s %s\n' "$i" "$ip"; done; networksetup -getairportnetwork en0 2>/dev/null; scutil --nwi 2>/dev/null | head -n 12 ;;
      audio)     system_profiler SPAudioDataType 2>/dev/null | sed 's/^ *//' | grep -Ei '^[^:]+:$|Default|Input|Output' | cap ;;
      camera)    system_profiler SPCameraDataType 2>/dev/null | sed 's/^ *//' | cap ;;
      *)         printf 'unknown section\n' ;;
    esac
  else
    case "$s" in
      system)    have hostnamectl && hostnamectl | cap || { uname -a; cat /etc/os-release | head -n 4; } ;;
      cpu)       have lscpu && lscpu | grep -Ei 'Model name|^CPU\(s\)|Thread|MHz' | cap || grep -m1 'model name' /proc/cpuinfo; uptime ;;
      memory)    free -h | cap ;;
      disk)      df -h / /home 2>/dev/null | cap ;;
      battery)   for b in /sys/class/power_supply/BAT*; do [ -d "$b" ] && printf '%s %s%% %s\n' "$(basename "$b")" "$(cat "$b/capacity" 2>/dev/null)" "$(cat "$b/status" 2>/dev/null)"; done ;;
      displays)  have xrandr && DISPLAY="${DISPLAY:-:0}" xrandr --query 2>/dev/null | grep -E ' connected' | cap || printf 'xrandr not available\n' ;;
      usb)       have lsusb && lsusb | cap || printf 'lsusb not available\n' ;;
      bluetooth) have bluetoothctl && bluetoothctl devices 2>/dev/null | cap || printf 'bluetoothctl not available\n' ;;
      network)   ip -brief addr 2>/dev/null | cap ;;
      audio)     have pactl && pactl list short sinks 2>/dev/null | cap || have aplay && aplay -l 2>/dev/null | cap ;;
      camera)    ls /dev/video* 2>/dev/null || printf 'no video devices\n' ;;
      *)         printf 'unknown section\n' ;;
    esac
  fi
done
exit 0
