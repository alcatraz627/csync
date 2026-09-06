# csync on Android: can a phone be a target, and how

<!-- sessions: csync-plan-7c@2026-09-06 -->

Short answer: yes, a phone can be a csync target, through Termux, and most csync
verbs map onto it cleanly. But two promises that hold on a laptop do not hold on
a phone, and they are the whole reason to read the rest of this: Android has no
preinstalled ssh or curl, so "installs nothing" becomes "install one app once",
and Android kills background processes, so the tunnel needs a wake-lock and a
boot hook to stay up. A real screen screenshot is the one verb that cannot be
done without either root or a separate ADB channel.

This is a feasibility study and a plan, not built code. The claims marked
`[VERIFY]` are from knowledge of Android and Termux and need one session on a
real phone to confirm, because Android behaviour shifts version to version.

## What csync is today, so the parity is clear

csync's target path (repo `/Users/alcatraz627/Code/Claude/csync`, spec
`docs/spec.md`) is: paste one line, the target turns on its own sshd and opens a
reverse SSH tunnel into the console's relay, then the console drives it with one
verb per job. v1 targets are macOS and systemd Linux. The Android path is
greenfield: no Android code exists, so there is nothing to break, only a new
branch of the bootstrap and the ops scripts to add.

## The three ways a phone could be reached

| Way | Who starts the connection | Fits the reverse-tunnel model | Real screen shot | One-time setup on the phone |
|---|---|---|---|---|
| **Termux sshd + reverse tunnel** | the phone, like every other target | yes, directly | no (camera yes, screen needs root) | install Termux, grant a few permissions |
| **ADB over wireless debugging** | the console reaches the phone | no, it inverts the model | yes, `screencap` with no root | enable Developer Options and Wireless Debugging, pair |
| **Rooted phone** | the phone | yes | yes | root the device |

Termux is the path that keeps csync's shape. ADB is worth having as a second
mode precisely because it answers the one thing Termux cannot, a real screen
capture, but it is a different architecture and belongs in its own milestone.
Root is out: the audience is a friend's ordinary phone.

## The Termux path in detail

Termux is a terminal and a Linux userland on Android, installed as one app. From
inside it, `pkg install openssh rsync termux-api` gives the same `ssh`, `sshd`,
and `rsync` the Linux target path already uses. The bootstrap changes less than
it looks.

**What stays the same.** The token, the relay, the reverse `ssh -R` into the
console, the pinned host key, the gate in `authorized_keys`, the TTL deadline,
the teardown that removes the key line and `~/.csync`. All of it is plain ssh, so
it works unchanged.

**What changes.**

| Concern | Laptop | Android / Termux |
|---|---|---|
| ssh, curl present | preinstalled | Termux installed once; then `pkg install openssh rsync termux-api` |
| Who runs it | a login user | Termux's single sandbox user, no root, no sudo at all |
| sshd port | 22 | 8022, because a non-root process cannot bind 22 (the tunnel forwards to 127.0.0.1:8022, so the console never notices) |
| Turning sshd on | `systemsetup` / `systemctl` under sudo | `sshd` run directly in Termux, no privilege step, so the whole `sudo` half of the bootstrap disappears |
| Keeping the tunnel alive | LaunchAgent / systemd unit | `termux-wake-lock` plus the Termux:Boot add-on, or a foreground service; Android's Doze kills a plain background process `[VERIFY]` |
| The root teardown half | restores Remote Login, drop-in | none needed, because nothing was changed as root |

The `sudo` step vanishing is the good news: on Android there is no system service
to toggle and no privileged config to restore, so the target-side change is
smaller and the teardown is simpler and more complete than on a laptop.

## How each verb maps

| Verb | On Android | Confidence |
|---|---|---|
| `run` | runs in the Termux shell; that is the phone's Linux userland, not the Android system shell | solid |
| `push` / `pull` | rsync over the tunnel, into `~/storage/…` after `termux-setup-storage` grants file access | solid |
| `info` | `termux-battery-status`, `termux-telephony-deviceinfo`, `termux-wifi-connectioninfo`, `termux-sensor`, plus `getprop` for model and Android version; richer than a laptop | solid, needs termux-api |
| `say` | `termux-notification` puts a real notification on the phone | solid, needs termux-api |
| `shot` | `termux-camera-photo` grabs a camera frame (front or back). A real SCREEN capture is not possible without root or ADB `[VERIFY]` | camera yes, screen no |
| `logs` | `logcat -d` returns only the app's own logs on modern Android without root; the rich system log needs ADB or root `[VERIFY]` | limited |
| `open` | `termux-open <url>` or `am start` hands a URL or intent to Android | solid |
| `recipe` | streams shell to Termux exactly as elsewhere | solid |

The pattern: anything that lives in Termux's own sandbox works well, and the
Termux:API package turns the phone's hardware into better `info` than a laptop
gives. The two weak spots, screen capture and system logs, are both the same
Android security boundary, and both are answered by the ADB mode.

## The two honest deviations from the laptop promise

These are the reason this is a study and not just a patch. The owner should see
them before any code.

1. **"Installs nothing" cannot hold.** Android ships no ssh and no curl, so the
   phone must have Termux installed once, from F-Droid (the Play Store build is
   deprecated and breaks `pkg`) `[VERIFY]`. After that, the paste line works.
   The realistic Android onboarding is: install Termux, grant it storage,
   camera, and notification permissions, then paste one line. That is "install
   an app and grant permissions", not "just paste".

2. **The tunnel fights Doze.** Android aggressively suspends background apps. The
   tunnel needs `termux-wake-lock` and the Termux:Boot add-on to come back after
   the screen locks or the phone restarts `[VERIFY]`. Even then, an OEM's
   battery manager may kill it, so the connection is less reliable than a
   laptop's and may need the phone's battery settings relaxed for Termux, which
   is more taps.

## Refuse condition

At least one must hold for this to be worth building. This one does: the owner
asked whether it is possible, which is a real gap in a tool whose whole point is
reaching the machines a friend actually has, and phones are most of those. The
plan may still land as "Termux mode yes, ADB mode later", which is a scoping
call, not a refusal.

## Directives, each with a check

| ID | Directive | Check |
|---|---|---|
| A1 | The bootstrap detects Android and takes the Termux branch | on a phone, `uname -o` is `Android` and `$PREFIX` contains `com.termux`; the branch runs |
| A2 | The Termux branch installs openssh, rsync, termux-api and needs no sudo | a fresh Termux runs the paste line with no privilege prompt and ends connected |
| A3 | sshd runs on 8022 and the reverse tunnel forwards the console port to 127.0.0.1:8022 | `csync run <phone> -- uname -o` prints `Android` through the tunnel |
| A4 | The tunnel survives screen-lock and reboot | lock the phone, wait past Doze, `csync ls` still shows it online; reboot, it reconnects `[VERIFY]` |
| A5 | `info`, `say`, `push`, `pull`, `open`, `recipe` work; `shot` returns a camera frame and a clear message that screen capture needs the ADB mode | run each; read the camera photo back; confirm the shot message |
| A6 | teardown removes the key line, stops sshd, releases the wake-lock, removes `~/.csync`, and leaves no Termux:Boot script behind | after teardown, `find ~ -name '*csync*'` in Termux is empty and the boot script is gone |
| A7 | The gate refuses the destructive list in the Termux shell too | `csync run <phone> -- rm -rf ~` is refused with the reason logged |

## ADB mode, as its own later milestone

A second, optional way to reach a phone, for the two things Termux cannot do and
for a phone with no Termux. Over Wireless Debugging (Android 11+), a paired
computer can run `adb exec-out screencap -p` for a real screen shot,
`adb pull`/`push` for files, and `adb shell dumpsys` for deep device state, all
with no root. It does not fit the reverse-tunnel model, since the console reaches
the phone rather than the reverse, and it needs Developer Options plus a pairing
step, so it is a distinct mode with its own onboarding. Worth it only if the
screen-capture gap matters in practice.

## What needs a real phone before any of this is called done

Every `[VERIFY]` above, in one session on an Android device: that F-Droid Termux
still gives a working `pkg` and `sshd` on the current Android version; that the
wake-lock plus Termux:Boot keeps the tunnel up through Doze and a reboot; that
`termux-camera-photo` and the Termux:API verbs return what this plan assumes; and
that `logcat` without root is as limited as stated. A Linux VM cannot stand in
for this, because the Doze and permission behaviour is the Android part and that
is exactly what a VM does not have.

## Recommendation

Build the Termux target mode as csync v2, alongside the Windows mode already
parked in the spec. Treat it as "reaches the phone and drives it, with camera not
screen, and a documented one-time Termux install", and keep the ADB screen-and-
logs mode as a later, optional milestone gated on whether the gap actually bites.
State the two deviations to the owner up front, because they change what "csync
on a phone" honestly promises.

## Decisions the owner holds

| Id | Question | Default if silent |
|---|---|---|
| B1 | Is "install Termux once, then paste" an acceptable Android onboarding, given the laptop promise was "just paste" | yes; it is the only non-root option |
| B2 | Is camera-only capture enough for v2, with real screen capture deferred to the ADB mode | yes; defer ADB |
| B3 | Build the Termux mode now, or hold it until the macOS and Linux paths are confirmed on real second machines | hold until the laptop spikes pass, then build |
