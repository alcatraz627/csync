#!/bin/bash
# Collects a log slice into one tar.gz, prints a short digest, then "BUNDLE=<path>".
since="1h"; app=""; crash=0
while [ $# -gt 0 ]; do
  case "$1" in
    --since) shift; since="$1" ;;
    --app) shift; app="$1" ;;
    --crash) crash=1 ;;
  esac
  shift
done
os="$(uname -s)"
if [ -n "${PREFIX:-}" ] && [ -d "$PREFIX/bin" ]; then
  case "$PREFIX" in *com.termux*) os=Android ;; esac
fi
stamp="$(date +%Y%m%d-%H%M%S)"
d="$(mktemp -d "${TMPDIR:-/tmp}/csync-logs.XXXXXX")"
out="${TMPDIR:-/tmp}/csync-logs-$stamp.tar.gz"

if [ "$os" = "Darwin" ]; then
  log show --last "$since" --style compact --predicate 'messageType >= 16' 2>/dev/null | head -n 20000 > "$d/errors-and-faults-last-$since.log"
  if [ -n "$app" ]; then
    log show --last "$since" --style compact --predicate "process CONTAINS[c] \"$app\" OR subsystem CONTAINS[c] \"$app\"" 2>/dev/null | head -n 20000 > "$d/app-$app-last-$since.log"
  fi
  if [ $crash -eq 1 ]; then
    mkdir -p "$d/crash"
    find "$HOME/Library/Logs/DiagnosticReports" -maxdepth 1 -type f -mtime -7 -exec cp -f {} "$d/crash/" \; 2>/dev/null
    find /Library/Logs/DiagnosticReports -maxdepth 1 -type f -mtime -7 -readable -exec cp -f {} "$d/crash/" \; 2>/dev/null
  fi
  printf 'errors and faults in the last %s: %s lines\n' "$since" "$(wc -l < "$d/errors-and-faults-last-$since.log" | tr -d ' ')"
  printf 'noisiest processes:\n'
  awk '{print $4}' "$d/errors-and-faults-last-$since.log" | sed 's/\[.*//' | sort | uniq -c | sort -rn | head -n 8 | sed 's/^/  /'
  [ $crash -eq 1 ] && printf 'crash reports (7 days): %s\n' "$(ls "$d/crash" 2>/dev/null | wc -l | tr -d ' ')"
elif [ "$os" = "Android" ]; then
  # Without root, logcat returns only this app's own lines. Say that rather than
  # implying a full system log; the ADB mode is what reads the whole buffer.
  if command -v logcat >/dev/null 2>&1; then
    logcat -d -v time 2>/dev/null | head -n 20000 > "$d/logcat-visible.log"
    if [ -n "$app" ]; then
      grep -i "$app" "$d/logcat-visible.log" > "$d/logcat-$app.log" 2>/dev/null
    fi
    lines="$(wc -l < "$d/logcat-visible.log" | tr -d ' ')"
    printf 'logcat lines visible to this app: %s\n' "$lines"
    [ "$lines" -lt 5 ] && printf 'note: Android hides other apps logs without root; use the ADB mode for the full buffer\n'
    printf 'busiest tags:\n'
    awk '{print $6}' "$d/logcat-visible.log" 2>/dev/null | sed 's/(.*//' | sort | uniq -c | sort -rn | head -n 8 | sed 's/^/  /'
  else
    printf 'no logcat on PATH\n' > "$d/logcat-visible.log"
    printf 'logcat is not available in this Termux install\n'
  fi
  printf 'device: %s, android %s\n' "$(getprop ro.product.model 2>/dev/null)" "$(getprop ro.build.version.release 2>/dev/null)"
  if [ $crash -eq 1 ]; then
    printf 'crash reports need the ADB mode on Android\n'
  fi
else
  case "$since" in
    *h) js="${since%h} hours ago" ;;
    *m) js="${since%m} minutes ago" ;;
    *d) js="${since%d} days ago" ;;
    *) js="$since" ;;
  esac
  journalctl --since "$js" -p warning --no-pager 2>/dev/null | head -n 20000 > "$d/warnings-last-$since.log"
  if [ -n "$app" ]; then
    journalctl --since "$js" --no-pager -g "$app" 2>/dev/null | head -n 20000 > "$d/app-$app-last-$since.log"
  fi
  if [ $crash -eq 1 ] && command -v coredumpctl >/dev/null 2>&1; then
    coredumpctl list --no-pager 2>/dev/null > "$d/coredumps.txt"
  fi
  printf 'warnings and worse in the last %s: %s lines\n' "$since" "$(wc -l < "$d/warnings-last-$since.log" | tr -d ' ')"
  printf 'noisiest units:\n'
  awk '{print $5}' "$d/warnings-last-$since.log" | sed 's/\[.*//; s/:$//' | sort | uniq -c | sort -rn | head -n 8 | sed 's/^/  /'
fi

tar czf "$out" -C "$d" . && rm -rf "$d"
printf 'BUNDLE=%s\n' "$out"
