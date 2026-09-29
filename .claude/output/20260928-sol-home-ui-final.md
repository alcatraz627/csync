# Native Home parity handoff — 2026-09-28

## Verdict

Home renders the current plain-headline clickthrough structure in light and dark, normal and 1.3 font scale. The Home controls exercised below work on the installed emulator build. The `android-ui-home` gate remains **FAIL** because Media uses a separate bottom navigation layout with visible labels. I stopped at the delegated Home boundary and did not edit Media.

## Reference and scope

- Current clickthrough light: `/private/tmp/csync-current-clickthrough-home.png`.
- Current clickthrough dark: `/private/tmp/csync-current-clickthrough-home-dark.png`.
- `/Users/alcatraz627/Code/Claude/csync/assets/android-ui-clickthrough/app.js` SHA-256: `33afbce0354b03cf1d99268b2dc971a3dbeed00ea580b9f2c6ecc24c29efc81f`, rechecked before comparison.
- The current clickthrough has a plain Home headline and no circle hero. The older `co-20260927-091724-60` whole-clickthrough route check was not rerun in this scoped native pass; Home has no hero.
- Only `/Users/alcatraz627/Code/csync-hub/app/src/main/res/layout/page_home_v2.xml`, Home methods in `/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/MainActivity.java`, and `/Users/alcatraz627/Code/csync-hub/app/src/main/res/layout/activity_main.xml` were edited by this pass. Parent's concurrent NotesActivity work was left alone. No commit or push.

## Changes

- `/Users/alcatraz627/Code/csync-hub/app/src/main/res/layout/page_home_v2.xml:33`: grouped Devices, Capabilities, and Pick up section icons/titles with 24dp drawn disclosure icons. Pi/Mac statuses now use a right-aligned badge plus 16dp arrow. Capability cards use consistent 82dp minimum height and 11dp padding. Pick up keeps a real title and trailing arrow. No fixture data or hero was added.
- `/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/MainActivity.java:226`: connected section and row chevrons, retained section click handlers and live capability routes. At `:434`, card icon/title rows use a 20dp icon, 13sp title, 8dp horizontal gap, centered alignment, and supporting text underneath. At `:477`, a two-stroke drawable draws down/right chevrons instead of a text `v`. At `:376`, Pick up displays the latest real chat or start prompt. At `:250`, the start prompt opens a new chat. Pi's status dot now treats either assistant or media availability as online, matching its status text.
- `/Users/alcatraz627/Code/csync-hub/app/src/main/res/layout/activity_main.xml:25`: bottom bar uses five 24dp icons in a 64dp row with `labelVisibilityMode="unlabeled"`; item titles remain available for accessibility.

## Build and installed checks

- `JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew assembleDebug --offline` — exit 0, `BUILD SUCCESSFUL in 716ms`, 34 tasks: 4 executed, 30 up-to-date. The earlier visual-edit build also succeeded in 1s, 34 tasks: 10 executed, 24 up-to-date.
- `adb -s emulator-5554 install -r app/build/outputs/apk/debug/app-debug.apk` — exit 0, `Success`. Latest APK was launched and captured at `/private/tmp/csync-sol-home-final-installed-after-last-build.png` and scrolled at `/private/tmp/csync-sol-home-final-installed-scrolled.png`.
- The emulator's `dumpsys package com.csync.hub` reports `timeStamp=2026-09-28 02:22:42` and `lastUpdateTime=2026-09-28 02:22:42` (IST). That is the installed build used for the final Home interaction captures. The APK currently on disk has a later `stat` time of `2026-09-28 02:35:54 IST` from the parent's separate NotesActivity Pins rebuild. I did not install or exercise that later build, and I make no Pins runtime claim.
- `git diff --check` in `/Users/alcatraz627/Code/csync-hub` — exit 0, no output. The working tree contains extensive parent changes outside this page; no whole-repo clean-state claim.
- **PASS** Search icon opens the Search your hub dialog: `/private/tmp/csync-sol-home-search.png`.
- **PASS** Devices, Capabilities, and Pick up expand/collapse with down/right drawn chevrons. Light: `/private/tmp/csync-sol-home-devices-collapsed.png`, `/private/tmp/csync-sol-home-capabilities-collapsed.png`, `/private/tmp/csync-sol-home-pickup-collapsed.png`. Dark expanded `/private/tmp/csync-sol-home-dark-collapse-state.png`; dark all collapsed `/private/tmp/csync-sol-home-dark-three-collapsed.png`.
- **PASS** Pick up's empty-state row opens a new chat after the latest build: `/private/tmp/csync-sol-home-final-pickup-route.png`. Media capability opened MediaActivity; Camera capability opened its live preview. Home tab returned from deep routes.
- **PASS** Home, Share, Chat, and More bottom tabs show icons only with selected tint. Share `/private/tmp/csync-sol-home-nav-share.png`; Chat deep route `/private/tmp/csync-sol-home-final-pickup-route.png`; More `/private/tmp/csync-sol-home-nav-more.png`.
- **FAIL** Media tab shows visible bottom labels: `/private/tmp/csync-sol-home-nav-media.png`. `/Users/alcatraz627/Code/csync-hub/app/src/main/res/layout/activity_media.xml:189` explicitly sets `app:labelVisibilityMode="labeled"`. That file was outside my authorized edit scope. This prevents claiming five-tab icons-only parity.
- **UNRUN** Physical Android phone validation and Pi APK delivery. This pass installed only on `emulator-5554`.

## Whole-frame visual review

| State | Native screenshot |
| --- | --- |
| Light normal top | `/private/tmp/csync-sol-home-final-light-normal.png` |
| Light normal scrolled | `/private/tmp/csync-sol-home-final-light-scrolled.png` |
| Light 1.3 text top | `/private/tmp/csync-sol-home-final-light-large.png` |
| Light 1.3 text scrolled | `/private/tmp/csync-sol-home-final-light-large-scrolled.png` |
| Dark normal top | `/private/tmp/csync-sol-home-final-dark-normal.png` |
| Dark normal scrolled | `/private/tmp/csync-sol-home-final-dark-scrolled.png` |
| Dark 1.3 text top | `/private/tmp/csync-sol-home-final-dark-large.png` |
| Dark 1.3 text scrolled | `/private/tmp/csync-sol-home-final-dark-large-scrolled.png` |

The native frame now has the mock's headline, three collapsible sections, two-column capability rhythm at normal scale, compact icon/title card rows, trailing device statuses, and icons-only MainActivity tab bar. At 1.3 font scale, cards reflow to one column without clipping. Live data differs from the clickthrough fixture: native shows current Pi/Mac state and zero chats. Remaining visual differences: native device rows use status dots rather than the mock's icon tiles, section icons differ, and native card subtitles do not reproduce mock status bullets/counts. The latter would require live values and should not be copied from mock fixtures.

## Owner callouts

I ran `bash /Users/alcatraz627/.claude/scripts/callouts/callouts.sh gate android-ui-home` after recording these rechecks. It exited 1 and listed only `co-20260927-204449-73` as lacking a fresh pass. Rows were not retired.

| Row | Result | Evidence |
| --- | --- | --- |
| `co-20260927-204447-e5` chevrons | PASS | Light and dark expanded/collapsed captures above. |
| `co-20260927-204447-b4` proportions | PASS | Normal/large captures; explicit card dimensions above. |
| `co-20260927-204448-01` icon/text alignment | PASS | Whole-frame light/dark normal/large captures above. |
| `co-20260927-204448-76` card rhythm | PASS | Top/scrolled frames compared against current clickthrough light/dark. |
| `co-20260927-204449-73` icons-only tabs | FAIL | Media tab screenshot and `/Users/alcatraz627/Code/csync-hub/app/src/main/res/layout/activity_media.xml:189`. |
| `co-20260927-204449-c2` top bar | PASS | Light/dark Home top frames against current clickthrough. |
| `co-20260927-204450-0e` device ends | PASS | Pi/Mac status and arrow at normal/large in both themes. |

## Parent next action

Review the installed Home captures against the two current mock captures. If acceptable, handle Media's separate bottom nav in `/Users/alcatraz627/Code/csync-hub/app/src/main/res/layout/activity_media.xml:189`, rerun the five-tab callout, then run phone/Pi delivery checks in the parent workflow. The owner explicitly asked that the main agent atone for the earlier sloppy iteration; that message was sent through project IPC during this pass.
