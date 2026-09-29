# csync Android redesign: master requirements ledger

Built from the owner's messages 2026-09-24 to 2026-09-28, the 82 callout rows, the improvement backlog, and two independent adversarial-review indictments. Every row traces to an owner source (message file:line or callout id). Codex-authored planning docs (`android-ui-final-spec.md`, `android-ui-round4-reconciliation.md`) were not used as a source of any ask; they were skimmed only to check nothing owner-voiced was missed, and nothing new surfaced there beyond what appears below.

Sources read in full: `owner-msgs-early.md`, `owner-msgs.md`, `callouts.jsonl` (all 82 rows), `android-improvement-backlog.md`, both indictments, `recovered-brief.md`. Claude Code transcripts before 2026-09-24 were not searched (out of the stated budget for this pass). If earlier Android asks exist there, they are not captured below.

Legend: Kind = mock-ui (the HTML clickthrough only) / native-ui (the installed Android app) / feature (functional capability, either surface) / pi-service (Raspberry Pi side) / process (review/testing/workflow demand). Priority = now / later (owner explicitly deferred).

---

## Global shell (top bar, breadcrumb, back, bottom nav, drawers, icons, text rules)

| ID | Requirement | Owner quote | Source | Kind | Priority |
|---|---|---|---|---|---|
| G-01 | Top bar renders as a proper breadcrumb, not an inconsistent one | "Right now it only shows an inconsistent breadcrumb. Let's make this a proper breadcrumb." | owner-msgs-early.md:336 | native-ui | now |
| G-02 | Back button always goes exactly one level up, never in circles | "the back button should should not go in circles but actuall just go one level up" | owner-msgs-early.md:336 | native-ui | now |
| G-03 | Back button is navigation-only: never repurposed for file/folder traversal, stopping media, or any other action | "This back button should NEVER ever be used for file folder path traversal or stopping the media or something else, this is purely navigation" | owner-msgs-early.md:336 | native-ui | now |
| G-04 | Breadcrumb bar never scrolls | "Make sure the top breadcrumb bar does not scroll" | owner-msgs-early.md:413 | native-ui | now |
| G-05 | Breadcrumb bar height never changes when contents change | "and does not change height when the contents change" | owner-msgs-early.md:413 | native-ui | now |
| G-06 | Every crumb that shows an icon for its route shows that icon consistently, every time that crumb appears | "In breadcrumbs when showing an icon for a crumb, ensure it is consistently shown always for that" | owner-msgs-early.md:440 | native-ui | now |
| G-07 | Circular hero/focus cards ("named receivers", "your hub", "Raspberry Pi is ready" style) removed from every screen that has one | "Get rid of the top card with the circle bg from everywhere, you're not doing it properly, the card with 'named recievers' or 'your hub', all the places it shows" | owner-msgs-early.md:415 | native-ui | now |
| G-08 | Any control lost by removing a hero card is relocated to exactly one place elsewhere, never duplicated | "ensure the controls in it are shown elsewhere (do not double-add)" | owner-msgs-early.md:415 | native-ui | now |
| G-09 | Bottom drawers/sheets have no close button at the top of the drawer | "remove the close button on top and the second close button at the bottom, this is fucking stupid" | owner-msgs-early.md:416 | native-ui | now |
| G-10 | Bottom drawers/sheets have no close button at the bottom of the drawer | same as G-09 | owner-msgs-early.md:416 | native-ui | now |
| G-11 | Drawer dismissal is by slide-down or tap-outside only | "Just let the slide down / tap outside be the closing action" | owner-msgs-early.md:416 | native-ui | now |
| G-12 | No ellipsis ("...") anywhere in the app, on text or in an input box | "There should be no '...' anywhere in the app, not on a text or input box." | owner-msgs-early.md:427 | native-ui | now |
| G-13 | Every tab or button across the app has a leading icon | "Give each tab or button across the app an icon to the left" | owner-msgs-early.md:409 | native-ui | now |
| G-14 | Icon-only controls (e.g. bottom nav) keep an accessible label for the icon even when no visible text is shown | derived from repeated icon-only asks; contrast rule at co-20260927-212104-00 requires "accessible labels" | callouts.jsonl:co-20260927-212104-00 | native-ui | now |
| G-15 | Title+subtitle pattern (established for Notes) is reused elsewhere where it adds context, not applied everywhere indiscriminately | "The title and subtitle for notes is a good pattern, lets use thiss in other places werever applicable (do not spam everywhere)" | owner-msgs-early.md:418 | native-ui | now |
| G-16 | The final native app uses Material components, motion, and guidance as much as possible; the HTML mock does not exempt the real app from this | "Ensure that in the final android app you use as much of native material components and animations and guides as possible, this mock html is fine but do not skip this in the final app" | owner-msgs-early.md:417 | native-ui | now |
| G-17 | Disclosure/expand-collapse affordances use a drawn chevron icon, never a literal text character like "v" or "⌄" | "don't forget the v usage sloppiness, use a proper cared down" | callouts.jsonl:co-20260927-204447-e5 | native-ui | now |
| G-18 | Icon size, label text size, and the gap/padding around them keep a proper, consistent ratio across all cards/rows | "why are the icons so small compared to the text and why does the buttin not have proper text size to spacing around it in a proper ratio" | callouts.jsonl:co-20260927-204447-b4 | native-ui | now |
| G-19 | Icons and text are vertically/baseline aligned and relatively spaced consistently across all cards | "ALL ICONS AND TEXT SHOULD BE PROPERL ALIGNED AND RELATIVELY SPACED" | callouts.jsonl:co-20260927-204448-01 | native-ui | now |
| G-20 | Card sizing, internal padding, and row/column/section spacing are consistent with the approved mock, not ad hoc per screen | "MORE CONTENT SIZE <> VERTICAL <> HORIZONTAL spacing fuckups" | callouts.jsonl:co-20260927-204448-76 | native-ui | now |
| G-21 | Primary bottom navigation shows icons only, no visible text labels, with stable selected state | "ARE YOU FUCKING BLIND I FUCKING ASKED FOR ICONS ONLY" | callouts.jsonl:co-20260927-204449-73 | native-ui | now |
| G-22 | Top bar spacing, sizing, and background are compact and consistent across screens/themes, matching the mock | "LOOK AT THE PATHETIC MESS OF A TOP BAR SPACING AND SIZING AND BACKGROUND" | callouts.jsonl:co-20260927-204449-c2 | native-ui | now |
| G-23 | Status text and its trailing chevron stay aligned with a consistent right inset (e.g. device rows on Home) | "YOU COULDN'T ALING ONE FUCKING THING" | callouts.jsonl:co-20260927-204450-0e | native-ui | now |
| G-24 | Section tab strips (e.g. Media Files/Videos/History/Access) each carry an aligned icon plus label, with a selected state and accessible labels | "NO FUCKING ICONS FOR THE TABS" | callouts.jsonl:co-20260927-212104-00 | native-ui | now |
| G-25 | Disclosure/action rows use a drawn chevron, at least 48dp touch height, balanced padding, and visible pressed/expanded states | "CARET, AND THIS TOUCH SURFACE IS AN EMBARRASSMENT" | callouts.jsonl:co-20260927-212105-d9 | native-ui | now |
| G-26 | Top bar/context row is consistent in height, background, and hierarchy across every native page, not just some | "shameful top bar" | callouts.jsonl:co-20260927-212103-81 | native-ui | now |
| G-27 | No screen or component text reads as AI-generated slop | "ensure no text on any screen reads AI-slop" | owner-msgs.md:62 (goal update) | native-ui | now |

## Home

| ID | Requirement | Owner quote | Source | Kind | Priority |
|---|---|---|---|---|---|
| H-01 | The "Raspberry Pi is ready" (or equivalent) focus card loses its subtitle | "Simplify the 'Raspberry Pi is ready' top focus card, here and everywhere - Remove the subtitle" | owner-msgs-early.md:339 | native-ui | now |
| H-02 | That card's title is rendered smaller | "make the title smaller here" | owner-msgs-early.md:339 | native-ui | now |
| H-03 | This simplification pattern applies everywhere the same style of card exists, not only Home | "here and everywhere" | owner-msgs-early.md:339 | native-ui | now |
| H-04 | "Open an area" section is renamed "Capabilities" | "Change the title 'Open an area' -> 'Capabilities'" | owner-msgs-early.md:341 | native-ui | now |
| H-05 | Each Capabilities row's second line is a status dot (green/grey/red/yellow) plus status text | "In this, put the green/grey/red/yellow dot + status as the second line subtitle" | owner-msgs-early.md:342 | native-ui | now |
| H-06 | Capabilities section shows more features than before, with qualifying/available ones listed first | "We can be showing more features here, list the ones that qualify first" | owner-msgs-early.md:343 | native-ui | now |
| H-07 | Devices, Open-an-area/Capabilities, and Pick-up sections are each collapsible by clicking the section title | "allow each section (devices, open an area, pick up) to be collapsible by title click" | owner-msgs-early.md:325 | native-ui | now |
| H-08 | A caret is shown to the right of each collapsible section title, vertically aligned with it | "a caret shown right to the title vertically aligned" | owner-msgs-early.md:325 | native-ui | now |
| H-09 | The "Open an area" card's subtitle can show a second, dot-separated status (online/offline/counts) | "I think the subtitle can also show a dot separated second status for online / offline / counts" | owner-msgs-early.md:325 | native-ui | now |

## Search

| ID | Requirement | Owner quote | Source | Kind | Priority |
|---|---|---|---|---|---|
| S-01 | A single, real global Search screen replaces the ad hoc chat-title-only dialog: scope tabs, mixed named results, exact result identity, empty/offline states | "Home/Search is an AlertDialog over local chat titles and keyword shortcuts instead of the approved full Search route with scope tabs, mixed named results, exact item identity, empty/offline states" | callouts.jsonl:co-20260928-001821-03 | native-ui | now |
| S-02 | Search query and scope survive returning from a result (Back retains query) | "preserve query on return" | callouts.jsonl:co-20260928-001821-03 | native-ui | now |
| S-03 | Search results must not all be cosmetic re-skins of one screen; it is one real distinct search flow with query, domain filters, and mixed results | "for search these are essentially the same screens with one card added or some spacing change" | owner-msgs-early.md:326 | mock-ui | now |

## Media (Files / Videos / History / Access / source drawer)

| ID | Requirement | Owner quote | Source | Kind | Priority |
|---|---|---|---|---|---|
| M-01 | The hero card at the top of Media > Access is removed | "Get rid of the card on top" | owner-msgs-early.md:344 | native-ui | now |
| M-02 | "Switch source" moves to the right of the search button as an icon-only control (pick a different icon than currently used) | "show the 'switch source' right of the search button, make it an icon only (pick another icon)" | owner-msgs-early.md:345 | native-ui | now |
| M-03 | Tapping switch-source opens the same choose-a-source drawer as today | "it can open the choose a source drawer the same as now" | owner-msgs-early.md:345 | native-ui | now |
| M-04 | Selecting a drive/source never silently changes the selected section (History/Files) or leaves a stale source label | Section/source consistency finding: header simultaneously said History, BROWSING Pi USB, and Choose a drive | indictment.md (2026-09-26):20,71 | native-ui | now |
| M-05 | Previously-existing media files on the Pi that were not visible via the app must actually show | "it already used to have some media files but I can't see those via the phone app" | owner-msgs-early.md:154 | feature | now |
| M-06 | Optional: history of all played media files, tappable to resume that specific play | "the app should also show me a history of all the media files I've played, and allow me to tap that to resume that specific play" | owner-msgs-early.md:16 | feature | now |
| M-07 | Rotation control for playing media | "NO way to rotste it" | owner-msgs-early.md:245 | feature | later |
| M-08 | Loop control for playing media | "ot set it to looping" | owner-msgs-early.md:245 | feature | later |
| M-09 | Raspi disk browser: folder rows get a download-folder-to-phone action | "for the folders shown, allow downloading a folder to phone" | owner-msgs-early.md:420 | feature | now |
| M-10 | File rows expose whichever of download / send-to-chat / share / show-on-screen the file type actually supports, inclusively (never build only one action) | "for media that can be shared to the screen show an option for that, and for files show an option to download / send to chat / share. Do not implement these exclusively, these are inclusive for whatever the file / folder can support" | owner-msgs-early.md:420 | feature | now |
| M-11 | Media History correctly shows History content/heading/selected tab even while a Files drive-listing request from a prior tab is still in flight | "History visually shows Files selected, Files heading, and drive rows after a pending drives callback" | callouts.jsonl:co-20260927-222855-a6 | native-ui | now |
| M-12 | Media History header stays "CONTINUE" and does not get overwritten by a transient playback-status string during a background refresh | "History section heading above resume rows says Pi playback stopped instead of CONTINUE after playback refresh" | callouts.jsonl:co-20260927-233145-b0 | native-ui | now |
| M-13 | Media History rows show friendly metadata (icon, readable title, Resume action), not raw long cast filenames dominating the row | "Native History has persistent Search media, an ungrouped raw filename list, no icons/Resume, and much taller top content" | callouts.jsonl:co-20260927-233145-a1 | native-ui | now |
| M-14 | Media Files keeps a compact search/top area without a separate source-selector/title consuming extra height, while phone/YouTube contextual actions stay reachable | "Native Files search and Find row is taller than mock; prominent From phone or YouTube card changes Files hierarchy" | callouts.jsonl:co-20260927-233146-24 | native-ui | now |

## Player (full, mini row, expanded half-sheet, notification player)

| ID | Requirement | Owner quote | Source | Kind | Priority |
|---|---|---|---|---|---|
| P-01 | Volume and play/pause commands from the app must reliably sync to the actual Pi player state (bug fix) | "the volume and play/pause are not syncing, I had to disconnect the hdmi because a movie I played via the app was being a nuissance to pause and blasting full volumne. Bug fix needed." | owner-msgs-early.md:165 | feature | now |
| P-02 | Single-row transport: Favorite, Rewind, Pause, Forward, Stop, all as buttons | "Favorite, Rewind, Pause, Forward (allow the duration of the skip to be set by a button with a dropdown here as well), Stop (buttons all of them)" | owner-msgs-early.md:349 | native-ui | now |
| P-03 | Skip/rewind duration is configurable via a dropdown on that row | same as P-02 | owner-msgs-early.md:349 | native-ui | now |
| P-04 | Below the transport row, a 2x2 grid of Volume / Speed / Rotate / Loop settings | "put the playback controls all in a 2x2 grid below it" | owner-msgs-early.md:350 | native-ui | now |
| P-05 | Tapping a 2x2 tile opens a drawer for that setting | same as P-04 | owner-msgs-early.md:350 | native-ui | now |
| P-06 | Volume and Speed drawers show a slider | "Let the drawer for volume and speed open a slider in the drawer" | owner-msgs-early.md:350 | native-ui | now |
| P-07 | Rotate and Loop are click-to-toggle (not sliders) | "let rotate and loop be click to toggle" | owner-msgs-early.md:350 | native-ui | now |
| P-08 | Rotate and Loop apply with a 2-second debounce | "give it. 2s debounce when changing these two" | owner-msgs-early.md:350 | native-ui | now |
| P-09 | Volume and Speed apply instantly, no debounce | "volume and speed should be instant though" | owner-msgs-early.md:350 | native-ui | now |
| P-10 | Player controls reflect the actual playback state; if a value changes elsewhere (agent, another client), the player screen best-effort syncs to it | "Ensure that the controls here also sync the values from the actual media play itself, so if the values change somewhere else this player does best effort to sync upto it" | owner-msgs-early.md:351 | feature | now |
| P-11 | A pending debounced setting (e.g. a queued Rotate) must not silently apply after Stop has ended the session | Stop must cancel any pending debounced setting change (adversarial finding, direct extension of P-08/P-10) | indictment.md (2026-09-27) rank 5 | mock-ui/native-ui | now |
| P-12 | A second setting selection (e.g. Loop) must not silently cancel a still-pending first setting (e.g. Rotate) without being an explicit external override | same finding, second half | indictment.md (2026-09-27) rank 5 | mock-ui/native-ui | now |
| P-13 | Tapping the collapsed mini player row expands it floating above the app to about half height | "When tapped, allow this to expand floating above he main app to like half the height, and show the same playback screen here" | owner-msgs-early.md:353 | native-ui | now |
| P-14 | The expanded half-height panel never scrolls | "ensure no scroll" | owner-msgs-early.md:353 | native-ui | now |
| P-15 | A drawer handle is shown on top when expanded | "Show a drawer handle on top when expanded" | owner-msgs-early.md:354 | native-ui | now |
| P-16 | Dragging the handle to full height opens the full playback screen | "if the user drags it full height then open the playback screen" | owner-msgs-early.md:354 | native-ui | now |
| P-17 | Dragging the handle down returns to the single collapsed row | "if drag down then go back to the single row" | owner-msgs-early.md:354 | native-ui | now |
| P-18 | The collapsed mini row has buttons right of Stop that open the volume/speed drawer with a slider | "In the collapsed player row, also show buttons right of the stop to open the volume ann speed drawer with the slider" | owner-msgs-early.md:355 | native-ui | now |
| P-19 | Only one drawer/sheet is open at a time across the player surfaces; flag if this can't be guaranteed | "I hope the multiple drawers won't cause issues. If so, please flag that." | owner-msgs-early.md:356 | feature | now |
| P-20 | Playing media appears as an Android notification-region / media-session player in the standard notification drawer | "ensure the playing media shows as the android notification region player plugging into the standard drawer" | owner-msgs-early.md:357 | feature | now |
| P-21 | The full player shows title, target/output, elapsed/total time on a labeled seek control, icon transport, volume, and a distinct Stop, as its own dedicated surface rather than being embedded in the file browser footer | Indictment finding: the mock gives player its own frame; implementation mixed player controls into the media browser layout | indictment.md (2026-09-26) rank 6 | native-ui | now |
| P-22 | The output chooser names the destination, shows availability, and states the playback consequence (e.g. muted startup, replacing another session) before the tap commits | "The output choice needs an explanation before the effect" | indictment.md (2026-09-26) rank 12 | native-ui | now |
| P-23 | Full player, mini row, and expanded panel remain usable with all controls reachable at large system text size, without requiring undiscoverable scrolling or cutting off controls | large-text player transport/settings clipped or requiring scroll in both indictments | indictment.md (2026-09-27) rank 13 | native-ui | now |
| P-24 | Pause/Resume/Stop text labels are kept (icons for the rest, but these specific words stay legible text) | "Keep text on Pause/Resume and Stop" | indictment.md (2026-09-26):153 | native-ui | now |
| P-25 | Video/image frame rate on the Pi screen must actually be smooth, not slow | "the frame rate of the videos on the screen is still slow" | owner-msgs-early.md:228 | feature | now |
| P-26 | Media/casting/streaming reliability: routes must not be laggy or fail to play about half the time | "its laggy and doesn't play half the time" | owner-msgs-early.md:195 | feature | now |

## Output/cast

| ID | Requirement | Owner quote | Source | Kind | Priority |
|---|---|---|---|---|---|
| O-01 | The Android app can browse/connect/pick a media file from any storage device attached to the Pi and play it on the connected projector | "I want to be able to use the android app (the existing one) to be able to seamlessly browse / connect / pick a media file from the storage devices connected to raspi and play it on the projector." | owner-msgs-early.md:13 | feature | now |
| O-02 | If the Pi is connected (to the projector), the app can pick and play on it | "If raspi is connected then I want to be able to use the app to pick and play." | owner-msgs-early.md:13 | feature | now |
| O-03 | If the phone is connected directly (no Pi), consider the phone casting media onto the Pi as a local device that then projects to the screen | "Maybe this could be the phone being able to cast media onto raspi as a local device that then projects to the screen." | owner-msgs-early.md:15 | feature | now |
| O-04 | When connected via phone, the app is the conduit for streaming from the Pi via the phone to the projector over HDMI | "If connected via phone, then let the app be the conduit for streaming from raspi via the phone to the projector over hdmi" | owner-msgs-early.md:17 | feature | now |
| O-05 | General casting of anything (a media file or a YouTube video) to the screen(s) linked to the Pi | "I also want to be able to cast anything like a media file or a youtube video to the screen(s) linked to raspi as well; general casting behavior." | owner-msgs-early.md:162 | feature | now |
| O-06 | YouTube sharing must work directly from the YouTube app share sheet; pasting a link is not an acceptable UX | "the youtube share needs to be directly via the youtube app to be usable, no one's pasting a link" | owner-msgs-early.md:195 | feature | now |
| O-07 | Explore whether the VLC Android app can be used as the actual player while csync remains the intermediate/control layer | "is there a way to use the vlc android app to control the streaming (our app does the intermediate stuff), vlc is already a mature player" | owner-msgs-early.md:165 | feature | now |
| O-08 | Determine whether a native Google-Cast-discoverable receiver on the Pi/HDMI output is feasible so YouTube's own Cast picker can find it, separate from csync's own Share-to-Pi route | "There is still no real android cast option available huh to the screen so I can play a youtube video natively to the screen" | owner-msgs-early.md:229 | feature | now |
| O-09 | Explore streaming the Pi's own camera, or the phone's camera, to the Pi display, under one unified output system | "I hope I can also stream the raspi camera or my android phone camera to screen via the app, look into that as well, all under the unified system" | owner-msgs-early.md:154 | feature | now |
| O-10 | Investigate the newly attached Wi-Fi USB dongle on the Pi for a cast-enabled receiver path (hardware enablement step) | "On the cast-enabled reciever issue, I have a WiFi USB dongle, I have plugged it into the raspi, please check" | owner-msgs-early.md:234 | pi-service | now |

## Share (compose, inbox, history, Android share-target routing)

| ID | Requirement | Owner quote | Source | Kind | Priority |
|---|---|---|---|---|---|
| SH-01 | Compose shows full history of everything sent from this device | "Show full history of all sent via this device." | owner-msgs-early.md:360 | native-ui | now |
| SH-02 | Compose allows sending files | "Also allow sending files" | owner-msgs-early.md:361 | feature | now |
| SH-03 | Compose allows sending from clipboard (images or other content) | "Also allow clipboard to send images or other things" | owner-msgs-early.md:362 | feature | now |
| SH-04 | csync's send/compose screen is registered as an Android share target so other apps can share into it | "We need to update the android share showing of this app so that this send screen is alo a target." | owner-msgs-early.md:363 | feature | now |
| SH-05 | Sharing a video into csync offers to play it on a connected screen | "Video: Offer to play it on a connected screen" | owner-msgs-early.md:364 | feature | now |
| SH-06 | Sharing an image into csync offers to download it onto the phone (like an older version of the app did, Instagram-save style) | "Image: Offer to be downloaded onto the phone (like a very older version of this apk did on this phone, the instagram save feature)" | owner-msgs-early.md:365 | feature | now |
| SH-07 | Sharing an image into csync offers to set it as the Pi cover image | "Image: Set as the raspi cover image" | owner-msgs-early.md:366 | feature | now |
| SH-08 | Sharing a YouTube link into csync allows casting with selectable options (loop/speed/volume), defaulting to previous options but always editable | "Youtube share: Allow it to be cast (and select options like loop / speed / volume / etc) when selecting, keep previous options as default selected but always allow selecting" | owner-msgs-early.md:367 | feature | now |
| SH-09 | Sharing an Instagram reel allows playing it on the Pi, downloading first via the revived Instagram-save feature if needed | "Instagram reel: Same, allow playing it on raspi. If it needs to be downloaded first via the save instagram media feature you will revive, then we do that first" | owner-msgs-early.md:368 | feature | now |
| SH-10 | Sharing any other file into csync offers sending it to a device | "(any) File: Send to a device" | owner-msgs-early.md:369 | feature | now |
| SH-11 | Compose's recipient and Inbox actions move into the breadcrumb's right-side toolbar, icon-only | "In send to mac, move inbox + recipient button to the breadcrumb right side toolbar (right side of the title, icon only for both)" | owner-msgs-early.md:441 | native-ui | now |
| SH-12 | Share-to-chat lets the user pick which conversation to share to, instead of a primitive single-target send | "Your share to chat is primitive and needs to let me select the chat" | owner-msgs-early.md:421 | feature | now |
| SH-13 | A failed file send retains the attachment/item for retry rather than silently clearing it while the UI still claims it is retained | "Failed file send clears the attachment while the page says it is retained" | indictment.md (2026-09-27) rank 7 | mock-ui | now |
| SH-14 | Sharing a capture (e.g. from Captures) into Compose actually carries the captured item as an attachment or represented text, not an empty compose screen | "Sharing a capture enters Compose without the capture attached or represented as text" | indictment.md (2026-09-27) rank 8 | mock-ui | now |

## Pi screen/cover image

| ID | Requirement | Owner quote | Source | Kind | Priority |
|---|---|---|---|---|---|
| C-01 | The screen shows a default image, pickable from the phone, persistently shown as wallpaper | "Let the screen show a default image I can pic from the phone (locally), can be saved to pi if it helps, persistently shown as a wallpaper" | owner-msgs-early.md:168 | feature | now |
| C-02 | All past cover images are shown as a small thumbnail gallery, selectable again | "all the images selected for showing in the past, show them as a small thumbnail gallery view where I can select an older one again for showing" | owner-msgs-early.md:373 | native-ui | now |
| C-03 | The currently selected thumbnail shows a gradient border to indicate selection | "For that image, show a gradient border around it to indicate it is selected." | owner-msgs-early.md:373 | native-ui | now |
| C-04 | Each image can be rotated, and shown as cover / contain / stretch | "Allow this image to be rotated / cover / contain / stretch in some way or the other as well" | owner-msgs-early.md:374 | feature | now |
| C-05 | Optional: allow selecting a crop region without modifying the underlying image | "ALlow selecting a crop region of the image to be shown. Do not modify the actual image, but just the crop region + rotation + stretch + object-fit." | owner-msgs-early.md:375 | feature | later |
| C-06 | Crop/rotation/fit settings are saved per-image (never global), and can be edited or cleared at any time | "Save this per image (not global), and let it be edited or cleared anytime." | owner-msgs-early.md:375 | feature | now |
| C-07 | Pi display is a general output hub, not tied to one feature: capable of showing a media file, a camera source, a share-video source, or the default/cover image | "I think the raspi display need to be more of a first class citizen, as a hub ... where I can throw in sources from either pi or the phone, be a media file or a camera source or a share video source from another app or the default screen shown" | owner-msgs-early.md:397 | feature | now |
| C-08 | This hub reframing is a mental model shift only; do not wreck existing designs to force it | "do not wreck the designs, this is more of a mental model" | owner-msgs-early.md:397 | process | now |

## Chat (list tabs, conversation, input, attach drawer, model/effort, fork, title edit)

| ID | Requirement | Owner quote | Source | Kind | Priority |
|---|---|---|---|---|---|
| CH-01 | All tool-call rich results the app already renders continue to be supported | "The tool call rich results are good, let's ensure we support all of them" | owner-msgs-early.md:378 | feature | now |
| CH-02 | Tapping a message shows a copy button below it | "Allow each message to be tapped and show a copy button below it" | owner-msgs-early.md:379 | native-ui | now |
| CH-03 | Messages show human-readable, terse timestamps | "human readable terse timestamps" | owner-msgs-early.md:379 | native-ui | now |
| CH-04 | (later) A fork button on a message opens a drawer/modal showing the scrollable chat up to that point, then lets the user pick model settings and confirm to create the fork | "a fork button for the chat so far, will not directly fork but show a drawer / modal with the scrollable chat so far and below that allow me to select model settings and a button to create for confirmation" | owner-msgs-early.md:379 | feature | later |
| CH-05 | Fork preview renders as proper chat bubbles, not a plain list | "For the fork chat preview, show proper bubbles" | owner-msgs-early.md:429 | native-ui | now |
| CH-06 | Rich tool/file/image content is tappable with an explored best presentation (icon/title/subtitle) leading to a rich view | "Explore what is the best way to show (icon / title / subtitle) and allow click for a rich textbox (could be a file an image anything the model made or some tool integration)" | owner-msgs-early.md:380 | feature | now |
| CH-07 | The message text box floats at the bottom, above the player/drawer rows | "Ensure message textbox floats at the bottom, above the player or drawer rows" | owner-msgs-early.md:381 | native-ui | now |
| CH-08 | Left-side attach icon opens a drawer offering: send image | "Send image" | owner-msgs-early.md:383 | feature | now |
| CH-09 | Attach drawer offers upload file | "Upload file" | owner-msgs-early.md:384 | feature | now |
| CH-10 | Attach drawer offers a Model picker grouped by family (gemini / openai / claude / local); local comes later once local models are hooked up | "Model: Grouped list of registered models, the group being gemini / openai / claude / local (local comes later when we hook local models)" | owner-msgs-early.md:386 | feature | now |
| CH-11 | The model list does not close/save on click; the drawer stays open for further selection | "do not close this and save when clicked" | owner-msgs-early.md:386 | native-ui | now |
| CH-12 | Effort selector shows only the effort levels the selected model actually supports, never a fixed static list | "Effort: <effort level of the selected model>, do not show just for the sake of it, show the values supported by the selected model" | owner-msgs-early.md:387 | feature | now |
| CH-13 | Model/effort drawer requires an explicit Send or Save button; it never auto-commits on tap | "Don't let this one click to save, have an explicit button to either send or save" | owner-msgs-early.md:388 | native-ui | now |
| CH-14 | (later) Explore other attachment types/settings in the attach drawer | "[Later]: I want to explore other types of attachments or settings here" | owner-msgs-early.md:389 | feature | later |
| CH-15 | Chat view top shows title + subtitle with model details | "Let the chat view top have the title + subtitle with the model details." | owner-msgs-early.md:390 | native-ui | now |
| CH-16 | An edit button beside the chat title allows editing the title | "Ensure I have an edit button besides the chat title to be able to edit." | owner-msgs-early.md:390 | native-ui | now |
| CH-17 | Subtitle area has favorite/archive buttons (owner left exact placement to be decided) | "Let the subtitle have favorite / archive buttons, or maybe title right idk decide." | owner-msgs-early.md:390 | native-ui | now |
| CH-18 | Subtitle can show session telemetry (e.g. token count) only when it is actually measured; never a forced/wrong placeholder value | "Also some place in the same subtitle to show stats like token count for the session (whatever telemetry we do set up, don't force a value and get it wrong)" | owner-msgs-early.md:390 | feature | now |
| CH-19 | Conversations list gets a "Tools" tab that is a plain grouped markdown reference of all tools, one line per tool as key:value, grouped by category | "Add one more pag tabs, 'tools' - tools is just a rich markdown write-up explaining all the tools. Key: value, one line per tool each; tools lines can be grouped by categories if needed" | owner-msgs-early.md:391 | native-ui | now |
| CH-20 | Right of the "New chat" button, a plain icon Settings button opens the chat settings drawer to choose default model settings | "Right of the 'New chat' button, show a plain Settings button (with an icon) that opens the chat settings drawer but lets me select the default model settings." | owner-msgs-early.md:393 | native-ui | now |
| CH-21 | The Tools tab is a companion filter of the same Conversations screen (alongside All/Favorites/Archived), never a separate page/navigation | "that tab is a companion of the all / favorite / archived buddy not a different page" | owner-msgs-early.md:414 | native-ui | now |
| CH-22 | Conversations list rows show Pi online/checking/offline as a green/yellow/gray ball to the left of the status text in the subtitle | "Let the conversations tab show pi online / checking / offline with a green / yellow / gray ball left to the status in the subtitle" | owner-msgs-early.md:419 | native-ui | now |
| CH-23 | Conversation name edit uses a subtler, icon-only edit affordance | "For the conversation name edit, make the icon subtler (only show the icon)" | owner-msgs-early.md:428 | native-ui | now |
| CH-24 | The text beside that icon is the actual chat title (not a generic label), and is inline-editable there directly, with no separate rename drawer | "the title besides it should be the actual chat title instead of the icon. Actually, allow inline editing of the title there itself, no drawer" | owner-msgs-early.md:428 | native-ui | now |
| CH-25 | Copy/Fork buttons on a chat bubble are subtler: icon-only, no text or filled button body | "For the chat bubble, make the copy and fork more subtler, icons only, no text or button body." | owner-msgs-early.md:430 | native-ui | now |
| CH-26 | Favorite/Archive buttons get the same icon-only, no-body treatment | "Same for the favorite / archive buttons." | owner-msgs-early.md:430 | native-ui | now |
| CH-27 | Chat subtitle never shows "tokens unavailable"; it omits the token stat entirely when not available | "In chat subtitle, do not show 'tokens unavailable', only show if available" | owner-msgs-early.md:431 | native-ui | now |
| CH-28 | Token counts, when shown, are formatted human-readable | "make the numbers human readable" | owner-msgs-early.md:431 | native-ui | now |
| CH-29 | Effort label drops the "effort" prefix, e.g. "effort medium" becomes "medium" | "'effort medium' -> 'medium'" | owner-msgs-early.md:431 | native-ui | now |
| CH-30 | Effort label color is slightly lighter than the model id's color | "make the effort color slightly ligher to the model id" | owner-msgs-early.md:431 | native-ui | now |
| CH-31 | When the composer draft exceeds 2 lines, a drawer opens above the message row that can be dragged up for more room | "if the input message is larger than 2 lines on overflow, show a drawer on top of the message row that lets me drag it up an dhave it take more space" | owner-msgs-early.md:432 | native-ui | now |
| CH-32 | That expanded drawer floats above the chat while still allowing full independent scroll of the chat | "this should float above the chat but still allow full scroll up of the chat" | owner-msgs-early.md:432 | native-ui | now |
| CH-33 | Default/collapsed composer height is exactly one line | "default state the input height should collapse down to one line" | owner-msgs-early.md:432 | native-ui | now |
| CH-34 | The expand/collapse behavior must be UX-consistent end to end, not a quick one-shot | "Ensure this is behaviorally and UX wise consistent, don't just one shot and call it done" | owner-msgs-early.md:432 | process | now |
| CH-35 | Chat bubbles render Markdown richly on both sides | "ensure markdown is rich rendered" | owner-msgs-early.md:433 | native-ui | now |
| CH-36 | Links inside chat bubbles are clickable | "links are clickable" | owner-msgs-early.md:433 | native-ui | now |
| CH-37 | Users can select some or all of a bubble's text, separate from the copy button | "allow me to select some or all of the text (apart from the copy button)" | owner-msgs-early.md:433 | native-ui | now |
| CH-38 | Every history row opens its own distinct conversation with its own title and messages, not one shared global transcript across rows | "Every history row opens the same mutable transcript. New chat is not added to history; renaming a chat changes the detail title but not its history row." | indictment.md (2026-09-27) rank 10 | mock-ui | now |
| CH-39 | Favorites and Archived filters actually filter to favorited/archived conversations, not showing the same list as All | "Both filters display the same three rows as All, regardless of favorite/archive state." | indictment.md (2026-09-27) rank 11 | mock-ui | now |
| CH-40 | Expanded composer draft never overlaps/obscures its own composer row, including at large text on a narrow screen | "The expanded draft overlaps its own composer by about 35 px in the narrow dark/large fixture, hiding part of the text field and Send control." | indictment.md (2026-09-27) rank 12 | mock-ui | now |

## Camera/Captures

| ID | Requirement | Owner quote | Source | Kind | Priority |
|---|---|---|---|---|---|
| CA-01 | Add a camera tab that starts and shows a camera stream, allows photos, and allows recording | "add another tab to the app, that starts and shows a camera stream + allows photos + record" | owner-msgs-early.md:62 | feature | now |
| CA-02 | The camera stream closes when the tab/page is not open | "closes the stream when page not open" | owner-msgs-early.md:62 | feature | now |
| CA-03 | The top "live capture" hero card is removed from Camera | "Mostly looks good, ged rid of the top card with the 'live capture'" | owner-msgs-early.md:396 | native-ui | now |
| CA-04 | Camera and null/technical errors are translated into a useful status message, not a raw exception concatenation | "Translate null or raw technical errors into a useful status." (current source concatenates raw exceptions) | indictment.md (2026-09-26):149 | native-ui | now |

## Tools

| ID | Requirement | Owner quote | Source | Kind | Priority |
|---|---|---|---|---|---|
| T-01 | Ideate on widgets and Android quick actions for the app | "Ideate on widgets and android quick actions for the android app" | owner-msgs-early.md:197 | feature | now |
| T-02 | Replace the current hacky shell-based process monitor/manager with an accurate one: available memory, CPU, swap/pressure, thermal state, process trends | "Better system process monitor/manager (the current one is a hacky shell)" / backlog acceptance row | owner-msgs-early.md:199; android-improvement-backlog.md:16 | feature | now |
| T-03 | Any process action requires explicit per-action confirmation and demonstrated benefit before shipping | Backlog acceptance: "Add safe process actions only with explicit per-action confirmation and measured benefit." | android-improvement-backlog.md:16 | feature | now |
| T-04 | No background polling continues after leaving the Tools/process screen | Backlog acceptance: "Verify no background polling after leaving Tools." | android-improvement-backlog.md:16 | feature | now |
| T-05 | Tools content must remain usable and scrollable at large system text size, not have controls clipped by a fixed-height layout | "At font scale 1.5, the widget explanation consumes the screen, Refresh is clipped, and the diagnostic status disappears." | indictment.md (2026-09-26) rank 11 | native-ui | now |
| T-06 | Tools/Process/Widgets honestly label what is live vs. planned (e.g. Shizuku off state, Pi actions not yet built) instead of implying capability that doesn't exist | "Process must label live phone Shizuku sampling and planned Pi actions honestly; Widgets must mark xkcd Built and media remote, Quick Settings, app shortcuts Planned." | callouts.jsonl:co-20260928-001724-f9 | native-ui | now |
| T-07 | Widgets rows each carry an aligned, meaningful icon and a working trailing chevron leading to a real detail/action | "rows lack mock trailing chevrons and appear status-only" | callouts.jsonl:co-20260928-013641-7b | native-ui | now |
| T-08 | Process metric cards each carry a leading icon | "Process metrics lack leading icons" | callouts.jsonl:co-20260928-013642-bd | native-ui | now |

## Notes/Pins

| ID | Requirement | Owner quote | Source | Kind | Priority |
|---|---|---|---|---|---|
| N-01 | Basic notes feature: save, edit, view, share | "let's add basic notes we can save / edit / view / share (to devices or to chats, from the note itself)" | owner-msgs-early.md:407 | feature | now |
| N-02 | Notes markdown-render with a plain / rich / preview view toggle, both editable | "markdown render, preview / rich / plain view toggle, editable both" | owner-msgs-early.md:407 | feature | now |
| N-03 | Notes support GFM extras: tables, images, Mermaid diagrams | "allow gfm stuff like tables or images or mermaid diagrams" | owner-msgs-early.md:407 | feature | now |
| N-04 | The Pi agent gets tools for full CRUD on notes, including making or updating notes itself if needed | "allow the raspi agent to have tools to do full crud here, it can even make or update or read notes if needed" | owner-msgs-early.md:407 | pi-service | now |
| N-05 | Notes page has exactly one "new note" action, not two plus buttons | "the notes page has two plus buttons" (fix implied) | owner-msgs-early.md:418 | native-ui | now |
| N-06 | (later) Notes list gets a Pins section: share URLs/text snippets with optional title/tags/description | "I also want the Notes list to have a pin list as well where I can share urls / text snippets and optionally give them a title / tags / description apart from the main url / content" | owner-msgs-early.md:434 | feature | later |
| N-07 | Pins support the same Android-app save-and-share flow as notes, including sharing via the Android share menu | "same support for sharing to android app to save and allow sharing it via android share menu" | owner-msgs-early.md:434 | feature | later |
| N-08 | All images/media/notes/pins shown in the app are shareable via the Android share menu | "Actually let all images / media / notes / pins shown in the app be also shared via the android menu" | owner-msgs-early.md:434 | feature | now |
| N-09 | A file shared from csync back into csync must expose routing options: to screen / notes / pins / chat, exercising the same capability path inline and via Android share; treated as a behavior test of consistency, not a new feature to hand-build per surface | "I can think of a circular consistency where I can even share a file from the app back to the app and in the options I can select routing to screen / notes / pins / chat; the same stuff that works inline is also exposed to android share so this kind of a workflow just works instead of having to be built explicitly, this is more of a behavior test." | owner-msgs-early.md:435 | feature | now |
| N-10 | Disclosure rows on Notes use a real drawn chevron, not a literal "›" text character | "shows text › on saved-note cards" (chevron requirement applies to Notes too) | callouts.jsonl:co-20260927-212103-bf | native-ui | now |

## Settings/Appearance

| ID | Requirement | Owner quote | Source | Kind | Priority |
|---|---|---|---|---|---|
| SE-01 | Theme and text size controls are not wrapped in their own section/card; the flat button-group selector already used is fine as-is | "The theme adn text size do not belong in their own section ad card, the button group selector is fine" | owner-msgs-early.md:400 | native-ui | now |
| SE-02 | Theme options are System / Light / Dark, each with its own icon | "For theme show system / light / dark, each with an icon" | owner-msgs-early.md:401 | native-ui | now |
| SE-03 | Text size options are sm (current normal) / md (large) / lg (larger) | "For text size give sm (current norma) / md (larhe) / lg (larger)" | owner-msgs-early.md:402 | native-ui | now |
| SE-04 | Text-size choice resizes consistently across the whole app, not just one or two elements | "Ensure this is consistent resizing and not just one or two text elements out of all" | owner-msgs-early.md:402 | native-ui | now |
| SE-05 | Primary color control keeps only the color circle/ball, no surrounding card or label | "Primary color is good but only keep the color circle ball not the card or the label." | owner-msgs-early.md:403 | native-ui | now |
| SE-06 | Primary color subtitle is removed | "Remove the subtitle." | owner-msgs-early.md:403 | native-ui | now |
| SE-07 | The Gold color option is removed | "Remove the gold color" | owner-msgs-early.md:403 | native-ui | now |
| SE-08 | Gold is replaced by a custom color picker whose value persists; tapping it opens the editor, while tapping any other swatch selects that color | "make it a custom color picker that persists its value and clicking it opens the edit but clicking on some other color picks that" | owner-msgs-early.md:403 | feature | now |
| SE-09 | The "applies to" section becomes a footnote-level element, not its own prominent block; keep its icons but reduce its space | "The 'applies to' section is useless, can be just a footnote, icons are good but not so much space" | owner-msgs-early.md:404 | native-ui | now |
| SE-10 | Assistant capabilities gets a richer markdown-rendered write-up | "Assistant capabilities and help & about can have a better markdown rich render write-up" | owner-msgs-early.md:405 | native-ui | now |
| SE-11 | Help & about gets the same richer markdown-rendered write-up | same as SE-10 | owner-msgs-early.md:405 | native-ui | now |
| SE-12 | Appearance route offers System theme plus sm/md/lg text size, shipped accents plus additional reviewed accents and Custom, replacing the current Light/Dark-plus-four-accents-only set | "Settings Appearance has Light/Dark and four preset accents only; approved route includes System theme, sm/md/lg text size, review accents and Custom." | callouts.jsonl:co-20260928-001940-bf | native-ui | now |
| SE-13 | Appearance choices persist and apply consistently across Main/Media/Notes activities, including matching system-bar (status/nav bar) appearance | Derived from same callout ("matching system bars") plus the indictment's status-bar-icon finding | callouts.jsonl:co-20260928-001940-bf; indictment.md (2026-09-26) rank 8 | native-ui | now |
| SE-14 | Appearance is applied at a single shared point before every activity inflates, so it never drifts between screens (e.g. Violet on Settings but Coral on Media) | "MainActivity calls applyAppearance(); MediaActivity does not set the saved accent before inflating." | indictment.md (2026-09-26) rank 8 | native-ui | now |
| SE-15 | Dark mode correctly sets light/dark status-bar icon color so system clock/battery icons stay visible against the dark background | "Both captured dark screens retain black system clock, Wi-Fi, signal, and battery icons." | indictment.md (2026-09-26) rank 8 | native-ui | now |
| SE-16 | Accent-colored text meets at least 4.5:1 contrast against its background in both themes, not reusing a fill color at insufficient contrast for small text | Measured Coral/Teal/Violet all under 4.5:1 against page background | indictment.md (2026-09-26) rank 9 | native-ui | now |
| SE-17 | Each accent swatch shows a clear selected-state marker and an accessible name, not color alone | "no new palette direction is required... Add a selected marker and accessible name to each accent swatch" | indictment.md (2026-09-26):95 | native-ui | now |
| SE-18 | The provider/model selector can never let the user save/select a model the connected Pi does not actually support (e.g. saving Claude while Pi reports chatSupported=false must be blocked, not merely discouraged) | "Settings provider UI can save advertised Claude even though Pi chat returns HTTP501, breaking Chat globally." | callouts.jsonl:co-20260928-021830-7b | feature | now |
| SE-19 | A capability shown as "on" is derived from the live, Pi-approved state, never merely from the name of an advertised capability | "Run commands 'on' based only on advertised capability is misleading." | callouts.jsonl:co-20260928-021830-6e | native-ui | now |
| SE-20 | Settings screen keeps Devices & connections and Media & display reachable without appearance/connection detail cards pushing them offscreen | "Settings native opens huge Appearance card and raw connection fields, pushing Devices & connections and Media & display offscreen." | callouts.jsonl:co-20260927-235712-42 | native-ui | now |

## More

| ID | Requirement | Owner quote | Source | Kind | Priority |
|---|---|---|---|---|---|
| MO-01 | Each More child screen (Camera, Tools, Settings, etc.) has a real back affordance and Android system Back returns to More, never exits the app | "More → Settings → Android Back exits to the launcher. There is no parent/back affordance in the Settings header." | indictment.md (2026-09-26) rank 4 | native-ui | now |
| MO-02 | More stays selected in bottom navigation while a child screen from More is open | "Keep More selected in bottom navigation while a child is open." | indictment.md (2026-09-26):65 | native-ui | now |
| MO-03 | More screen removes the giant blank gap under its top bar and gives rows leading icons at proper card height | "More native has giant blank gap under top bar, rows lack leading icons... cards are much taller." | callouts.jsonl:co-20260927-235711-9b | native-ui | now |
| MO-04 | Pi Notes entry sits in the correct hierarchy section per the approved mock, not lumped into Areas | "Pi Notes sits in Areas instead of mock hierarchy" | callouts.jsonl:co-20260927-235711-9b | native-ui | now |

## Pi-side services/agent tools

| ID | Requirement | Owner quote | Source | Kind | Priority |
|---|---|---|---|---|---|
| PI-01 | The Pi-linked agent gets tools to search, play, seek, and change settings of the playing media app | "I also want the raspi agent linked in the app to have tools to search and play and seek around and change settings for the playing app as well." | owner-msgs-early.md:14 | pi-service | now |
| PI-02 | Nothing should be agent-exclusive UI: every capability the agent gets must exist as a proper media player/browse surface in the app, with the agent simply tapping into it | "None of it shoud be agent linked; it should all have proper media player and media browse surfaces within the app, the agent should just be able to tap into them and understand them properly" | owner-msgs-early.md:14 | pi-service | now |
| PI-03 | The agent stays aware of the current play state and can query media files | "also be aware of the current play state or media file querying" | owner-msgs-early.md:14 | pi-service | now |
| PI-04 | Storage drives attached to the Pi become available on SMB, FTP, and the Android app automatically whenever they are connected | "I want the storage drives of raspi of these to just 'be available on smb / ftp / the android app' ... whenever they are connected." | owner-msgs-early.md:19 | pi-service | now |
| PI-05 | The app makes it easier to access the Pi's FTP/SMB, and optionally SSH (owner not bullish on SSH) | "I also want to make it easier using the app to access raspi's ftp / smb; and maybe ssh if possible although not too bullish on that." | owner-msgs-early.md:21 | pi-service | now |
| PI-06 | The Pi agent can load/use/diagnose/suggest fixes for issues in this system, and potentially edit its own code to help fix things | "I want your help... the raspi agent being able to load / use / diagnose / suggest what to do on this. ... Maybe if the raspi agent can edit its own code it can also help me with fixing that." | owner-msgs-early.md:23 | pi-service | now |
| PI-07 | The app installs/updates itself via the Pi's update feature as the finish criterion for the current work | "Latest finish criteria from the owner: the installed app must update through its Pi update feature." | recovered-brief.md:11 | pi-service | now |
| PI-08 | The Pi Notes feature is used to leave a work summary note (what works, screenshots) as part of finishing this round | "leave a note in the app (via the raspi notes feature) with a proper summary of all done, what all works, screenshots, etc)" | owner-msgs.md:16 | pi-service | now |
| PI-09 | A second Pi note lists all features the owner can test out | "another with all the feayures I can test out (that would be cool)" | owner-msgs.md:16 | pi-service | now |

## Deployment/update/Pi notes deliverables

| ID | Requirement | Owner quote | Source | Kind | Priority |
|---|---|---|---|---|---|
| D-01 | Once the build is done, halt further testing and finalize/deploy the APK | "Halt the testing, finalise the apk completion and deploy it" | owner-msgs.md:145 | process | now |
| D-02 | Keep dropping the updated APK onto the Pi at proper checkpoints, not excessively | "Keep dropping the updated apk into the pi on proper checkpoints (not too much), and keep going buddy" | owner-msgs.md:33 | process | now |
| D-03 | The HTML mocks are the source of truth for UI; use the written guide/spec for functionality | "the mocks are the source of truth for the UI, for the functionality use your guide" | owner-msgs.md:33 | process | now |

## Process/quality demands (review gates, testing expectations)

| ID | Requirement | Owner quote | Source | Kind | Priority |
|---|---|---|---|---|---|
| PR-01 | Do not run review agents too frequently; only run them at the end of a major direction, to conserve usage | "Keep going as you were, do not keep running review agents you're eating into my codex usage, only do it at the very end of a major direction instead of so frequently." | owner-msgs-early.md:192 | process | now |
| PR-02 | Keep giving status updates on what is started and what is done | "Keep giving me updates on what task is started and what is done." | owner-msgs-early.md:192 | process | now |
| PR-03 | Never one-shot a design/UI pass; produce a well-thought-out plan and rich variants preview | "Don't just sheepishly one-shot, I WANT A WELL-THOUGHT OUT plan and understand of the UI and a RICH variants preview html page" | owner-msgs-early.md:294 | process | now |
| PR-04 | When presenting options/variants, remember and implement ALL of them where relevant, not just the one selected; never silently drop items never explicitly called out | "MOST IMPORTANT YOU ACTUALLY remembering and understanding the options you present and implementing all in it instead of just what you selected" | owner-msgs-early.md:294 | process | now |
| PR-05 | Reconcile all prior answers into one coherent whole and flag conflicts to the owner, rather than presenting contradictory partial states | "fail to first reconcile all the answers into a coherent self and flagging conflicts to me" | owner-msgs-early.md:294 | process | now |
| PR-06 | Presented "variants" must be genuinely, substantively different, not the same layout with a spacing tweak | "THE VARIANTS ARE THE SAME THINGS" | owner-msgs-early.md:309 | process | now |
| PR-07 | Always show the full absolute file path, never a relative link, and never place a period immediately after a path | "I can't open the doc buddy it si a relative link + followed by a dot" | owner-msgs-early.md:26 | process | now |
| PR-08 | Use an isolated browser/CLI tool (playwright/chrome-devtools MCP) for UI testing instead of the user's main Chrome profile | "Bro just use a playwright mcp server or cli for the testing, you don't need my main cchrome" | owner-msgs-early.md:303 | process | now |
| PR-09 | Kill any spawned browser process properly when done, and encode the lifecycle as a standard reusable skill/guide | "Do ensure you kill the process properly once done + encode it as a standarad skill / guide for codex for proper usage instructions and help and lifecycle sanitization" | owner-msgs-early.md:306 | process | now |
| PR-10 | Write a comprehensive task list grouped by segment, with specific guidance on every common UI pattern (buttons, top bars, breadcrumbs, icons, cards, links, options), each carrying scope-out / implement / code-check / self-review / correctness-check / full-review stages, and check in after each completed page | "Write a proper task list (comprehensive, grouped by segment, specific guidance on ALL common patterns be it buttons top bar breadcrumbs icons cards links options or what not..., and give it a proper scope out / implement / code-check / self-review / correctness criteria check, and finally a full review pass... ensure you check in on it every time a full page is done" | owner-msgs.md:45 | process | now |
| PR-11 | Get a final independent adversarial review for inconsistencies, missing data, and inconsistent spacing before writing the final spec and starting the Android build; incorporate agreed feedback, then write the final spec plus context notes (functional, UI, UX) | "Once all is done, get an agent $adversarial-review for inconsistencies and missing data / shown diffferently in different spaces / inconsistent spacing... take its feedback, incorporate whatever you agree with, then write down a final report with a spec + context notes, functional and UI and UX, and get started with the android app" | owner-msgs-early.md:444 | process | now |
| PR-12 | No screen text may read as AI-generated slop | "ensure no text on any screen reads AI-slop" | owner-msgs.md:62 | process | now |
| PR-13 | Reconcile all owner feedback and prior todo notes at the end, confirming everything is done and working consistently, before declaring finished | "At the end, ensure you reconccile all the feedabck ad your todo notes and all is done and working consistently." | owner-msgs-early.md:437 | process | now |

## Later/parked

| ID | Requirement | Owner quote | Source | Kind | Priority |
|---|---|---|---|---|---|
| L-01 | Plan and build the same casting/streaming capability from the owner's laptop | "Next I'd wanna plan for and also do the same from my laptop" | owner-msgs-early.md:162 | feature | later |
| L-02 | A csync macOS top-bar widget with additional csync-related features | "we can have a csync mac os top bar widget that can also have more csync related features, so let's do and plan it all later" | owner-msgs-early.md:162 | feature | later |
| L-03 | Explore a better/more distinctive launcher icon or favicon (notification icon, widget branding, web favicon) | "Exploring and finding a better favicon" / backlog acceptance | owner-msgs-early.md:198; android-improvement-backlog.md:15 | feature | later |
| L-04 | Full performance audit of the csync app itself (CPU, memory, network, battery, startup, frame time, cleanup) | "Perf audit of this app (does it hog more resources than it needs to)" | owner-msgs-early.md:200 | process | later |
| L-05 | Full performance audit of the phone (why it feels laggy despite available RAM) | "a perf audit of my phone... I need to understand why my phone feels laggy even when so much RAM is available" | owner-msgs-early.md:200 | process | later |
| L-06 | Design system primitives/variants/composites documented and used to standardize the app, to be done once current work is finished | "Maybe you wanna put together a design system primitives, variants, and composites together and use those to standardize? You can do this after the current work is done, just an idea" | owner-msgs-early.md:210 | feature | later |

---

## Round 4 variant picks (`csync UI feedback · round 4`)

Owner-selected layout letter per screen/element (source: owner-msgs-early.md:316-327, verbatim block). This is a decision record, not atomic requirements; preserve every choice exactly.

**Primary color:** Coral (shipped)
**Preview default:** light, normal text, idle scenario

| Screen | Chosen |
|---|---|
| Home | C |
| Search | B |
| Media Files | C |
| Media Videos | C |
| Media History | B |
| Media Access | C |
| Output | C |
| Player | C |
| YouTube share | C |
| Share | C |
| Inbox | C |
| Chat history | B |
| Chat view | B |
| Camera | C |
| Captures | C |
| Tools | C |
| Process | C |
| Widgets | C |
| Settings | C |
| Appearance | B |
| More | B |

| Shared primitive | Chosen |
|---|---|
| Heading | B |
| Navigation | B |
| Row | B |
| Status | B |
| Action | B |
| Tab | C |
| Input | B |
| Transport | B |
| Appearance | B |

| Shared composite | Chosen |
|---|---|
| Navigation shell | B |
| Media library | B |
| Output chooser | B |
| Full player | B |
| Share flow | B |
| Conversation | B |
| Capture | B |
| Diagnostics | B |
| Settings group | B |

| Icon identity | Chosen |
|---|---|
| Home | geometric |
| Media | geometric |
| Share | solid |
| Chat | line |
| More | line |
| Camera | solid |
| Search | line |
| Screen | solid |
| History | line |
| Files | geometric |
| Access | geometric |
| Tools | line |
| Settings | solid |
| Launcher | solid |

**Reconciliation note:** these screens were flagged C but genuinely share the same underlying architecture and must be reconciled as one consistent treatment rather than 12 separate C's: Home, Media Files, Media Videos, Media Access, Output chooser, Full player, YouTube Share, Share Compose, Share Inbox, Pi camera Live, Pi camera Captures, Tools Diagnostics, Tools Process monitor, Tools Widgets, Settings. Shared overrides: Section tab = C.

**Owner notes attached to this round:**
- `screen.home.c`: Like the "Open an area" card where icon+title is one line and subtitle is below; subtitle can also show a dot-separated second status (online/offline/counts); each section (devices, open-an-area, pick-up) should be collapsible by title click with a right-aligned vertically-centered caret. Elaborated further on 2026-09-27, see Conflicts.
- `screen.search.c`: The presented Search variants were not real variants, just the same screen with a card added or a spacing change, flagged as invalid variant work, not a layout pick. See CONFLICT note and S-03.
- **Implementation instruction (owner's own words):** "preserve every named choice and note; reconcile mixed treatments across shared callers before building."

---

## Conflicts (later owner message overrides an earlier one)

1. **Home "Open an area" naming and hierarchy.** Round 4 (2026-09-26, owner-msgs-early.md:325) kept the section named "Open an area" with collapsible sections and a dot-separated subtitle. The 2026-09-27 08:41 message (owner-msgs-early.md:341-343, rows H-04 to H-06) renames it to "Capabilities" and changes what the subtitle shows (colored status dot plus text, more qualifying features listed first). **H-04 through H-06 supersede the round-4 `screen.home.c` note's naming; the collapsible/caret behavior (H-07, H-08) from round 4 is not contradicted and still stands.**
2. **Search variants.** Round 4 assigned Search a "B" layout pick as though it were a normal variant choice. In the same round-4 message the owner immediately flagged Search's presented variants as not real variants at all ("essentially the same screens with one card added or some spacing change"). The later clickthrough round explicitly settled Search as one real scoped-search flow (S-01/S-03), which **supersedes the round-4 letter-pick framing for Search.** Search was never validly A/B/C-differentiated and should be treated as a from-scratch build against S-01/S-02/S-03, not "variant B."
3. **Design-system completeness callout, reopened after a false pass.** `co-20260926-122349-81` was marked pass at 2026-09-26T12:27:29Z, then the owner reopened it as fail at 2026-09-26T12:49:47Z ("Owner found rendered alternatives equivalent despite earlier markup-difference and completeness checks; prior pass was invalid") before it was re-verified and passed again later. **The 12:27 pass is superseded by the 12:49 fail; only the later, re-verified passes (12:55 onward) count as settled.**
4. **Reviewer cadence.** The 2026-09-24 plan message asked for a `$skeptical-review` and `$adversarial-review` at specific plan/build milestones. On 2026-09-25 (owner-msgs-early.md:192) the owner explicitly throttled this: "do not keep running review agents you're eating into my codex usage, only do it at the very end of a major direction instead of so frequently." **The 09-25 throttling instruction supersedes the earlier per-milestone review cadence implied on 09-24; PR-01 is the standing rule.**

No other direct reversals were found. Later messages in this window are almost entirely additive feedback rounds layered on top of the round-4/round-5 baseline, not corrections of an earlier explicit ruling.

---

## Counts per group

| Group | Rows |
|---|---|
| Global shell | 27 |
| Home | 9 |
| Search | 3 |
| Media | 14 |
| Player | 26 |
| Output/cast | 10 |
| Share | 14 |
| Pi screen/cover image | 8 |
| Chat | 40 |
| Camera/Captures | 4 |
| Tools | 8 |
| Notes/Pins | 10 |
| Settings/Appearance | 20 |
| More | 4 |
| Pi-side services/agent tools | 9 |
| Deployment/update/Pi notes | 3 |
| Process/quality | 13 |
| Later/parked | 6 |
| **Total atomic rows** | **228** |

Plus one round-4 variant-pick table (21 screens, 9 primitives, 9 composites, 14 icon identities, reconciliation set, 2 notes) and 4 flagged conflicts.

## Ambiguous asks needing an owner ruling

1. **CH-17** (favorite/archive button placement): the owner explicitly wrote "or maybe title right idk decide," a genuine open placement call the owner left to the implementer's judgment, not a settled spec.
2. **Round-4 vs round-5 Home hierarchy naming.** Conflict #1 above resolves the direct contradiction, but it is not clear whether the round-4 collapsible/caret behavior for "Devices" and "Pick up" sections is still wanted verbatim now that "Open an area" is renamed "Capabilities." The 09-27 message only discusses Capabilities' own content, not whether Devices/Pick-up retain the round-4 collapse behavior. Treated here as compatible (H-07/H-08 kept), but this is an inference, not an explicit re-confirmation.
3. **P-19** ("I hope the multiple drawers won't cause issues. If so, please flag that.") is explicitly conditional; the owner asked to be told if a problem exists, not for a specific fix. Whether the eventual one-drawer-at-a-time design fully answers this, or whether the owner wants to review the flagged tradeoff first, is unresolved.
4. **PI-06** ("Maybe if the raspi agent can edit its own code it can also help me with fixing that") is phrased as a speculative "maybe," not a firm requirement. Worth an explicit yes/no before building agent self-modification tooling, given the risk profile of an agent editing its own running code.
5. **O-07 / O-08** (VLC-as-player and native Google Cast receiver) both depend on a hardware/vendor decision (whether a Cast-enabled HDMI device is acceptable) that the backlog itself marks as still requiring an owner decision: "Decide whether a Cast-enabled HDMI device is acceptable for native YouTube Cast."
