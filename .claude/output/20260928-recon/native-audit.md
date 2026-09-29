# csync Android native app vs design mock: recon audit

Session: 2026-09-28. Read-only on source (csync-hub and csync repos untouched).
Build and install only, plus adb driving of the emulator.

## 1. Installed version, before and after

| | versionCode | versionName |
|---|---|---|
| Installed before this session | 33 | 2.31 |
| Fresh debug build, installed this session | 34 | 2.32 |

Build: `env JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home /Users/alcatraz627/Code/csync-hub/gradlew -p /Users/alcatraz627/Code/csync-hub assembleDebug --offline --console=plain`
Result: BUILD SUCCESSFUL, all 34 tasks UP-TO-DATE. The build already reflected the uncommitted Codex working-tree changes. APK: `/Users/alcatraz627/Code/csync-hub/app/build/outputs/apk/debug/app-debug.apk`, installed with `adb -s emulator-5554 install -r`.

No crashes. `adb logcat -d -t 300 '*:E'` filtered for `com.csync.hub` / `FATAL` / `AndroidRuntime` returned zero lines across the whole drive session (Home, Search, Media x4 tabs, Share, Inbox, Chat list plus conversation, Camera, Captures, Tools, More, Settings, Appearance x2 theme switches, Notes, Note detail, Player).

## 2. Source map: screen to Activity/method to layout XML

Everything except Search, Media, and Notes lives inside one God Activity, `MainActivity.java` (2728 lines). It inflates each "page" as a `View` swapped into a single content frame rather than using separate Activities or Fragments.

| Screen (mock id) | Built by | Layout XML actually inflated | file:line |
|---|---|---|---|
| Home | `MainActivity.onCreate` | `page_home_v2.xml` | `MainActivity.java:78` |
| Share / Compose (plus Inbox, merged) | `MainActivity.onCreate` | `page_share_v2.xml` | `MainActivity.java:79` |
| Chat list and conversation | `MainActivity.onCreate` | `page_chat.xml` (no v2 exists) | `MainActivity.java:80` |
| Tools/Diagnostics | `MainActivity.onCreate` | `page_tools_v2.xml` | `MainActivity.java:81` |
| Settings and Appearance | `MainActivity.onCreate` | `page_settings.xml` (no v2 exists) | `MainActivity.java:82` |
| Camera (live preview) | `MainActivity.onCreate` | `page_camera_v2.xml` | `MainActivity.java:83` |
| More | `MainActivity.onCreate` | `page_more_v2.xml` | `MainActivity.java:84` |
| Media Files/Videos/History/Access | `MediaActivity.onCreate` | `activity_media.xml` | `MediaActivity.java:88` |
| Search | `SearchActivity.onCreate` | `activity_search.xml` | `SearchActivity.java:76` |
| Notes / Note detail | `NotesActivity.onCreate` | none. `setContentView(root)`, `root` is a `LinearLayout` built entirely in Java | `NotesActivity.java:68` |
| Share-target intent receiver (Android's system Share Sheet into csync) | `ShareActivity` | none. No `setContentView` call at all; this class only handles the incoming-share intent, it is not the Compose screen | grep confirmed, no match |

Dead layout files (present in `res/layout/`, never inflated by any code path, confirmed via `rg "R.layout\."` across all Java sources): `page_home.xml` (82 lines), `page_tools.xml` (94), `page_camera.xml` (31), `page_more.xml` (43), `page_share.xml` (103). All five were superseded by their `_v2` counterparts. 353 dead lines total. Live, non-`_v2` layouts still in use: `page_chat.xml` (237 lines), `page_settings.xml` (289 lines). These never got a v2 pass.

## 3. Native screenshots captured (emulator-5554, dark unless noted)

All under `/Users/alcatraz627/Code/Claude/csync/.claude/output/20260928-recon/native-shots/`:
`native-home-dark.png`, `native-home-light.png`, `native-search-dark.png`, `native-media-files-dark.png`, `native-media-videos-dark.png`, `native-media-history-dark.png`, `native-media-access-dark.png`, `native-player-dark.png` (full player and mini player both visible in one capture, live playback), `native-share-dark.png` (compose plus merged inbox section), `native-inbox-dark.png` (same page, scrolled), `native-chat-history-dark.png`, `native-chat-view-dark.png`, `native-camera-dark.png`, `native-captures-dark.png`, `native-tools-dark.png`, `native-more-dark.png`, `native-more-light.png`, `native-settings-dark.png`, `native-appearance-dark.png`, `native-appearance-light.png`, `native-notes-dark.png`, `native-note-detail-dark.png`.

Matching mock screenshots were captured with a purpose-built Playwright script (`native-shots/mockcap.mjs`, read-only against the mock, drives `state`/`render()` in the click-through and screenshots the `#phone` element at 412x915): `mock-home-dark.png`, `mock-home-light.png`, `mock-search-dark.png`, `mock-media-files-dark.png`, `mock-media-videos-dark.png`, `mock-media-history-dark.png`, `mock-media-access-dark.png`, `mock-player-dark.png`, `mock-share-dark.png`, `mock-inbox-dark.png`, `mock-chat-history-dark.png`, `mock-chat-view-dark.png`, `mock-camera-dark.png`, `mock-captures-dark.png`, `mock-tools-dark.png`, `mock-notes-dark.png`, `mock-note-detail-dark.png`, `mock-more-dark.png`, `mock-more-light.png`, `mock-settings-dark.png`, `mock-appearance-dark.png`.

## 4. Per-screen parity

| Screen | Native state | Verdict | Concrete differences |
|---|---|---|---|
| Home | Live: Pi Online, Mac Offline, capability tiles | CLOSE | Structure matches (breadcrumb, hero line, DEVICES/CAPABILITIES sections, 2-col capability grid, 5-tab bottom nav). Native device cards use a plain colored dot for status; mock uses an icon-avatar square. Native capability subtitles are mostly static copy ("Browse Pi files", "Choose a saved device") where the mock shows live counts ("121 videos, Pi ready", "3 threads, assistant ready"). Only Chat's subtitle is genuinely live-derived ("1 saved conversation"). |
| Search | Live: 8 results, All/Media/Chats/Files/Devices filter chips | CLOSE | Structure matches closely: heading, subheading, search box, filter row, numbered results list with icons. Mock's filter row order and icon set line up. No major gaps found. |
| Media / Files | Native gates on "Choose a drive" (Pi USB and Elements both show Disconnected) before any folder/file list renders | FAR | Mock jumps straight into a FOLDERS/FILES listing with real rows (Media, Shared, Photos folders; Sample film.mp4 etc.) under a "Search Pi USB" box. No drive-picker step shown by default. Native never got to render an actual file/folder row in this session because both drives are disconnected in the emulator; the drive-chooser step itself is a structural addition not in the mock. Breadcrumb label differs too: native says "Files", mock says "Media" for the parent crumb region. |
| Media / Videos | "Videos, 0 files", "No videos found, connect a drive or browse its folders" | CLOSE (structure) / UNCONFIRMED (content) | Tab strip and empty-state card style match the visual language. Could not verify the populated-list state since no drive is connected. |
| Media / History | Live: 4+ real resume entries (YouTube titles, Pi-USB video, "Resume at" timestamps) | MATCH | Structural elements (CONTINUE header, card layout, Resume button, chevron) line up with mock's History screen. This is clearly real, working functionality, not a stub. |
| Media / Access | Live: real SMB/FTP URLs (`smb://100.65.188.9/sandisk`, `ftp://100.65.188.9/Media`), Sources list, "Check Pi media service" with live status ("Pi media reachable, SMB and FTP sign-in not checked") | MATCH | Rich, genuinely wired-up screen. Sections (PI USB ACCESS / SOURCES / CONNECTION) match the mock's intent for an Access screen even though the mock's own Access screen wasn't in the captured set for a 1:1 pixel check. |
| Full Player | Live: "F-Droid 2.0 - The Biggest Update In Years" actually playing on the Pi, position 5:45/10:18 advancing, volume 0%, transport row (favorite/prev/pause/next/stop/settings), PLAYBACK grid (Volume/Speed/Rotate/Loop) | MATCH | Structure matches the mock's player concept (title, scrub bar, transport row, secondary controls grid) closely. The preview area correctly shows "Preview unavailable on this screen" rather than faking a video thumbnail. Honest empty state. |
| Mini player | Visible as a persistent bottom bar above the nav (title, progress bar, Pause/Stop) while playback is active, on Home in this capture | MATCH | Present and functional. Appears and disappears with playback state as expected. |
| Share / Compose | Live: recipient auto-selected ("Send to xiaomi-m2101k6p"), Message box, Send text/Clipboard buttons, File chooser row | CLOSE | Mock's Compose page has a distinct "Sent from this device" history list with delivered items. Native has the same section header but shows "No sends yet" (correct empty state, unverified against a populated state). |
| Inbox | Not a separate screen. Merged into the bottom of the same Share/Compose page as an "INBOX" section ("Nothing received yet.") | FAR | The mock treats Compose (`share`) and Inbox as two distinct routable screens, reached differently (Inbox via a dedicated icon). Native's "Inbox" icon just scrolls the same Compose page to reveal a section. No separate screen, no separate breadcrumb. This is a structural, not cosmetic, mismatch. |
| Chat / Conversations | Live: "Pi online, saved threads", All/Favorites/Archived/Tools filter row, search box, 1 real conversation row, New chat / Settings buttons | MATCH | Structure and content both line up well with the mock's Conversations screen. |
| Chat / Conversation | Live: real chat session "UI-control-check", model badge "gemini-3.8-flash, medium", Thinking/Available skills (21 skills) expandable blocks, message composer "Message the Pi" | MATCH | Functional, not a stub. Actual assistant plumbing visible (thinking traces, skill count). |
| Camera | "Connecting to Pi camera" (preview never resolved in this session, Pi camera stream unreachable from emulator), transport row (history/photo/record), AFTER CAPTURE section with Captures/Pi display links | CLOSE | Structure matches. Honest "connecting" empty state rather than a fake preview. Could not verify the live video preview itself resolves (backend not reachable for this specific stream in the sandbox). |
| Captures | Live: "28 saved on Pi", real recording and photo rows with timestamps and file sizes | MATCH | Rich, working list. Clearly not a stub. |
| Tools / Diagnostics | Live: "One issue to check" leads to a real undervoltage warning with Recheck button, SERVICE HEALTH (Pi media service: reachable, Pi power: undervoltage now, App performance: planned), UTILITIES (Browse Pi media, Process monitor via Shizuku, Widgets) | MATCH | Genuinely live hardware diagnostics. Undervoltage detection is a real signal, not a placeholder. Matches the mock's "mixed: built plus planned" status for this area. |
| More | Live: AREAS (Pi camera, Tools & diagnostics, Settings) plus REFERENCE (Assistant capabilities, Pi Notes, Help and about) | MATCH | Matches mock's More screen concept (parent-child return hub) well. |
| Settings | Live: DEVICES & CONNECTIONS (Raspberry Pi, Mac, Tailscale & pairing), MEDIA & DISPLAY, ASSISTANT (Provider & model), APP (Appearance) | MATCH | Section grouping and content both line up with the mock's Settings screen intent. |
| Appearance | Live and functional: Theme (System/Light/Dark, verified toggling both ways during this session), Text size (sm/md/lg), Primary color (7 swatches plus custom picker) | MATCH | This is a genuinely built, working feature. Toggling Light/Dark in the emulator visibly re-themed the whole app instantly, matching the mock's "Set the whole phone interface" framing almost exactly, including the copy "Applies across screens and system bars; status colors keep their meaning." |
| Notes | Live: "2 notes and 0 pins on Pi", search box, 2 real saved notes with revision numbers, New note / Save a pin buttons | MATCH (content), bug found | Bottom nav highlights "Home" as the active tab while on Notes (Notes isn't one of the 5 primary tabs, reached via More). A minor but real state-tracking inconsistency, not present in the mock, which has its own Notes tab state. |
| Note detail | Live: real markdown note, Share/Add image/Delete actions, Preview/Rich/Plain mode tabs, rendered markdown body (headings, bold, code span) | MATCH | Matches the mock's "One markdown source, plain/rich/preview, share and delete" description closely. This is a working markdown editor, not a stub. |

## 5. Implementation approach: Material vs hand-rolled

- `grep -c "MaterialToolbar\|BottomNavigationView\|BottomSheetDialogFragment\|Chip\|MaterialButton\|MaterialCardView"` across `app/src/main/java/com/csync/hub/*.java`: MainActivity 18 hits, SixTabNavigationView 2, SearchActivity 1, MediaActivity 1, NotesActivity 2. `SixTabNavigationView.java:7` does `extends BottomNavigationView` (real Material component, not reinvented), so the bottom nav itself is legitimate Material.
- Everything inside each "page" is built by hand in Java. `grep -c "new LinearLayout(\|new TextView(\|new Button(\|.setBackgroundColor(\|.setTextColor(\|GradientDrawable("`: MainActivity 82, NotesActivity 55, MediaActivity 39, SearchActivity 15. That is a lot of one-off, per-call-site view construction and styling rather than declarative XML plus a shared style/theme layer.
- No `styles.xml` exists in `app/src/main/res/values/` at all (`find` returned nothing). Only `themes.xml` (245 lines). Per-page visual decisions (card backgrounds, corner radii, spacing) are made ad hoc in Java (`GradientDrawable`, `setBackgroundColor`, `setTextColor` calls scattered through MainActivity/NotesActivity/MediaActivity) rather than through a shared style resource layer.
- `NotesActivity.java:68` does `setContentView(root)` where `root` is assembled entirely in Java, no XML at all for Notes/Note-detail. The most hand-rolled screen in the app despite being one of the better-matching screens visually.
- `ShareActivity.java` never calls `setContentView`. It's purely an intent-handling shim for Android's system Share Sheet, not a UI screen; the actual Compose UI lives inside `MainActivity`'s `page_share_v2.xml`.

**MainActivity size estimate**: 2728 total lines; 14 private helper methods with signatures matching `View`/`LinearLayout`/`TextView`/`Button`-returning builders (`rg -c "private (View|LinearLayout|TextView|Button) "`), plus the 82 direct `new View(...)`/styling calls above. A conservative read is that well over half of MainActivity's body is layout-building and styling code interleaved with business logic, not separated into layout XML plus a thin controller.

## 6. Functional smoke notes

- Nav tabs (Home/Media/Share/Chat/More): all opened without crash across the whole session.
- Back arrow and breadcrumb back navigation worked correctly everywhere it was used (Camera to Captures to back to back to More; Search to back to Home; etc).
- Sub-tab strips (Media's Files/Videos/History/Access): all four switched cleanly.
- One real UI bug found: on the Notes screen (reached via More, then Pi Notes), the bottom nav's "Home" icon stays visually highlighted even though Notes is not one of the five primary destinations. A leftover or incorrect active-tab state, not present in the mock.
- Two real data-model gaps found (not bugs, but places where the native app's flow differs structurally from the mock's screen model, not just visually):
  1. Inbox is not a routable screen; it is a scrolled section of the Compose page.
  2. Media / Files gates all folder/file content behind a "Choose a drive" step that isn't present in the mock's default state.
- `adb logcat -d -t 300 '*:E'`, filtered by reading (not piped) for `csync`/`FATAL`/`AndroidRuntime`: zero matches across the entire session. No crashes were triggered by any of the navigation above.
- Connectivity observed during the session: Home's device tile, Chat, History, Access, Player, and Tools all showed live Pi data (device online, real watch history, real SMB/FTP addresses, real playback, real undervoltage reading). Media's drive-level browsing (Files/Videos tabs) showed both Pi USB and Elements as "Disconnected" the whole session. This is a different connectivity path (USB-drive mount, not the Pi media-service API) and was not something this task could fix per the given constraints.

## 7. Honest overall estimate

Of the screens and states in scope for this audit, this session found 13 MATCH (Media/History, Media/Access, full Player, mini player, Chat list, Chat conversation, Captures, Tools, More, Settings, Appearance, Notes, Note detail), 5 CLOSE (Home, Search, Media/Videos, Share/Compose, Camera), and 2 FAR or effectively missing (Media/Files, Inbox). See the table above for the exact reasoning per row.

This is a materially more complete native implementation than "not even there yet" would suggest. Home, Search, History, Access, the full media Player, Chat (including a real assistant conversation with thinking traces and a skill count), Captures, Tools diagnostics (real undervoltage sensor reading), Settings, and a fully working Appearance system (live theme, text-size, and color switching) are all genuinely wired to a live Pi backend, not stubs.

The gaps that are real:

1. The app is architecturally one 2728-line `MainActivity` God object with hand-rolled Java view-building rather than declarative layouts plus a shared style layer. Confirmed by the 82/55/39/15 programmatic-view-construction counts and the absence of any `styles.xml`.
2. Two structural mismatches against the mock's screen model: Inbox is not a screen, and Files is gated behind an extra drive-picker step.
3. Five dead pre-v2 layout files were never cleaned up.
4. One nav-state bug exists on Notes.

Rough coverage read: roughly 60 to 70 percent of the mock's built-tier screens have a genuinely working, data-backed native counterpart. The remainder is either present but structurally different (Inbox, Files) or was not independently verifiable in this sandbox (populated Files/Videos lists, since both test drives were disconnected).
