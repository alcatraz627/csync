# Home parent review, 28 September 2026

Status: **Home visual and checked controls PASS; offline state UNRUN**. The delegated Home correction and the parent's Media bottom-navigation fix are installed in the emulator. The parent inspected whole-frame light, dark, large-text, and scrolled captures, read the delegated interaction report, then rebuilt and checked the final shared bottom bar. The Home callout gate exited 0 after fresh rechecks. Search is a separate route and remains open.

## Reference and installed frames

| State | Current clickthrough | Installed Android |
| --- | --- | --- |
| Light, normal | `/private/tmp/csync-current-clickthrough-home.png` | `/private/tmp/csync-sol-home-final-light-normal.png` |
| Dark, normal | `/private/tmp/csync-current-clickthrough-home-dark.png` | `/private/tmp/csync-sol-home-final-dark-normal.png` |
| Light, large text | Current clickthrough route at normal text is the design reference; large-text behavior is checked as a native constraint. | `/private/tmp/csync-sol-home-final-light-large.png` |
| Dark, large text | Same reference. | `/private/tmp/csync-sol-home-final-dark-large.png` |
| Scrolled bottom | Current clickthrough scroll includes the lower Capabilities cards and Pick up. | `/private/tmp/csync-sol-home-final-light-scrolled.png`, `/private/tmp/csync-sol-home-final-dark-scrolled.png` |

The current `/Users/alcatraz627/Code/Claude/csync/assets/android-ui-clickthrough/app.js` SHA-256 is `33afbce0354b03cf1d99268b2dc971a3dbeed00ea580b9f2c6ecc24c29efc81f`. The prior hero screenshot came from older HTML and is not a valid acceptance frame.

## Whole-frame visual reading

The installed screen shows a compact Home context row, a plain Pi heading, Devices, two-column Capabilities, Pick up below the fold, and five icon-only bottom tabs. The section headers now use drawn chevrons. Pi and Mac badges and row arrows align as trailing groups. Card icon/title rows are vertically centered; supporting lines are below them with a consistent gap. The light and dark frames preserve the same hierarchy. At 1.3x font scale the cards become a single column, their text remains visible, and the bottom navigation remains reachable. The scrolled frame shows the final Tools card and Pick up row.

## Parent checks and remaining work

1. **PASS:** The delegated report at `/Users/alcatraz627/Code/Claude/csync/.claude/output/20260928-sol-home-ui-final.md` records installed collapse/expand, Search dialog, Media, Camera, Pick up, deep-route return, and light/dark/large/scrolled screenshots. The parent inspected those frames and source.
2. **PASS:** The parent changed `/Users/alcatraz627/Code/csync-hub/app/src/main/res/layout/activity_media.xml` to the same 64dp icon-only bottom bar. `assembleDebug --offline` exited 0 (`BUILD SUCCESSFUL in 519ms`); `adb install -r` returned `Success`. `/private/tmp/csync-media-icons-only.png` shows five icons and selected Media. The Android hierarchy exposed accessible names Home, Media, Share, Chat, More. Returning to Home produced `/private/tmp/csync-home-parent-final.png` with the same corrected hierarchy.
3. **PASS:** `bash /Users/alcatraz627/.claude/scripts/callouts/callouts.sh gate android-ui-home` exited 0: `gate clean: every open call-out on 'android-ui-home' has a fresh pass recheck`. Rows remain open for owner review.
4. **UNRUN:** Pi-offline runtime behavior was not exercised in this Home pass. It needs a controlled disconnected state and a restored connection.
5. **OPEN:** Search still opens a dialog for chats and devices; the clickthrough has a separate scoped mixed-result route. Its page loop has not started.

The Pi still serves Android 2.28/code30. This Home revision has not been staged there.
