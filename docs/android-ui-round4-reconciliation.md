# Android UI round 4 decision map

This maps the owner's round 4 feedback to one clickable proposal. The prior [variant page](../assets/android-ui-variants/index.html) remains unchanged. The new [clickthrough](../assets/android-ui-clickthrough/index.html) demonstrates the combined choices; it does not claim Android behavior has shipped.

## Composition rules

| Layer | Owner choice | Clickthrough rule |
|---|---|---|
| Screen hierarchy | Per-screen B or C below | C leads with the current task, target, or result; B uses a grouped list. The large empty C hero from the old page is compressed so first actions remain visible. |
| Shared primitives | Heading, navigation, row, status, action, input, transport, appearance B; Section tab C | The same row, action, state, and icon treatment appears at each caller. Section tabs use the C segmented treatment, including inside B screen layouts. |
| Shared composites | All nine B | Navigation shell, media library, output chooser, player, share flow, conversation, capture, diagnostics, and settings groups retain their multi-part B behavior. Screen C determines their placement and emphasis. |
| Icon identity | Per-concept choices below | Each concept uses one selected identity across navigation, cards, rows, and actions. The mock vectors are concept previews; they do not claim to be Android Material assets. |
| Color and initial state | Coral, light, normal text, idle | The clickthrough opens with these values. Appearance offers light/dark, normal/large text, and eight accent samples. Scenario controls expose other states. Coral is reserved for selection and the primary action; status retains its own meaning. |

## Screen routes

| Area | Screen | Pick | Essential paths and state in the clickthrough |
|---|---|---|---|
| Home | `home` | C | Named device state, Open an area, Pick up, search; sections collapse by title and aligned caret. |
| Search | `search` | B | One grouped search with query, domain filters, mixed results, and result routing. |
| Media | `media-files` | C | Source, scoped search, folders/files, output choice, History. |
| Media | `media-videos` | C | Indexed videos and output choice. |
| Media | `media-history` | B | Resume position and unavailable-source explanation. |
| Media | `media-access` | C | SMB/FTP access, copy actions, connection help. |
| Playback | `output` | C | Target availability and replacement effect before starting. |
| Playback | `player` | C | Output identity, position, seek, volume, Pause/Resume, Stop, Rotate/Loop. |
| Playback | `youtube-share` | C | Shared title, Pi/phone route, blocked-content state, native Cast distinction. |
| Share | `share` | C | Named recipient, text, clipboard, file, upload state, Inbox. |
| Share | `inbox` | C | Received items, transfer history, open/share actions. |
| Chat | `chat-history` | B | Search, All/Favorites/Archived, new conversation. |
| Chat | `chat-view` | B | Conversation, media result, composer, matching player controls. |
| Camera | `camera` | C | Live preview, Photo, Record/Stop, Captures, close-on-exit explanation. |
| Camera | `captures` | C | Photo/video detail and output/share actions. |
| Tools | `tools` | C | Service health, Pi power, performance, process and widget routes. |
| Tools | `process` | C | Memory, CPU, thermal, pressure, process detail and gated action. |
| Tools | `widgets` | C | Built xkcd widget, proposed media remote and quick actions. |
| Settings | `settings` | C | Connections, media/display, assistant, app and appearance. |
| Settings | `appearance` | B | Light/dark and Coral, with the other shipped colors visible as choices. |
| More | `more` | B | Camera, Tools, Settings children with return to More. |

## Shared choices

| Category | Choice |
|---|---|
| Primitives | `heading=B navigation=B row=B status=B action=B tab=C input=B transport=B appearance=B` |
| Composites | `navigation-shell=B media-library=B output-chooser=B full-player=B share-flow=B conversation=B capture=B diagnostics=B settings-group=B` |
| Geometric icons | Home, Media, Files, Access |
| Solid icons | Share, Camera, Screen, Settings, Launcher |
| Line icons | Chat, More, Search, History, Tools |

## Reconciled notes and open boundaries

| Feedback | Resolution |
|---|---|
| `home=C` and the requested “Open an area” card from the earlier treatment | Keep C's task-first Home order. Use a compact icon and title on one line, then a subtitle with a dot-separated status or count. Devices, Open an area, and Pick up each toggle from the section title; the caret aligns with that title. This is a local card detail, not a switch to Home B. |
| `tab=C` while all composites are B | The segmented C tab is a shared primitive used inside each B composite. The composite still carries its selected constituent actions and states. |
| `search=B` with a note that Search A/B/C were cosmetic | Use B for the clickthrough's Search hierarchy. Do not copy the old Search variants or ask the owner to choose between them again. Keep the rejection attached to future search explorations. |
| Light idle preview versus appearance choices | Light/Coral/idle is the starting fixture. The in-page appearance control changes the mock preview only. It does not persist to the Android app. |
| Screen C versus B navigation and component picks | Screen choice controls page hierarchy; shared choices control the component grammar. A C screen does not silently replace a B navigation item, row, action, or composite. |

The clickthrough uses fixtures for devices, media, and conversations. Planned features are visibly marked. Actual playback reliability, Pi frame rate, native Cast, rotation/loop, process actions, widgets, performance, and the installed app's narrow/large-text defects remain open in the [backlog](android-improvement-backlog.md) and [adversarial review](../.claude/output/20260926-0324-adversarial-review/indictment.md). A clickable mock cannot close those runtime checks.

## Carry-forward checks for Android implementation

These are the outstanding behaviors from the two linked documents. A mock interaction demonstrates a proposed treatment where named; every Android acceptance check remains open.

| Source | Requirement carried into the plan | Clickthrough evidence or limit |
|---|---|---|
| Indictment 1–3 | Preserve the chosen output from mini player to full controls. Show actual loading, playing, paused, completed, pending, and failed states; prevent duplicate commands. | Output-named mini rows open the matching player; Pause has a pending step and failure copy. Android must bind session identity and observed state to real commands. |
| Indictment 4–5 | More children return to More; source, Media section, and content stay consistent. | More → Settings → Appearance has visible Back. Media's source control changes source without switching the selected tab. Android Back and real source changes still need device checks. |
| Indictment 6–7 | Mini player opens a dedicated full player; Home shows named reachability and actual continuation. | Full player has position, seek, transport, target, volume, Stop; Home has named devices, collapsible areas, and Pick up. Real recent content must replace fixtures. |
| Indictment 8–9 | Theme and accent span every activity and system bar. Accent text must have measured contrast. | One theme/accent state drives all mock routes; light accent samples use at least 4.5:1 against white. Android resources and system bars remain unverified. |
| Indictment 10–12 | Use one component grammar throughout; preserve large-text access; name output availability, muted start, and replacement effect. | Shared B components and C tabs render across all routes. Large text and narrow preview are selectable. Output chooser spells out those effects. Installed app font scaling and actual target availability remain open. |
| Backlog: casting/streaming and Pi frame rate | Measure startup, buffering, visible video/audio, command response, dropped frames, load, voltage, and output mode across routes. | Mock names output and command status; no media service is exercised. These are runtime and hardware checks. |
| Backlog: rotation, looping, YouTube share, native Cast | Expose Rotate/Loop modes; show YouTube title, output, blocked state; distinguish Share → csync from native Cast discovery. | Controls and dedicated YouTube route are clickable; Cast is visibly planned. Persistence, native YouTube tap, playback, and Cast hardware remain open. |
| Backlog: whole-app UI, design system, widgets, launcher | Carry every screen/component/icon choice into the installed app; test themes, text scale, mini states, widget lifecycle, and launcher assets. | This page is the route/component/icon contract and includes proposed widgets. Launcher icon audit and phone installation are separate work. |
| Backlog: process manager and performance | Show accurate process and pressure data, confirm process actions, stop polling on exit; trace app and phone lag before tuning. | Tools/Process show the intended hierarchy and gated action. Metrics are fixtures; no polling, process action, or performance measurement occurs. |
