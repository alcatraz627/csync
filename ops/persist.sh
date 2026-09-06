#!/bin/bash
# Turns always-on behaviour on or off on the target without ending the session.
# On Android that means the Termux wake-lock and the boot script; on a laptop the
# tunnel keeper is already a normal service and this only reports.
#   persist.sh on|off|status
action="${1:-status}"
CS="$HOME/.csync"
[ -d "$CS" ] || { echo "no csync session on this machine" >&2; exit 1; }
# shellcheck source=/dev/null
. "$CS/state.env"

os_now="$(uname -s)"
if [ -n "${PREFIX:-}" ] && [ -d "$PREFIX/bin" ]; then
  case "$PREFIX" in *com.termux*) os_now=Android ;; esac
fi

boot_dir="$HOME/.termux/boot"
boot_file="$boot_dir/csync-$id.sh"

if [ "$os_now" != "Android" ]; then
  case "$action" in
    status) printf 'supervisor=%s\nalways_on=yes (a normal service on this OS)\n' "${supervisor:-unknown}" ;;
    on|off) printf 'nothing to toggle on this OS; the tunnel keeper is a normal service\n' ;;
  esac
  exit 0
fi

case "$action" in
  on)
    termux-wake-lock >/dev/null 2>&1 && printf 'wake-lock held\n' || printf 'wake-lock failed (termux-api installed?)\n'
    mkdir -p "$boot_dir"
    printf '#!%s\ntermux-wake-lock\nexec %s "%s/tunnel.sh"\n' "${bash_bin:-$PREFIX/bin/bash}" "${bash_bin:-$PREFIX/bin/bash}" "$CS" > "$boot_file"
    chmod 700 "$boot_file"
    printf 'boot script written to %s\n' "$boot_file"
    printf 'battery: to exempt Termux from optimisation, open the settings page with\n'
    printf '  am start -a android.settings.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS -d package:com.termux\n'
    ;;
  off)
    termux-wake-unlock >/dev/null 2>&1 && printf 'wake-lock released\n' || printf 'no wake-lock held\n'
    rm -f "$boot_file" && printf 'boot script removed\n'
    printf 'battery: to put Termux back under optimisation, open\n'
    printf '  am start -a android.settings.IGNORE_BATTERY_OPTIMIZATION_SETTINGS\n'
    printf 'the tunnel keeps running until the deadline or teardown\n'
    ;;
  status)
    if [ -e "$boot_file" ]; then printf 'boot script: present (%s)\n' "$boot_file"; else printf 'boot script: absent\n'; fi
    if command -v termux-wake-lock >/dev/null 2>&1; then printf 'termux-api: installed\n'; else printf 'termux-api: missing\n'; fi
    printf 'deadline: %s\n' "$(date -d "@$deadline" '+%Y-%m-%d %H:%M' 2>/dev/null || date -r "$deadline" '+%Y-%m-%d %H:%M' 2>/dev/null || echo "$deadline")"
    ;;
  *) echo "usage: persist.sh on|off|status" >&2; exit 2 ;;
esac
