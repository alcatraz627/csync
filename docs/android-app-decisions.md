<!-- sessions: csync-ui-7c@2026-09-29 -->
# csync phone app: conflicts found and how each is settled

Written 2026-09-29. Each row is a place where the owner's recorded asks, the
docs, the old mock and build 2.34 disagree. Each has a ruling. An independent review on 2026-09-29
(`/Users/alcatraz627/Code/Claude/csync/.claude/output/20260929-ui-mock/review-opus.md`)
added rows B14, D7, D8 and section D2. The owner gave
this session authority to decide on 2026-09-29 ("I trust you to take decisions
on your procedure or extra things to do"), so rulings marked **Decided** are
applied in the app model and the mock. Rows marked **Owner** need the owner's
word because they authorise something outside the interface; the mock takes
the safe reading until then.

To overturn a ruling, change its row here and the matching section of
`/Users/alcatraz627/Code/Claude/csync/docs/android-app-model.md` together.

Evidence paths are relative to
`/Users/alcatraz627/Code/Claude/csync/.claude/output/20260929-ui-audit/screens/`
unless they start with a slash. Ledger ids refer to
`/Users/alcatraz627/Code/Claude/csync/.claude/output/20260928-recon/requirements-ledger.md`.

## A. Structure

| # | Conflict | Evidence | Ruling |
|---|---|---|---|
| A1 | Every bar place is drawn as a child of Home. Media, a bar place, shows a Back arrow and "Home / Media". The old mock defines it that way, so the native app copied a wrong model faithfully. | `assets/android-ui-clickthrough/app.js:58`; `40-media-files.png`, `20-chat-all.png`, `30-more.png` | **Decided.** The five bar places are siblings. A bar place shows no arrow and no "Home /". App model section 3 and 4. |
| A2 | Breadcrumbs drop the middle level in some places and keep it in others. Tools reads "Home / Tools", Captures reads "Home / Camera / Captures", the assistant guide reads "Home / More / Capabilities". | `32-tools.png`, `52-camera-captures.png`, `34-assistant-capabilities.png`; `app.js:85` | **Decided.** The path is never shortened by removing a step. When it does not fit, earlier steps keep their icon and lose their words. |
| A3 | The audit backlog offers "drop the breadcrumbs" as an option. The owner asked for a proper breadcrumb six times (G-01 to G-06). | `combined-backlog.md` item 2; ledger G-01 | **Decided.** Breadcrumbs stay and are derived from the map. Dropping them is not an option. |
| A4 | Notes and Pi display are children of Home in the old mock, Notes is reached from More in the app, and Camera and Tools are children of More in both. Home's grid mixes all three kinds. MO-04 says Notes in More's Areas list is wrong "per the approved mock". | `app.js:58`; `30-more.png`; ledger MO-04 | **Decided.** One rule: a place that is not in the bar lives in More. Home's tiles are shortcuts. Notes lives in More. This overrides MO-04, because MO-04 measured against a mock whose hierarchy was the problem. More's sections are named On the Pi, Looking after things and Reference, so nothing is filed under "Areas". **The owner should look at this one.** |
| A5 | Pi display is a page, the full player is another page, and the idle full player shows a grey box with disabled controls. | `app.js:205-219`, `features.js:3-11`; ledger C-07, C-08 | **Decided.** One page per output. Media / Pi screen is the player while something plays and shows the cover and ways to play when idle. |
| A6 | The output chooser is a page between Media and the player, so Back from the player lands on a chooser. | `app.js:58` (`player:'output'`) | **Decided.** Choosing an output is a sheet. Back from the player goes to Media. |
| A7 | Detail opens as a page in Tools, a sheet in some of Settings and a page in the rest of Settings. | `60-tools-power-detail.png`, `54-settings-device-detail.png`, `64-settings-provider.png` | **Decided.** The table in app model section 5 decides by what the detail is. |
| A8 | Media, Notes and Search are separate Android activities, each drawing its own bottom bar. The rest are pages inside one activity with Back handled case by case. | `MainActivity.java:100-103`, `:483-491`, `:577` | **Decided for the mock:** one shell. **For native:** one shared bar and one Back handler that reads the map. Whether that means one activity or a shared base is an implementation choice made when the native work starts. |
| A9 | Share's second mode (received items) hides behind an unlabelled icon. SH-11 asks for exactly that icon placement. | `10-share-compose.png`; ledger SH-11 | **Decided.** SH-11 stands. Received is a child page of Share, reached by the icon, with its own breadcrumb and Back. |

## B. Things that shipped against a recorded ask

| # | Conflict | Evidence | Ruling |
|---|---|---|---|
| B1 | Home 2.34 has a hero card titled "Your hub" with a circular graphic. G-07 asks for that card to be removed everywhere and names "your hub". The owner confirmed on 2026-09-29 that the hero was accepted out of fatigue, not chosen. | `01-home.png`; ledger G-07, H-01, H-02 | **Decided.** No hero card. Home opens with a one-line plain heading that states the hub's state. |
| B2 | Home's section is named "Do something". H-04 asks for "Capabilities". | `01-home.png`; ledger H-04 | **Decided.** "Capabilities". |
| B3 | Home shows one line for one device. H-07 asks for a collapsible Devices section. | `01-home.png`; ledger H-07 | **Decided.** Devices is a section of named devices, collapsible, with Pick up and Capabilities. |
| B4 | "Set up ›" on Home uses a text chevron. G-17 forbids text chevrons. | `01-home.png`; ledger G-17 | **Decided.** Drawn chevrons only. |
| B5 | The thinking selector's fourth option is drawn as three dots. G-12 forbids an ellipsis anywhere. The ledger status marks G-12 as passing because a search for three literal dots in the source found nothing; the dots come from the text being cut at run time. | `64-settings-provider.png`; ledger G-12; `ledger-status.md` row G-12 | **Decided.** A control never cuts its own label. The check for G-12 is a rendered check, not a source search. |
| B6 | Long titles are cut mid-word with no mark ("Blackadde / rs.Christmas.Carol.1080p.BluR"). | `42-media-history.png`, `41-media-videos.png` | **Decided.** Readable title, two lines, fade on the second. Raw filename in the facts sheet. |
| B7 | Section labels are sentence case on some paths and tracked capitals on others, for the same label on the same tab ("Continue" and "CONTINUE"). The mini player prints "THIS PHONE · PLAYING". | `42-media-history.png`, `45-media-resume-sheet.png`, `50-search.png`, `53-settings-top.png`; `MediaMiniPlayer.java:59,77` | **Decided.** Sentence case everywhere, from one text style. |
| B8 | The model drawer commits on tap. CH-11 and CH-13 ask for an explicit Save or Send. | `ledger-status.md` rows CH-11, CH-13 | **Decided.** Save and Send buttons; rows only select. |
| B9 | Resume on a Pi item played on the phone. | `structural-map.md` section 3, last bullet | **Decided.** The output is named in the action's words. App model section 6. |
| B10 | Process monitor shows four tiles whose value is a dash. | `61-tools-process-monitor.png`; ledger T-06 | **Decided.** Unmeasured values are not drawn. The page leads with what is missing and how to start it. |
| B11 | Tools' heading says "Pi services are ready" above "Undervoltage was recorded since boot". | `32-tools.png` | **Decided.** The heading states the worst current state. |
| B12 | The Pi power sheet repeats the row's own subtitle and adds nothing. | `60-tools-power-detail.png` | **Decided.** A facts sheet carries facts the row does not: the reading, since when, what it blocks, what to do. |
| B13 | Widgets, Tools and the old mock list planned features as rows inside the app. | `62-tools-widgets.png`, `32-tools.png` | **Decided.** The app shows what exists. Planning lives in docs. The mock's review panel, outside the phone, says which screens the native app has not built yet. |
| B14 | T-06 asks Widgets to mark what is built and what is planned. Ruling B13 removes planned rows, which would leave the media remote, the tiles and the shortcuts looking available when native has not built them. | ledger T-06; review finding on B13 | **Decided.** The mock is the target, so it shows them. The native app shows a widget or tile row only in the release that builds it, and never with a "planned" label. The mock's review panel says which screens native has not built. |

## C. Rules that were attributed to the owner but are not in the owner's words

| # | Rule as handed over | What the record says | Ruling |
|---|---|---|---|
| C1 | "No ALL-CAPS eyebrows" | Not in the owner's messages to 28 Sep or in the 82 call-outs. It is a finding in `/Users/alcatraz627/Code/Claude/csync/.claude/output/20260929-ui-diagnostic.md`. | **Decided.** Kept as a design rule, on its merits. Recorded as a design decision, not an owner quote. |
| C2 | "No middle-dot status strings" | Same source. The owner's H-09 asks for a dot-separated second status. | **Decided.** A line may join two short facts with a middle dot. Status uses the dot-and-words form. Three or more facts on one line is not allowed. |
| C3 | "The coral accent marks one primary action and live state only" | Same source. The fresh review found coral on every icon tile in 2.34. | **Decided.** Kept: accent for the primary action and the selected item. Live state is green, not accent. |

## D. Names

| # | Conflict | Evidence | Ruling |
|---|---|---|---|
| D1 | Home and Settings talk about "Mac" while the roster holds seven named devices, and Home says the Mac is offline while a Mac in the roster is online. | `01-home.png`, `11-share-inbox.png`, `33-settings.png` | **Decided.** Devices are shown by their own names. No fixed "Mac". |
| D2 | Connection settings say "Home peer", "Assistant peer", "Mesh token". | `63-settings-tailscale.png` | **Decided.** "Raspberry Pi address", "Second address (optional)", "Access token", each with one line saying what it is for. |
| D3 | Every device has a phone icon. | `11-share-inbox.png`, `50-search.png` | **Decided.** The icon follows the device kind the roster already reports (laptop, phone, desktop, Pi). |
| D4 | The same assistant tools have two names ("Pi health" and "Home health", "Your devices" and "List peers"). | `23-chat-tools.png`, `34-assistant-capabilities.png` | **Decided.** The plain names from Chat's Tools view are used everywhere. |
| D5 | Captures are titled "Photo · 7:22 AM" with the subtitle "Photo · 20 kB", and carry no date. | `52-camera-captures.png` | **Decided.** Title is the kind and the day, subtitle is the time and size, grouped by day. |
| D6 | Notes show "Markdown · revision 19". | `35-notes.png` | **Decided.** "Edited today" style dates. The revision is in the note's facts sheet. |
| D7 | "Tools" names two things: Chat's list of what the assistant can use (CH-19, the owner's word) and the page in More (T-asks and "More, Tools, Update csync from Pi", also the owner's words). | `23-chat-tools.png`, `32-tools.png` | **Decided.** Both keep the owner's word. They have different icons, and the assistant guide opens the list as a sheet instead of jumping to Chat. |
| D8 | One action had several names: Download and Save, Save as a note and Add to a note. | review finding 1 | **Decided.** One name each, listed in app model section 7a. |

## D2. Product choices that were in the app without a record

| # | Choice | Evidence | Ruling |
|---|---|---|---|
| P1 | Playback on the Pi screen starts muted. | The old design system and the old mock both state it; P-01 reports a film "blasting full volume". | **Decided.** Kept as the default, and made a setting: Settings, Playback, Starting volume. |
| P2 | The Pi online dot sits in Chat's page heading, not on each conversation row. | ledger CH-22; round 5 plan, Conversations row | **Decided.** Heading. The Pi's state is one fact about the assistant, not a fact about each conversation. This follows round 5's reading of CH-22. |
| P3 | Loop had three states with no queue to loop over. | ledger P-07 "click to toggle" | **Decided.** Loop is On or Off. |
| P4 | Sending the phone's own camera to the Pi screen (O-09). | ledger O-09 "look into that" | **Owner.** Not shown. It needs a feasibility test on the hardware first. The Pi camera to the Pi screen is shown. |

## E. The five rulings the ledger left open

| # | Question | Ruling |
|---|---|---|
| E1 | CH-17: where Favorite and Archive sit in a conversation | **Decided.** On the title row, right side, icon-only, after the edit icon. The owner wrote "idk decide". |
| E2 | Whether Devices and Pick up still collapse on Home | **Decided.** Yes, all three sections collapse (H-07 was never withdrawn). |
| E3 | P-19: whether one sheet at a time is acceptable | **Decided.** Yes. It is a guarantee of the design, not a limitation: a second sheet replaces the first. |
| E4 | PI-06: whether the Pi assistant may edit its own code | **Owner.** Not an interface question. The mock shows no such control. Default until ruled: no. |
| E5 | O-07, O-08: whether a Cast-capable HDMI device is acceptable | **Owner.** A hardware purchase. The mock offers Pi screen, This phone and Open in VLC, and no Cast row. |

## E2. The owner's rulings of 2026-09-30, after reviewing the mock

Answered on the decision page `csync-final-look`. The owner's answer string
was `D1b D2b D3a D4a D5a`, with one note on D5.

| # | Question | Ruling |
|---|---|---|
| R1 | Which tab style | **Owner.** The underline. One style everywhere; the other three variants are removed from the mock. |
| R2 | Settings: four pages or one | **Owner.** One Settings page. Playback, Assistant and Appearance are folding groups on it. Connection keeps its own page because it is the long one with Save. |
| R3 | Where else depth comes out | **Owner.** Covers is a sheet on the Pi screen page. Design system sits beside Help under More. File browsing shows a tappable path line in place of the Up row. Tools and Notes keep their children. |
| R4 | Which screens keep a filled button | **Owner.** As in the mock: filled only for Send, Save, Install and Create. `runChecks()` enforces it. |
| R5 | Showing this phone's screen or one app on the Pi screen | **Owner.** Build it, then test and fix once the Pi has proper power. In the owner's words: "pi needs to be fixed; we can build all and then test and fix it". Its delay is still unmeasured, so it ships marked as untested until then. |
| R6 | More than one display | **Owner.** "this pi display is just one, I also have a projector I want it tuned for, or later some other screen or monitor; ensure the architecture and discovery can handle this kind of variance". The Pi reports the display that is plugged in by name. Size, turn, sound path, starting volume and cover framing are kept per display, keyed by what the display reports about itself, never by a fixed mode. The app reads the display from the Pi and never assumes one. Building and testing the second display comes later. |

## F. Records that cannot be trusted as they stand

| # | Record | Problem | What to do |
|---|---|---|---|
| F1 | `ledger-status.md` | Generated before 2.33 and 2.34. G-07, H-04 and H-07 read PASS and no longer are. | Regenerate after the native rebuild, from rendered checks. |
| F2 | `callouts.jsonl` status field | Reads open on all 82 rows. | Use the last recheck. Twelve failing rechecks predate the Kit and are unknown, not failing. |
| F3 | The audit screenshots | `11-share-inbox.png` is the recipient sheet, `43-media-access.png` is the phone's launcher. Received and Access were never captured. History, the source sheet and the resume sheet were captured after the UI report was written and were never reviewed. | Recapture when the emulator is running. |
| F4 | "The God Activity was fixed by the Kit" | `MainActivity.java` is 2,758 lines. Search has 2 Kit calls, Notes 20. | The native rebuild moves every screen onto the shared layer and measures it. |
