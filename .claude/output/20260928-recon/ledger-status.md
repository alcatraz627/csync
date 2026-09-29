# csync Android: owner asks, mock and app status

Every ask the owner gave, with its status in the clickthrough mock and in the native app.
PASS has evidence; FAIL is present but wrong, or not proven (unconfirmed counts as FAIL);
UNBUILT has no implementation; N/A means that side has no surface for the ask (a Pi service,
a working-process rule, or a real Android system feature a static mock cannot show).
Evidence columns point at files beside this one. Regenerate with merge_ledger.py.


## Global shell (top bar, breadcrumb, back, bottom nav, drawers, icons, text rules)

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| G-01 | Top bar renders as a proper breadcrumb, not an inconsistent one | PASS | PASS | `sweep-shots/media-files-tap-check.png`; `native-chat-history-dark.png` |
| G-02 | Back button always goes exactly one level up, never in circles | PASS | PASS | `MainActivity.java:513-522` |
| G-03 | Back button is navigation-only: never repurposed for file/folder traversal, stopping media, or any other action | PASS | PASS | MediaActivity.renderTop(): back closes the player or leaves Media; folders go up via an Up row in browse() |
| G-04 | Breadcrumb bar never scrolls | PASS | PASS | `page_home_v2.xml:7-16`, `page_tools_v2.xml:12` |
| G-05 | Breadcrumb bar height never changes when contents change | PASS | PASS | same as G-04 |
| G-06 | Every crumb that shows an icon for its route shows that icon consistently, every time that crumb appears | PASS | PASS | `sweep-shots/home-dark-start.png`, `media-files-tap-check.png` |
| G-07 | Circular hero/focus cards ("named receivers", "your hub", "Raspberry Pi is ready" style) removed from every screen that has one | PASS | PASS | `sweep-shots/home-dark-start.png` |
| G-08 | Any control lost by removing a hero card is relocated to exactly one place elsewhere, never duplicated | PASS | FAIL | none gathered |
| G-09 | Bottom drawers/sheets have no close button at the top of the drawer | PASS | PASS | `sweep-shots/media-switch-source-drawer.png` |
| G-10 | Bottom drawers/sheets have no close button at the bottom of the drawer | PASS | PASS | same |
| G-11 | Drawer dismissal is by slide-down or tap-outside only | PASS | PASS | kit-shots/media-history-sheet-dark.png then media-history-closed.png: bottom sheet with handle, tap outside closed it |
| G-12 | No ellipsis ("...") anywhere in the app, on text or in an input box | PASS | PASS | `rg "\.\.\."` across `res/layout/*.xml` and Java: zero hits |
| G-13 | Every tab or button across the app has a leading icon | PASS | PASS | kit-shots/media-history-sheet-dark.png, chat-attach-sheet.png: drawer rows all carry leading icons (Kit.sheet) |
| G-14 | Icon-only controls (e.g. bottom nav) keep an accessible label for the icon even when no visible text is shown | PASS | PASS | `NotesActivity.java:514` `chevron.setContentDescription(null)` vs `home_search` `contentDescription="Search your hub"` (`page_home_v2.xml:20`) |
| G-15 | Title+subtitle pattern (established for Notes) is reused elsewhere where it adds context, not applied everywhere indiscriminately | PASS | FAIL | none gathered |
| G-16 | The final native app uses Material components, motion, and guidance as much as possible; the HTML mock does not exempt the real app from this | N/A | FAIL | Partial: BottomSheetDialog and Slider now used via Kit; most page bodies are still built by hand in Java |
| G-17 | Disclosure/expand-collapse affordances use a drawn chevron icon, never a literal text character like "v" or "⌄" | PASS | PASS | `NotesActivity.java:511-513` `ic_chevron_right` ImageView; `page_home_v2.xml` chevron ImageViews |
| G-18 | Icon size, label text size, and the gap/padding around them keep a proper, consistent ratio across all cards/rows | PASS | PASS | `sweep-shots/home-dark-start.png`, `native-media-files-dark.png` |
| G-19 | Icons and text are vertically/baseline aligned and relatively spaced consistently across all cards | PASS | PASS | same screenshots |
| G-20 | Card sizing, internal padding, and row/column/section spacing are consistent with the approved mock, not ad hoc per screen | PASS | PASS | same screenshots |
| G-21 | Primary bottom navigation shows icons only, no visible text labels, with stable selected state | PASS | PASS | `sweep-shots/home-dark-start.png` |
| G-22 | Top bar spacing, sizing, and background are compact and consistent across screens/themes, matching the mock | PASS | PASS | `home-dark-start.png` vs `media-files-tap-check.png` vs `native-chat-history-dark.png` |
| G-23 | Status text and its trailing chevron stay aligned with a consistent right inset (e.g. device rows on Home) | PASS | PASS | `home-dark-start.png` |
| G-24 | Section tab strips (e.g. Media Files/Videos/History/Access) each carry an aligned icon plus label, with a selected state and accessible labels | PASS | PASS | `native-media-files-dark.png` |
| G-25 | Disclosure/action rows use a drawn chevron, at least 48dp touch height, balanced padding, and visible pressed/expanded states | PASS | FAIL | `media-files-tap-check.png` "Choose a drive" row |
| G-26 | Top bar/context row is consistent in height, background, and hierarchy across every native page, not just some | PASS | PASS | screenshots across Home/Media/Chat/Player |
| G-27 | No screen or component text reads as AI-generated slop | PASS | FAIL | none gathered |

## Home

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| H-01 | The "Raspberry Pi is ready" (or equivalent) focus card loses its subtitle | PASS | PASS | `sweep-shots/home-dark-start.png` |
| H-02 | That card's title is rendered smaller | PASS | PASS | kit-shots/home-dark.png: Home title 18sp while other page titles use Kit.Text.PageTitle 22sp |
| H-03 | This simplification pattern applies everywhere the same style of card exists, not only Home | N/A | FAIL | none gathered |
| H-04 | "Open an area" section is renamed "Capabilities" | PASS | PASS | `home-dark-start.png` |
| H-05 | Each Capabilities row's second line is a status dot (green/grey/red/yellow) plus status text | PASS | PASS | `sweep-shots/final-state-check.png` |
| H-06 | Capabilities section shows more features than before, with qualifying/available ones listed first | PASS | FAIL | `home-dark-start.png` shows 7 tiles (Media/Share/Chat/Camera/Notes/Pi display/+1 offscreen) |
| H-07 | Devices, Open-an-area/Capabilities, and Pick-up sections are each collapsible by clicking the section title | PASS | PASS | `home-dark-start.png` |
| H-08 | A caret is shown to the right of each collapsible section title, vertically aligned with it | PASS | PASS | `page_home_v2.xml:49` `home_devices_chevron` ImageView right-aligned, vertically centered in the toggle row |
| H-09 | The "Open an area" card's subtitle can show a second, dot-separated status (online/offline/counts) | PASS | PASS | `home-dark-start.png` "Browse Pi files" is single status; Devices row shows dot-separated "Offline · sharing receiver" |

## Search

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| S-01 | A single, real global Search screen replaces the ad hoc chat-title-only dialog: scope tabs, mixed named results, exact result identity, empty/offline states | PASS | PASS | `native-audit.md` Search row; `SearchActivity.java` (455 lines, dedicated activity) |
| S-02 | Search query and scope survive returning from a result (Back retains query) | PASS | FAIL | none gathered |
| S-03 | Search results must not all be cosmetic re-skins of one screen; it is one real distinct search flow with query, domain filters, and mixed results | PASS | N/A | ledger Kind=mock-ui |

## Media (Files / Videos / History / Access / source drawer)

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| M-01 | The hero card at the top of Media > Access is removed | PASS | PASS | `native-audit.md` Media/Access row (MATCH, no hero card) |
| M-02 | "Switch source" moves to the right of the search button as an icon-only control (pick a different icon than currently used) | PASS | PASS | `sweep-shots/media-files-tap-check.png` |
| M-03 | Tapping switch-source opens the same choose-a-source drawer as today | PASS | PASS | `sweep-shots/media-switch-source-drawer.png` |
| M-04 | Selecting a drive/source never silently changes the selected section (History/Files) or leaves a stale source label | FAIL | FAIL | `MediaActivity.java:126-131` back/tab logic |
| M-05 | Previously-existing media files on the Pi that were not visible via the app must actually show | N/A | FAIL | `native-media-files-dark.png`, `sweep-shots/media-files-tap-check.png` |
| M-06 | Optional: history of all played media files, tappable to resume that specific play | PASS | PASS | `native-audit.md` Media/History row (MATCH, 4+ real resume entries with "Resume at" timestamps) |
| M-07 | Rotation control for playing media *(later)* | PASS | UNBUILT | PLAYER-DIALOGS: `MediaActivity.java:1032` `chooseRotation()` |
| M-08 | Loop control for playing media *(later)* | PASS | PASS | `MediaActivity.java:1038` `chooseLoop()` |
| M-09 | Raspi disk browser: folder rows get a download-folder-to-phone action | PASS | FAIL | none gathered |
| M-10 | File rows expose whichever of download / send-to-chat / share / show-on-screen the file type actually supports, inclusively (never build only one action) | PASS | FAIL | `ShareActivity.java:132` inclusive image choices found for the share-in direction only |
| M-11 | Media History correctly shows History content/heading/selected tab even while a Files drive-listing request from a prior tab is still in flight | PASS | FAIL | `MediaActivity.java:141-146` tab selection logic |
| M-12 | Media History header stays "CONTINUE" and does not get overwritten by a transient playback-status string during a background refresh | PASS | FAIL | none gathered |
| M-13 | Media History rows show friendly metadata (icon, readable title, Resume action), not raw long cast filenames dominating the row | PASS | PASS | `native-audit.md` Media/History row (MATCH: real titles, Resume button, chevron, not raw filenames) |
| M-14 | Media Files keeps a compact search/top area without a separate source-selector/title consuming extra height, while phone/YouTube contextual actions stay reachable | PASS | PASS | `native-media-files-dark.png` |

## Player (full, mini row, expanded half-sheet, notification player)

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| P-01 | Volume and play/pause commands from the app must reliably sync to the actual Pi player state (bug fix) | N/A | FAIL | none gathered |
| P-02 | Single-row transport: Favorite, Rewind, Pause, Forward, Stop, all as buttons | PASS | FAIL | `native-player-dark.png`; `MediaActivity.java:171-172` `player_favorite` disabled + alpha 0.45f |
| P-03 | Skip/rewind duration is configurable via a dropdown on that row | PASS | PASS | `MediaActivity.java:182,1006-1013` `chooseSkip()` |
| P-04 | Below the transport row, a 2x2 grid of Volume / Speed / Rotate / Loop settings | PASS | PASS | `native-player-dark.png` |
| P-05 | Tapping a 2x2 tile opens a drawer for that setting | PASS | PASS | Kit.sliderSheet / Kit.sheet replace every player AlertDialog (MediaActivity chooseVolume/chooseSpeed/chooseSkip/chooseSetting); UNCONFIRMED live: Pi idle keeps tiles disabled |
| P-06 | Volume and Speed drawers show a slider | PASS | PASS | Kit.sliderSheet: Material Slider, applied on release; UNCONFIRMED live: Pi idle |
| P-07 | Rotate and Loop are click-to-toggle (not sliders) | PASS | PASS | MediaActivity.chooseRotation/chooseLoop step on tap; UNCONFIRMED live: Pi idle |
| P-08 | Rotate and Loop apply with a 2-second debounce | PASS | PASS | commitRotation/commitLoop posted 2000 ms after the last tap; UNCONFIRMED live: Pi idle |
| P-09 | Volume and Speed apply instantly, no debounce | PASS | PASS | `changeSetting()` calls request() directly, no delay |
| P-10 | Player controls reflect the actual playback state; if a value changes elsewhere (agent, another client), the player screen best-effort syncs to it | PASS | FAIL | `MediaMiniPlayer.java` polls every 2s |
| P-11 | A pending debounced setting (e.g. a queued Rotate) must not silently apply after Stop has ended the session | PASS | UNBUILT | P-08 finding |
| P-12 | A second setting selection (e.g. Loop) must not silently cancel a still-pending first setting (e.g. Rotate) without being an explicit external override | PASS | UNBUILT | P-08 finding |
| P-13 | Tapping the collapsed mini player row expands it floating above the app to about half height | PASS | FAIL | `MediaMiniPlayer.java:142-144` `mini_open` triggers `startActivity(MediaActivity.class)` |
| P-14 | The expanded half-height panel never scrolls | PASS | N/A | consequence of P-13 |
| P-15 | A drawer handle is shown on top when expanded | PASS | UNBUILT | `view_media_mini.xml` IDs: no handle view |
| P-16 | Dragging the handle to full height opens the full playback screen | PASS | UNBUILT | consequence of P-13/P-15 |
| P-17 | Dragging the handle down returns to the single collapsed row | PASS | UNBUILT | consequence of P-13/P-15 |
| P-18 | The collapsed mini row has buttons right of Stop that open the volume/speed drawer with a slider | PASS | FAIL | MINI-PLAYER-MINIMAL: `view_media_mini.xml` has only open/pause/stop/progress |
| P-19 | Only one drawer/sheet is open at a time across the player surfaces; flag if this can't be guaranteed | PASS | FAIL | none gathered |
| P-20 | Playing media appears as an Android notification-region / media-session player in the standard notification drawer | PASS | FAIL | `PhonePlaybackService.java:78-83` plain `Notification.Builder`, no `MediaStyle`/`MediaSession` |
| P-21 | The full player shows title, target/output, elapsed/total time on a labeled seek control, icon transport, volume, and a distinct Stop, as its own dedicated surface rather than being embedded in the file browser footer | PASS | PASS | `native-player-dark.png` |
| P-22 | The output chooser names the destination, shows availability, and states the playback consequence (e.g. muted startup, replacing another session) before the tap commits | PASS | PASS | `ShareActivity.java:146-147` confirmation dialog "This saves the image as the Pi cover and replaces active Pi playback." |
| P-23 | Full player, mini row, and expanded panel remain usable with all controls reachable at large system text size, without requiring undiscoverable scrolling or cutting off controls | PASS | PASS | `sweep-shots/home-large-text.png` at 1.5x font scale |
| P-24 | Pause/Resume/Stop text labels are kept (icons for the rest, but these specific words stay legible text) | PASS | PASS | `native-player-dark.png` |
| P-25 | Video/image frame rate on the Pi screen must actually be smooth, not slow | N/A | FAIL | none gathered |
| P-26 | Media/casting/streaming reliability: routes must not be laggy or fail to play about half the time | N/A | FAIL | none gathered |

## Output/cast

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| O-01 | The Android app can browse/connect/pick a media file from any storage device attached to the Pi and play it on the connected projector | PASS | PASS | `native-media-files-dark.png`, `MediaActivity.java` full browse/connect/play flow |
| O-02 | If the Pi is connected (to the projector), the app can pick and play on it | PASS | PASS | same |
| O-03 | If the phone is connected directly (no Pi), consider the phone casting media onto the Pi as a local device that then projects to the screen | PASS | FAIL | `PhonePlaybackService.java` phone-as-local-player exists |
| O-04 | When connected via phone, the app is the conduit for streaming from the Pi via the phone to the projector over HDMI | N/A | FAIL | `PhonePlaybackService.java` HDMI/display handling (`DisplayManager`, `Presentation`) present |
| O-05 | General casting of anything (a media file or a YouTube video) to the screen(s) linked to the Pi | PASS | PASS | `ShareActivity.java:76-90` "Show on Pi screen" for YouTube; `MediaActivity.java:135-138` "Send a phone file"/"Play a YouTube link" |
| O-06 | YouTube sharing must work directly from the YouTube app share sheet; pasting a link is not an acceptable UX | N/A | PASS | `sweep-shots/share-youtube-dialog.png` |
| O-07 | Explore whether the VLC Android app can be used as the actual player while csync remains the intermediate/control layer | N/A | PASS | `VlcStreamProvider.java` (103-line dedicated ContentProvider exposing Pi media to VLC) |
| O-08 | Determine whether a native Google-Cast-discoverable receiver on the Pi/HDMI output is feasible so YouTube's own Cast picker can find it, separate from csync's own Share-to-Pi route | UNBUILT | UNBUILT | `rg -i "googlecast" / "mediarouter" / "castcontext"` across all Java: zero hits for each |
| O-09 | Explore streaming the Pi's own camera, or the phone's camera, to the Pi display, under one unified output system | UNBUILT | FAIL | `CameraController.java` (554 lines) exists for Pi-camera preview |
| O-10 | Investigate the newly attached Wi-Fi USB dongle on the Pi for a cast-enabled receiver path (hardware enablement step) | N/A | N/A | ledger Kind=pi-service |

## Share (compose, inbox, history, Android share-target routing)

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| SH-01 | Compose shows full history of everything sent from this device | PASS | PASS | `native-audit.md` Share/Compose row: "Sent from this device" section present (empty state "No sends yet") |
| SH-02 | Compose allows sending files | PASS | PASS | `MainActivity.java:1080-1081` `shareFilePicker.launch(...)` plus `sendSelectedFile()` |
| SH-03 | Compose allows sending from clipboard (images or other content) | PASS | FAIL | `MainActivity.java:2718-2724` `clipboardText()` uses `coerceToText` only |
| SH-04 | csync's send/compose screen is registered as an Android share target so other apps can share into it | UNBUILT | PASS | `sweep-shots/share-target-youtube.png` |
| SH-05 | Sharing a video into csync offers to play it on a connected screen | PASS | PASS | `ShareActivity.java:109-115` "Play on Pi screen" choice for playable media |
| SH-06 | Sharing an image into csync offers to download it onto the phone (like an older version of the app did, Instagram-save style) | PASS | PASS | `ShareActivity.java:132` "Save on this phone" |
| SH-07 | Sharing an image into csync offers to set it as the Pi cover image | PASS | PASS | `ShareActivity.java:132,146-147` "Set as Pi cover" with consequence-confirmation dialog |
| SH-08 | Sharing a YouTube link into csync allows casting with selectable options (loop/speed/volume), defaulting to previous options but always editable | PASS | FAIL | `sweep-shots/share-youtube-dialog.png`: "Show on Pi screen" casts directly |
| SH-09 | Sharing an Instagram reel allows playing it on the Pi, downloading first via the revived Instagram-save feature if needed | PASS | UNBUILT | `rg -i instagram` across all Java: zero hits |
| SH-10 | Sharing any other file into csync offers sending it to a device | PASS | PASS | `ShareActivity.java:77` "Send to peer" for generic files |
| SH-11 | Compose's recipient and Inbox actions move into the breadcrumb's right-side toolbar, icon-only | PASS | FAIL | `page_share_v2.xml` has "crumb" elements (`rg -l crumb`) confirming a real breadcrumb exists |
| SH-12 | Share-to-chat lets the user pick which conversation to share to, instead of a primitive single-target send | PASS | FAIL | `ShareActivity.java` "Send to chat" routes generically |
| SH-13 | A failed file send retains the attachment/item for retry rather than silently clearing it while the UI still claims it is retained | PASS | N/A | ledger Kind=mock-ui |
| SH-14 | Sharing a capture (e.g. from Captures) into Compose actually carries the captured item as an attachment or represented text, not an empty compose screen | PASS | N/A | ledger Kind=mock-ui |

## Pi screen/cover image

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| C-01 | The screen shows a default image, pickable from the phone, persistently shown as wallpaper | PASS | PASS | `MediaActivity.java:138,153` `wallpaperPicker.launch("image/*")` |
| C-02 | All past cover images are shown as a small thumbnail gallery, selectable again | PASS | UNBUILT | `rg -i cover` across all Java: only `ShareActivity.java`/`MeshService.java` |
| C-03 | The currently selected thumbnail shows a gradient border to indicate selection | PASS | UNBUILT | consequence of C-02 |
| C-04 | Each image can be rotated, and shown as cover / contain / stretch | PASS | UNBUILT | no rotate/cover/contain/stretch controls found for the cover image specifically (only Rotate exists for video playback, a different feature) |
| C-05 | Optional: allow selecting a crop region without modifying the underlying image *(later)* | UNBUILT | UNBUILT | consequence of C-02 |
| C-06 | Crop/rotation/fit settings are saved per-image (never global), and can be edited or cleared at any time | PASS | UNBUILT | consequence of C-02 |
| C-07 | Pi display is a general output hub, not tied to one feature: capable of showing a media file, a camera source, a share-video source, or the default/cover image | PASS | PASS | `MediaActivity.java:135-138` "Choose a drive"/"Send a phone file"/"Play a YouTube link"/"Choose Pi screen image" all route through the same Pi-display surface |
| C-08 | This hub reframing is a mental model shift only; do not wreck existing designs to force it | N/A | N/A | ledger Kind=process |

## Chat (list tabs, conversation, input, attach drawer, model/effort, fork, title edit)

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| CH-01 | All tool-call rich results the app already renders continue to be supported | PASS | FAIL | `native-chat-view-dark.png` shows Thinking/Available-skills rich blocks |
| CH-02 | Tapping a message shows a copy button below it | PASS | PASS | kit-shots/chat-bubble-tap.png: tap on message reveals icon-only copy and fork |
| CH-03 | Messages show human-readable, terse timestamps | PASS | PASS | `native-chat-history-dark.png` "18h ago" |
| CH-04 | (later) A fork button on a message opens a drawer/modal showing the scrollable chat up to that point, then lets the user pick model settings and confirm to create the fork *(later)* | PASS | UNBUILT | `MainActivity.java:2417-2449` `previewFork()` shows chat plus Close only, no model-settings selector or create-confirm |
| CH-05 | Fork preview renders as proper chat bubbles, not a plain list | PASS | PASS | `MainActivity.java:2417-2445` bubble TextViews with rounded background, accent color for "mine", end/start gravity |
| CH-06 | Rich tool/file/image content is tappable with an explored best presentation (icon/title/subtitle) leading to a rich view | PASS | FAIL | `native-chat-view-dark.png` shows expandable Thinking/skills rows |
| CH-07 | The message text box floats at the bottom, above the player/drawer rows | PASS | PASS | `native-chat-view-dark.png` |
| CH-08 | Left-side attach icon opens a drawer offering: send image | PASS | UNBUILT | kit-shots/chat-attach-sheet.png: + drawer lists only Model and effort; image sending not built |
| CH-09 | Attach drawer offers upload file | PASS | UNBUILT | kit-shots/chat-attach-sheet.png: file upload not built |
| CH-10 | Attach drawer offers a Model picker grouped by family (gemini / openai / claude / local); local comes later once local models are hooked up | PASS | PASS | `MainActivity.java:1473` `populateModelsAndEfforts(providerId, ...)` |
| CH-11 | The model list does not close/save on click; the drawer stays open for further selection | PASS | FAIL | Model drawer closes on each pick (Kit.sheet dismiss on select) |
| CH-12 | Effort selector shows only the effort levels the selected model actually supports, never a fixed static list | PASS | PASS | `MainActivity.java:1473-1494` |
| CH-13 | Model/effort drawer requires an explicit Send or Save button; it never auto-commits on tap | PASS | FAIL | Model then Effort drawers commit per tap; no explicit Save or Send button yet |
| CH-14 | (later) Explore other attachment types/settings in the attach drawer *(later)* | N/A | N/A | ledger priority=later, exploratory ask |
| CH-15 | Chat view top shows title + subtitle with model details | PASS | PASS | `native-chat-view-dark.png` "UI-control-check" plus "gemini-3.8-flash · medium" |
| CH-16 | An edit button beside the chat title allows editing the title | PASS | PASS | `native-chat-view-dark.png` pencil icon beside title |
| CH-17 | Subtitle area has favorite/archive buttons (owner left exact placement to be decided) | PASS | PASS | `native-chat-view-dark.png` heart plus archive-box icons beside title/pencil |
| CH-18 | Subtitle can show session telemetry (e.g. token count) only when it is actually measured; never a forced/wrong placeholder value | PASS | UNBUILT | `rg -i token` in MainActivity.java: all hits are auth/mesh tokens, none are session telemetry |
| CH-19 | Conversations list gets a "Tools" tab that is a plain grouped markdown reference of all tools, one line per tool as key:value, grouped by category | PASS | PASS | `MainActivity.java:1699,1709` `chat_filter_tools`, Tools filter renders markdown content |
| CH-20 | Right of the "New chat" button, a plain icon Settings button opens the chat settings drawer to choose default model settings | PASS | PASS | `native-chat-history-dark.png` "Settings" button with icon right of "New chat" |
| CH-21 | The Tools tab is a companion filter of the same Conversations screen (alongside All/Favorites/Archived), never a separate page/navigation | PASS | PASS | `MainActivity.java:1699` `chat_filter_tools` alongside `selectChatFilter(...)` for All/Favorites/Archived |
| CH-22 | Conversations list rows show Pi online/checking/offline as a green/yellow/gray ball to the left of the status text in the subtitle | PASS | FAIL | `MainActivity.java:2108-2116` `setDot()` only called for the screen-level header dot, never per conversation row |
| CH-23 | Conversation name edit uses a subtler, icon-only edit affordance | PASS | PASS | `native-chat-view-dark.png` plain grey pencil icon, no fill/text |
| CH-24 | The text beside that icon is the actual chat title (not a generic label), and is inline-editable there directly, with no separate rename drawer | PASS | FAIL | `MainActivity.java:2126` `AlertDialog.Builder(this).setTitle("Rename chat").setView(in)` |
| CH-25 | Copy/Fork buttons on a chat bubble are subtler: icon-only, no text or filled button body | PASS | PASS | `MainActivity.java:2402-2407` fork ImageView, 48dp, `list_selector_background`, no text |
| CH-26 | Favorite/Archive buttons get the same icon-only, no-body treatment | PASS | FAIL | none gathered |
| CH-27 | Chat subtitle never shows "tokens unavailable"; it omits the token stat entirely when not available | PASS | PASS | consequence of CH-18 |
| CH-28 | Token counts, when shown, are formatted human-readable | PASS | N/A | consequence of CH-18 |
| CH-29 | Effort label drops the "effort" prefix, e.g. "effort medium" becomes "medium" | PASS | PASS | `MainActivity.java:1894` `chatSubtitle.setText(m + ... + ef ...)` |
| CH-30 | Effort label color is slightly lighter than the model id's color | PASS | FAIL | `MainActivity.java:1894-1898` single `setText` call, one `ColorStateList` applied only to the compound drawable tint |
| CH-31 | When the composer draft exceeds 2 lines, a drawer opens above the message row that can be dragged up for more room | PASS | FAIL | `MainActivity.java:1698-1712` `chatInput` grows via `setComposerLines`/drag directly in place |
| CH-32 | That expanded drawer floats above the chat while still allowing full independent scroll of the chat | PASS | N/A | consequence of CH-31 |
| CH-33 | Default/collapsed composer height is exactly one line | PASS | PASS | `MainActivity.java:1700` `setComposerLines(chatExpanded ? 1 : 6)` default path |
| CH-34 | The expand/collapse behavior must be UX-consistent end to end, not a quick one-shot | N/A | N/A | ledger Kind=process |
| CH-35 | Chat bubbles render Markdown richly on both sides | PASS | PASS | `MainActivity.java:2432` `markwon.setMarkdown(bubble, ...)` |
| CH-36 | Links inside chat bubbles are clickable | PASS | PASS | `MainActivity.java:2434` `bubble.setMovementMethod(LinkMovementMethod.getInstance())` |
| CH-37 | Users can select some or all of a bubble's text, separate from the copy button | PASS | PASS | `MainActivity.java:2433` `bubble.setTextIsSelectable(true)` |
| CH-38 | Every history row opens its own distinct conversation with its own title and messages, not one shared global transcript across rows | PASS | N/A | ledger Kind=mock-ui |
| CH-39 | Favorites and Archived filters actually filter to favorited/archived conversations, not showing the same list as All | PASS | N/A | ledger Kind=mock-ui |
| CH-40 | Expanded composer draft never overlaps/obscures its own composer row, including at large text on a narrow screen | PASS | N/A | ledger Kind=mock-ui |

## Camera/Captures

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| CA-01 | Add a camera tab that starts and shows a camera stream, allows photos, and allows recording | PASS | PASS | `native-audit.md` Camera row (transport row: history/photo/record); `CameraController.java` (554 lines) |
| CA-02 | The camera stream closes when the tab/page is not open | PASS | PASS | `MainActivity.java:185,204,238,243-246` `cameraController.hide()`/`show()` on tab switch and `onPause` |
| CA-03 | The top "live capture" hero card is removed from Camera | PASS | PASS | `native-audit.md` Camera row (no "live capture" hero card observed) |
| CA-04 | Camera and null/technical errors are translated into a useful status message, not a raw exception concatenation | PASS | FAIL | none gathered |

## Tools

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| T-01 | Ideate on widgets and Android quick actions for the app | N/A | FAIL | none gathered |
| T-02 | Replace the current hacky shell-based process monitor/manager with an accurate one: available memory, CPU, swap/pressure, thermal state, process trends | N/A | FAIL | `native-audit.md` Tools row: "Process monitor via Shizuku" present |
| T-03 | Any process action requires explicit per-action confirmation and demonstrated benefit before shipping | PASS | FAIL | none gathered |
| T-04 | No background polling continues after leaving the Tools/process screen | N/A | FAIL | none gathered |
| T-05 | Tools content must remain usable and scrollable at large system text size, not have controls clipped by a fixed-height layout | PASS | PASS | `page_tools_v2.xml:12,235` `ScrollView` wraps content below a fixed header |
| T-06 | Tools/Process/Widgets honestly label what is live vs. planned (e.g. Shizuku off state, Pi actions not yet built) instead of implying capability that doesn't exist | PASS | FAIL | `native-audit.md` Tools row: "App performance: planned" label observed |
| T-07 | Widgets rows each carry an aligned, meaningful icon and a working trailing chevron leading to a real detail/action | PASS | FAIL | none gathered |
| T-08 | Process metric cards each carry a leading icon | PASS | FAIL | none gathered |

## Notes/Pins

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| N-01 | Basic notes feature: save, edit, view, share | PASS | PASS | `NotesActivity.java:530-543` "New note" button; `native-audit.md` Note detail row (MATCH) |
| N-02 | Notes markdown-render with a plain / rich / preview view toggle, both editable | PASS | PASS | `native-audit.md` Note detail row: "Preview/Rich/Plain mode tabs, rendered markdown body" |
| N-03 | Notes support GFM extras: tables, images, Mermaid diagrams | PASS | FAIL | none gathered |
| N-04 | The Pi agent gets tools for full CRUD on notes, including making or updating notes itself if needed | N/A | N/A | ledger Kind=pi-service |
| N-05 | Notes page has exactly one "new note" action, not two plus buttons | PASS | PASS | `NotesActivity.java:530-543` single "New note" button; `NotesActivity.java:553` distinct "Save a pin" button |
| N-06 | (later) Notes list gets a Pins section: share URLs/text snippets with optional title/tags/description *(later)* | UNBUILT | PASS | `NotesActivity.java:553` "Save a pin" |
| N-07 | Pins support the same Android-app save-and-share flow as notes, including sharing via the Android share menu *(later)* | UNBUILT | FAIL | none gathered |
| N-08 | All images/media/notes/pins shown in the app are shareable via the Android share menu | FAIL | PASS | `ShareActivity.java` handles inbound `ACTION_SEND`; `sweep-shots/share-target-youtube.png` confirms csync appears as an outbound share target |
| N-09 | A file shared from csync back into csync must expose routing options: to screen / notes / pins / chat, exercising the same capability path inline and via Android share; treated as a behavior test of consistency, not a new feature to hand-build per surface | PASS | PASS | `sweep-shots/share-youtube-dialog.png`: "Show on Pi screen" / "Save URL pin" / "New note" / "Send to chat" / "Send to peer" all present in one dialog |
| N-10 | Disclosure rows on Notes use a real drawn chevron, not a literal "›" text character | PASS | PASS | `NotesActivity.java:511-513` `ic_chevron_right` ImageView |

## Settings/Appearance

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| SE-01 | Theme and text size controls are not wrapped in their own section/card; the flat button-group selector already used is fine as-is | PASS | FAIL | `native-audit.md` Appearance row (MATCH overall) |
| SE-02 | Theme options are System / Light / Dark, each with its own icon | PASS | PASS | `native-audit.md` Appearance row: "Theme (System/Light/Dark, verified toggling both ways)" |
| SE-03 | Text size options are sm (current normal) / md (large) / lg (larger) | PASS | PASS | `native-audit.md` Appearance row: "Text size (sm/md/lg)" |
| SE-04 | Text-size choice resizes consistently across the whole app, not just one or two elements | PASS | PASS | `Appearance.java:16-22` `wrap()` scales `config.fontScale` at the Context level |
| SE-05 | Primary color control keeps only the color circle/ball, no surrounding card or label | PASS | FAIL | `native-audit.md`: "Primary color (7 swatches plus custom picker)" |
| SE-06 | Primary color subtitle is removed | PASS | FAIL | same |
| SE-07 | The Gold color option is removed | PASS | FAIL | `Appearance.java:29-42` accent switch: teal/violet/rust/blue/leaf/rose/custom/default(coral) |
| SE-08 | Gold is replaced by a custom color picker whose value persists; tapping it opens the editor, while tapping any other swatch selects that color | PASS | PASS | `Appearance.java:36-41` `case "custom":` applies `DynamicColors` from `Prefs.customAccent(activity)` |
| SE-09 | The "applies to" section becomes a footnote-level element, not its own prominent block; keep its icons but reduce its space | PASS | FAIL | none gathered |
| SE-10 | Assistant capabilities gets a richer markdown-rendered write-up | PASS | FAIL | none gathered |
| SE-11 | Help & about gets the same richer markdown-rendered write-up | PASS | FAIL | none gathered |
| SE-12 | Appearance route offers System theme plus sm/md/lg text size, shipped accents plus additional reviewed accents and Custom, replacing the current Light/Dark-plus-four-accents-only set | PASS | PASS | `Appearance.java` theme modes (system/dark/light) plus 3 text sizes plus 6 named accents plus custom |
| SE-13 | Appearance choices persist and apply consistently across Main/Media/Notes activities, including matching system-bar (status/nav bar) appearance | PASS | PASS | APPEARANCE-WIRED |
| SE-14 | Appearance is applied at a single shared point before every activity inflates, so it never drifts between screens (e.g. Violet on Settings but Coral on Media) | PASS | PASS | APPEARANCE-WIRED: `MediaActivity.java:85,89` |
| SE-15 | Dark mode correctly sets light/dark status-bar icon color so system clock/battery icons stay visible against the dark background | N/A | PASS | `Appearance.java:46-53` `systemBarFlags()`/`applySystemBars()` sets `SYSTEM_UI_FLAG_LIGHT_STATUS_BAR`/`LIGHT_NAVIGATION_BAR` when not dark |
| SE-16 | Accent-colored text meets at least 4.5:1 contrast against its background in both themes, not reusing a fill color at insufficient contrast for small text | PASS | FAIL | none gathered |
| SE-17 | Each accent swatch shows a clear selected-state marker and an accessible name, not color alone | PASS | FAIL | none gathered |
| SE-18 | The provider/model selector can never let the user save/select a model the connected Pi does not actually support (e.g. saving Claude while Pi reports chatSupported=false must be blocked, not merely discouraged) | UNBUILT | PASS | `MainActivity.java:1467-1469,1507-1511` `chatSupported()` gate returns before applying settings when the provider cannot chat |
| SE-19 | A capability shown as "on" is derived from the live, Pi-approved state, never merely from the name of an advertised capability | UNBUILT | FAIL | `MainActivity.java:1467-1469` `chatSupported()` reads a live provider capability field |
| SE-20 | Settings screen keeps Devices & connections and Media & display reachable without appearance/connection detail cards pushing them offscreen | PASS | FAIL | none gathered |

## More

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| MO-01 | Each More child screen (Camera, Tools, Settings, etc.) has a real back affordance and Android system Back returns to More, never exits the app | PASS | PASS | BACKSTACK-FIXED: `MainActivity.java:514`. Settings-detail-open falls back to Settings; Settings/Tools tab falls back to More (state 6). |
| MO-02 | More stays selected in bottom navigation while a child screen from More is open | PASS | FAIL | none gathered |
| MO-03 | More screen removes the giant blank gap under its top bar and gives rows leading icons at proper card height | PASS | FAIL | `native-audit.md` More row (MATCH overall) |
| MO-04 | Pi Notes entry sits in the correct hierarchy section per the approved mock, not lumped into Areas | PASS | FAIL | none gathered |

## Pi-side services/agent tools

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| PI-01 | The Pi-linked agent gets tools to search, play, seek, and change settings of the playing media app | N/A | N/A | ledger Kind=pi-service |
| PI-02 | Nothing should be agent-exclusive UI: every capability the agent gets must exist as a proper media player/browse surface in the app, with the agent simply tapping into it | N/A | N/A | ledger Kind=pi-service |
| PI-03 | The agent stays aware of the current play state and can query media files | N/A | N/A | ledger Kind=pi-service |
| PI-04 | Storage drives attached to the Pi become available on SMB, FTP, and the Android app automatically whenever they are connected | N/A | N/A | ledger Kind=pi-service |
| PI-05 | The app makes it easier to access the Pi's FTP/SMB, and optionally SSH (owner not bullish on SSH) | PASS | N/A | ledger Kind=pi-service |
| PI-06 | The Pi agent can load/use/diagnose/suggest fixes for issues in this system, and potentially edit its own code to help fix things | N/A | N/A | ledger Kind=pi-service |
| PI-07 | The app installs/updates itself via the Pi's update feature as the finish criterion for the current work | N/A | N/A | ledger Kind=pi-service |
| PI-08 | The Pi Notes feature is used to leave a work summary note (what works, screenshots) as part of finishing this round | N/A | N/A | ledger Kind=pi-service |
| PI-09 | A second Pi note lists all features the owner can test out | N/A | N/A | ledger Kind=pi-service |

## Deployment/update/Pi notes deliverables

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| D-01 | Once the build is done, halt further testing and finalize/deploy the APK | N/A | N/A | ledger Kind=process |
| D-02 | Keep dropping the updated APK onto the Pi at proper checkpoints, not excessively | N/A | N/A | ledger Kind=process |
| D-03 | The HTML mocks are the source of truth for UI; use the written guide/spec for functionality | N/A | N/A | ledger Kind=process |

## Process/quality demands (review gates, testing expectations)

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| PR-01 | Do not run review agents too frequently; only run them at the end of a major direction, to conserve usage | N/A | N/A | ledger Kind=process |
| PR-02 | Keep giving status updates on what is started and what is done | N/A | N/A | ledger Kind=process |
| PR-03 | Never one-shot a design/UI pass; produce a well-thought-out plan and rich variants preview | N/A | N/A | ledger Kind=process |
| PR-04 | When presenting options/variants, remember and implement ALL of them where relevant, not just the one selected; never silently drop items never explicitly called out | N/A | N/A | ledger Kind=process |
| PR-05 | Reconcile all prior answers into one coherent whole and flag conflicts to the owner, rather than presenting contradictory partial states | N/A | N/A | ledger Kind=process |
| PR-06 | Presented "variants" must be genuinely, substantively different, not the same layout with a spacing tweak | N/A | N/A | ledger Kind=process |
| PR-07 | Always show the full absolute file path, never a relative link, and never place a period immediately after a path | N/A | N/A | ledger Kind=process |
| PR-08 | Use an isolated browser/CLI tool (playwright/chrome-devtools MCP) for UI testing instead of the user's main Chrome profile | N/A | N/A | ledger Kind=process |
| PR-09 | Kill any spawned browser process properly when done, and encode the lifecycle as a standard reusable skill/guide | N/A | N/A | ledger Kind=process |
| PR-10 | Write a comprehensive task list grouped by segment, with specific guidance on every common UI pattern (buttons, top bars, breadcrumbs, icons, cards, links, options), each carrying scope-out / implement / code-check / self-review / correctness-check / full-review stages, and check in after each completed page | N/A | N/A | ledger Kind=process |
| PR-11 | Get a final independent adversarial review for inconsistencies, missing data, and inconsistent spacing before writing the final spec and starting the Android build; incorporate agreed feedback, then write the final spec plus context notes (functional, UI, UX) | N/A | N/A | ledger Kind=process |
| PR-12 | No screen text may read as AI-generated slop | N/A | N/A | ledger Kind=process |
| PR-13 | Reconcile all owner feedback and prior todo notes at the end, confirming everything is done and working consistently, before declaring finished | N/A | N/A | ledger Kind=process |

## Later/parked

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| L-01 | Plan and build the same casting/streaming capability from the owner's laptop *(later)* | N/A | UNBUILT | none gathered |
| L-02 | A csync macOS top-bar widget with additional csync-related features *(later)* | N/A | UNBUILT | none gathered |
| L-03 | Explore a better/more distinctive launcher icon or favicon (notification icon, widget branding, web favicon) *(later)* | UNBUILT | FAIL | none gathered |
| L-04 | Full performance audit of the csync app itself (CPU, memory, network, battery, startup, frame time, cleanup) *(later)* | N/A | UNBUILT | none gathered |
| L-05 | Full performance audit of the phone (why it feels laggy despite available RAM) *(later)* | N/A | N/A | ledger Kind=process, and it concerns the phone as a whole |
| L-06 | Design system primitives/variants/composites documented and used to standardize the app, to be done once current work is finished *(later)* | PASS | UNBUILT | NO-MATERIAL-SHELL |

## Totals

| Status | Mock | App |
|---|---|---|
| PASS | 171 | 103 |
| FAIL | 2 | 64 |
| UNBUILT | 9 | 21 |
| N/A | 46 | 40 |
| Total | 228 | 228 |
