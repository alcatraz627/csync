# Camera and Captures native page handoff

**Page verdict: code ready for parent emulator review; native rendering and Pi runtime behavior are UNRUN.** Scope is the Camera and Captures pair only. No commit, push, deploy, emulator action, or other agent action was performed.

## Goal and source

The requested native pair follows the Camera and Captures dark references at `/private/tmp/csync-reference-20260928/camera-dark.png` and `/private/tmp/csync-reference-20260928/captures-dark.png`, the current clickthrough routes in `/Users/alcatraz627/Code/Claude/csync/assets/android-ui-clickthrough/app.js:300-317`, and the live Pi camera contract in `/Users/alcatraz627/Code/Claude/csync/media/server.py:1010-1017` and `:1065-1072`. I read `/Users/alcatraz627/Code/Claude/csync/.claude/output/20260928-android-native-parity-tasks.md`, `/Users/alcatraz627/Code/Claude/csync/docs/android-ui-final-spec.md`, the Android README and UI brief, sibling More page, MainActivity lifecycle, existing MediaClient and FileProvider, and owner callouts. The clickthrough is a fixture; it does not establish installed behavior.

The native layout now has separate Camera and Captures views inside MainActivity's existing Camera page. Camera has a compact crumb, captures action, preview, status, three labeled controls, and After capture rows. Captures has its own heading, Pi-backed list, empty/loading/error states, and a Storage refresh row. It does not fabricate the clickthrough's sample photos, recordings, durations, or Today grouping; the Pi API returns only `name` and `bytes`.

## Changed files

- `/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/CameraController.java`: page switch and breadcrumb behavior at lines 119-187; guarded on-demand stream and observed status at lines 189-274; duplicate action guard at lines 276-303; Pi list, semantic rows, and item actions at lines 306-407; authenticated capture transfer, preview, open/share, and correct MIME at lines 410-483; save to phone at lines 485-544.
- `/Users/alcatraz627/Code/csync-hub/app/src/main/res/layout/page_camera_v2.xml`: compact top bar and Camera content at lines 1-85; distinct Captures route, list, and storage row at lines 86-122.
- `/Users/alcatraz627/Code/csync-hub/app/src/main/res/drawable/camera_action_bg.xml`: circular outlined Camera action surface.
- `/Users/alcatraz627/Code/csync-hub/app/src/main/res/drawable/camera_shutter_bg.xml`: circular shutter using the selected theme's primary color.
- `/Users/alcatraz627/Code/csync-hub/app/src/main/res/drawable/camera_record_dot.xml`: record-state dot icon.
- `/Users/alcatraz627/Code/Claude/csync/.claude/output/20260928-camera-captures-sol-handoff.md`: this report.

No other file was edited for this task. The Android repository already has many concurrent modified and untracked files; the five Android paths above are my scoped changes.

## Lifecycle and API correctness

- `/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/MainActivity.java:185,204,238,246` calls controller hide/show on route changes and pause/resume. The controller starts `/v1/camera/stream` only on the Camera subpage and closes the connection, clears the frame, and invalidates callbacks when Captures opens or Camera leaves (`CameraController.java:137-235`). This is **source proof of the intended client lifecycle**, not a measured Pi viewer count.
- The Pi stream handler unsubscribes in `finally` at `/Users/alcatraz627/Code/Claude/csync/media/server.py:1087-1110`. `/Users/alcatraz627/Code/Claude/csync/media/camera.py:118-138` finishes recording after the last listener leaves and terminates the capture process when idle. The controller relies on that server behavior when the preview closes, so it does not issue a racing duplicate Stop request. Explicit Stop remains available while recording is observed.
- Camera status is polled from `/v1/camera/status`; the controller uses the observed `recording` field for its control state (`CameraController.java:240-274`). Photo and Record require a live frame and status; one action is in flight at a time. Start/Stop responses update the observed state, and errors request a fresh status. Status text distinguishes loading, preview, recording, and error.
- Captures come from `/v1/camera/captures`, and bytes are fetched with the token from `/v1/camera/captures/{encoded name}` (`CameraController.java:306-337,410-483`). Photos preview inside the app and can open externally. MP4 opens through an Android video app. Both can share through a granted FileProvider URI and save to Downloads/csync or the document picker on older Android.
- Raw `.mjpeg` rows say Raw MJPEG. Their download, open, and share MIME is `video/x-motion-jpeg` (`CameraController.java:390-408`), matching `/Users/alcatraz627/Code/Claude/csync/media/server.py:1112-1117`. The UI warns that phone playback needs a compatible app; it never labels a raw recording MP4.

## Six-step check

| Step | Result | Evidence |
| --- | --- | --- |
| 1. Scope | PASS, source only | Inspected both dark references, clickthrough routes, final spec, task list, Android docs, sibling More layout, MainActivity, Pi service, and relevant callouts. Light/large mock frames and installed frames remain for parent. |
| 2. Implement | PASS, source only | Five Android paths listed above. The parent-owned MainActivity was untouched. |
| 3. Code check | PASS | Command in `/Users/alcatraz627/Code/csync-hub`: `JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew assembleDebug --offline`. Exit 0, `BUILD SUCCESSFUL in 1s`, `34 actionable tasks: 10 executed, 24 up-to-date`. One annotation-processor source-version warning and nonincremental processor note. `git diff --check` exited 0 with no output. |
| 4. Self review | UNRUN on device | Parent owns emulator. I inspected the two reference images and code hierarchy, but captured no installed screenshots and exercised no installed controls. |
| 5. Correctness | PARTIAL | Source checks cover token use, MIME, action guard, status, stale callbacks, and route lifecycle. Pi viewer count, exact list content, offline/error states, large text, both themes, Back behavior, URI grant, and external video apps need emulator and Pi exercise. |
| 6. Checkpoint | PASS | This report is the page checkpoint. Parent review is next; no next page was started. |

## Parent emulator check

1. Install the current offline APK on the parent's emulator. Open More → Pi camera. Capture whole frames at normal and large text in light and dark, plus a scrolled frame. Compare with the two `/private/tmp/csync-reference-20260928/` images and the current HTML source revision.
2. With Pi access, read authenticated `/v1/camera/status`. Camera should change `viewers` from 0 to 1 while previewing; Captures and any other tab should return it to 0. Reopen Camera and check it returns to 1. Check Camera error and offline states without leaking the token.
3. Tap Photo twice quickly, Record twice quickly, then Stop. Confirm one action at a time, the observed recording label, a saved item on Pi, and no duplicate command. Leave Camera during recording and confirm the Pi finishes it when the final listener leaves. Inspect the saved MP4 or raw MJPEG result.
4. Open Captures, test loading, empty, populated, missing item, and offline states. Test photo in-app preview, external open, share, and save. Test MP4 open/share/save. For a raw MJPEG item, check its label, warning, and `video/x-motion-jpeg` save/share/open intent. Verify FileProvider URI grants and return to the same list.
5. Test the crumb and hardware Back from Captures, Camera, and an external viewer. Check bottom navigation, accessibility names, 48dp targets, selected theme color, and large text. Record results against the open app-wide callouts in `/Users/alcatraz627/Code/Claude/csync/.claude/callouts.jsonl`; this scoped task did not recheck or retire them.

## Open gaps for parent

- **Hardware Back from Captures needs parent routing.** The crumb returns to Camera. This controller registers an `OnBackPressedCallback`, but `/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/MainActivity.java:513-518` overrides `onBackPressed()` and routes page 5 directly to More, so the callback may never receive hardware Back. MainActivity is outside my write scope. Parent should delegate Back to Captures when that subpage is open, then rerun the route check.
- The clickthrough's Show on Pi capture action has no confirmed capture-to-display endpoint or selected-file handoff in this scoped contract. The native item menu offers preview/open/share/save and leaves Pi display navigation with MainActivity. Parent must decide a real target contract before adding Show on Pi.
- The Captures list uses the Pi's `name` and `bytes`. The API supplies no duration or capture timestamp field, so rows derive a local time from the UTC filename when possible and show Raw MJPEG distinctly. The mock's Today/Storage grouping and video duration require richer server metadata or an explicitly accepted filename-derived grouping.
- Source/build checks cannot prove camera frames, viewer count, screenshot fidelity, external app availability, or physical camera behavior. Installed and Pi checks are UNRUN pending the parent's emulator review.
