# Android UI clickthrough mock audit

Scope: `/Users/alcatraz627/Code/Claude/csync/assets/android-ui-clickthrough/` (index.html, app.js, features.js, styles.css, icons.js, choices.js). Read-only; no mock file was edited. Method: read every source file in full, then captured all 28 routes with a headless Playwright Chromium at 412x915 (phone viewport), light and dark, plus large text on the eight densest routes, plus about a dozen interactive states (drawers, expanded player, notification shade, playing player). Screenshots and the capture script live in `/Users/alcatraz627/Code/Claude/csync/.claude/output/20260928-recon/mock-shots/` (77 PNGs + `capture.mjs`). Every finding below was either read directly in the source or confirmed by looking at a screenshot; screenshot paths are given for each visual claim.

## Route inventory

All 28 routes render at both text themes with no console errors during capture (`errors: []` in the capture run). Source: `choices.js:27-56` (the `screens` array), each id captured as `<id>__light.png` / `<id>__dark.png` in mock-shots.

| Route id | Label | Layout pick | Screenshot (light) |
| --- | --- | --- | --- |
| home | Home | C | home__light.png |
| search | Search | B | search__light.png |
| media-files | Files | C | media-files__light.png |
| media-videos | Videos | C | media-videos__light.png |
| media-history | History | B | media-history__light.png |
| media-access | Access | C | media-access__light.png |
| output | Output chooser | C | output__light.png |
| player | Full player | C | player__light.png (idle), player-playing-full__light.png (playing) |
| youtube-share | YouTube Share | C | youtube-share__light.png |
| share | Compose | C | share__light.png |
| inbox | Inbox | C | inbox__light.png |
| chat-history | Conversations | B | chat-history__light.png |
| chat-view | Conversation | B | chat-view__light.png |
| camera | Live camera | C | camera__light.png |
| captures | Captures | C | captures__light.png |
| tools | Diagnostics | C | tools__light.png |
| process | Process monitor | C | process__light.png |
| widgets | Widgets & actions | C | widgets__light.png |
| settings | Settings | C | settings__light.png |
| appearance | Appearance | B | appearance__light.png |
| more | More | B | more__light.png |
| display | Pi display | C | display__light.png |
| cover-gallery | Cover gallery | C | cover-gallery__light.png |
| share-entry | Incoming share | C | share-entry__light.png |
| notes | Notes | B | notes__light.png |
| note-detail | Note editor | B | note-detail__light.png, note-detail-rich.png |
| assistant-guide | Assistant capabilities | B | assistant-guide__light.png |
| help | Help & about | B | help__light.png |

## Owner-feedback compliance

Each row cites the 2026-09-27/28 feedback item, the route(s) it applies to, and file:line evidence in the current source, not just the screenshot.

| Ask | Verdict | Route(s) | Evidence |
| --- | --- | --- | --- |
| Breadcrumb is a proper breadcrumb; back always goes one level up, never used for folder/file traversal or stopping playback | PASS | all | `back()` only calls `go(parent(state.screen))` (app.js:608); folder "Up" uses a separate `folder` action (app.js:163), stop uses a separate `stop` action (app.js:227, 683). Confirmed in media-files__light.png the folder "Up" row is distinct from the header back arrow. |
| Breadcrumb icon shown consistently for every crumb | PASS | all | `pageTop()` renders `icon(crumbSymbols[part],13)` for every segment, current and link alike (app.js:86-87); visible in every screenshot's header row. |
| Top breadcrumb bar does not scroll and does not change height | PASS | all | `.page-top{height:43px;min-height:43px;max-height:43px;overflow:hidden}` plus `position:sticky` (styles.css:26,28). |
| Home: simplify "Raspberry Pi is ready" card, remove subtitle, smaller title | PARTIAL | home | Subtitle is gone (`heading(pi?'Raspberry Pi is ready':...)` passes no subtitle, app.js:127). Title still renders at the full 27px `.page-heading h2` size (home__light.png) — no smaller treatment was actually applied despite the ask. |
| Home: "Open an area" → "Capabilities", with status dot + text as second line | PASS | home | Section title is `'Capabilities'` (app.js:129); `areaCard()` renders `<span class="dot ...">` + status text as the subtitle line (app.js:104). Visible in home__light.png / home__dark.png. |
| Media > Access: remove top card, switch-source as icon right of search, in-drawer close buttons removed | PASS | media-access | `mediaAccessScreen()` has no hero/card, just a heading (app.js:182-184); page-top right side has search-toggle then source-sheet icon buttons only (app.js:183). Source drawer has no close button (sheetMarkup `source` branch sets `actions=''`, app.js:434-439). Confirmed in media-access__light.png and media-source-drawer.png. |
| Player: single-row transport (favorite, rewind, pause, forward+skip dropdown, stop) | PARTIAL | player | The 6 controls (`favorite, skip-back, pause, skip-forward, stop, skip-sheet`) do render in one `.transport-row` grid (app.js:222-229, styles.css:21). But the skip-duration control is the **last** button, after Stop, not attached to Forward as the feedback phrased it ("Forward, allow the duration ... here as well"). Functionally present, ordering doesn't match the ask. See player-playing-full__light.png. |
| Player: 2x2 settings grid (volume/speed/rotate/loop), volume+speed slider drawers, rotate+loop toggle with 2s debounce | PARTIAL | player | 2x2 grid confirmed (`setting-grid{grid-template-columns:repeat(2,...)}`, styles.css:21; player-playing-full__light.png). Volume/speed open slider drawers (player-volume-drawer.png). But rotate/loop tiles open a **list-picker drawer** (player-rotate-drawer.png), not "click to toggle" on the tile — the debounce (`delayed-setting`, app.js:687-699) is real and correct, but there are also two dead, unused `case 'rotate'` / `case 'loop'` handlers (app.js:705-706) that implement instant, un-debounced toggling and are never wired to any element — leftover from an earlier design, confusing for a future implementer. |
| Player row (mini): expand to ~half height on tap, drawer handle, drag up to full player / down to collapse; volume+speed buttons right of Stop | PASS | player | `player-panel` at `height:48%` with a `.panel-handle` drag target (styles.css:21, app.js:409-412); pointerup handlers open full player on drag-up, collapse on drag-down (app.js:887-888). Mini row shows Pause/Stop/Volume/Speed icon buttons (app.js:407). Confirmed in mini-row.png and player-panel-expanded.png. |
| Playing media shows as Android notification-style player | PASS | player (shade) | `notificationMarkup()` renders a system-styled panel with title/output/Pause/Stop when a player is active (app.js:421-424). Confirmed in notification-shade-active.png. |
| Compose: full sent history, allow files, allow clipboard | PASS | share | `sentHistory` list rendered (app.js:261), file picker via `file-sheet` (app.js:716), clipboard via `clipboard-sheet` (app.js:713). Confirmed in share__light.png. |
| Share intake: type-driven actions for video/image/YouTube/Instagram/file, adjustable playback defaults | PASS | share-entry | `incomingActions` table keyed by kind (features.js:22) matches the spec's per-type action list; loop/speed/volume inline controls for youtube/instagram (features.js:30). Confirmed in share-entry__light.png. |
| Raspi cover image: thumbnail gallery, gradient border on selected, fit/rotate/crop per image | PASS | cover-gallery | 3-thumbnail grid, `.cover-thumb.selected` gets a gradient border (styles.css:22); Fit/Rotation/Crop rows with per-image state in `state.coverSettings` (app.js:28, 801-807). Confirmed in cover-gallery__light.png with the rainbow border on "Sunset desk". |
| Chat: tap message → copy button, terse timestamp, (later) fork preview via drawer | PASS | chat-view | Tapping a bubble reveals icon-only Copy/Fork (app.js:298); timestamps already terse ("Yesterday · 18:40"); fork opens a drawer with transcript-through-that-message + model settings + "Create fork · planned" (app.js:492-503). Confirmed in chat-view-selected.png and chat-fork-drawer.png. |
| Chat composer floats above player/drawer rows; left icon opens attach drawer with Send image / Upload file / Model+effort, explicit Save/Send | PASS | chat-view | `chatComposerMarkup()` is rendered outside `.phone-scroll`, always above `miniMarkup()`/`bottomMarkup()` (app.js:588); attach sheet has the three rows (app.js:480-484); model sheet requires `chat-model-save` or `chat-model-send`, no click-to-save (app.js:750,756). Confirmed in chat-attach-drawer.png, chat-model-drawer.png. |
| Chat title + subtitle with model details, edit icon, favorite/archive in subtitle, token stats only if available | PASS | chat-view | Inline `chat-title-input` in place (no drawer) (app.js:287, 757); subtitle carries model id, effort, favorite/archive icon buttons; `tokens` string only renders `Number.isFinite(state.chatTokens)` (app.js:288-289, default `chatTokens:null` — never fabricated). Confirmed in chat-view__light.png. |
| Conversations gets a "Tools" tab, sibling of All/Favorite/Archived, not a separate page | PASS | chat-history | `tabs(['All','Favorites','Archived','Tools'],...)` (app.js:278); Tools content renders inline in the same `chat-history` route via `chatToolsContent()` (app.js:279). Confirmed in chat-tools.png — same breadcrumb ("Home / Chats"), same route. |
| Settings button right of "New chat", icon + plain label, opens chat settings drawer | PASS | chat-history | `button('New chat',...)+button('Settings','chat-settings','settings','quiet')` (app.js:282). Confirmed in chat-history__light.png. |
| Camera: remove top "live capture" card | PASS | camera | `cameraScreen()` has no hero/card, just heading + preview + action row (app.js:300-310). Confirmed in camera__light.png. |
| Appearance: theme selector with icons (system/light/dark), text size sm/md/lg consistent resize, color = circle only (no card/label/subtitle), gold removed + custom picker, "applies to" reduced to a footnote | PASS | appearance | Theme/size tabs both carry icons via `tabSymbols` (app.js:90-96); palette is 7 named colors + a persistent custom swatch, no gold (app.js:364-366); color section is bare circles, no card/subtitle (app.js:373); "applies to" text is now a one-line `small-note` (app.js:374). Text scaling is global via `--text-scale` zoom + `.phone.large` rules (styles.css:17, 22), not a couple of one-off elements. Confirmed in appearance__light.png. |
| No "..." anywhere, not on text or inputs | PASS | all | `rg '\.\.\.' app.js features.js styles.css choices.js` returns only JS spread operators, zero literal ellipsis in rendered strings. CSS truncation is `text-overflow:ellipsis` in several base rules (styles.css:10,21,27) but every one of those selectors is re-overridden to `text-overflow:clip` later in the same file (styles.css:29,32,34) — net effect is no "…" glyph is ever rendered, confirmed visually (chat-view__light.png, media-access__light.png titles are hard-clipped, not ellipsized). |
| Notes: pattern reused sensibly, notes page should not have two plus buttons | PASS | notes | `pageTop('notes')` passes no right-side action (features.js:35); only one "New note" button at the bottom (features.js:38). Confirmed in notes__light.png — a single plus button. |
| Remove close button(s) from bottom drawers/sheets; slide-down or tap-outside closes | PARTIAL | sheets vs. notification shade | Every `sheet-backdrop`/`sheet` (media source, media options, model, fork, etc.) has zero close buttons — confirmed by grep (`app.js` sheetMarkup, no `close-sheet` button in the body) and in media-source-drawer.png / chat-model-drawer.png. But the **notification shade** (a different surface, same "drawer-like panel" family) still has an explicit `✕` `iconButton('notification-shade','close',...)` at app.js:423, visible in notification-shade-active.png. That may be intentional (it mimics real Android system UI, which is swipe-dismissed, not X-dismissed either) — worth a one-line ruling on whether the shade is exempt from the "no close buttons" rule or should lose the X too. |
| Send to Mac: move Inbox + recipient buttons into the breadcrumb-row toolbar, icon only | PASS | share | `pageTop('share','Share', <recipient-sheet icon><inbox icon>)` (app.js:255). Confirmed in share__light.png — both actions are icon-only, top right, no duplicate elsewhere on the page. |
| Share to chat needs a real chat picker | PASS | media options → share | `chat-recipient` sheet lists open threads + "New chat" (app.js:456-459). Confirmed in chat-recipient-drawer.png. |
| Folder actions: allow downloading a folder to phone; file actions inclusive (download/send-to-chat/share, plus show-on-screen for playable media) | PASS | media-files (options drawer) | `media-options` sheet body composes actions by kind: folder gets Open/Download/Share; video/image additionally gets "Show on Pi screen" before the shared Download/Send to chat/Share set (app.js:451-455). Confirmed in media-options-drawer.png (a video file shows all 4 actions). |
| Large text keeps controls reachable, no clipped/overlapping tab strips | FAIL (regression, see Consistency C1) | chat-history at lg | See below — Conversations' filter tabs overlap and become illegible at large text, worse than the prior audit's F1 finding. |

## Consistency findings (ranked by how many routes they touch)

**C1 — P1: Conversations' filter tabs overlap illegibly at large text, while the identical tab component elsewhere scrolls cleanly.**
Every other tab strip (Media's Files/Videos/History/Access, Search's All/Media/Chats/Files/Devices, Share's Compose/Inbox) uses the generic rule `.tabs{overflow-x:auto}` + `.tab{flex:1 0 auto}` (styles.css:43-44), and at large text they simply scroll to keep the active tab visible and legible — confirmed working in media-access__light-lg.png and media-files__light-lg.png. Conversations gets its own override: `.phone[data-screen="chat-history"] .phone-page>.tabs{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));overflow:hidden}` (styles.css:45-47). At large text this grid can't shrink further and `overflow:hidden` removes the scroll escape hatch the rest of the app relies on, so "All / Favorites / Archived / Tools" render on top of each other with visibly overlapping glyphs — see `chat-history__light-lg.png`. This is a real, reproducible defect, not a fixture limitation, and it is the single clearest bug in the mock.
*Fix:* delete the chat-history-specific grid override (styles.css:45-47) and let it use the same scrollable `.tabs` rule as every other tab strip; the `@media(max-width:390px)` icon-hiding rule at styles.css:47 can stay or go with it.

**C2 — P2: The mini player bar stays visible underneath the Full Player screen itself, duplicating its own controls.**
`miniMarkup()` renders for every active player regardless of the current route (app.js:407, called unconditionally in `render()` at app.js:588). When you're already on `#player`, the bottom of the screen still shows a second "PI SCREEN · PLAYING / Sample film.mp4" row with its own Pause/Stop/Volume/Speed buttons directly below the full transport row that does the same job — see `player-playing-full__light.png`. This reads as a bug, not a deliberate persistent-mini-player pattern, because every other screen that has an active player (Home, Media, Chat) shows exactly one mini row, and Player is the one place two copies of the same controls stack.
*Fix:* skip rendering `miniMarkup()` for the output whose player is the one currently open in the full `player` screen (or suppress it entirely on `state.screen==='player'`).

**C3 — P2: One icon (`home`) is reused for two unrelated meanings — the Home destination and "This phone" as a playback target.**
`outputScreen()` renders the "This phone" destination row with `row('This phone', ..., 'home', ...)` (app.js:198) — the same house glyph used for Home in the bottom nav, breadcrumbs, and area cards. In `output__light.png` this reads as if choosing "This phone" is somehow the Home destination. A phone/device icon (the same one used for "Mac" and "Raspberry Pi" device rows) would disambiguate.
*Fix:* pick a distinct "this phone" icon, e.g. the existing `device` shape already used for the Settings Devices row.

**C4 — P3: Conversation subtitle inverts the "effort lighter than model id" ask.**
`.chat-meta{color:var(--phone-dim)}` makes the model id dim by inheritance, but `.model-effort{color:var(--phone-text)}` (styles.css:30) makes the effort text *darker/more prominent* than the model id, the opposite of the owner's "make the effort color slightly lighter to the model id." Visually the two are close enough to look identical in `chat-view__light.png`, so this reads as unfinished rather than deliberate.
*Fix:* give `.model-effort` a dimmer tone than `.model-id` (or just drop the rule and let both inherit `.chat-meta`'s dim color, then explicitly darken `.model-id`).

**C5 — P3: The "fork" icon is easy to misread as a phone/call icon.**
The fork glyph (icons.js: `fork: '<path d="M7 3v10a5 5 0 0 0 5 5h5M17 18l-3-3M17 18l-3 3M7 3l-3 3M7 3l3 3"/>'`) is a git-style branch shape, but at 15-18px next to "Create fork" it reads ambiguously close to a phone-handset/call-forward icon (see `chat-fork-drawer.png`, and the icon-only button next to a selected bubble in `chat-view-selected.png`). There's no calling feature anywhere else in the app, so a reader has no other icon to disambiguate against.
*Fix:* swap for a clearer branch/split icon, or pair it with the row label everywhere it appears (it already has a label on the drawer's primary button; the bubble's icon-only affordance is the ambiguous one).

**C6 — P3: The notification shade keeps an explicit close (X) button while every other drawer had its removed.**
See compliance table row above — `app.js:423`. Worth a one-line decision on whether the shade should be brought in line with the "no close buttons" rule (swipe/tap-outside only) or is deliberately exempt as simulated system UI.

## Copy findings

- "1 saved notes" on Home's Notes card (app.js:121: `${state.userNotes.length||2} saved notes`) — the fallback default of 2 makes the fixture read as "1 saved notes" once a real note count of 1 occurs; needs singular/plural handling. Visible in `home__light.png`.
- "Fork conversation · later" and "Create fork · planned" bake development-status words into user-facing copy (app.js:493, 503). Consistent with how the rest of the mock marks unbuilt routes ("Planned" badges elsewhere), so likely intentional, but it is the one spot where the status word sits inside a sentence/button label rather than as a separate badge — flagging in case that inconsistency wasn't deliberate.
- No other AI-slop, filler, or truncated copy found in the screens reviewed; body text throughout (Home, Media, Player, Chat, Appearance, Notes) reads as plain, specific sentences.

## Structure verdict

There is a real shared component layer, not per-route one-off markup: `row()`, `button()`, `iconButton()`, `tabs()`, `section()`, `surface()`, `heading()`, `pageTop()`, and `playerControls()` (app.js:60-238) are used by every one of the 28 screen functions, and the CSS in `styles.css` is organized around those same primitives (`.row`, `.tab`, `.surface`, `.button`, `.section`) rather than per-screen classes. This is a legitimate design-system layer, and it is why the compliance table above is mostly PASS — a fix to `row()` or `.tabs` propagates everywhere, which is exactly what happened for the breadcrumb, close-button, and icon-consistency asks.

The debt is in **leftover code from prior iterations that was never deleted once the owner's fix landed**, which is consistent with the owner's "Codex spent too long on this yet it still needs improvement" framing — the effort went into iterating in place rather than cleaning up after each iteration:

- `hero()` (app.js:76-78) no longer emits the `.hero` wrapper div at all — it was reduced to `heading()+actions` in response to the "get rid of the card with the circle bg" feedback — but its signature still takes `kicker` and `symbol` params that are silently discarded, and every one of its ~9 call sites (`mediaHead`, `outputScreen`, `youtubeShareScreen`, `capturesScreen`, `toolsScreen`, `processScreen`, `widgetsScreen`, `settingsScreen`) still passes those dead arguments plus a `compact` flag that also does nothing. Meanwhile `styles.css:6` still carries the full `.hero{border-radius:20px;padding:16px;background:linear-gradient(...)}` block plus `.hero:before`, `.hero-eyebrow`, `.hero-actions`, `.hero.compact` — roughly 700 bytes of CSS with zero live callers (verified: `rg 'class="hero'` across app.js/features.js returns nothing).
- Two dead action handlers, `case 'rotate'` and `case 'loop'` (app.js:705-706), implement instant un-debounced toggling and are not wired to any element in the current UI (the settings tiles all route through `setting-sheet` → the debounced `delayed-setting` picker instead). A future implementer grepping for how rotate/loop work will find two contradictory mechanisms.
- The stylesheet accumulates fixes as append-only patch blocks rather than editing the original rule: `/* Round 5 clickthrough controls */` (styles.css:19-25) and `/* Round 5 owner corrections */` (styles.css:26-33) both redeclare properties (`text-overflow`, `.page-top` height/position, `.tabs`) that an earlier rule in the same file already set, then override them again in later un-labeled lines (styles.css:34, 43-56). It works, and it's how the "no ellipsis" and "sticky non-scrolling header" asks ended up correctly satisfied — but a reader has to trace 3-4 overriding declarations for the same selector to find the one that actually wins, and it is exactly the kind of layering that produced C1 (a screen-specific override that nobody re-checked against the general rule it was meant to specialize).

None of this blocks porting to native Android — the primitive set is the right shape to carry over — but it does mean "read app.js/styles.css top to bottom" is not a reliable way to understand current behavior; the true behavior is whatever the last override in file order says.

## Proposed minimal fix list (ordered, each item small)

1. Delete the chat-history tab-strip override (`styles.css:45-47`) so Conversations' filter tabs scroll like every other tab strip instead of overlapping at large text (C1).
2. Suppress `miniMarkup()` for a player whose output is already the one open on the `player` route, so the full player screen doesn't show its own mini-row duplicate underneath itself (C2).
3. Swap the "This phone" output-destination icon from `home` to `device` (or another distinct glyph) in `outputScreen()` (app.js:198) (C3).
4. Delete the dead `case 'rotate'` / `case 'loop'` handlers in `handleAction` (app.js:705-706); the debounced `delayed-setting` path is the one actually used.
5. Delete the dead `.hero`, `.hero:before`, `.hero-eyebrow`, `.hero-actions`, `.hero.compact` CSS (styles.css:6) and drop the unused `kicker`/`symbol`/`compact` parameters from `hero()` and its ~9 call sites.
6. Fix `.model-effort` to read dimmer than the model id instead of darker (styles.css:30) (C4).
7. Make the Home "Notes" card's saved-count copy singular/plural aware instead of "1 saved notes" (app.js:121).
8. Decide and apply one rule for the notification shade's close button — keep it (documented exception, simulated system UI) or remove it to match every other drawer (C6).
9. Give the mock's `.transport-row` skip-duration button (`skip-sheet`) a position next to Forward instead of after Stop, if the intent was "Forward, with its duration adjustable via a dropdown right there" rather than a sixth standalone control.
10. Reconsider the `fork` icon glyph, or always pair it with a visible label (not icon-only) since it is currently ambiguous with a phone/call icon (C5).
