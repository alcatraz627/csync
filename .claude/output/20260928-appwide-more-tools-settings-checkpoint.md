# More, Tools, and Settings installed checkpoint, 2026-09-28 06:14 IST

## Verdict

**FAIL/open for page acceptance.** This checkpoint proves route reachability and identifies remaining visual and behavior gaps. It is suitable for parent review and staging as an interim APK, not final acceptance.

## Build and installed source

- Android repository: `/Users/alcatraz627/Code/csync-hub`. Clickthrough JavaScript: `/Users/alcatraz627/Code/Claude/csync/assets/android-ui-clickthrough/app.js`, SHA-256 `33afbce0354b03cf1d99268b2dc971a3dbeed00ea580b9f2c6ecc24c29efc81f` when last checked.
- APK: `/Users/alcatraz627/Code/csync-hub/app/build/outputs/apk/debug/app-debug.apk`, modified `2026-09-28 06:07:41 IST`, size 6,159,694 bytes, SHA-256 `ea963dea1f05c400f3e76a0da82b4900e8d55c2ddbf28f4b054d91335b4c599e`.
- `JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew assembleDebug --offline`: exit 0, `BUILD SUCCESSFUL in 691ms`, 34 tasks, 4 executed, 30 up-to-date. `adb install -r /Users/alcatraz627/Code/csync-hub/app/build/outputs/apk/debug/app-debug.apk`: `Success`. `git diff --check`: exit 0.
- My page edits are in `/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/MainActivity.java`, `/Users/alcatraz627/Code/csync-hub/app/src/main/res/layout/page_more_v2.xml`, `/Users/alcatraz627/Code/csync-hub/app/src/main/res/layout/page_tools_v2.xml`, `/Users/alcatraz627/Code/csync-hub/app/src/main/res/layout/page_settings.xml`, and `/Users/alcatraz627/Code/csync-hub/app/src/main/res/values/themes.xml`. The shared tree has concurrent parent changes; this list is a page scope, not ownership of every diff hunk.

## Installed checks

| Route or action | Result | Evidence |
| --- | --- | --- |
| More overview, dark normal | PARTIAL | `/private/tmp/csync-more-current-dark.png`. Leading icons, aligned chevrons, Areas and Reference grouping, Pi Notes in Reference, Help route visible. Rows remain taller than the mock; Settings and Help reuse the same tune icon. |
| Assistant capabilities from More | PASS for destination and live Pi tool list; FAIL for final visual parity | Before fix: `/private/tmp/csync-more-current-capabilities.png` showed colliding name/description columns. After changing live rows to vertical cards and installing: `/private/tmp/csync-more-capabilities-fixed.png` is readable. Back returned to More. |
| Settings overview, dark normal | PARTIAL | `/private/tmp/csync-settings-current-dark.png`. Devices & connections and Media & display are above raw connection and Appearance fields. Large text and light theme UNRUN. |
| Settings > Raspberry Pi > Assistant settings | PASS for destination visibility, FAIL for separate-page parity | `/private/tmp/csync-settings-pi-menu.png` and `/private/tmp/csync-settings-assistant-current.png`. Provider, model, thinking and Apply are visible. The scroll target still leaves an Appearance row above the Assistant card; it should become a clean subpage. Back action and saving a provider change UNRUN. |
| Tools overview and utilities | PARTIAL | `/private/tmp/csync-tools-current-dark.png`, `/private/tmp/csync-tools-current-scrolled.png`. Live media and power health render; the Pi reports undervoltage. Process and Widgets routes are reachable but start below the fold because health cards are tall. |
| Widgets & quick actions route | PASS for route and truthful labels | `/private/tmp/csync-tools-widgets-current.png`. Built xkcd and planned media remote, Quick Settings, and app shortcuts are explicit. Back returned to Tools. |
| Process monitor route | PASS for route and unavailable state | `/private/tmp/csync-tools-process-current.png`. It identifies live phone sampling through Shizuku and planned Pi actions. Shizuku was not running, so live sampling was UNRUN. |
| Appearance controls | FAIL | `/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/Prefs.java` and `/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/Appearance.java` persist Light/Dark and four preset accents only. System theme, sm/md/lg text size, three review colors and Custom are absent. Cross-activity persistence for those missing modes cannot be exercised. |

## Open checks before page acceptance

1. Match the current light and dark mock for More, Settings and Tools at normal and 1.3 text scale. Inspect complete scrolled frames, not only each first viewport.
2. Make Settings detail routes render as clean subpages. Exercise Pi, Mac, Tailscale, Assistant, Appearance, media playback, and Back, including saved settings.
3. Implement and exercise approved Appearance choices across Main, Media, and Notes activities with legible system bars. The relevant callout `co-20260928-001940-bf` remains FAIL.
4. Exercise Help, Camera and Pi Notes destinations from More. Do not edit `/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/NotesActivity.java` until the parent hands it over.
5. Tools: exercise Refresh and update route separately; confirm xkcd widget behavior on a launcher if claimed. Process sampling remains UNRUN while Shizuku is off.

No owner callout rows were retired. This report records results for parent review; the open gates remain open.

## Source revision after the checkpoint, 07:22 IST

The installed Appearance frame `/private/tmp/csync-appearance-v4-large.png` still displayed the Settings overview above the detail card. I wrapped the overview in `settings_overview` in `/Users/alcatraz627/Code/csync-hub/app/src/main/res/layout/page_settings.xml` and changed `/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/MainActivity.java` to hide it while a detail is open, restore it on Back, and scroll the selected detail to the top. Offline `JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew assembleDebug --offline` exited 0: `BUILD SUCCESSFUL in 1s`, 34 tasks, 10 executed. `git diff --check` exited 0. The parent owns the emulator for the 2.29→2.30 updater test, so this Settings revision is **UNRUN** as installed UI and does not satisfy either open `android-ui-settings` callout yet.

## Installed Settings revision and provider guard, 07:47 IST

The parent returned the emulator after an exact 2.29→2.30 in-app updater test. I installed later local code32/name2.30 builds. The final installed `/Users/alcatraz627/Code/csync-hub/app/build/outputs/apk/debug/app-debug.apk` was modified 2026-09-28 07:46:22 IST, 6,221,385 bytes, SHA-256 `7d57832e000e9dfa98250060f04564c778558cba1ddbcf9c1930266b6bf83710`. `adb install -r` returned `Success`. This is **different** from the parent's staged and updater-tested Pi APK hash `1b8878a5c7d2c4bb9c9e1726b3a683aaf76654fc57cebaea001e3091f756a84e`. Final offline `assembleDebug --offline` exited 0: `BUILD SUCCESSFUL in 723ms` (34 tasks, 4 executed); `git diff --check` exited 0.

| Check | Result | Evidence |
| --- | --- | --- |
| Settings overview | PASS for current hierarchy | `/private/tmp/csync-settings-v5-overview-light.png` shows Devices & Connections, Media & Display, Assistant and App rows, with fixed five-icon nav. |
| Appearance detail and Back | PASS for route separation, FAIL for full Appearance contract | `/private/tmp/csync-settings-v5-appearance-light.png` shows only the detail at top; `/private/tmp/csync-settings-v5-back-light.png` shows overview restored. System theme, sm/md/lg, blue/leaf/rose and Custom remain missing. |
| Direct Assistant detail | PASS for navigation | `/private/tmp/csync-settings-v5-assistant-light.png` shows provider, model, effort and Apply at top with overview hidden. |
| Raspberry Pi → Assistant settings | PASS for destination | `/private/tmp/csync-settings-v5-pi-menu-light.png` menu selection reached `/private/tmp/csync-settings-v5-pi-assistant-light.png`. Provider Apply was not tapped; Pi config was not changed. |
| Provider support | PASS for disabled unsupported choice and client guard | Parent deployed Pi `/providers` support flags: Gemini true, Claude false. `/private/tmp/csync-settings-v7-provider-disabled.png` shows Claude greyed and a warning. Parsed installed `/private/tmp/csync-settings-provider-v7.xml`: Gemini `enabled=true checked=true`, Claude `enabled=false checked=false`. `/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/MainActivity.java:1286` uses the flag and defaults older Pi responses to Gemini only; line 1327 blocks unsupported Apply before POST. Claude was not selected for a test. |
| Run commands status | PASS for honest wording | `/private/tmp/csync-settings-v7-provider-disabled.png` says `Available with Pi approval`; line 1351 no longer maps an advertised command name to `on`. The actual Pi allow_exec gate was not exercised. |
| Tools Pi power null branch | UNRUN for null live value | `/private/tmp/csync-tools-null-fix-installed-light.png` currently shows `Undervoltage now` plus a real fix string. The branch that omits a null fix builds but the Pi did not return null during this installed check. |

Two new owner Settings callouts, `co-20260928-021830-7b` and `co-20260928-021830-6e`, have fresh PASS rechecks. The older Appearance callout `co-20260928-001940-bf` remains FAIL. Dark and 1.3-text Settings captures and the remaining Mac/Tailscale/connection behavior are still UNRUN in this revision. No rows were retired.
