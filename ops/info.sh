#!/bin/bash
# Hardware and device summary. Args are section names; prints "## section" then its lines.
os="$(uname -s)"
if [ -n "${PREFIX:-}" ] && [ -d "$PREFIX/bin" ]; then
  case "$PREFIX" in *com.termux*) os=Android ;; esac
fi
cap() { head -n 60; }
sec() { printf '## %s\n' "$1"; }
have() { command -v "$1" >/dev/null 2>&1; }
prop() { getprop "$1" 2>/dev/null; }

# df says how full a volume is. This says what it is FOR, which is what an
# operator actually wants when a stranger's machine has four disks attached.
# A mounted volume answers with its mount point. A detached one answers with
# where it was last used, which ext filesystems record and nothing else does.
roles_linux() {
  have lsblk || { printf 'volume roles need lsblk\n'; return; }
  lsblk -rno NAME,TYPE 2>/dev/null | while read -r n t; do
    case "$t" in part|disk|lvm) ;; *) continue ;; esac
    d="/dev/$n"
    fs="$(lsblk -rndo FSTYPE "$d" 2>/dev/null)"
    # A whole disk carrying no filesystem is just the container for the partitions
    # under it. A USB stick formatted with no partition table does carry one, and
    # that is why whole disks are not skipped outright.
    if [ "$t" = disk ] && [ -z "$fs" ]; then continue; fi
    size="$(lsblk -rndo SIZE "$d" 2>/dev/null)"
    lab="$(lsblk -rndo LABEL "$d" 2>/dev/null)"
    mnt="$(lsblk -rndo MOUNTPOINT "$d" 2>/dev/null)"
    if [ -n "$mnt" ]; then
      where="mounted at $mnt"
    else
      where="not mounted"
      case "$fs" in
        ext2|ext3|ext4)
          if have tune2fs; then
            last="$(tune2fs -l "$d" 2>/dev/null | sed -n 's/^Last mounted on: *//p')"
            case "$last" in
              ""|"<not available>") where="not mounted, and its last use is only readable as root" ;;
              *)                    where="not mounted, last used at $last" ;;
            esac
          else
            where="not mounted, and reading its last use needs tune2fs from e2fsprogs"
          fi
          ;;
      esac
    fi
    printf '%-14s %-8s %-7s %-14s %s\n' "$d" "${size:--}" "${fs:--}" "${lab:--}" "$where"
  done
}

# macOS keeps no record of where a detached volume was last used, so the volume
# name carries the whole answer here and unmounted means unmounted.
roles_darwin() {
  diskutil list 2>/dev/null | sed -n 's/^ *[0-9][0-9]*: *//p' | while read -r rest; do
    id="${rest##* }"
    # diskN with no slice is the container, not a volume anyone stores anything on.
    case "$id" in disk*s*) ;; *) continue ;; esac
    mnt="$(diskutil info "$id" 2>/dev/null | sed -n 's/^ *Mount Point: *//p')"
    name="$(diskutil info "$id" 2>/dev/null | sed -n 's/^ *Volume Name: *//p')"
    case "$name" in "Not applicable"*) name="-" ;; esac
    [ -n "$mnt" ] && where="mounted at $mnt" || where="not mounted"
    printf '%-12s %-26s %s\n' "$id" "${name:--}" "$where"
  done
}

section() {
  s="$1"
  if [ "$os" = "Darwin" ]; then
    case "$s" in
      system)    sw_vers; sysctl -n kern.hostname; system_profiler SPHardwareDataType 2>/dev/null | sed -n '/Model Name/,/Serial/p' | sed 's/^ *//' | cap ;;
      cpu)       sysctl -n machdep.cpu.brand_string; printf 'cores %s\n' "$(sysctl -n hw.ncpu)"; uptime ;;
      memory)    printf '%s GB installed\n' "$(( $(sysctl -n hw.memsize) / 1073741824 ))"; vm_stat | head -n 8 ;;
      disk)      df -h / /System/Volumes/Data 2>/dev/null | cap; printf '\n'; roles_darwin | cap ;;
      battery)   pmset -g batt | cap ;;
      displays)  system_profiler SPDisplaysDataType 2>/dev/null | sed 's/^ *//' | grep -Ei 'Chipset|Resolution|Display Type|Main Display|Connection|^[A-Z].*:$' | cap ;;
      usb)       system_profiler SPUSBDataType 2>/dev/null | sed 's/^ *//' | grep -Ei '^[^:]+:$|Product ID|Vendor ID|Manufacturer' | cap ;;
      bluetooth) system_profiler SPBluetoothDataType 2>/dev/null | sed 's/^ *//' | grep -Ei 'State|Connected|Address|^[^:]+:$' | cap ;;
      network)   for i in en0 en1; do ip="$(ipconfig getifaddr $i 2>/dev/null)"; [ -n "$ip" ] && printf '%s %s\n' "$i" "$ip"; done; networksetup -getairportnetwork en0 2>/dev/null; scutil --nwi 2>/dev/null | head -n 12 ;;
      audio)     system_profiler SPAudioDataType 2>/dev/null | sed 's/^ *//' | grep -Ei '^[^:]+:$|Default|Input|Output' | cap ;;
      camera)    system_profiler SPCameraDataType 2>/dev/null | sed 's/^ *//' | cap ;;
      *)         printf 'unknown section\n' ;;
    esac
  elif [ "$os" = "Android" ]; then
    case "$s" in
      system)    printf 'model %s\nmanufacturer %s\ndevice %s\nandroid %s (sdk %s)\nsecurity patch %s\nbuild %s\n' \
                   "$(prop ro.product.model)" "$(prop ro.product.manufacturer)" "$(prop ro.product.device)" \
                   "$(prop ro.build.version.release)" "$(prop ro.build.version.sdk)" "$(prop ro.build.version.security_patch)" "$(prop ro.build.display.id)"
                 printf 'uptime %s\n' "$(cut -d. -f1 /proc/uptime 2>/dev/null) s" ;;
      cpu)       prop ro.soc.model; grep -m1 'Hardware' /proc/cpuinfo 2>/dev/null; printf 'cores %s\nabi %s\n' "$(nproc 2>/dev/null)" "$(prop ro.product.cpu.abi)"; cat /proc/loadavg 2>/dev/null ;;
      memory)    grep -E 'MemTotal|MemAvailable|SwapTotal' /proc/meminfo 2>/dev/null ;;
      disk)      df -h "$HOME" /storage/emulated/0 2>/dev/null | cap
                 printf '\nAndroid hides the block devices, so what each volume is for is not readable from Termux.\n' ;;
      battery)   have termux-battery-status && termux-battery-status || printf 'termux-api not installed\n' ;;
      displays)  have termux-window-manager && termux-window-manager 2>/dev/null; printf 'density %s\n' "$(prop ro.sf.lcd_density)"; have wm && wm size 2>/dev/null ;;
      usb)       ls /sys/bus/usb/devices 2>/dev/null | cap || printf 'no usb listing without root\n' ;;
      bluetooth) have termux-bluetooth-scaninfo && printf 'use termux-bluetooth-scaninfo interactively\n' || printf 'bluetooth needs termux-api and a permission grant\n' ;;
      network)   have termux-wifi-connectioninfo && termux-wifi-connectioninfo; ip -brief addr 2>/dev/null | cap ;;
      audio)     have termux-audio-info && termux-audio-info || printf 'termux-api not installed\n' ;;
      camera)    have termux-camera-info && termux-camera-info || printf 'termux-api not installed\n' ;;
      telephony) have termux-telephony-deviceinfo && termux-telephony-deviceinfo || printf 'termux-api not installed\n' ;;
      location)  have termux-location && termux-location -p network 2>/dev/null || printf 'termux-api not installed, or location permission not granted\n' ;;
      sensors)   have termux-sensor && termux-sensor -l 2>/dev/null | cap || printf 'termux-api not installed\n' ;;
      *)         printf 'unknown section\n' ;;
    esac
  else
    case "$s" in
      system)    have hostnamectl && hostnamectl | cap || { uname -a; cat /etc/os-release | head -n 4; } ;;
      cpu)       have lscpu && lscpu | grep -Ei 'Model name|^CPU\(s\)|Thread|MHz' | cap || grep -m1 'model name' /proc/cpuinfo; uptime ;;
      memory)    free -h | cap ;;
      disk)      df -h / /home 2>/dev/null | cap; printf '\n'; roles_linux | cap ;;
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
}

# A section that finds nothing must say nothing was found. Printing a bare header
# reads as a broken tool, and the operator cannot tell "this machine has no
# battery" apart from "the battery check failed". Guarding it here rather than in
# each branch means a section added later inherits the guarantee.
for s in "$@"; do
  sec "$s"
  body="$(section "$s")"
  if [ -n "$(printf '%s' "$body" | tr -d '[:space:]')" ]; then
    printf '%s\n' "$body"
  else
    printf 'nothing found: this machine reports no %s\n' "$s"
  fi
done
exit 0
