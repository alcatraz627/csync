# Android 2.29 Pi update checkpoint — 28 September 2026

## Scope

This checkpoint records the staged Android update, the emulator installer run, and the two Pi Notes. It does not accept the whole Android UI: the 28-route review and the owner's app-wide callouts remain open.

## Build and Pi artifact

- Android package: `com.csync.hub`, `versionCode 31`, `versionName 2.29`.
- Offline Gradle command in `/Users/alcatraz627/Code/csync-hub`: `JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew assembleDebug --offline` → exit 0, `BUILD SUCCESSFUL in 912ms`.
- `aapt dump badging` reported package `com.csync.hub`, code 31, name 2.29.
- Debug APK SHA-256: `a51796a1bdcc004235fb2dbbcdfce1ee93a15f7e2b9eb0cbb07b490e83a4f391`.
- The prior Pi 2.28 APK hash was checked against `a084d78949c99f3106ba1dd313b5413ed48bbf10189335837f01eb55ee3fe3da`, then backed up to `/home/alcatraz627/.local/state/csync/csync-hub-update-2.28-before-2.29.apk`. The 2.29 APK was uploaded to a temporary path, hash checked, atomically moved to `/home/alcatraz627/.local/state/csync/csync-hub-update.apk`, and its served-file hash checked again.

## In-app installer exercise

The exact backed-up Pi 2.28 APK was downloaded to `/private/tmp/csync-hub-pi-228.apk` and matched the prior hash. `aapt` reported code 30/name 2.28. `adb install -r -d /private/tmp/csync-hub-pi-228.apk` returned `Success`; Android package info reported code 30/name 2.28. In More → Tools, the Update csync from Pi action showed a downloading state. After installation, Android package info reported code 31/name 2.29. The app reopened on Home with its saved Pi connection and current Pi reachability.

Evidence captures: `/private/tmp/csync-229-update-from-228.png` and `/private/tmp/csync-229-home-after-pi-update.png`. The updater was exercised on the emulator; the owner's physical phone remains untested.

Afterward, authenticated live requests to Pi mesh `/whoami` on port 8790, assistant `/whoami` on port 8791, and media `/v1/pins` on port 8792 each returned HTTP 200. The Pins response held zero items.
Pi `systemctl --user show` reported `ActiveState=active` for `csync-media.service`, `csync-assist.service`, and `csync-agent.service`.

The current Pi source test run returned `Ran 29 tests in 21.384s` and `OK` for `python3 -m unittest -v tests.test_media_service`. `go test -count=1 ./...` in `/Users/alcatraz627/Code/Claude/csync/assist` returned `ok` in 0.729s. These checks cover source contracts; they do not establish physical screen or phone behavior.

## Pi Notes and other observed app checks

`python3 /Users/alcatraz627/Code/Claude/csync/.claude/output/20260928-update-pi-notes-229.py` returned `{"progress_revision": 17, "progress_images": 47, "try_revision": 13}`. A later authenticated read returned the same revisions and image count, and found the 2.29 release labels in both bodies. Seven PNGs were added to the progress Note: update entry, post-update Home, Media bottom navigation, Pin list/detail tags, retained conflict draft, and cleaned Pin list. The second Note lists features the owner can try and labels unfinished routes.

The local candidate installed before staging showed Pin tags in list/detail and retained a stale edit draft after Pi `PIN_CONFLICT`. The disposable Pin was deleted through the app; authenticated Pi `GET /v1/pins` returned zero items. See `/Users/alcatraz627/Code/Claude/csync/.claude/output/20260928-pins-tags-conflict-check.md` for the runtime sequence.

## Open gates

- Complete native parity and a rendered interaction pass for all 28 clickthrough routes.
- Re-run the owner's open app-wide callouts across light/dark and normal/large text.
- Check search, Pi-offline Home, circular sharing for images/media/Notes, physical phone, mounted-drive playback, and visible HDMI output.
- Stage another coherent APK checkpoint after the app-wide UI pass, then repeat the in-app updater exercise.
