# Android 2.32 Pi release — 28 September 2026

The owner stopped further feature and visual testing and asked for the current Android changes to be packaged and deployed. This is a deployment checkpoint, not a claim that all 28 native routes or the physical phone passed.

## APK and Pi deployment

- `/Users/alcatraz627/Code/csync-hub/app/build.gradle` now sets versionCode 34 and versionName 2.32.
- `JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew assembleDebug --offline --console=plain` exited 0: `BUILD SUCCESSFUL in 959ms`, 34 actionable tasks, 7 executed, 27 up-to-date.
- `/opt/homebrew/share/android-commandlinetools/build-tools/34.0.0/aapt dump badging app/build/outputs/apk/debug/app-debug.apk` reported `package: name='com.csync.hub' versionCode='34' versionName='2.32'`.
- The build and `/private/tmp/csync-hub-232-checkpoint.apk` are 5,904,339 bytes, SHA-256 `65d0a585be8932fdcbf96978996de231b07923c2443832f338c2d066fe0fd830`.
- Before replacement, the Pi's served APK matched the recorded 2.31 SHA-256 `6281d3e359e6c2bd58aa444311b9d5784e71d2c049478d4a4519fa490cec3436`.
- The upload was hash-checked before replacement. `/private/tmp/csync-stage-232.sh` backed up 2.31 to `/home/alcatraz627/.local/state/csync/csync-hub-update-2.31-before-2.32.apk` and atomically moved 2.32 to `/home/alcatraz627/.local/state/csync/csync-hub-update.apk`. The remote command exited 0 and printed the expected backup and live hashes.
- Authenticated `GET http://100.65.188.9:8792/v1/app/apk` returned HTTP 200, `application/vnd.android.package-archive`, 5,904,339 bytes, and the exact 2.32 SHA-256 above. This is the endpoint used by the app's Pi updater.
- `git diff --check` exited 0 in both `/Users/alcatraz627/Code/csync-hub` and `/Users/alcatraz627/Code/Claude/csync`.

## Pi Notes

The two existing Pi Notes were updated in place by `/Users/alcatraz627/Code/Claude/csync/.claude/output/20260928-update-pi-notes-232.py`: progress note `507509ca-bcf5-423d-830e-36be58e8bf62` is revision 23, and things-to-try note `058033af-9bd2-4ab1-a3c4-a2953b6a6a5c` is revision 19. Their new leading sections identify 2.32 as the current Pi APK, explain that older attached screenshots show emulator checkpoints, and state the testing boundary. Their earlier detailed history remains below those sections.

## Verification boundary

The previous Pi2.30→2.31 in-app update passed on the emulator with an installed APK hash equal to the Pi file. **2.31→2.32 installation through the app was not run**, at the owner's instruction to halt testing. The physical phone and Pi HDMI image/sound were unavailable. Open native screen, callout, sharing, and receiver checks remain in `/Users/alcatraz627/Code/Claude/csync/.claude/output/20260928-android-native-parity-tasks.md` and the task ledger. No commit or push was made.
