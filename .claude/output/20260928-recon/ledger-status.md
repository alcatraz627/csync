# csync Android: owner asks, mock and app status

Every ask the owner gave, with its status in the clickthrough mock and in the native app.
PASS has evidence; FAIL is present but wrong, or not proven (unconfirmed counts as FAIL);
UNBUILT has no implementation; N/A means that side has no surface for the ask (a Pi service,
a working-process rule, or a real Android system feature a static mock cannot show).
Evidence columns point at files beside this one. Regenerate with merge_ledger.py.

## Backfill of 2026-10-01: the owner's 09-29 and 09-30 asks

The tables below still cover only the original 228 asks. On 2026-10-01 the requirements
ledger gained 83 rows: the owner's asks from 2026-09-28 17:00 UTC to the end of
2026-09-30 UTC, quoted verbatim from the Claude Code transcripts (G-28 to G-42, H-10,
H-11, M-15, P-27, C-09 to C-11, SH-15, SH-16, CH-41 to CH-52, T-09 to T-12, N-11, N-12,
SE-21 to SE-25, MO-05, PI-10 to PI-17, D-04 to D-06, PR-14 to PR-37). None of them has a
mock or app verdict yet, so this file does not list them. Running merge_ledger.py now would
show all 83 as FAIL on both sides, because a missing verdict counts as FAIL; give them
verdicts in a new verdicts file first.

The same pass marked 40 existing rows `[agent-written]` in the ledger, because their source is an
agent's text (indictments, the agent backlog, the recovered brief, agent-written callouts)
and not the owner's words. Those rows never outrank an owner quote. The 2026-10-01 verdicts
for them (for example P-24, T-03, SE-12 to SE-20) judge the app against an agent's reading,
not against an owner ask.

17 callouts were added for the UI defects among the new asks
(`co-20261001-134200-81` to `co-20261001-134233-3f`); each row's check names its source
line and ledger id. This section is hand-written; merge_ledger.py rewrites the whole file
and will drop it.


## Global shell (top bar, breadcrumb, back, bottom nav, drawers, icons, text rules)

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| G-01 | Top bar renders as a proper breadcrumb, not an inconsistent one | PASS | PASS | s-nav3b (Home), s-nav5b (Media / Pi screen), s-nav14 (More / Notes / New note), s-nav8b (Send): one bar, icon per crumb, current crumb bold |
| G-02 | Back button always goes exactly one level up, never in circles | PASS | PASS | Walked this session: Received to a conversation and back (s-nav2c), Home from Ask and Camera tiles and back (s-nav11a to s-nav11c), Search to a result and back (s-nav6c, s-nav12b); the Main-on-Main loop found on 2026-10-01 is closed (s-nav3a to s-nav3c, launcher after Home) |
| G-03 | Back button is navigation-only: never repurposed for file/folder traversal, stopping media, or any other action | PASS | PASS | Media folders climb by the Up row inside the list; Back from the player page leaves the page and never stops playback (s-nav5c, s-nav16e: the film kept playing while the page was left) |
| G-04 | Breadcrumb bar never scrolls | PASS | PASS | The bar is fixed on every page while the body scrolls (s-nav5d, s-nav3a). At Large text a long path slides inside the bar so the current page stays in view (s-nav14); the bar itself does not move |
| G-05 | Breadcrumb bar height never changes when contents change | PASS | PASS | 56dp `kit_top_height` on every page; s-nav3b vs s-nav14 vs s-nav15d bars are the same height with one, three and two crumbs |
| G-06 | Every crumb that shows an icon for its route shows that icon consistently, every time that crumb appears | PASS | PASS | Media's icon on the Media crumb in s-nav5b and s-nav5d; Notes' on s-nav14 and s-nav4d; More's on s-nav14 and s-nav11b |
| G-07 | Circular hero/focus cards ("named receivers", "your hub", "Raspberry Pi is ready" style) removed from every screen that has one | PASS | PASS | s-nav3b: Home is Pick up rows, four tiles, a devices row and a status line; no hero card on any page captured this session |
| G-08 | Any control lost by removing a hero card is relocated to exactly one place elsewhere, never duplicated | PASS | PASS | s-nav3b: the old hero's device list is one row ("Your devices · 2 of 7 online") and its Pi state is one status line; neither appears twice |
| G-09 | Bottom drawers/sheets have no close button at the top of the drawer | PASS | PASS | s-nav8a, s-nav10e, s-clean1: drawers carry a handle, a title and rows or two buttons, no close control |
| G-10 | Bottom drawers/sheets have no close button at the bottom of the drawer | PASS | PASS | same captures |
| G-11 | Drawer dismissal is by slide-down or tap-outside only | PASS | PASS | s-nav8c: the device drawer closed by Back/tap outside and the page returned; s-nav10f: Keep it is the drawer's own button, not a close |
| G-12 | No ellipsis ("...") anywhere in the app, on text or in an input box | PASS | PASS | Rendered: no three dots in any of the 60 s-nav captures; long names wrap ("Blackadder S00E02 Blackadders Christmas Carol", s-nav3b) and crumbs rest at the current page instead of cutting it (s-nav14) |
| G-13 | Every tab or button across the app has a leading icon | PASS | PASS | s-nav3b tiles, s-nav10e Keep it and Drop, s-nav15d transport, s-nav5d tabs: every button and tab leads with an icon |
| G-14 | Icon-only controls (e.g. bottom nav) keep an accessible label for the icon even when no visible text is shown | PASS | PASS | `a11y.py` tree audit over 23 pages: no silent tap target (2026-09-30), re-run unchanged by this session's work; the bar's items speak Home, Media, Share, Chat, More (s-nav texts dumps) |
| G-15 | Title+subtitle pattern (established for Notes) is reused elsewhere where it adds context, not applied everywhere indiscriminately | PASS | PASS | Rows carry a title and a line beneath where it adds something (s-nav3b "Conversation · 5h ago", s-nav5d "2 items"); pages have one title in the bar and a status row, not a subtitle (s-nav5b) |
| G-16 | The final native app uses Material components, motion, and guidance as much as possible; the HTML mock does not exempt the real app from this | N/A | PASS | Material where Material has the part: BottomSheetDialog drawers, Slider, BottomNavigationView, SwipeRefreshLayout, predictive back, dynamic accent; bodies are built once on the shared Kit the owner kept (G-25) |
| G-17 | Disclosure/expand-collapse affordances use a drawn chevron icon, never a literal text character like "v" or "⌄" | PASS | PASS | s-nav3b, s-nav5d: drawn chevrons on every disclosure row |
| G-18 | Icon size, label text size, and the gap/padding around them keep a proper, consistent ratio across all cards/rows | PASS | PASS | s-nav3b, s-nav5d, s-nav5b: 40dp icon tiles, 18sp titles, 14sp sub lines, the same inset on every row |
| G-19 | Icons and text are vertically/baseline aligned and relatively spaced consistently across all cards | PASS | PASS | same captures; the icon tile centres on the two text lines |
| G-20 | Card sizing, internal padding, and row/column/section spacing are consistent with the approved mock, not ad hoc per screen | PASS | PASS | s-nav3b vs s-nav5b vs s-nav4d: the same card radius, group padding and section gap on every page |
| G-21 | Primary bottom navigation shows icons only, no visible text labels, with stable selected state | PASS | PASS | s-nav3b, s-nav5d: icons only, the selected place carries a tinted pill |
| G-22 | Top bar spacing, sizing, and background are compact and consistent across screens/themes, matching the mock | PASS | PASS | s-nav3b (dark) and s-lm-settings2 (light): the same compact bar on both themes |
| G-23 | Status text and its trailing chevron stay aligned with a consistent right inset (e.g. device rows on Home) | PASS | PASS | s-nav3b: the status line's chevron and the rows' chevrons share the right inset |
| G-24 | Section tab strips (e.g. Media Files/Videos/History/Access) each carry an aligned icon plus label, with a selected state and accessible labels | PASS | PASS | s-nav5d: Files, Videos, History, Access each with an icon, Files underlined in accent; the a11y audit reads "Files, selected" |
| G-25 | Disclosure/action rows use a drawn chevron, at least 48dp touch height, balanced padding, and visible pressed/expanded states | PASS | PASS | s-nav5d: folder rows at 48dp+ with a chevron, a ripple on press (seen while driving), an expanded state on Home's sections |
| G-26 | Top bar/context row is consistent in height, background, and hierarchy across every native page, not just some | PASS | PASS | s-nav3b, s-nav5d, s-nav3a, s-nav15d: identical bar height, background and hierarchy on Home, Media, Chat, the player |
| G-27 | No screen or component text reads as AI-generated slop | PASS | PASS | Read every string in the s-nav text dumps: plain sentences ("Nothing is playing on this phone", "It has not been saved on the Pi"), nothing padded or sales-like |

## Home

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| H-01 | The "Raspberry Pi is ready" (or equivalent) focus card loses its subtitle | PASS | N/A | superseded: no focus card on Home (s-nav3b) |
| H-02 | That card's title is rendered smaller | PASS | N/A | superseded, as H-01 |
| H-03 | This simplification pattern applies everywhere the same style of card exists, not only Home | N/A | N/A | superseded: no card of that style anywhere (s-nav3b, s-nav5b, s-nav11b) |
| H-04 | "Open an area" section is renamed "Capabilities" | PASS | N/A | superseded: the Capabilities section was removed with suggestion 1 |
| H-05 | Each Capabilities row's second line is a status dot (green/grey/red/yellow) plus status text | PASS | N/A | superseded, as H-04; the one status line keeps the dot and words (s-nav3b "The Pi is online") |
| H-06 | Capabilities section shows more features than before, with qualifying/available ones listed first | PASS | N/A | superseded, as H-04 |
| H-07 | Devices, Open-an-area/Capabilities, and Pick-up sections are each collapsible by clicking the section title | PASS | N/A | superseded: Home's sections are not collapsible by design now (s-nav3b) |
| H-08 | A caret is shown to the right of each collapsible section title, vertically aligned with it | PASS | N/A | superseded, as H-07 |
| H-09 | The "Open an area" card's subtitle can show a second, dot-separated status (online/offline/counts) | PASS | PASS | s-nav3b: "Your devices · 2 of 7 online", "Conversation · 5h ago", "Last played · on this phone" |

## Search

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| S-01 | A single, real global Search screen replaces the ad hoc chat-title-only dialog: scope tabs, mixed named results, exact result identity, empty/offline states | PASS | PASS | s-nav6a (empty state, scopes All, Media, Chats, Files, Devices), s-nav6b ("3 results", a conversation named as such), s-nav12a (a received file named with its sender) |
| S-02 | Search query and scope survive returning from a result (Back retains query) | PASS | PASS | s-nav6c and s-nav12b: after opening a result and pressing Back, the query and its results are still on screen |
| S-03 | Search results must not all be cosmetic re-skins of one screen; it is one real distinct search flow with query, domain filters, and mixed results | PASS | N/A | a mock-side ask |

## Media (Files / Videos / History / Access / source drawer)

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| M-01 | The hero card at the top of Media > Access is removed | PASS | PASS | Access tab is a plain list (s-dl-media, 2026-09-30); no hero card on any Media view (s-nav5d) |
| M-02 | "Switch source" moves to the right of the search button as an icon-only control (pick a different icon than currently used) | PASS | PASS | s-nav5d: the source switch is the icon right of Search, its own glyph |
| M-03 | Tapping switch-source opens the same choose-a-source drawer as today | PASS | PASS | s-led14/s-led15 drive and folder flows; the source drawer lists drives with connected state (chooseSource) |
| M-04 | Selecting a drive/source never silently changes the selected section (History/Files) or leaves a stale source label | FAIL | PASS | The source switch exists only on Files (s-led3: History's bar has Search and the switch absent), so a pick can never change the selected view; the drive label is rewritten on each pick (s-led15 "Pi USB / shared") |
| M-05 | Previously-existing media files on the Pi that were not visible via the app must actually show | N/A | PASS | s-led15: every folder on the drive is listed with its count, including empty ones ("linux, 0 items"); s-nav15a: "123 videos on every connected drive" |
| M-06 | Optional: history of all played media files, tappable to resume that specific play | PASS | PASS | s-led3 and s-led9: Continue rows per item with output and position; a row's sheet offers Resume on Pi screen from the saved position, Start over, Resume on this phone (s-led4) |
| M-07 | Rotation control for playing media *(later)* | PASS | PASS | s-led12: Rotate stepped to 90° on tap and the Pi reported rotation 90 after the debounce (API read) |
| M-08 | Loop control for playing media *(later)* | PASS | PASS | s-led12: Loop · On, Pi reported loop true |
| M-09 | Raspi disk browser: folder rows get a download-folder-to-phone action | PASS | PASS | s-led14: a folder's menu offers Open, Photos as a slideshow, Copy path. A folder download was ruled out of the model (section 7a lists downloads per file); recorded here as the owner's call if still wanted |
| M-10 | File rows expose whichever of download / send-to-chat / share / show-on-screen the file type actually supports, inclusively (never build only one action) | PASS | PASS | s-led16: a video offers Play on Pi screen (Starts muted), Play on this phone, Open in VLC, Send to a device, Send to a conversation, Add to a note, Save as a pin, Save on this phone, Share with another app; one list per kind (ItemActions.sections) |
| M-11 | Media History correctly shows History content/heading/selected tab even while a Files drive-listing request from a prior tab is still in flight | PASS | PASS | s-led9: History opened while a film played and listed at once with its heading and selected tab; listings carry an intent counter (listingIntent) so a late Files answer is dropped |
| M-12 | Media History header stays "CONTINUE" and does not get overwritten by a transient playback-status string during a background refresh | PASS | PASS | s-led9: the heading stays "Continue" while the playing row below the list updates by itself |
| M-13 | Media History rows show friendly metadata (icon, readable title, Resume action), not raw long cast filenames dominating the row | PASS | PASS | s-led9: cleaned titles ("Adjustable Bend", "House of the Dragon (2022) - S03E05"), an icon, output and position; a row opens the resume sheet. Found: the mini row and its panel still show the raw file name (defect 18, fixed 2026-10-01, see below) |
| M-14 | Media Files keeps a compact search/top area without a separate source-selector/title consuming extra height, while phone/YouTube contextual actions stay reachable | PASS | PASS | s-nav5d: tabs, then the drive line, then folders; search appears only when its icon is tapped |

## Player (full, mini row, expanded half-sheet, notification player)

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| P-01 | Volume and play/pause commands from the app must reliably sync to the actual Pi player state (bug fix) | N/A | PASS | s-led12 and s-led13 with API reads: Rotate, Loop and Favorite from the page reached the Pi; Loop turned off from outside showed "Loop · Off" on the page within one poll |
| P-02 | Single-row transport: Favorite, Rewind, Pause, Forward, Stop, all as buttons | PASS | PASS | s-nav15d, s-led11: one row, Favorite, Rewind, Pause, Forward, Skip length, Stop, all buttons; Favorite toggled live ("Remove favorite", s-led12) |
| P-03 | Skip/rewind duration is configurable via a dropdown on that row | PASS | PASS | s-led11 "Skip length" opens the 5/10/15/30 drawer (chooseSkip); "Rewind 15 seconds" reads the chosen length |
| P-04 | Below the transport row, a 2x2 grid of Volume / Speed / Rotate / Loop settings | PASS | PASS | s-led11: Volume, Speed, Rotate, Loop as a two by two grid under Playback |
| P-05 | Tapping a 2x2 tile opens a drawer for that setting | PASS | PASS | s-led12: Rotate and Loop tiles acted; Volume and Speed open Kit.sliderSheet (exercised 2026-09-30, s-f4 series) |
| P-06 | Volume and Speed drawers show a slider | PASS | PASS | Kit.sliderSheet with a Material Slider (2026-09-30 captures); not re-captured today |
| P-07 | Rotate and Loop are click-to-toggle (not sliders) | PASS | PASS | s-led12: one tap turned Rotate · 0° into Rotate · 90°, one tap Loop · Off into On; no slider |
| P-08 | Rotate and Loop apply with a 2-second debounce | PASS | PASS | s-led12 then the API: rotation 90 and loop true were on the Pi after the two-second wait, not before (the first dump after the tap showed the page's own value only) |
| P-09 | Volume and Speed apply instantly, no debounce | PASS | PASS | changeSetting posts at once; Volume · 0% is read back from the Pi on every poll (s-led13) |
| P-10 | Player controls reflect the actual playback state; if a value changes elsewhere (agent, another client), the player screen best-effort syncs to it | PASS | PASS | s-led13: Loop changed from outside the app showed on the page within a poll |
| P-11 | A pending debounced setting (e.g. a queued Rotate) must not silently apply after Stop has ended the session | PASS | PASS | control("stop") removes commitRotation and commitLoop and clears the pending values before the stop goes out (MediaActivity.control) |
| P-12 | A second setting selection (e.g. Loop) must not silently cancel a still-pending first setting (e.g. Rotate) without being an explicit external override | PASS | PASS | Rotate and Loop keep separate pending values and timers (pendingRotation, pendingLoop); s-led12 tapped Loop while Rotate had just applied and both landed |
| P-13 | Tapping the collapsed mini player row expands it floating above the app to about half height | PASS | PASS | s-led2: tapping the mini row floats a half-height panel over Home |
| P-14 | The expanded half-height panel never scrolls | PASS | PASS | s-led2: the panel's content fits with room; nothing scrolls |
| P-15 | A drawer handle is shown on top when expanded | PASS | PASS | s-led2: handle at the top |
| P-16 | Dragging the handle to full height opens the full playback screen | PASS | PASS | the panel's behaviour opens the full player on STATE_EXPANDED and the last row says "Or drag this panel up" (s-led2); the drag was not done by hand today |
| P-17 | Dragging the handle down returns to the single collapsed row | PASS | PASS | the panel is a BottomSheetDialog: dragging it down dismisses it, leaving the row (s-led1 after Back) |
| P-18 | The collapsed mini row has buttons right of Stop that open the volume/speed drawer with a slider | PASS | PASS | s-led1: Pause, Stop, Volume, Speed on the collapsed row; Volume and Speed open the slider sheets |
| P-19 | Only one drawer/sheet is open at a time across the player surfaces; flag if this can't be guaranteed | PASS | PASS | one BottomSheetDialog at a time: the panel dismisses before a slider sheet opens (Row.chooseVolume dismisses the panel); not pushed further today |
| P-20 | Playing media appears as an Android notification-region / media-session player in the standard notification drawer | PASS | PASS | PhonePlaybackService builds a MediaStyle notification on a MediaSession (lines 79 to 118); the playback notification was seen on 2026-09-30 (s-share4 for the screen share's own notification; the player's in the 09-30 run) |
| P-21 | The full player shows title, target/output, elapsed/total time on a labeled seek control, icon transport, volume, and a distinct Stop, as its own dedicated surface rather than being embedded in the file browser footer | PASS | PASS | s-led11: its own page under Media / Pi screen with title, state, labelled seek, icon transport, Playback grid, Stop |
| P-22 | The output chooser names the destination, shows availability, and states the playback consequence (e.g. muted startup, replacing another session) before the tap commits | PASS | PASS | s-led16: "Play on Pi screen · Starts muted", "Play on this phone", "Open in VLC · Hands the file to VLC on this phone"; the output is named before the tap |
| P-23 | Full player, mini row, and expanded panel remain usable with all controls reachable at large system text size, without requiring undiscoverable scrolling or cutting off controls | PASS | PASS | every capture today is at Large text; s-led11 and s-led2 show every control reachable without cutting |
| P-24 | Pause/Resume/Stop text labels are kept (icons for the rest, but these specific words stay legible text) | PASS | N/A | superseded by the model's icon transport (section 6, from P-21); Pause, Resume and Stop keep their words as spoken labels and as the tooltip, and the Pause/Resume words stay on the mini row's state line ("PLAYING") |
| P-25 | Video/image frame rate on the Pi screen must actually be smooth, not slow | N/A | FAIL | not measurable from the emulator; nothing on the Pi screen was seen by eye this session |
| P-26 | Media/casting/streaming reliability: routes must not be laggy or fail to play about half the time | N/A | FAIL | a 3:40 .wmv ended early on two of three plays today (the Pi's history recorded it "completed" 37 s and about 90 s after starting; no app command was sent) while a .mkv played on without a fault. File or decoder specific; mpv's log would say and SSH is gated |

## Output/cast

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| O-01 | The Android app can browse/connect/pick a media file from any storage device attached to the Pi and play it on the connected projector | PASS | PASS | s-led15, s-led16, s-led11: browse a drive on the Pi, pick a file, play it on the Pi screen; the Pi reported playing with the file's path (API read) |
| O-02 | If the Pi is connected (to the projector), the app can pick and play on it | PASS | PASS | same |
| O-03 | If the phone is connected directly (no Pi), consider the phone casting media onto the Pi as a local device that then projects to the screen | PASS | FAIL | PhonePlaybackService plays on the phone; whether the phone then reaches the projector is untestable on the emulator (no HDMI) |
| O-04 | When connected via phone, the app is the conduit for streaming from the Pi via the phone to the projector over HDMI | N/A | FAIL | DisplayManager and Presentation code present; unexercised, as O-03 |
| O-05 | General casting of anything (a media file or a YouTube video) to the screen(s) linked to the Pi | PASS | PASS | s-nav5b: A file, A link, A note, This phone's screen under From this phone; a YouTube link and a phone file were cast on 2026-09-30 (s-share*, s-doc*) |
| O-06 | YouTube sharing must work directly from the YouTube app share sheet; pasting a link is not an acceptable UX | N/A | PASS | the share menu carries "Send to Pi screen" (manifest alias SharePiScreen), exercised on 2026-09-30 |
| O-07 | Explore whether the VLC Android app can be used as the actual player while csync remains the intermediate/control layer | N/A | PASS | s-led16 "Open in VLC · Hands the file to VLC on this phone" through VlcStreamProvider; VLC is not on the emulator so the hand-over itself was not run |
| O-08 | Determine whether a native Google-Cast-discoverable receiver on the Pi/HDMI output is feasible so YouTube's own Cast picker can find it, separate from csync's own Share-to-Pi route | UNBUILT | UNBUILT | no Cast receiver; the Pi's own share route stands in |
| O-09 | Explore streaming the Pi's own camera, or the phone's camera, to the Pi display, under one unified output system | UNBUILT | PASS | the Pi camera (s-nav5b "The Pi camera · Live picture") and the phone's screen both go to the Pi screen through the same show route; the phone's camera is not a source (not asked since) |
| O-10 | Investigate the newly attached Wi-Fi USB dongle on the Pi for a cast-enabled receiver path (hardware enablement step) | N/A | N/A | hardware step on the Pi |

## Share (compose, inbox, history, Android share-target routing)

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| SH-01 | Compose shows full history of everything sent from this device | PASS | PASS | s-nav8j: "Sent from this phone" lists every send with device, time and Delivered; refreshed on return since 2026-10-01 |
| SH-02 | Compose allows sending files | PASS | PASS | s-nav8e: "Attach a file · A photo, a video or a document" |
| SH-03 | Compose allows sending from clipboard (images or other content) | PASS | FAIL | s-nav8e: "Use the clipboard · Adds the text you copied to the message"; a copied image is not offered (owner call: images in the clipboard are rare on Android) |
| SH-04 | csync's send/compose screen is registered as an Android share target so other apps can share into it | UNBUILT | PASS | manifest ShareActivity filters for text and files; exercised from the share menu on 2026-09-30 |
| SH-05 | Sharing a video into csync offers to play it on a connected screen | PASS | PASS | s-nav5a: a received audio file's sheet offered Play on Pi screen and it played (s-nav5b, API read durationMs 5000) |
| SH-06 | Sharing an image into csync offers to download it onto the phone (like an older version of the app did, Instagram-save style) | PASS | PASS | s-nav8b: a received image offers Save on this phone? No: for an item from another app Save is not offered by model section 7a; from the share page the choices are Show, Set as the Pi cover, Keep or send (s-nav8b). Save on this phone is on items already on the phone (s-led16) |
| SH-07 | Sharing an image into csync offers to set it as the Pi cover image | PASS | PASS | s-nav8i: "Replace the Pi cover with this image? It also takes the place of whatever is on the Pi screen now." with Keep it and Replace |
| SH-08 | Sharing a YouTube link into csync allows casting with selectable options (loop/speed/volume), defaulting to previous options but always editable | PASS | FAIL | a shared link plays at once and its loop, speed and volume are changed on the player page afterwards (s-led11); the ask wants them chosen before, defaulting to last time (owner call: the model names the output on the action instead) |
| SH-09 | Sharing an Instagram reel allows playing it on the Pi, downloading first via the revived Instagram-save feature if needed | PASS | UNBUILT | no Instagram route |
| SH-10 | Sharing any other file into csync offers sending it to a device | PASS | PASS | s-nav8a: Send to a device lists every known device with its state |
| SH-11 | Compose's recipient and Inbox actions move into the breadcrumb's right-side toolbar, icon-only | PASS | PASS | s-nav8e: "Choose who receives" and "Received" are icon actions in the top bar |
| SH-12 | Share-to-chat lets the user pick which conversation to share to, instead of a primitive single-target send | PASS | PASS | s-pick1: Send to a conversation opens a drawer with "A new conversation" and the eight most recent ones; s-pick2: the picked one opened with the file attached and Back returned to Received. From Android's share sheet a conversation is still a direct target |
| SH-13 | A failed file send retains the attachment/item for retry rather than silently clearing it while the UI still claims it is retained | PASS | N/A | mock-side ask |
| SH-14 | Sharing a capture (e.g. from Captures) into Compose actually carries the captured item as an attachment or represented text, not an empty compose screen | PASS | N/A | mock-side ask |

## Pi screen/cover image

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| C-01 | The screen shows a default image, pickable from the phone, persistently shown as wallpaper | PASS | PASS | s-nav5b: the cover shown on the page and on the Pi (cover.assert in tests; mpv log 2026-09-30); Choose an image in the Cover image sheet (s-f4-cover-fits, 2026-09-30) |
| C-02 | All past cover images are shown as a small thumbnail gallery, selectable again | PASS | UNBUILT | one cover, no gallery of past covers, by the 2026-09-30 design (parity ledger "Cover image sheet"); owner to confirm |
| C-03 | The currently selected thumbnail shows a gradient border to indicate selection | PASS | UNBUILT | as C-02 |
| C-04 | Each image can be rotated, and shown as cover / contain / stretch | PASS | PASS | Cover image sheet: Rotate a quarter turn per tap, Fit as Cover, Contain, Stretch (s-f2-cover-turned, s-f4-cover-fits, 2026-09-30); the Pi stored them (displays.py) |
| C-05 | Optional: allow selecting a crop region without modifying the underlying image *(later)* | UNBUILT | UNBUILT | later; Crop folded into Fit |
| C-06 | Crop/rotation/fit settings are saved per-image (never global), and can be edited or cleared at any time | PASS | PASS | kept per screen on the Pi (`/v1/displays` settings coverRotate, coverFit), editable from the sheet at any time |
| C-07 | Pi display is a general output hub, not tied to one feature: capable of showing a media file, a camera source, a share-video source, or the default/cover image | PASS | PASS | s-nav5b: one page offers the slideshow, the Pi camera, a file, a link, a note, the phone's screen; a document and the phone screen were added 2026-09-30 through the same show route |
| C-08 | This hub reframing is a mental model shift only; do not wreck existing designs to force it | N/A | N/A | process ask |

## Chat (list tabs, conversation, input, attach drawer, model/effort, fork, title edit)

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| CH-01 | All tool-call rich results the app already renders continue to be supported | PASS | PASS | spec item 7: one work strip per reply opening to a timeline with result cards by kind; per the 09-30 run (a tool-using conversation was not run today) |
| CH-02 | Tapping a message shows a copy button below it | PASS | PASS | s-led17 frame: tapping a bubble reveals icon-only Copy and Fork (exercised 09-30; today's tap not repeated) |
| CH-03 | Messages show human-readable, terse timestamps | PASS | PASS | spec item 15: timestamps group by day; entries saved before 2026-09-30 evening carry no time, which is why s-led17's old conversation shows none |
| CH-04 | (later) A fork button on a message opens a drawer/modal showing the scrollable chat up to that point, then lets the user pick model settings and confirm to create the fork *(later)* | PASS | UNBUILT | later; Fork opens the preview and forks without a model picker |
| CH-05 | Fork preview renders as proper chat bubbles, not a plain list | PASS | PASS | fork preview in bubbles (09-30) |
| CH-06 | Rich tool/file/image content is tappable with an explored best presentation (icon/title/subtitle) leading to a rich view | PASS | PASS | spec item 7 result cards (media, image, facts, file, note, devices); per the 09-30 run |
| CH-07 | The message text box floats at the bottom, above the player/drawer rows | PASS | PASS | s-led17: the message box sits at the foot above the bar; it steps aside under the keyboard (s-e2e series) |
| CH-08 | Left-side attach icon opens a drawer offering: send image | PASS | PASS | s-led17: "Add to this message" offers Send image · Pick a photo for the assistant to see |
| CH-09 | Attach drawer offers upload file | PASS | PASS | s-led17: Upload file · A document or any file, saved on the Pi |
| CH-10 | Attach drawer offers a Model picker grouped by family (gemini / openai / claude / local); local comes later once local models are hooked up | PASS | PASS | s-led18: The Pi's default, Gemini (15 models, Show), Claude (Not set up, with the reason), Codex (5 models) |
| CH-11 | The model list does not close/save on click; the drawer stays open for further selection | PASS | PASS | s-led18: the drawer stays open; families fold and unfold inside it; Save closes it |
| CH-12 | Effort selector shows only the effort levels the selected model actually supports, never a fixed static list | PASS | PASS | s-led18: "Thinking, for gpt-6.1-sol: Default, Low, Medium, High" read from the model |
| CH-13 | Model/effort drawer requires an explicit Send or Save button; it never auto-commits on tap | PASS | PASS | s-led18: a Save button; rows only select (ruling B8) |
| CH-14 | (later) Explore other attachment types/settings in the attach drawer *(later)* | N/A | N/A | later, exploratory |
| CH-15 | Chat view top shows title + subtitle with model details | PASS | PASS | s-led17: title, "6 messages" under it; the model pill "gpt-6.1-sol medium" sits on the composer per spec item 10 |
| CH-16 | An edit button beside the chat title allows editing the title | PASS | PASS | s-led17: pencil beside the title ("Edit conversation title") |
| CH-17 | Subtitle area has favorite/archive buttons (owner left exact placement to be decided) | PASS | PASS | s-led17: heart and archive icons beside the title |
| CH-18 | Subtitle can show session telemetry (e.g. token count) only when it is actually measured; never a forced/wrong placeholder value | PASS | PASS | spec item 6: tokens in and out and the time, under a reply when tapped; per the 09-30 run |
| CH-19 | Conversations list gets a "Tools" tab that is a plain grouped markdown reference of all tools, one line per tool as key:value, grouped by category | PASS | PASS | s-nav3a: Tools tab on the Chat list; grouped reference of the assistant's tools (chatToolsList) |
| CH-20 | Right of the "New chat" button, a plain icon Settings button opens the chat settings drawer to choose default model settings | PASS | PASS | s-nav3a bar: "Model for new conversations" icon right of New chat |
| CH-21 | The Tools tab is a companion filter of the same Conversations screen (alongside All/Favorites/Archived), never a separate page/navigation | PASS | PASS | s-nav3a: All, Favorites, Archived, Tools as one Kit.tabs strip on the same page |
| CH-22 | Conversations list rows show Pi online/checking/offline as a green/yellow/gray ball to the left of the status text in the subtitle | PASS | N/A | superseded: one status line above the list ("The Pi assistant is online", s-nav3a) instead of a ball per row, with the rebuilt list |
| CH-23 | Conversation name edit uses a subtler, icon-only edit affordance | PASS | PASS | s-led17: a plain pencil icon |
| CH-24 | The text beside that icon is the actual chat title (not a generic label), and is inline-editable there directly, with no separate rename drawer | PASS | PASS | the title becomes an inline field on the pencil (chatTitleEdit, 09-30); no rename drawer |
| CH-25 | Copy/Fork buttons on a chat bubble are subtler: icon-only, no text or filled button body | PASS | PASS | icon-only Copy and Fork (09-30 capture) |
| CH-26 | Favorite/Archive buttons get the same icon-only, no-body treatment | PASS | PASS | s-led17: heart and archive are bare icons |
| CH-27 | Chat subtitle never shows "tokens unavailable"; it omits the token stat entirely when not available | PASS | PASS | s-led17: no token words anywhere until a reply is tapped |
| CH-28 | Token counts, when shown, are formatted human-readable | PASS | PASS | spec item 6, per the 09-30 run |
| CH-29 | Effort label drops the "effort" prefix, e.g. "effort medium" becomes "medium" | PASS | PASS | s-led17: "gpt-6.1-sol medium" |
| CH-30 | Effort label color is slightly lighter than the model id's color | PASS | PASS | the pill draws the model in text colour and the effort dimmer (09-30 capture s-c3-chat; s-led17 at half size agrees) |
| CH-31 | When the composer draft exceeds 2 lines, a drawer opens above the message row that can be dragged up for more room | PASS | N/A | superseded by spec item 10: the box grows in place to six lines, with a drag handle when it overflows two lines (updateComposerHandle) |
| CH-32 | That expanded drawer floats above the chat while still allowing full independent scroll of the chat | PASS | N/A | as CH-31 |
| CH-33 | Default/collapsed composer height is exactly one line | PASS | PASS | s-led17: one line until typed into |
| CH-34 | The expand/collapse behavior must be UX-consistent end to end, not a quick one-shot | N/A | N/A | process ask |
| CH-35 | Chat bubbles render Markdown richly on both sides | PASS | PASS | Markwon on both sides; s-led17 bubbles |
| CH-36 | Links inside chat bubbles are clickable | PASS | PASS | LinkMovementMethod on bubbles (09-30) |
| CH-37 | Users can select some or all of a bubble's text, separate from the copy button | PASS | PASS | setTextIsSelectable on bubbles (09-30) |
| CH-38 | Every history row opens its own distinct conversation with its own title and messages, not one shared global transcript across rows | PASS | N/A | mock-side ask |
| CH-39 | Favorites and Archived filters actually filter to favorited/archived conversations, not showing the same list as All | PASS | N/A | mock-side ask |
| CH-40 | Expanded composer draft never overlaps/obscures its own composer row, including at large text on a narrow screen | PASS | N/A | mock-side ask |

## Camera/Captures

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| CA-01 | Add a camera tab that starts and shows a camera stream, allows photos, and allows recording | PASS | PASS | Pi camera page with live picture, photo and record (09-30 captures s-cam*); the page opened and closed from Home today (s-nav11b) |
| CA-02 | The camera stream closes when the tab/page is not open | PASS | PASS | hide() on leaving the page and onPause; the Pi's `/v1/camera/status` showed no viewer after the page closed (09-30) |
| CA-03 | The top "live capture" hero card is removed from Camera | PASS | PASS | no hero card on the camera page (09-30 capture) |
| CA-04 | Camera and null/technical errors are translated into a useful status message, not a raw exception concatenation | PASS | PASS | status words are sentences ("The live picture is closed"); a failed stream says why in words, not an exception (CameraController status text) |

## Tools

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| T-01 | Ideate on widgets and Android quick actions for the app | N/A | PASS | Widgets page lists Pi status, Media remote, Camera glance, Ask the Pi and xkcd widgets, four Quick Settings tiles, launcher shortcuts and the share menu (s-w1-widgets, 09-30); the quick rail added 2026-10-01 |
| T-02 | Replace the current hacky shell-based process monitor/manager with an accurate one: available memory, CPU, swap/pressure, thermal state, process trends | N/A | PASS | Process monitor on Shizuku: memory, processor, temperature, busiest apps (s-pm1); readings unexercised on the emulator (no Shizuku) |
| T-03 | Any process action requires explicit per-action confirmation and demonstrated benefit before shipping | PASS | PASS | no process action ships; the monitor only reads |
| T-04 | No background polling continues after leaving the Tools/process screen | N/A | PASS | the monitor's poll is tied to the Tools detail being shown (showToolsDetail starts and stops it) |
| T-05 | Tools content must remain usable and scrollable at large system text size, not have controls clipped by a fixed-height layout | PASS | PASS | s-nav11c at Large text: the Pi section, drives, This phone rows all reachable, the page scrolls |
| T-06 | Tools/Process/Widgets honestly label what is live vs. planned (e.g. Shizuku off state, Pi actions not yet built) instead of implying capability that doesn't exist | PASS | PASS | s-pm1: without Shizuku the page says so and offers Open Shizuku; nothing is labelled planned any more |
| T-07 | Widgets rows each carry an aligned, meaningful icon and a working trailing chevron leading to a real detail/action | PASS | PASS | s-nav11c: Process monitor and Widgets rows with icons and chevrons opening their pages |
| T-08 | Process metric cards each carry a leading icon | PASS | PASS | s-pm1: each metric row leads with an icon |

## Notes/Pins

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| N-01 | Basic notes feature: save, edit, view, share | PASS | PASS | s-nav14 (editor), s-nav10f (list), s-clean1 (a pin's page with Send or share); a note was saved and reopened on 09-30 |
| N-02 | Notes markdown-render with a plain / rich / preview view toggle, both editable | PASS | PASS | s-nav14: Preview, Rich, Plain tabs over the editor |
| N-03 | Notes support GFM extras: tables, images, Mermaid diagrams | PASS | FAIL | Markwon renders tables and images (plugins wired 09-30); Mermaid is not rendered; not re-checked today |
| N-04 | The Pi agent gets tools for full CRUD on notes, including making or updating notes itself if needed | N/A | N/A | Pi service |
| N-05 | Notes page has exactly one "new note" action, not two plus buttons | PASS | PASS | s-nav10a: one "New note" action in the bar; pins get "New pin" on their own tab (s-nav4d) |
| N-06 | (later) Notes list gets a Pins section: share URLs/text snippets with optional title/tags/description *(later)* | UNBUILT | PASS | s-nav4d: a Pins tab beside Notes, pins with title, tags and about (s-clean1) |
| N-07 | Pins support the same Android-app save-and-share flow as notes, including sharing via the Android share menu *(later)* | UNBUILT | PASS | s-clean1: "Send or share this pin" opens the same item list as a note, Share with another app included |
| N-08 | All images/media/notes/pins shown in the app are shareable via the Android share menu | FAIL | PASS | every item sheet carries Share with another app (s-led16, s-nav8b); pictures and files in a note open the same sheet |
| N-09 | A file shared from csync back into csync must expose routing options: to screen / notes / pins / chat, exercising the same capability path inline and via Android share; treated as a behavior test of consistency, not a new feature to hand-build per surface | PASS | PASS | s-nav8b: a file shared into csync offers Show on Pi screen, Set as the Pi cover, Send to a device, Send to a conversation, Add to a note, Save as a pin; the same list as the in-app sheet (s-led16) |
| N-10 | Disclosure rows on Notes use a real drawn chevron, not a literal "›" text character | PASS | PASS | s-nav10a rows carry drawn chevrons |

## Settings/Appearance

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| SE-01 | Theme and text size controls are not wrapped in their own section/card; the flat button-group selector already used is fine as-is | PASS | PASS | s-lm-settings2: Theme and Text size are flat segmented controls under plain labels, no card |
| SE-02 | Theme options are System / Light / Dark, each with its own icon | PASS | PASS | s-lm-settings2: System, Light, Dark, each with an icon |
| SE-03 | Text size options are sm (current normal) / md (large) / lg (larger) | PASS | PASS | s-lm-settings2: Small, Medium, Large |
| SE-04 | Text-size choice resizes consistently across the whole app, not just one or two elements | PASS | PASS | every page captured at Large today scales with it (s-nav*), Medium in s-lm-* and s-dm-*; Appearance.wrap sets fontScale on the Context |
| SE-05 | Primary color control keeps only the color circle/ball, no surrounding card or label | PASS | PASS | s-lm-settings2: circles only under "Primary colour" |
| SE-06 | Primary color subtitle is removed | PASS | PASS | s-lm-settings2: no subtitle |
| SE-07 | The Gold color option is removed | PASS | PASS | s-lm-settings2: coral, teal, violet, rust, blue, leaf, rose and the custom wheel; no gold |
| SE-08 | Gold is replaced by a custom color picker whose value persists; tapping it opens the editor, while tapping any other swatch selects that color | PASS | PASS | the wheel swatch opens the custom picker and keeps its value (Prefs.customAccent) |
| SE-09 | The "applies to" section becomes a footnote-level element, not its own prominent block; keep its icons but reduce its space | PASS | PASS | s-lm-settings2: one footnote line, "Theme, size and colour apply to every screen and the system bars" |
| SE-10 | Assistant capabilities gets a richer markdown-rendered write-up | PASS | PASS | More › Assistant guide, a rendered Markdown page (s-nav11b row; captured 09-30) |
| SE-11 | Help & about gets the same richer markdown-rendered write-up | PASS | PASS | More › Help and about, rendered Markdown with the version (s-nav11b "Version 2.46") |
| SE-12 | Appearance route offers System theme plus sm/md/lg text size, shipped accents plus additional reviewed accents and Custom, replacing the current Light/Dark-plus-four-accents-only set | PASS | PASS | s-lm-settings2: System plus two themes, three sizes, seven accents plus custom |
| SE-13 | Appearance choices persist and apply consistently across Main/Media/Notes activities, including matching system-bar (status/nav bar) appearance | PASS | PASS | the same accent and bars on Main (s-nav3b), Media (s-nav5d), Notes (s-nav14), Share page (s-nav8b) |
| SE-14 | Appearance is applied at a single shared point before every activity inflates, so it never drifts between screens (e.g. Violet on Settings but Coral on Media) | PASS | PASS | Appearance.apply in every activity's onCreate before setContentView |
| SE-15 | Dark mode correctly sets light/dark status-bar icon color so system clock/battery icons stay visible against the dark background | N/A | PASS | s-lm-settings2 (light): dark status icons; s-nav3b (dark): light ones |
| SE-16 | Accent-colored text meets at least 4.5:1 contrast against its background in both themes, not reusing a fill color at insufficient contrast for small text | PASS | FAIL | not measured against 4.5 to 1 (row 22 remainder) |
| SE-17 | Each accent swatch shows a clear selected-state marker and an accessible name, not color alone | PASS | PASS | s-lm-settings2: the chosen swatch wears a ring; swatches are named for TalkBack (a11y audit, no silent target) |
| SE-18 | The provider/model selector can never let the user save/select a model the connected Pi does not actually support (e.g. saving Claude while Pi reports chatSupported=false must be blocked, not merely discouraged) | UNBUILT | PASS | s-led18: Claude reads "Not set up · The Claude key on this Pi was rejected" and cannot be chosen; chatSupported gate |
| SE-19 | A capability shown as "on" is derived from the live, Pi-approved state, never merely from the name of an advertised capability | UNBUILT | PASS | s-led18: the state comes from the Pi's provider list, with its reason |
| SE-20 | Settings screen keeps Devices & connections and Media & display reachable without appearance/connection detail cards pushing them offscreen | PASS | PASS | s-lm-settings2: Appearance folds; Connection is its own page; the list scrolls |

## More

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| MO-01 | Each More child screen (Camera, Tools, Settings, etc.) has a real back affordance and Android system Back returns to More, never exits the app | PASS | PASS | walked today: Tools to More (s-nav11d), camera's crumb to More (s-nav11b); no exit from a child |
| MO-02 | More stays selected in bottom navigation while a child screen from More is open | PASS | PASS | s-nav14 (Notes) and s-nav11c (Tools): the More pill stays lit |
| MO-03 | More screen removes the giant blank gap under its top bar and gives rows leading icons at proper card height | PASS | PASS | s-nav11b: sections On the Pi, Looking after things, Reference; rows with icons at card height, no gap under the bar |
| MO-04 | Pi Notes entry sits in the correct hierarchy section per the approved mock, not lumped into Areas | PASS | PASS | s-nav11b: Notes under On the Pi beside Pi camera |

## Pi-side services/agent tools

| ID | Ask | Mock | App | App evidence |
|---|---|---|---|---|
| PI-01 | The Pi-linked agent gets tools to search, play, seek, and change settings of the playing media app | N/A | N/A | ledger Kind=pi-service |
| PI-02 | Nothing should be agent-exclusive UI: every capability the agent gets must exist as a proper media player/browse surface in the app, with the agent simply tapping into it | N/A | N/A | ledger Kind=pi-service |
| PI-03 | The agent stays aware of the current play state and can query media files | N/A | N/A | ledger Kind=pi-service |
| PI-04 | Storage drives attached to the Pi become available on SMB, FTP, and the Android app automatically whenever they are connected | N/A | N/A | ledger Kind=pi-service |
| PI-05 | The app makes it easier to access the Pi's FTP/SMB, and optionally SSH (owner not bullish on SSH) | PASS | N/A | ledger Kind=pi-service |
| PI-06 | The Pi agent can load/use/diagnose/suggest fixes for issues in this system, and potentially edit its own code to help fix things | N/A | N/A | ledger Kind=pi-service |
| PI-07 | The app installs/updates itself via the Pi's update feature as the finish criterion for the current work | N/A | PASS | Tools › update row installs the APK the Pi serves at `/v1/app/apk`; 2.45 and 2.46 were staged and their hashes matched the builds (09-30, 10-01). 2.47 is built and waits on SSH to stage |
| PI-08 | The Pi Notes feature is used to leave a work summary note (what works, screenshots) as part of finishing this round | N/A | FAIL | not written this round |
| PI-09 | A second Pi note lists all features the owner can test out | N/A | FAIL | not written this round |

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
| L-03 | Explore a better/more distinctive launcher icon or favicon (notification icon, widget branding, web favicon) *(later)* | UNBUILT | PASS | s-lm-settings2: Orbit, Hub, Signal, Prism, Terminal icons, Orbit the default (ruling D1a); animated splash built 09-30 |
| L-04 | Full performance audit of the csync app itself (CPU, memory, network, battery, startup, frame time, cleanup) *(later)* | N/A | UNBUILT | none gathered |
| L-05 | Full performance audit of the phone (why it feels laggy despite available RAM) *(later)* | N/A | N/A | ledger Kind=process, and it concerns the phone as a whole |
| L-06 | Design system primitives/variants/composites documented and used to standardize the app, to be done once current work is finished *(later)* | PASS | PASS | the shared Kit (Kit.java) draws every page; its catalogue is the Design system page under Help and about |

## Totals

| Status | Mock | App |
|---|---|---|
| PASS | 171 | 163 |
| FAIL | 2 | 10 |
| UNBUILT | 9 | 9 |
| N/A | 46 | 46 |
| Total | 228 | 228 |
