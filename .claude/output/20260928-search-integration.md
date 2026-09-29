# Native Search integration, 2026-09-28 08:52 IST

## Source change

- `/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/MainActivity.java`: Home search opens the new SearchActivity. Its four result identities are consumed after page setup and on a new intent. A saved conversation ID opens that thread; a missing ID says it is no longer saved. An inbox file path is canonicalized under the app inbox, its exact row is highlighted and scrolled into view, and a missing or external path gets an unavailable message. A named recipient is selected only when it still exists in the roster; the recipient section remains visible and nothing is sent.
- `/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/MediaActivity.java`: a Search media ID is resolved against actual Pi folder pages by exact ID and relative path. A folder opens that folder; a file appears as the selected item and opens the same output menu as its row. Missing, changed, disconnected, and invalid items show an explicit unavailable state. The generic drives list is not used as a silent fallback. The same edit fixes empty search copy, the cross-drive folder label, and the dark slate bottom nav surface.
- SearchActivity and its layout were supplied by the isolated Sol handoff at `/Users/alcatraz627/Code/Claude/csync/.claude/output/20260928-search-sol-handoff.md`. The parent registered SearchActivity in `/Users/alcatraz627/Code/csync-hub/app/src/main/AndroidManifest.xml`.

## Checks and boundary

- `JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew assembleDebug --offline --console=plain`: exit 0, `BUILD SUCCESSFUL in 765ms`, 34 tasks, 4 executed, 30 up-to-date. `git diff --check`: exit 0.
- The parent has the shared emulator for Notes and Search. This integration has **not** been installed or tapped by this agent. Exact result routing, Back retention, unavailable states, light/dark large text, and Media nav color are **UNRUN** until the installed review.
- The Pi does not expose a direct item-by-ID endpoint. Media resolves the result within its reported parent folder and pages until the exact ID matches. A changed file version no longer matches and produces the unavailable state.
- The Media top Back control returns directly to Search when Media was opened from a Search result. The Chat conversation breadcrumb Back does the same for a Search-opened thread, including after Activity recreation. Android Back also returns to the underlying Search activity. These route transitions remain **UNRUN** on device. Latest offline build after these source changes exited 0: `BUILD SUCCESSFUL in 758ms`, 34 tasks, 4 executed.
- Main now saves the open Chat conversation even when its composer is empty, so a theme or text-size recreation can restore the exact thread and the Search-origin breadcrumb behavior. This source change is **UNRUN** on device. Latest offline build exited 0: `BUILD SUCCESSFUL in 747ms`, 34 tasks, 4 executed.

## Parent installed captures inspected read-only

The parent captured `/private/tmp/csync-search-media-exact-light.png`, `/private/tmp/csync-search-chat-open-light.png`, `/private/tmp/csync-search-named-share-light.png`, and `/private/tmp/csync-search-return2-mp4-light.png`. They show the exact Pi video output menu, the named saved conversation, the chosen named Share peer, and Search with `mp4` still in the field after returning. These are parent runtime probes, not actions this agent ran. The Share capture also shows an irrelevant home-peer configuration toast during automatic scanning; Main now tries the configured assistant host when the home peer is absent or fails. That later fallback is **UNRUN** on an installed build.

## Source recheck while emulator was with parent

- The current clickthrough `/Users/alcatraz627/Code/Claude/csync/assets/android-ui-clickthrough/app.js` SHA-256 is `33afbce0354b03cf1d99268b2dc971a3dbeed00ea580b9f2c6ecc24c29efc81f`.
- The Search launch intents in `/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/SearchActivity.java` carry `conversation_id`, `inbox_file_path`, `recipient_name`, and `search_item_id` plus drive/path/query. The Main and Media receivers consume these same keys. Main preserves the Search origin through Activity recreation; Media checks exact item ID and path in the Pi folder listing.
- `JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew assembleDebug --offline --console=plain`: exit 0, `BUILD SUCCESSFUL in 269ms`, 34 tasks up-to-date. `git diff --check`: exit 0. This was a source/build recheck; no emulator command was run during the parent's Notes/Search review.
- The Media Access address strings correspond to the share names and FTP binds in `/Users/alcatraz627/Code/Claude/csync/docs/media-operations.md`. `/v1/diagnostics` reports drives and player state, not an authenticated SMB/FTP login result. Access connection success remains **UNRUN**; the source does not claim it was exercised.
