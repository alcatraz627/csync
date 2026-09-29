# Android 2.30 Pi APK checkpoint — 28 September 2026

## Build and staged file

The Android source at `/Users/alcatraz627/Code/csync-hub` now uses `versionCode 32` and `versionName 2.30`. `JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew assembleDebug --offline` exited 0 with `BUILD SUCCESSFUL in 632ms` and 34 tasks (7 executed). `/opt/homebrew/share/android-commandlinetools/build-tools/34.0.0/aapt dump badging` reported package `com.csync.hub`, code 32, name 2.30. `git diff --check` exited 0. The exact checkpoint copy is `/private/tmp/csync-hub-230-checkpoint.apk`, 5,853,935 bytes, SHA-256 `1b8878a5c7d2c4bb9c9e1726b3a683aaf76654fc57cebaea001e3091f756a84e`.

The Pi's previously served APK matched the recorded 2.29 hash `a51796a1bdcc004235fb2dbbcdfce1ee93a15f7e2b9eb0cbb07b490e83a4f391`. I uploaded the 2.30 checkpoint to a temporary Pi path and verified its hash. A guarded script copied 2.29 to `/home/alcatraz627/.local/state/csync/csync-hub-update-2.29-before-2.30.apk` and verified the backup. It then atomically replaced `/home/alcatraz627/.local/state/csync/csync-hub-update.apk` and checked the served file's 2.30 hash. The script exited 0 and printed both expected hashes.

An authenticated live `GET http://100.65.188.9:8792/v1/app/apk` returned HTTP 200, `application/vnd.android.package-archive`, 5,853,935 bytes, and SHA-256 `1b8878a5c7d2c4bb9c9e1726b3a683aaf76654fc57cebaea001e3091f756a84e`. The endpoint serves the exact checkpoint file.

This checkpoint contains the agent's Tools/Process/Widgets structure work and the parent's Pi Note screenshot and incoming Image actions. The installed page and image test evidence is in `/Users/alcatraz627/Code/Claude/csync/.claude/output/20260928-appwide-tools-handoff.md` and `/Users/alcatraz627/Code/Claude/csync/.claude/output/20260928-circular-share-gap.md`. Full 28-route native parity remains open.

`python3 -m py_compile /Users/alcatraz627/Code/Claude/csync/.claude/output/20260928-update-pi-notes-230.py` exited 0. Running that script updated the live progress Note to revision 18 with 51 screenshots and the testable-features Note to revision 14. An authenticated read confirmed both 2.30 labels and the image count. The progress Note describes the staged APK and its still-pending 2.29→2.30 in-app test, plus the image round trip and exact wallpaper restoration. Four installed emulator captures were attached.

## In-app update gate

The 2.29→2.30 in-app update passed on the emulator. I downloaded `/home/alcatraz627/.local/state/csync/csync-hub-update-2.29-before-2.30.apk` to `/private/tmp/csync-hub-pi-229-for-update.apk` and verified SHA-256 `a51796a1bdcc004235fb2dbbcdfce1ee93a15f7e2b9eb0cbb07b490e83a4f391`. `aapt dump badging` reported package `com.csync.hub`, code 31, name 2.29. `adb install -r -d` returned `Success`, and Android package info reported code 31/name 2.29.

I opened Home → More → Tools and found the Update csync from Pi control in the scrolled overview. `/private/tmp/csync-230-update-entry-20260928.png` captures the entry before tapping it. After tapping it, Android closed the app during installation. Package info then reported code 32/name 2.30. I reopened the app; Home reported “Raspberry Pi is ready” and its Pi badge was Online. Capture: `/private/tmp/csync-230-home-after-update-20260928.png`. Pulling Android's installed `base.apk` to `/private/tmp/csync-hub-installed-after-pi-230.apk` yielded the exact served SHA-256 `1b8878a5c7d2c4bb9c9e1726b3a683aaf76654fc57cebaea001e3091f756a84e`. Authenticated live requests to Pi mesh `/whoami` on 8790, assistant `/whoami` on 8791, and media `/v1/display/wallpaper` on 8792 each returned HTTP 200.

The update path is verified on the emulator with the exact Pi APK and retained Pi connectivity. The owner's physical phone remains UNRUN. Later Android source edits after this checkpoint are not in the staged 2.30 APK.

`python3 -m py_compile /Users/alcatraz627/Code/Claude/csync/.claude/output/20260928-confirm-pi-notes-230-update.py` exited 0. Running the script changed the progress Pi Note to revision 19 with 53 images and the “things to try” Pi Note to revision 15. An authenticated read confirmed the installer result in both bodies and the image count. The two new attachments show the updater entry on 2.29 and Home after 2.30 installed.
