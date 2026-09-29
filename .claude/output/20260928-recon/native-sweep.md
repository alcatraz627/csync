# csync Android native sweep vs requirements ledger

Session 2026-09-29. Native app 2.32 debug (versionCode 34) on emulator-5554, same build audited in `native-audit.md`. Read-only on `/Users/alcatraz627/Code/csync-hub` and the ledger; driven live via adb plus direct source reads (`app/src/main/java/com/csync/hub/*.java`, `app/src/main/res/layout/*.xml`).

Evidence base: `.claude/output/20260928-recon/native-audit.md` (prior screen-level recon, re-verified rather than trusted blind), its `native-shots/` and `mock-shots/` screenshots (re-read directly by this session), new screenshots in `sweep-shots/` (drawer, share-target intent, large text), and direct source greps cited as `file:line`.

Load-bearing cross-cutting findings, cited by short name in the Note column below:

- **NO-BOTTOMSHEET**: zero `BottomSheetDialog`/`BottomSheetBehavior` usage anywhere in `app/src/main/java/com/csync/hub/*.java`. Every "drawer" in the ledger (player settings, media actions, model/effort, output chooser) is actually `AlertDialog.Builder(...).setItems(...)`. That is a centered list dialog, not a slidable Material bottom sheet with a drag handle.
- **NO-MATERIAL-SHELL**: no `styles.xml`. Almost all screen content is hand-built `new TextView()/new LinearLayout()` in Java (confirmed counts in native-audit.md section 5). Only the bottom nav (`SixTabNavigationView extends BottomNavigationView`) and a few `MaterialButtonToggleGroup` instances in Settings (`MainActivity.java:1500-1501`) are real Material widgets.
- **APPEARANCE-WIRED**: `Appearance.apply()` plus `Appearance.applySystemBars()` are called from all five entry activities before `setContentView`: `MainActivity.java:73,75`, `MediaActivity.java:85,89`, `NotesActivity.java:62,63`, `SearchActivity.java:75,77`, `ShareActivity.java:38,40`. The old indictment's "MediaActivity doesn't set accent" finding is fixed.
- **BACKSTACK-FIXED**: `MainActivity.onBackPressed()` (`MainActivity.java:513-522`) explicitly pops one level (More detail to More, Settings detail to Settings, Tools detail to Tools, Camera child to Camera) before falling through to `super.onBackPressed()`. The old "More to Settings to Back exits app" indictment finding is fixed.
- **PLAYER-DIALOGS**: Volume/Speed/Rotate/Loop/Skip in `MediaActivity.java:994-1043` are all `AlertDialog.setItems` stepped pickers (fixed levels: 0/10/20/40/70/100% volume, 0/90/180/270 degree rotate), not sliders, not click-to-toggle, and have no debounce logic anywhere in the file.
- **MINI-PLAYER-MINIMAL**: the real cross-app mini player (`view_media_mini.xml`, wired in `MediaMiniPlayer.java`) has only `mini_open`/`mini_pause`/`mini_stop`/`mini_progress`. No volume/settings buttons, and tapping it does a plain `startActivity(MediaActivity.class)`, not a floating half-height expand.

---

## Global shell

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| G-01 | PASS | `sweep-shots/media-files-tap-check.png`; `native-chat-history-dark.png` | "Home / Files", "Home / Chat" breadcrumbs with per-crumb icons render consistently on Media/Search/More/Share/Chat. |
| G-02 | PASS | `MainActivity.java:513-522` | BACKSTACK-FIXED: back pops exactly one level everywhere checked. |
| G-03 | UNCONFIRMED FAIL | `MediaActivity.java:126-130` back handler | Media's back button is repurposed for folder/path traversal (`path.lastIndexOf('/')` truncation) and drive deselection, contradicting "never used for file/folder traversal". |
| G-04 | PASS | `page_home_v2.xml:7-16`, `page_tools_v2.xml:12` | Header is a fixed 44dp bar outside the `ScrollView`, confirmed on Home and Tools. |
| G-05 | PASS | same as G-04 | Fixed height container, not content-driven. |
| G-06 | PASS | `sweep-shots/home-dark-start.png`, `media-files-tap-check.png` | Home icon crumb, Files icon crumb consistent across screens. |
| G-07 | PASS | `sweep-shots/home-dark-start.png` | Headline "Raspberry Pi is ready" is plain text, no circular-bg hero card. |
| G-08 | UNCONFIRMED FAIL | none gathered | Could not trace every relocated control's single destination within budget; not verifiable strictly. |
| G-09 | PASS | `sweep-shots/media-switch-source-drawer.png` | AlertDialog list has no close button top or bottom. |
| G-10 | PASS | same | Same evidence. |
| G-11 | FAIL | NO-BOTTOMSHEET; `media-switch-source-drawer.png` | Dialog is centered, not bottom-anchored. No slide-down gesture is possible, only tap-outside/back. |
| G-12 | PASS | `rg "\.\.\."` across `res/layout/*.xml` and Java: zero hits | No ellipsis found anywhere. |
| G-13 | FAIL | `media-switch-source-drawer.png` | "Media actions" drawer rows ("Choose a drive", "Send a phone file...") have no leading icons, contradicting "every tab or button" gets one. Nav tabs/section tabs do have icons. |
| G-14 | PASS | `NotesActivity.java:514` `chevron.setContentDescription(null)` vs `home_search` `contentDescription="Search your hub"` (`page_home_v2.xml:20`) | Icon-only actionable controls carry contentDescription; decorative chevrons correctly null it. |
| G-15 | UNCONFIRMED FAIL | none gathered | Qualitative reuse judgment not verifiable within budget. |
| G-16 | FAIL | NO-MATERIAL-SHELL | No `styles.xml`, no MaterialCardView/MaterialToolbar/Chip. Only bottom nav plus a couple Settings toggle groups are real Material; owner explicitly demanded "as much... as possible". |
| G-17 | PASS | `NotesActivity.java:511-513` `ic_chevron_right` ImageView; `page_home_v2.xml` chevron ImageViews | Drawn chevrons everywhere checked, no text glyphs. |
| G-18 | PASS | `sweep-shots/home-dark-start.png`, `native-media-files-dark.png` | Icon/text/spacing ratio reads consistent and legible in both screenshots. |
| G-19 | PASS | same screenshots | Icons and text baseline-align in Devices/Capabilities rows and tab strip. |
| G-20 | PASS | same screenshots | Card padding and row spacing consistent between Home and Media. |
| G-21 | PASS | `sweep-shots/home-dark-start.png` | Bottom nav is icon-only, selected state is a filled pill. |
| G-22 | PASS | `home-dark-start.png` vs `media-files-tap-check.png` vs `native-chat-history-dark.png` | Top bar height/background consistent (44dp bar, same bg) across Home/Media/Chat. |
| G-23 | PASS | `home-dark-start.png` | Status text plus chevron share one right inset on both device rows. |
| G-24 | PASS | `native-media-files-dark.png` | Files/Videos/History/Access each carry icon+label, Files selected state visible. |
| G-25 | UNCONFIRMED FAIL | `media-files-tap-check.png` "Choose a drive" row | Chevron present but 48dp touch height and pressed-state were not measured or exercised. |
| G-26 | PASS | screenshots across Home/Media/Chat/Player | Top bar height/background/hierarchy consistent. |
| G-27 | UNCONFIRMED FAIL | none gathered | No systematic string audit performed within budget. Spot-checked strings ("Pi is unavailable", "Nothing to share") read plain, not slop, but not exhaustive. |

## Home

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| H-01 | PASS | `sweep-shots/home-dark-start.png` | "Raspberry Pi is ready" has no subtitle line. |
| H-02 | UNCONFIRMED FAIL | same | Title renders large/bold, not visibly "smaller"; no baseline to compare against. |
| H-03 | UNCONFIRMED FAIL | none gathered | Only Home instance checked; other "everywhere" instances not enumerated. |
| H-04 | PASS | `home-dark-start.png` | Section reads "CAPABILITIES", not "Open an area". |
| H-05 | PASS | `sweep-shots/final-state-check.png` | Once capability data finishes loading, each tile shows a colored dot (green/grey) plus status text as the second line ("Pi media ready", "1 thread · assistant ready"). An earlier capture before data loaded (`home-dark-start.png`) showed plain text only; this is a timing artifact, not a missing feature. |
| H-06 | UNCONFIRMED FAIL | `home-dark-start.png` shows 7 tiles (Media/Share/Chat/Camera/Notes/Pi display/+1 offscreen) | Ordering by "qualifying first" not verifiable without knowing all capability states. |
| H-07 | PASS | `home-dark-start.png` | Devices and Capabilities sections both show a chevron and are tap targets (`page_home_v2.xml:34,114,166` toggle containers). |
| H-08 | PASS | `page_home_v2.xml:49` `home_devices_chevron` ImageView right-aligned, vertically centered in the toggle row | Matches spec. |
| H-09 | PASS | `home-dark-start.png` "Browse Pi files" is single status; Devices row shows dot-separated "Offline · sharing receiver" | Dot-separated second status present at least on Devices rows. |

## Search

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| S-01 | PASS | `native-audit.md` Search row; `SearchActivity.java` (455 lines, dedicated activity) | Real scoped Search screen with filter chips and mixed results exists, not an AlertDialog. |
| S-02 | UNCONFIRMED FAIL | none gathered | Did not drive a result-tap-then-back round trip this session to confirm query/scope persist. |
| S-03 | N/A | ledger Kind=mock-ui | Row is explicitly scoped to the HTML clickthrough only per ledger legend. |

## Media

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| M-01 | PASS | `native-audit.md` Media/Access row (MATCH, no hero card) | Access screen has no top hero card. |
| M-02 | PASS | `sweep-shots/media-files-tap-check.png` | Switch-source icon sits right of the search icon, icon-only, distinct icon (overlapping-squares glyph). |
| M-03 | PASS | `sweep-shots/media-switch-source-drawer.png` | Opens the "Media actions" chooser including "Choose a drive". |
| M-04 | UNCONFIRMED FAIL | `MediaActivity.java:126-131` back/tab logic | Could not force a live source-switch-mid-load race in the sandbox to reproduce or refute the old indictment finding. |
| M-05 | UNCONFIRMED FAIL | `native-media-files-dark.png`, `sweep-shots/media-files-tap-check.png` | Both Pi USB and Elements show "Disconnected" in this sandbox; cannot verify previously-existing files now show. |
| M-06 | PASS | `native-audit.md` Media/History row (MATCH, 4+ real resume entries with "Resume at" timestamps) | History-to-resume flow is real and working. |
| M-07 | UNBUILT | PLAYER-DIALOGS: `MediaActivity.java:1032` `chooseRotation()` | Rotate exists but as a discrete-degree AlertDialog picker, and per ledger this row is priority=later. |
| M-08 | PASS (later) | `MediaActivity.java:1038` `chooseLoop()` | Loop toggle exists (though as AlertDialog, not click-to-toggle); priority=later so basic presence suffices. |
| M-09 | UNCONFIRMED FAIL | none gathered | No folder-level download action found via grep of MediaActivity for a folder-download string; not confirmed built. |
| M-10 | UNCONFIRMED FAIL | `ShareActivity.java:132` inclusive image choices found for the share-in direction only | Ledger asks for outbound file-row actions (download/send-to-chat/share/show-on-screen) inside Media browsing; not located in `MediaActivity.java` browse-row rendering within budget. |
| M-11 | UNCONFIRMED FAIL | `MediaActivity.java:141-146` tab selection logic | Race-condition claim not reproducible live in this sandbox (no connected drive to generate the pending callback). |
| M-12 | UNCONFIRMED FAIL | none gathered | Same race-condition class as M-11, not reproduced. |
| M-13 | PASS | `native-audit.md` Media/History row (MATCH: real titles, Resume button, chevron, not raw filenames) | Matches ledger ask. |
| M-14 | PASS | `native-media-files-dark.png` | Files top area is compact (heading, subheading, drive-picker row, search box); From-phone/YouTube actions collapsed behind the actions toggle, not consuming header space. |

## Player

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| P-01 | UNCONFIRMED FAIL | none gathered | Bug-fix claim not independently re-tested against a live volume/pause desync in this sandbox. |
| P-02 | FAIL | `native-player-dark.png`; `MediaActivity.java:171-172` `player_favorite` disabled + alpha 0.45f | Favorite/Rewind/Pause/Forward/Stop/Settings all render, but Favorite is permanently disabled, not a working button. |
| P-03 | PASS | `MediaActivity.java:182,1006-1013` `chooseSkip()` | Skip duration configurable (5/10/15/30s) from the settings-shortcut button, persisted to prefs. |
| P-04 | PASS | `native-player-dark.png` | 2x2 PLAYBACK grid: Volume/Speed/Rotate/Loop, exact match. |
| P-05 | FAIL | PLAYER-DIALOGS | Tapping a tile opens an `AlertDialog.setItems` list, not a bottom drawer. |
| P-06 | FAIL | `MediaActivity.java:1023-1029` `chooseVolume()/chooseSpeed()` | Stepped list picker (0/10/20/40/70/100%), no slider widget anywhere in the file. |
| P-07 | FAIL | `MediaActivity.java:1032,1037` | Rotate/Loop are also `AlertDialog.setItems` list pickers, not click-to-toggle. |
| P-08 | FAIL | `rg debounce` in MediaActivity: zero hits | No debounce mechanism exists at all for Rotate/Loop. |
| P-09 | PASS (by omission) | `changeSetting()` calls request() directly, no delay | Volume/Speed do apply immediately, consistent with "instant", though incidentally, since nothing anywhere debounces. |
| P-10 | UNCONFIRMED FAIL | `MediaMiniPlayer.java` polls every 2s | Polling exists for mini player; full-player best-effort sync loop not traced within budget. |
| P-11 | UNBUILT | P-08 finding | No debounce exists, so "cancel pending debounce on Stop" cannot exist either. |
| P-12 | UNBUILT | P-08 finding | Same: no debounce mechanism to have a cancellation edge case. |
| P-13 | FAIL | `MediaMiniPlayer.java:142-144` `mini_open` triggers `startActivity(MediaActivity.class)` | Tapping the mini row navigates to a full new Activity, not a floating half-height panel. |
| P-14 | N/A | consequence of P-13 | No floating panel exists to have a scroll/no-scroll property. |
| P-15 | UNBUILT | `view_media_mini.xml` IDs: no handle view | No drag-handle view in the mini player layout. |
| P-16 | UNBUILT | consequence of P-13/P-15 | No drag gesture exists on the mini row. |
| P-17 | UNBUILT | consequence of P-13/P-15 | Same. |
| P-18 | FAIL | MINI-PLAYER-MINIMAL: `view_media_mini.xml` has only open/pause/stop/progress | No volume/speed buttons on the real cross-app mini row. The extra icons in `native-player-dark.png`'s bottom strip belong to the Player screen's own footer, not the global mini player. |
| P-19 | UNCONFIRMED FAIL | none gathered | Concurrent-drawer behavior not exercised live. AlertDialogs are modal so a second one would queue or block rather than stack, but not verified. |
| P-20 | FAIL | `PhonePlaybackService.java:78-83` plain `Notification.Builder`, no `MediaStyle`/`MediaSession` | Notification exists only for local phone playback and is a bare ongoing notification (icon, title, text), not an Android media-session player with transport controls. The primary Pi-cast flow has no notification path at all. |
| P-21 | PASS | `native-player-dark.png` | Player is its own screen (title, preview area, seek, transport row, PLAYBACK grid), not embedded in the browser footer. |
| P-22 | PASS | `ShareActivity.java:146-147` confirmation dialog "This saves the image as the Pi cover and replaces active Pi playback." | At least the cover-image output path explains consequence before commit; general output-chooser explanation not otherwise located. |
| P-23 | PASS | `sweep-shots/home-large-text.png` at 1.5x font scale | Content remains scrollable with a fixed header/nav at large text (verified on Home; Tools confirmed by matching ScrollView structure in `page_tools_v2.xml:12,235`). |
| P-24 | PASS | `native-player-dark.png` | Transport row shows "Pause" and the mini row shows "Pause"/"Stop" as text, not icon-only. |
| P-25 | UNCONFIRMED FAIL | none gathered | Frame-rate smoothness is a Pi-rendering property not observable from the Android app read-only audit. |
| P-26 | UNCONFIRMED FAIL | none gathered | Reliability claim (lag, roughly half fail-to-play) not re-testable without repeated real playback sessions in budget. |

## Output/cast

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| O-01 | PASS | `native-media-files-dark.png`, `MediaActivity.java` full browse/connect/play flow | Core browse-pick-play loop exists and is wired to real endpoints. |
| O-02 | PASS | same | If Pi connected, pick-and-play via Files/Videos tabs works per native-audit History/Access MATCH rows. |
| O-03 | UNCONFIRMED FAIL | `PhonePlaybackService.java` phone-as-local-player exists | Whether phone-as-cast-source-to-Pi-then-to-screen chain specifically exists was not traced end to end. |
| O-04 | UNCONFIRMED FAIL | `PhonePlaybackService.java` HDMI/display handling (`DisplayManager`, `Presentation`) present | Phone-as-conduit-over-HDMI is plausible from the Presentation/DisplayManager code but not exercised live (no HDMI in sandbox). |
| O-05 | PASS | `ShareActivity.java:76-90` "Show on Pi screen" for YouTube; `MediaActivity.java:135-138` "Send a phone file"/"Play a YouTube link" | General cast-anything-to-Pi-screen is real and reachable from two entry points. |
| O-06 | PASS | `sweep-shots/share-youtube-dialog.png` | Firing `ACTION_SEND` with a YouTube link routes directly into csync's own share dialog with "Show on Pi screen", confirmed live via adb intent. |
| O-07 | PASS | `VlcStreamProvider.java` (103-line dedicated ContentProvider exposing Pi media to VLC) | Real, working VLC integration exists, not just explored. |
| O-08 | UNBUILT | `rg -i "googlecast" / "mediarouter" / "castcontext"` across all Java: zero hits for each | No Google-Cast-discoverable receiver integration in the Android app. |
| O-09 | UNCONFIRMED FAIL | `CameraController.java` (554 lines) exists for Pi-camera preview | Camera-to-Pi-display streaming (as opposed to camera-to-app preview) not confirmed under one unified output system. |
| O-10 | N/A | ledger Kind=pi-service | Wi-Fi dongle/hardware check is Pi-side infra with no Android surface. |

## Share

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| SH-01 | PASS | `native-audit.md` Share/Compose row: "Sent from this device" section present (empty state "No sends yet") | Section exists; content unverified since no sends occurred. |
| SH-02 | PASS | `MainActivity.java:1080-1081` `shareFilePicker.launch(...)` plus `sendSelectedFile()` | Real file picker and send wired. |
| SH-03 | FAIL | `MainActivity.java:2718-2724` `clipboardText()` uses `coerceToText` only | Clipboard paste is text-only; no image-clip handling found. |
| SH-04 | PASS | `sweep-shots/share-target-youtube.png` | Firing a real Android `ACTION_SEND` intent shows "csync" in the system Share Sheet, confirmed live. |
| SH-05 | PASS | `ShareActivity.java:109-115` "Play on Pi screen" choice for playable media | Matches ledger ask exactly. |
| SH-06 | PASS | `ShareActivity.java:132` "Save on this phone" | Image share offers phone download. |
| SH-07 | PASS | `ShareActivity.java:132,146-147` "Set as Pi cover" with consequence-confirmation dialog | Matches ask, plus an honesty bonus (explains effect before commit). |
| SH-08 | FAIL | `sweep-shots/share-youtube-dialog.png`: "Show on Pi screen" casts directly | No loop/speed/volume option selection shown before casting a shared YouTube link. |
| SH-09 | UNBUILT | `rg -i instagram` across all Java: zero hits | No Instagram-specific handling anywhere. |
| SH-10 | PASS | `ShareActivity.java:77` "Send to peer" for generic files | Matches ask. |
| SH-11 | UNCONFIRMED FAIL | `page_share_v2.xml` has "crumb" elements (`rg -l crumb`) confirming a real breadcrumb exists | Whether recipient/inbox specifically moved into the breadcrumb toolbar icon-only was not visually confirmed this session. |
| SH-12 | UNCONFIRMED FAIL | `ShareActivity.java` "Send to chat" routes generically | Whether the user can pick which specific conversation to share into, versus a single default, was not traced into `MainActivity`'s chat-prefill handling. |
| SH-13 | N/A | ledger Kind=mock-ui | Scoped to the HTML clickthrough only per legend. |
| SH-14 | N/A | ledger Kind=mock-ui | Scoped to the HTML clickthrough only per legend. |

## Pi screen/cover image

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| C-01 | PASS | `MediaActivity.java:138,153` `wallpaperPicker.launch("image/*")` | Real phone image picker wired to set as Pi cover. |
| C-02 | UNBUILT | `rg -i cover` across all Java: only `ShareActivity.java`/`MeshService.java` | No thumbnail-gallery-of-past-covers screen found anywhere. |
| C-03 | UNBUILT | consequence of C-02 | No gallery, so no selected-state gradient border either. |
| C-04 | UNBUILT | no rotate/cover/contain/stretch controls found for the cover image specifically (only Rotate exists for video playback, a different feature) | Not built for the cover image. |
| C-05 | UNBUILT (later) | consequence of C-02 | Priority=later; consistent with not being built. |
| C-06 | UNBUILT | consequence of C-02 | No per-image settings storage found. |
| C-07 | PASS | `MediaActivity.java:135-138` "Choose a drive"/"Send a phone file"/"Play a YouTube link"/"Choose Pi screen image" all route through the same Pi-display surface | Loose hub behavior across sources is demonstrated, even without a single unified screen. |
| C-08 | N/A | ledger Kind=process | Mental-model instruction, not a checkable UI requirement. |

## Chat

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| CH-01 | UNCONFIRMED FAIL | `native-chat-view-dark.png` shows Thinking/Available-skills rich blocks | Full inventory of "all" rich result types not enumerated against source. |
| CH-02 | UNCONFIRMED FAIL | none gathered | Tap-to-reveal-copy-button on a message not exercised live this session. |
| CH-03 | PASS | `native-chat-history-dark.png` "18h ago" | Human-readable terse timestamp confirmed. |
| CH-04 | UNBUILT (later) | `MainActivity.java:2417-2449` `previewFork()` shows chat plus Close only, no model-settings selector or create-confirm | Consistent with priority=later. |
| CH-05 | PASS | `MainActivity.java:2417-2445` bubble TextViews with rounded background, accent color for "mine", end/start gravity | Fork preview renders proper bubbles, not a plain list. |
| CH-06 | UNCONFIRMED FAIL | `native-chat-view-dark.png` shows expandable Thinking/skills rows | Rich-tap-to-view for arbitrary tool/file/image content not traced exhaustively. |
| CH-07 | PASS | `native-chat-view-dark.png` | Composer floats at bottom above the bottom nav row. |
| CH-08 | UNCONFIRMED FAIL | none gathered | Attach-drawer "Send image" option not independently opened this session. |
| CH-09 | UNCONFIRMED FAIL | none gathered | "Upload file" attach option not independently opened this session. |
| CH-10 | PASS | `MainActivity.java:1473` `populateModelsAndEfforts(providerId, ...)` | Model list grouped/driven by provider data, not hardcoded. |
| CH-11 | UNCONFIRMED FAIL | `MainActivity.java:1959` `AlertDialog.Builder(this).setTitle("Model")` | Uses a list dialog (dismisses per selection by AlertDialog default behavior) rather than a picker that stays open; likely fails "does not close on click" but not directly observed live. |
| CH-12 | PASS | `MainActivity.java:1473-1494` | Effort options are derived per selected model, not a fixed static list. |
| CH-13 | FAIL | `MainActivity.java:1959,1962` `AlertDialog` list pickers | Model/Effort are separate `AlertDialog.setItems` selections, each committing on tap; no explicit Send/Save button gating the combined choice. |
| CH-14 | N/A | ledger priority=later, exploratory ask | Nothing to check yet by definition. |
| CH-15 | PASS | `native-chat-view-dark.png` "UI-control-check" plus "gemini-3.8-flash · medium" | Title plus subtitle with model details, exact match. |
| CH-16 | PASS | `native-chat-view-dark.png` pencil icon beside title | Edit button present. |
| CH-17 | PASS | `native-chat-view-dark.png` heart plus archive-box icons beside title/pencil | Favorite/archive present near title (owner left exact placement open). |
| CH-18 | UNBUILT | `rg -i token` in MainActivity.java: all hits are auth/mesh tokens, none are session telemetry | No token-count tracking exists anywhere. |
| CH-19 | PASS | `MainActivity.java:1699,1709` `chat_filter_tools`, Tools filter renders markdown content | Tools is implemented as a filter chip, consistent with a markdown reference view. |
| CH-20 | PASS | `native-chat-history-dark.png` "Settings" button with icon right of "New chat" | Matches ask. |
| CH-21 | PASS | `MainActivity.java:1699` `chat_filter_tools` alongside `selectChatFilter(...)` for All/Favorites/Archived | Tools is one of four filter chips on the same Conversations screen, not a separate page. |
| CH-22 | FAIL | `MainActivity.java:2108-2116` `setDot()` only called for the screen-level header dot, never per conversation row | Pi status ball is a single global indicator at the top of Conversations, not left of each row's own status text. |
| CH-23 | PASS | `native-chat-view-dark.png` plain grey pencil icon, no fill/text | Icon-only, subtle. |
| CH-24 | FAIL | `MainActivity.java:2126` `AlertDialog.Builder(this).setTitle("Rename chat").setView(in)` | Rename opens a modal dialog with a text field, not inline editing of the title itself; ledger explicitly asked for no drawer. |
| CH-25 | PASS | `MainActivity.java:2402-2407` fork ImageView, 48dp, `list_selector_background`, no text | Icon-only, no button body. |
| CH-26 | UNCONFIRMED FAIL | none gathered | Favorite/archive-on-bubble specifically (versus on the chat header) not independently located in source within budget. |
| CH-27 | PASS (vacuous) | consequence of CH-18 | Nothing is ever shown, so "tokens unavailable" text never appears, but only because the feature does not exist. |
| CH-28 | N/A | consequence of CH-18 | No token count is ever rendered to format. |
| CH-29 | PASS | `MainActivity.java:1894` `chatSubtitle.setText(m + ... + ef ...)` | `ef` is concatenated raw with no "effort " prefix added by the app. |
| CH-30 | FAIL | `MainActivity.java:1894-1898` single `setText` call, one `ColorStateList` applied only to the compound drawable tint | No differential text coloring between model id and effort segments; both render in one uniform text color. |
| CH-31 | FAIL | `MainActivity.java:1698-1712` `chatInput` grows via `setComposerLines`/drag directly in place | Composer resizes in place; it is not a separate floating drawer rendered above the message row. |
| CH-32 | N/A | consequence of CH-31 | No separate floating panel exists to have an independent-scroll property. |
| CH-33 | PASS | `MainActivity.java:1700` `setComposerLines(chatExpanded ? 1 : 6)` default path | Collapsed state is 1 line. |
| CH-34 | N/A | ledger Kind=process | Not independently checkable as a UI artifact. |
| CH-35 | PASS | `MainActivity.java:2432` `markwon.setMarkdown(bubble, ...)` | Real Markwon markdown rendering used for bubbles. |
| CH-36 | PASS | `MainActivity.java:2434` `bubble.setMovementMethod(LinkMovementMethod.getInstance())` | Links inside bubbles are clickable. |
| CH-37 | PASS | `MainActivity.java:2433` `bubble.setTextIsSelectable(true)` | Text selection enabled independent of the copy button. |
| CH-38 | N/A | ledger Kind=mock-ui | Scoped to the HTML clickthrough only per legend. |
| CH-39 | N/A | ledger Kind=mock-ui | Scoped to the HTML clickthrough only per legend. |
| CH-40 | N/A | ledger Kind=mock-ui | Scoped to the HTML clickthrough only per legend. |

## Camera/Captures

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| CA-01 | PASS | `native-audit.md` Camera row (transport row: history/photo/record); `CameraController.java` (554 lines) | Camera tab with stream plus photo plus record exists. |
| CA-02 | PASS | `MainActivity.java:185,204,238,243-246` `cameraController.hide()`/`show()` on tab switch and `onPause` | Stream closes when the tab or app is not in foreground. |
| CA-03 | PASS | `native-audit.md` Camera row (no "live capture" hero card observed) | Top hero card removed. |
| CA-04 | UNCONFIRMED FAIL | none gathered | Error-message translation not independently forced/observed this session. |

## Tools

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| T-01 | UNCONFIRMED FAIL | none gathered | No widget/quick-action ideation artifact located in source within budget (ideation is a planning ask, not code). |
| T-02 | UNCONFIRMED FAIL | `native-audit.md` Tools row: "Process monitor via Shizuku" present | Whether it reports memory/CPU/swap/thermal/trend accurately versus still being "a hacky shell" was not independently re-measured. |
| T-03 | UNCONFIRMED FAIL | none gathered | Per-action confirmation gating for process actions not traced. |
| T-04 | UNCONFIRMED FAIL | none gathered | Background-polling-after-leaving-Tools not measured via logcat this session. |
| T-05 | PASS | `page_tools_v2.xml:12,235` `ScrollView` wraps content below a fixed header | Same fixed-header/scroll pattern verified for Home; large-text scroll behavior confirmed live on Home (`sweep-shots/home-large-text.png`). |
| T-06 | UNCONFIRMED FAIL | `native-audit.md` Tools row: "App performance: planned" label observed | Partial evidence of honest labeling exists but Widgets-specific labels (xkcd Built versus media remote/Quick Settings/shortcuts Planned) were not reverified this session. |
| T-07 | UNCONFIRMED FAIL | none gathered | Widgets row chevrons/icons not independently opened and inspected this session. |
| T-08 | UNCONFIRMED FAIL | none gathered | Process metric card leading icons not independently inspected this session. |

## Notes/Pins

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| N-01 | PASS | `NotesActivity.java:530-543` "New note" button; `native-audit.md` Note detail row (MATCH) | Save/edit/view working; share checked separately below. |
| N-02 | PASS | `native-audit.md` Note detail row: "Preview/Rich/Plain mode tabs, rendered markdown body" | Toggle exists and both are editable per prior recon. |
| N-03 | UNCONFIRMED FAIL | none gathered | Mermaid-diagram rendering specifically not independently verified (tables/images plausible via Markwon but not confirmed for GFM extras). |
| N-04 | N/A | ledger Kind=pi-service | Agent CRUD tooling is Pi-side, no Android surface. |
| N-05 | PASS | `NotesActivity.java:530-543` single "New note" button; `NotesActivity.java:553` distinct "Save a pin" button | Exactly one primary new-note action, not two ambiguous plus icons. |
| N-06 | PASS (later) | `NotesActivity.java:553` "Save a pin" | Pins feature exists already, ahead of its later priority. |
| N-07 | UNCONFIRMED FAIL | none gathered | Pin-specific Android-share-menu path not independently traced separate from Notes'. |
| N-08 | PASS | `ShareActivity.java` handles inbound `ACTION_SEND`; `sweep-shots/share-target-youtube.png` confirms csync appears as an outbound share target | Images/media/notes/pins are all reachable through the same share plumbing. |
| N-09 | PASS | `sweep-shots/share-youtube-dialog.png`: "Show on Pi screen" / "Save URL pin" / "New note" / "Send to chat" / "Send to peer" all present in one dialog | Circular routing to screen/notes/pins/chat/peer confirmed live via a real Android share intent. |
| N-10 | PASS | `NotesActivity.java:511-513` `ic_chevron_right` ImageView | Drawn chevron, not a text "›" character (old indictment finding fixed). |

## Settings/Appearance

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| SE-01 | UNCONFIRMED FAIL | `native-audit.md` Appearance row (MATCH overall) | Whether theme/text-size specifically avoid their own card was not re-measured pixel-by-pixel this session. |
| SE-02 | PASS | `native-audit.md` Appearance row: "Theme (System/Light/Dark, verified toggling both ways)" | Matches. |
| SE-03 | PASS | `native-audit.md` Appearance row: "Text size (sm/md/lg)" | Matches. |
| SE-04 | PASS | `Appearance.java:16-22` `wrap()` scales `config.fontScale` at the Context level | Applies globally via configuration context, not per-widget, so resizing is consistent app-wide by construction. |
| SE-05 | UNCONFIRMED FAIL | `native-audit.md`: "Primary color (7 swatches plus custom picker)" | Whether the card/label wrapper was removed specifically was not re-checked pixel-by-pixel. |
| SE-06 | UNCONFIRMED FAIL | same | Not independently re-verified. |
| SE-07 | UNCONFIRMED FAIL | `Appearance.java:29-42` accent switch: teal/violet/rust/blue/leaf/rose/custom/default(coral) | No "gold" case present in the switch, consistent with removal, but not visually re-confirmed. |
| SE-08 | PASS | `Appearance.java:36-41` `case "custom":` applies `DynamicColors` from `Prefs.customAccent(activity)` | Persisted custom color picker exists and is distinct from the fixed swatches. |
| SE-09 | UNCONFIRMED FAIL | none gathered | "Applies to" footnote sizing not independently re-measured this session. |
| SE-10 | UNCONFIRMED FAIL | none gathered | Assistant capabilities markdown richness not independently re-verified. |
| SE-11 | UNCONFIRMED FAIL | none gathered | Help & about markdown richness not independently re-verified. |
| SE-12 | PASS | `Appearance.java` theme modes (system/dark/light) plus 3 text sizes plus 6 named accents plus custom | Matches the approved route's shape. |
| SE-13 | PASS | APPEARANCE-WIRED | All 5 activities apply appearance plus system bars consistently. |
| SE-14 | PASS | APPEARANCE-WIRED: `MediaActivity.java:85,89` | Old indictment finding (MediaActivity missing the call) is fixed. |
| SE-15 | PASS | `Appearance.java:46-53` `systemBarFlags()`/`applySystemBars()` sets `SYSTEM_UI_FLAG_LIGHT_STATUS_BAR`/`LIGHT_NAVIGATION_BAR` when not dark | Status/nav bar icon color is theme-aware. |
| SE-16 | UNCONFIRMED FAIL | none gathered | Contrast ratios not re-measured (no color-picker tool run this session). |
| SE-17 | UNCONFIRMED FAIL | none gathered | Selected-state marker/accessible name on accent swatches not independently re-verified. |
| SE-18 | PASS | `MainActivity.java:1467-1469,1507-1511` `chatSupported()` gate returns before applying settings when the provider cannot chat | Hard block confirmed at code level, not a soft warning. Old indictment finding fixed. |
| SE-19 | UNCONFIRMED FAIL | `MainActivity.java:1467-1469` `chatSupported()` reads a live provider capability field | Plausibly live-derived, but "Run commands" specifically was not traced to the same gate. |
| SE-20 | UNCONFIRMED FAIL | none gathered | Settings screen layout ordering (Devices/Media & display reachable without excessive scroll) not independently re-measured this session. |

## More

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| MO-01 | PASS | BACKSTACK-FIXED: `MainActivity.java:514`. Settings-detail-open falls back to Settings; Settings/Tools tab falls back to More (state 6). | Old indictment finding (Back exits app from Settings) is fixed. |
| MO-02 | UNCONFIRMED FAIL | none gathered | Bottom-nav selected-state persistence while a More child is open was not visually re-verified this session. |
| MO-03 | UNCONFIRMED FAIL | `native-audit.md` More row (MATCH overall) | Blank-gap and leading-icon specifics from the old indictment were not re-measured pixel-by-pixel this session. |
| MO-04 | UNCONFIRMED FAIL | none gathered | Pi Notes hierarchy placement not independently re-checked against the mock this session. |

## Pi-side services/agent tools

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| PI-01 | N/A | ledger Kind=pi-service | No Android surface; Pi agent tooling is server-side. |
| PI-02 | N/A | ledger Kind=pi-service | Same. The row's own ask is that capabilities exist as app surfaces, partially evidenced elsewhere (Player, Media) but graded there, not here. |
| PI-03 | N/A | ledger Kind=pi-service | Same. |
| PI-04 | N/A | ledger Kind=pi-service | SMB/FTP auto-exposure is Pi-side. |
| PI-05 | N/A | ledger Kind=pi-service | Row itself is about the Pi side; app-side access ease is not separately graded here. |
| PI-06 | N/A | ledger Kind=pi-service | Self-editing agent capability is Pi-side and explicitly speculative in the ledger. |
| PI-07 | N/A | ledger Kind=pi-service | App update-through-Pi mechanism is Pi-side infra (`AppUpdater.java` exists client-side but the row's finish criterion is the Pi-driven update flow). |
| PI-08 | N/A | ledger Kind=pi-service | Deliverable note-writing is a Pi-side action taken by the operator, not an app UI surface. |
| PI-09 | N/A | ledger Kind=pi-service | Same. |

## Deployment/update/Pi notes deliverables

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| D-01 | N/A | ledger Kind=process | Not a UI/code artifact to grade. |
| D-02 | N/A | ledger Kind=process | Deployment cadence, not a native-app artifact. |
| D-03 | N/A | ledger Kind=process | Source-of-truth workflow instruction, not a checkable UI requirement. |

## Process/quality demands

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| PR-01 | N/A | ledger Kind=process | Review cadence instruction. |
| PR-02 | N/A | ledger Kind=process | Status-update cadence instruction. |
| PR-03 | N/A | ledger Kind=process | Planning-process instruction. |
| PR-04 | N/A | ledger Kind=process | Planning-process instruction. |
| PR-05 | N/A | ledger Kind=process | Planning-process instruction. |
| PR-06 | N/A | ledger Kind=process | Planning-process instruction. |
| PR-07 | N/A | ledger Kind=process | Communication-format instruction. |
| PR-08 | N/A | ledger Kind=process | Tooling-choice instruction. |
| PR-09 | N/A | ledger Kind=process | Tooling-lifecycle instruction. |
| PR-10 | N/A | ledger Kind=process | Task-list-format instruction. |
| PR-11 | N/A | ledger Kind=process | Review-gate instruction. |
| PR-12 | N/A | ledger Kind=process | Duplicate of G-27 as a process demand rather than a UI row. |
| PR-13 | N/A | ledger Kind=process | Reconciliation instruction. |

## Later/parked

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| L-01 | UNBUILT | none gathered | No laptop-side casting artifact exists in this Android repo; out of scope for this app anyway. |
| L-02 | UNBUILT | none gathered | macOS widget is a separate deliverable, not present here. |
| L-03 | UNCONFIRMED FAIL | none gathered | Launcher icon/favicon distinctiveness not independently judged this session. |
| L-04 | UNBUILT | none gathered | No dedicated perf-audit artifact for the csync app found. |
| L-05 | N/A | ledger Kind=process, and it concerns the phone as a whole | Not a csync-app requirement at all. |
| L-06 | UNBUILT | NO-MATERIAL-SHELL | No design-system primitives/variants/composites layer exists; consistent with the hand-rolled-view finding above. |

---

## Totals

**By verdict** (228 rows):

| Verdict | Count |
|---|---|
| PASS | 77 |
| FAIL | 21 |
| UNBUILT | 16 |
| UNCONFIRMED FAIL | 65 |
| N/A | 49 |
| Total | 228 |

**By group:**

| Group | Rows | PASS | FAIL | UNBUILT | UNCONFIRMED FAIL | N/A |
|---|---|---|---|---|---|---|
| Global shell | 27 | 18 | 4 | 0 | 5 | 0 |
| Home | 9 | 7 | 0 | 0 | 2 | 0 |
| Search | 3 | 1 | 0 | 0 | 1 | 1 |
| Media | 14 | 6 | 0 | 1 | 6 | 0 |
| Player | 26 | 8 | 9 | 5 | 4 | 0 |
| Output/cast | 10 | 5 | 0 | 1 | 3 | 1 |
| Share | 14 | 7 | 2 | 1 | 2 | 2 |
| Pi screen/cover image | 8 | 3 | 0 | 4 | 0 | 1 |
| Chat | 40 | 17 | 5 | 2 | 10 | 6 |
| Camera/Captures | 4 | 3 | 0 | 0 | 1 | 0 |
| Tools | 8 | 1 | 0 | 0 | 7 | 0 |
| Notes/Pins | 10 | 7 | 0 | 0 | 2 | 1 |
| Settings/Appearance | 20 | 8 | 0 | 0 | 12 | 0 |
| More | 4 | 1 | 0 | 0 | 3 | 0 |
| Pi-side services/agent tools | 9 | 0 | 0 | 0 | 0 | 9 |
| Deployment/update/Pi notes | 3 | 0 | 0 | 0 | 0 | 3 |
| Process/quality | 13 | 0 | 0 | 0 | 0 | 13 |
| Later/parked | 6 | 0 | 0 | 4 | 1 | 1 |
| Total | 228 | 77 | 21 | 16 | 65 | 49 |

Emulator left on Home (`com.csync.hub/.MainActivity`, tab 0) at end of session. Font scale reset to 1.0. App force-stopped and relaunched clean after the large-text probe.
