# Pins tag display and conflict check, 28 September 2026

Status: **local build and installed behavior checked; Pi APK release pending**. The Pi still serves Android 2.28/code30. This check used a later local APK on `emulator-5554`.

## Change

`/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/NotesActivity.java` now shows stored `#tags` on Pin list rows and in Pin detail. The Pin editor stays open until the Pi confirms Save. On a revision conflict or network error, Save is re-enabled, the draft remains in the fields, and an error appears in the editor.

## Installed journey

1. `JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew assembleDebug --offline` exited 0 with `BUILD SUCCESSFUL in 681ms` for the Pins code build. The later Media-bar build also exited 0 with `BUILD SUCCESSFUL in 519ms`. `adb install -r app/build/outputs/apk/debug/app-debug.apk` returned `Success`.
2. More → Pi Notes rendered the two real Pi Notes at revisions 12 and 16 and zero Pins. I created disposable text Pin `csync_tag_visibility_probe` with `tagone,tagtwo`. Its list row showed `Text snippet · #tagone  #tagtwo` in `/private/tmp/csync-pin-tags-list.png`. Its detail showed the same tags in `/private/tmp/csync-pin-tags-detail.png`.
3. I opened Edit pin with Pi revision 1, typed `local_draft_preserved`, then changed the same Pin on the Pi to title `remote_change` at revision 2 through authenticated PUT. The Pi returned `remote_revision 2`. Tapping Save in the still-open editor showed `Changed on Pi. Copy your edits, close, and reopen to refresh.` The local title and other fields stayed visible; Save was enabled again. The frame is `/private/tmp/csync-pin-conflict-draft.png`.
4. I canceled the stale editor, left and reopened Pi Notes, saw `remote_change`, then deleted the disposable Pin through the app. The list returned to `2 notes and 0 pins on Pi` and `No pins yet.` in `/private/tmp/csync-pin-tags-cleanup.png`. Authenticated Pi `GET /v1/pins` returned `pins_count 0`.

The conflict test deliberately used only a disposable Pin. The owner's two Notes and their screenshots were not edited. Pin editing after a conflict requires closing and reopening the Pin; an in-dialog merge or reload flow remains open. A full Notes/Pin page visual review, physical phone, and Pi updater run for this newer local APK remain open.
