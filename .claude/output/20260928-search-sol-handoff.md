# Native Search page handoff

## Scope and changed files

This page implements the approved Search route within the assigned two-file scope. It uses the shared Android visual tokens and existing icon assets. It contains no clickthrough fixture records.

- `/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/SearchActivity.java` — query, five scope tabs, live and saved result collection, row identity, loading/offline/empty states, and navigation intents.
- `/Users/alcatraz627/Code/csync-hub/app/src/main/res/layout/activity_search.xml` — breadcrumb, heading, search field, horizontal scope tabs, grouped result surface, source status, and icon-only bottom navigation.

I did not edit the launcher, manifest, destination activities, shared resources, or emulator state.

## Source and destination map

| Scope | Source read by Search | Identity carried by row | Destination intent |
| --- | --- | --- | --- |
| Media | Authenticated Pi `GET /v1/search?q=` through `MediaClient`; on zero matches, `GET /v1/drives` checks mounted source availability. | Server `id`, `driveId`, `relativePath`, query. | `MediaActivity` with `search_item_id`, `search_drive_id`, `search_relative_path`, `search_query`. The receiver needs the parent change below. |
| Chats | `ChatStore.index()` and `ChatStore.transcript()` on the phone. Search includes title and saved message text. | Conversation `id`. | `MainActivity` with `destination=chat`, `conversation_id`. The receiver needs the parent change below. |
| Files | Actual files under the app's `getExternalFilesDir("inbox")/<sender>/`. | Absolute inbox file path, retained in the result object and intent. | `MainActivity` with `destination=share`, `inbox_file_path`. The receiver needs the parent change below. |
| Devices | `PeerStore.load()` immediately; authenticated `MeshClient.peers()` from the configured Pi refreshes the roster. Saved rows say availability has not been checked until the scan returns. | Named peer. | Pi opens Media; other peers open Share with `recipient_name`. Share preselection needs the parent change below. |

The page debounces query changes, rejects stale network responses by generation, keeps saved results if Pi media or peer scanning fails, reports missing mounted drives and truncated Pi results, and retains query and scope when a child activity returns or Android recreates Search. No media request runs for an empty or overlong query. The result row and tabs have spoken labels and touch targets. Search's five-item bottom navigation uses the existing icon-only navigation component and resource menu.

## Required parent integration

1. In `/Users/alcatraz627/Code/csync-hub/app/src/main/AndroidManifest.xml`, register `.SearchActivity` with `android:exported="false"` and the normal app theme.
2. In `/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/MainActivity.java`, replace the `home_search` dialog launcher in `setupHomePage()` with `startActivity(new Intent(this, SearchActivity.class))`.
3. In `/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/MediaActivity.java`, consume the four `search_*` extras. Locate the actual item by server ID and open the same folder/output action as tapping that row. Do not silently fall back to a general list when the ID is absent; show an unavailable-item state. The current activity only handles `player_target` at creation, so exact media routing is **UNRUN**.
4. In `/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/MainActivity.java`, after Chat is initialized, consume `conversation_id` with the existing `openConversation(id, title)` path. For `inbox_file_path`, validate the path stays under the app inbox and select or reveal that exact received item. For `recipient_name`, select the matching named peer in Share without sending. The current activity consumes only `destination` and share drafts, so exact Chat, Files, and peer routing is **UNRUN**.
5. Install the parent-integrated build on the emulator. Capture Search light/dark at normal and large text and compare with `/private/tmp/csync-reference-20260928/search-light.png` and `/private/tmp/csync-reference-20260928/search-dark.png`. Exercise mixed result, each scope, empty query, no matches, Pi media offline, drive absent, Back from each result, breadcrumb, and all five navigation icons. This visual/runtime check is **UNRUN** because the parent retained the emulator and this Search activity is not yet registered.

## Checks and self review

- `JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew assembleDebug --offline` in `/Users/alcatraz627/Code/csync-hub`: **BUILD SUCCESSFUL in 719ms; 34 actionable tasks, 4 executed, 30 up-to-date**. Javac emitted one annotation-processor source-level warning and no Search compile error.
- `git diff --check`: exit 0. Since both Search files are untracked, I also ran `git diff --no-index --check /dev/null` on each; each exited 1 for a file difference and printed no whitespace error.
- Inspected the new-file diff summary: Search activity 459 added lines; layout 100 added lines. `git status --short` lists only those two Search paths in my scope.
- Visual structure was checked against the light and dark reference images. I could not render this unregistered activity, so spacing, color, large text, accessibility traversal, and navigation behavior are **UNRUN**, not accepted.

## Open behavior boundary

Pi media search is a live filename search of mounted drives. It does not search saved Pi history while the Pi is offline because the existing phone code has no persisted Pi media index. The page says when Pi media is unavailable; it does not label unavailable media as a successful match. Exact result routing depends on the parent changes above. No emulator installation or Pi APK checkpoint was made from this scoped build.
