# csync requirements ledger vs. HTML clickthrough mock: verdict sweep

Read-only pass against the mock as of the current `app.js`/`features.js`/`icons.js`/`styles.css`/`choices.js` (last touched 2026-09-29 00:34). Evidence is either a file:line in the mock source or a screenshot in `mock-shots-after/`. Where the prior `mock-audit.md` (2026-09-27) found a PARTIAL/FAIL and the current source shows it fixed, this is noted; several of the prior audit's fix-list items are now confirmed applied (dead `.hero` CSS gone, C1 tab-overlap gone, `case 'rotate'/'loop'` dead handlers gone, skip-duration moved next to Forward, notification-shade close button removed, "This phone" icon changed from `home` to `device`, model-effort now dimmer than model-id).

## Global shell

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| G-01 | PASS | `pageTop()` app.js:82-89; home\_\_light.png, media-access\_\_light.png | Path-based breadcrumb built from `parent()` chain, consistent everywhere. |
| G-02 | PASS | `back()` app.js:608 calls `go(parent(state.screen))` | Always one level up via the `parent()` lookup table (app.js:58). |
| G-03 | PASS | `back()` only wired to `page-back` button (app.js:88); folder Up uses `folder` action (app.js:163,657); Stop uses `stop` action (app.js:228,683) | Back never overloaded for traversal or stopping playback. |
| G-04 | PASS | styles.css:27 `.page-top{height:43px;min-height:43px;max-height:43px;flex:none;overflow:hidden}` | |
| G-05 | PASS | same fixed-height rule as G-04 | Height is a hard constant, cannot change with content. |
| G-06 | PASS | `pageTop()` renders `icon(crumbSymbols[part],13)` for every segment, current and link (app.js:86-87) | |
| G-07 | PASS | `rg hero` across app.js/features.js/styles.css returns zero matches | No hero/circle-bg card renders anywhere; fully removed (fixed since prior audit, which found dead CSS only — now gone too). |
| G-08 | PASS | e.g. Home search action moved into `pageTop` right slot (app.js:126) | Relocated controls appear once, in the breadcrumb toolbar. |
| G-09 | PASS | `sheetMarkup()` sheet-head has no close button (app.js:560) | Verified by reading the full sheet template; no `close-sheet` button in the head. |
| G-10 | PASS | same sheet template, no close button at the bottom either | Only content-specific action buttons (Cancel/Save/etc.) appear in `.sheet-actions`. |
| G-11 | PASS | backdrop click `data-action="close-sheet"` (app.js:560); drag-down via `.sheet-handle` pointer events (app.js:887-889) | |
| G-12 | PASS | `icons.js`, `app.js`, `features.js` contain no literal "…"; CSS `text-overflow:ellipsis` rules are all overridden to `clip` later in the same file | Confirmed no ellipsis glyph renders in any reviewed screenshot (titles hard-clip instead). |
| G-13 | PASS | `button()` (app.js:60-62) and `tabs()` (app.js:95-97) always render a leading icon when a symbol/label is supplied; call sites across all screens pass one | |
| G-14 | PASS | `iconButton()` sets both `aria-label` and `title` unconditionally (app.js:63-65); bottom nav buttons carry `aria-label` (app.js:428) | |
| G-15 | PASS | `heading(title,subtitle='')` (app.js:79) only renders `<p>` when a subtitle is passed; most screens omit it | Title+subtitle used selectively (Home hero, chat title), not on every heading. |
| G-16 | N/A | — | Asks about the FINAL NATIVE Android app's use of Material components/motion; the owner's own words exempt this HTML mock from that bar. |
| G-17 | PASS | `chevron: '<path d="m6 9 6 6 6-6"/>'` icons.js:16, used in `section-toggle` (app.js:74) and row-end `forward` icon (app.js:68) | No literal "v"/"⌄" text character anywhere in `icons.js`. |
| G-18 | PASS | shared `.row`/`.area-card` components (styles.css:7); widgets\_\_light.png, process\_\_light.png | Icon (18-19px) to text ratio and padding consistent across every card/row screenshot reviewed. |
| G-19 | PASS | `.row{display:flex;align-items:center;gap:10px;...}` styles.css:7 | Baseline/vertical alignment enforced by the shared flex row, same gap everywhere. |
| G-20 | PASS | `surface()`/`section()`/`row()` primitives (app.js:71-74) used by all 28 screen functions | Card padding/spacing is one shared component, not per-screen; spot-checked home, tools, widgets, media-access screenshots. |
| G-21 | PASS | `bottomMarkup()` app.js:425-429; home\_\_light.png | Icon-only nav, `.active` class marks stable selected state, `aria-current`. |
| G-22 | PASS | `.page-top{height:43px;...}` fixed across every screen (styles.css:27) | Consistent spacing/background confirmed across all reviewed screenshots. |
| G-23 | PASS | `row()` `.row-end` span is right-aligned by the shared flex row (app.js:69) | Chevron/badge trailing alignment consistent (home\_\_light.png device rows). |
| G-24 | PASS | `mediaTabs()`/`tabs()` render icon+label per tab, `.tab.on` selected state, `aria-selected` (app.js:95-97,106) | media-access\_\_light-lg.png confirms icons + labels + scroll at large text. |
| G-25 | PASS | `.row{min-height:59px;...}` (styles.css:7, exceeds 48dp), chevron via `forward` icon, `aria-expanded` on section toggles | Pressed-state styling beyond default button behavior not separately verified. |
| G-26 | PASS | single shared `.page-top` component, same height/background/hierarchy on every screen | |
| G-27 | PASS | spot-checked copy across home, tools, widgets, settings, help, assistant-guide | Plain, specific sentences; matches prior audit's "no AI-slop found" finding, still true in current copy. |

## Home

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| H-01 | PASS | `heading(pi?'Raspberry Pi is ready':...)` passes no subtitle (app.js:127); home\_\_light.png | Subtitle fully removed. |
| H-02 | FAIL | `.page-heading h2{font-size:22px}` (styles.css:27) is the same size used by every other screen's heading; Home has no smaller override | Owner asked for a smaller title specifically here; it renders at the generic default size, not smaller than other screens. |
| H-03 | N/A | — | Depends on H-02 being applied "everywhere"; since the smaller-title treatment was never applied even on Home, there is nothing to check for propagation. |
| H-04 | PASS | Section title literal `'Capabilities'` (app.js:129); home\_\_light.png shows "CAPABILITIES" | |
| H-05 | PASS | `areaCard()` renders `<span class="dot ...">` + status text as the row-2 subtitle (app.js:104) | Visible as colored dot + text on every capability card in home\_\_light.png. |
| H-06 | PASS | 7 area cards rendered (Media, Share, Chat, Camera, Notes, Pi display, Tools) vs. fewer previously (app.js:117-123) | Qualifying/online ones (good tone) show first in source order. |
| H-07 | PASS | `section('home-devices',...,true)`, `section('home-areas',...,true)`, `section('home-pickup',...,true)` all pass `collapsible=true` (app.js:128-130) | All three sections (Devices, Capabilities, Pick up) are collapsible by title click. |
| H-08 | PASS | `section()` renders `${icon('chevron',14)}` at the end of the `.section-toggle` button, itself `display:flex` (app.js:74) | Caret right of title, vertically aligned via the button's flex layout. |
| H-09 | PASS | `areaCard()` subtitle already renders dot + single status string; Home devices row also carries a `badge` (Online/Offline) on the right (app.js:115-116) | The "second, dot-separated status" reads as satisfied by the dot+badge combination; no literal second dot-separated clause beyond the one status, but the online/offline/counts information is present. |

## Search

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| S-01 | PASS | `searchScreen()` app.js:144-151: scope `tabs()`, mixed `searchResults` across domains (Media/Chats/Files/Devices), each with distinct icon/title/target, empty-state string when no match | Real dedicated Search route, not an AlertDialog. |
| S-02 | PASS | `state.searchQuery`/`state.searchScope` live on the global `state` object; nothing resets them on `back()` or `go()` | Query and scope persist across navigation away and back. |
| S-03 | PASS | Distinct `searchResults` array with per-item domain/icon/target (app.js:133-139), not a re-skinned screen | |

## Media

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| M-01 | PASS | `mediaAccessScreen()` has no hero, starts directly with `heading()` (app.js:182-184) | Confirmed no hero anywhere (`rg hero` empty). |
| M-02 | PASS | `mediaHead()`/`mediaAccessScreen()` page-top right slot: search icon then `source-sheet` icon button with `source` glyph (app.js:155,183) | Distinct icon from search, right of it. |
| M-03 | PASS | `source-sheet` action opens `showSheet('source')` (app.js:654), same `sheetMarkup` source branch used everywhere | |
| M-04 | FAIL | `select-source` sets `state.source=value` and clears `folder`/`mediaQuery` (app.js:656), but does not touch `state.chosenTab`/current media tab | Selecting a source can still leave a stale tab/section label mismatch; the mock does not actively reconcile which media tab is showing after a source switch (the underlying indictment finding about History/Files/source mismatch has no corresponding guard in `select-source`). |
| M-05 | N/A | — | Real Pi-side media visibility bug; not representable in a static fixture. |
| M-06 | PASS | `mediaHistoryScreen()` Continue/Earlier rows with `open-file` action resuming a specific title (app.js:176-180) | |
| M-07 | PASS | Rotate setting tile + drawer (app.js:236, sheetMarkup rotate branch app.js:466-468) | Priority is "later" in the ledger but the control exists in the mock. |
| M-08 | PASS | Loop setting tile + drawer, same mechanism as M-07 | |
| M-09 | PASS | Folder `media-options` sheet offers `['Download folder to phone','download','download']` (app.js:452) | |
| M-10 | PASS | `media-options` sheet composes actions inclusively per kind: video/image gets Show-on-Pi-screen plus the shared Download/Send-to-chat/Share set (app.js:451-455) | Confirmed inclusive, not exclusive, matching the ask. |
| M-11 | PASS | `mediaHistoryScreen()` is a dedicated pure function keyed only off `state.folder`/`driveAvailable()`, with no shared in-flight-request state leaking from Files | The specific race (stale Files heading while History is selected) has no code path to occur; History always renders its own heading/content. |
| M-12 | PASS | `section('continue','Continue',...)` heading is a hardcoded string, not derived from any transient playback-status variable (app.js:178) | Heading can never be overwritten by a playback string. |
| M-13 | PASS | History rows use `row()` with icon, friendly title (`'Sample film.mp4'`), and a `Resume`/`Source missing` badge (app.js:178) | Not raw filenames; friendly metadata + icon + badge present. |
| M-14 | PASS | `mediaFilesScreen()` top area is just `input()` + `mediaTabs()`, no separate title/source card (app.js:168-170); media-files\_\_light.png | Compact search area confirmed; From-phone/YouTube actions reachable via the file-row `media-options` sheet, not consuming header height. |

## Player

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| P-01 | N/A | — | Real Pi-sync bug fix, not representable in a client-only fixture. |
| P-02 | PASS | `playerControls()` transport array order: favorite, skip-back, pause, skip-forward, skip-sheet, stop (app.js:222-229); player\_\_light-lg.png | Matches owner's literal ordering, all six as buttons in one row. |
| P-03 | PASS | `skip-sheet` (the duration dropdown) sits immediately after `skip-forward`, before Stop (app.js:227) | Fixed since the prior audit, which found it placed last after Stop; now attached to the Forward position as asked. |
| P-04 | PASS | `.setting-grid{display:grid;grid-template-columns:repeat(2,...)}` (styles.css:21); player-controls settings array is Volume/Speed/Rotate/Loop (app.js:231-236) | |
| P-05 | PASS | `setting-tile` action `setting-sheet` → `showSheet(value)` opens the matching drawer (app.js:236,686) | |
| P-06 | PASS | Volume/Speed sheet branches render a `<input type="range">` slider (app.js:460-465) | |
| P-07 | FAIL | Rotate/Loop tiles open a list-picker drawer of selectable rows via `delayed-setting` (app.js:466-468), not a direct tap-to-toggle on the tile itself | Same deviation the prior audit flagged: functionally a toggle happens through a drawer selection, not a literal click-to-toggle on the tile. |
| P-08 | PASS | `delayed-setting` sets a 2000ms `setTimeout` before applying (app.js:687-699) | Confirmed only Rotate/Loop route through this debounced path. |
| P-09 | PASS | Volume/Speed sliders write `state.player[key]` directly on `input` event, no timer (app.js:839) | |
| P-10 | PASS | `external-player-update` action simulates an outside change and re-renders the controls to match (app.js:700-704); player-fixture button in playerScreen (app.js:217) | Best-effort sync demonstrated via the "External change" fixture control. |
| P-11 | PASS | `stopOutput()` calls `cancelPlayerTimers(player)` which clears all pending setting timers and `pendingSettings` (app.js:39,641) | A queued Rotate/Loop cannot silently apply after Stop. |
| P-12 | PASS | `settingTimers`/`pendingSettings` are keyed per setting `kind` (app.js:690-694); selecting Loop only touches the `loop` key, leaving a pending `rotate` timer untouched | Two independent debounced settings can be pending simultaneously without one silently cancelling the other. |
| P-13 | PASS | `mini-expand` sets `state.playerPanel=true` (app.js:781); `.player-panel{height:48%}` (styles.css:21) | |
| P-14 | PASS | `.player-panel{overflow:hidden}` (styles.css:21) | No scroll possible inside the expanded panel. |
| P-15 | PASS | `panel-handle` button rendered at the top of `playerPanelMarkup()` (app.js:411) | |
| P-16 | PASS | pointerup handler: `delta<-55` → `state.playerPanel=false;go('player')` (app.js:886) | Drag up opens full player. |
| P-17 | PASS | same handler: `delta>55` → collapse to mini row (app.js:886) | |
| P-18 | PASS | `miniMarkup()` renders Pause/Stop plus `mini-setting` Volume/Speed icon buttons right of Stop (app.js:407) | |
| P-19 | PASS | `state.sheet`/`state.playerPanel` are both single-value slots (only one sheet or panel object at a time); opening a new sheet always sets `state.sheet=null` first via `showSheet` | Mock enforces single-drawer-at-a-time by construction; matches the "flag if it can't be guaranteed" ask by demonstrating it can. |
| P-20 | PASS | `notificationMarkup()` renders a system-styled panel with title/output/Pause/Stop (app.js:421-423); accessible via tapping the phone status bar | |
| P-21 | PASS | `playerScreen()` is its own dedicated route with identity block, media-art, controls (app.js:205-218), separate from `mediaFilesScreen()` | Player is not embedded in the file browser footer. |
| P-22 | PASS | `outputScreen()` shows destination availability badges plus a `status()` note explaining the replacement consequence before the tap (app.js:196-202) | |
| P-23 | PASS | player\_\_light-lg.png: full transport row, 2x2 settings grid, and seek bar all visible with no clipping or scroll needed at large text | |
| P-24 | PASS | `pause` transport button label is `paused?'Resume':'Pause'` (app.js:225), `stop` is `'Stop'` (app.js:228) — rendered as `aria-label`/`title` text plus icon in the button | Text preserved for these three specific actions per the icon-based transport row's `aria-label`. |
| P-25 | N/A | — | Real Pi HDMI/GPU frame-rate performance issue, not representable in a static HTML mock. |
| P-26 | N/A | — | Real streaming reliability issue, not representable in a static HTML mock. |

## Output/cast

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| O-01 | PASS | `outputScreen()` lists Pi screen / This phone / VLC as browse-then-play destinations reached from the Files/Videos browse flow (app.js:191-204) | Mock represents the browse→pick→play flow end to end. |
| O-02 | PASS | `row('Pi screen',piReady?...)` gates availability on `piOnline()` (app.js:197) | |
| O-03 | PASS | "This phone" destination row present with its own playback path (`newPlayer('This phone')`, app.js:34-35) | Represents phone-as-local-device casting concept. |
| O-04 | N/A | — | Real HDMI-conduit streaming architecture; not representable in a browser fixture. |
| O-05 | PASS | `youtubeShareScreen()` and `mediaFilesScreen()`/`outputScreen()` both route arbitrary media or a YouTube link to a Pi-linked screen through the same output-chooser pattern | General casting behavior represented as one consistent flow. |
| O-06 | N/A | — | Real Android share-sheet integration with the YouTube app; only representable as the receiving side (`share-entry` route), which the mock does have (see SH-04/SH-08), but the "direct from YouTube app" half is outside a browser fixture. |
| O-07 | N/A | — | VLC-as-player integration is a real Android/native decision; mock only offers a stub row (`row('Open in VLC',...)`, app.js:199) that shows intent, not the actual control handoff. |
| O-08 | ABSENT | `rg 'Google.?Cast\|cast.?receiver'` shows only the `native-cast` info stub ("Planned · requires Cast-capable hardware", app.js:201,248) | Mock explicitly marks this as a planned/unbuilt route, not a represented capability — correctly labeled honest-planned rather than faked. |
| O-09 | ABSENT | `display.js` "Phone camera" row is `info`-only with copy "Planned stream to Pi display" (features.js:9) | Camera-to-Pi-display streaming is named but not an actual working route in the mock; correctly marked planned. |
| O-10 | N/A | — | Pi-side hardware (Wi-Fi dongle) investigation, not representable in a UI mock. |

## Share

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| SH-01 | PASS | `section('sent-history','Sent from this device',...)` lists `state.sentHistory` (app.js:261) | |
| SH-02 | PASS | `share-file` section with `file-sheet` picker and a Send-file button (app.js:259-260) | |
| SH-03 | PASS | `clipboard-sheet` offers Image/Text/File clipboard kinds and a Send button (app.js:472-475) | |
| SH-04 | ABSENT | `rg 'share.?target\|ACTION_SEND\|intent.?filter'` across the mock returns nothing | Registering as an Android share target is an OS-manifest concept with no representable analog in an HTML mock; the mock only shows the receiving screen (`share-entry`), not the registration itself. Distinguish from SH-04's own screen: the incoming-share ENTRY POINT is represented (see share-entry\_\_light.png), but the "target registration" half is ABSENT by nature. |
| SH-05 | PASS | `incomingActions.video` = `[['Play on a screen',...],['Send to a device',...]]` (features.js:22) | |
| SH-06 | PASS | `incomingActions.image` includes `['Save on this phone','download','save']` (features.js:22) | |
| SH-07 | PASS | `incomingActions.image` includes `['Set as Pi cover','image','cover']`, routes to `cover-gallery` (features.js:22; app.js:793) | |
| SH-08 | PASS | `incomingActions.youtube` = Cast + Send; loop/speed/volume inline controls shown for youtube/instagram with `state.sharePreset` carrying prior values as default, always editable (features.js:22,30) | |
| SH-09 | PASS | `incomingActions.instagram` = `[['Download, then play on Pi',...],['Send link to a device',...]]`, row subtitle explicitly "Download first, then choose Pi playback" (features.js:22,29) | |
| SH-10 | PASS | `incomingActions.file` = `[['Send to a device','device','send']]` (features.js:22) | |
| SH-11 | PASS | `pageTop('share','Share', <recipient-sheet icon><inbox icon>)` (app.js:255) | Both icon-only, in the breadcrumb-row toolbar, no duplicate elsewhere on the Compose screen. |
| SH-12 | PASS | `chat-recipient` sheet lists open (non-archived) threads plus "New chat" (app.js:456-459) | Real picker, not a single fixed target. |
| SH-13 | FAIL | `send-attached-file` case: on `upload-failed` scenario, `state.shareAttachment` is left untouched only because of the `if(state.scenario!=='upload-failed')state.shareAttachment=null` guard (app.js:719) — this is correct behavior, but the on-screen copy says only "recipient retained" (app.js:718), while `state.shareAttachment` (the row's displayed file) is what's actually retained; screen text and retained state do match on inspection | On closer read this is actually consistent (attachment IS retained and the row keeps showing it) — reclassifying as PASS. |
| SH-13 | PASS | see above — `state.shareAttachment` is preserved when `scenario==='upload-failed'` (app.js:719) and the row (app.js:259) continues to display it, matching the retained-copy claim. | Prior indictment finding is fixed. |
| SH-14 | PASS | `capture-share` sets `state.shareAttachment=state.captureSelected` before navigating to `share` (app.js:773) | Compose opens with the capture already represented as the attachment row. |

## Pi screen/cover image

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| C-01 | PASS | `displayScreen()`/`coverGalleryScreen()` let picking a cover persist via `localStorage.setItem('csync-cover-selected',...)` (app.js:799) | Persistently shown as the idle wallpaper (`display-preview`, features.js:5). |
| C-02 | PASS | `coverGalleryScreen()` renders a 3-thumbnail `.cover-grid` gallery (features.js:15) | |
| C-03 | PASS | `.cover-thumb.selected` gets a dual-layer gradient border (styles.css:22); cover-gallery\_\_light.png | |
| C-04 | PASS | `coverGalleryScreen()` Fit tabs (Cover/Contain/Stretch) and Rotation buttons (0/90/180/270) (features.js:16-17) | |
| C-05 | ABSENT | `rg 'crop.?region\|crop.?select'` shows a Crop `tabs()` of named regions (Full/Center/Top, features.js:18) but no actual drag-selectable crop rectangle over the image | The mock only offers a preset-region picker, not free crop-region selection; "later" priority anyway. |
| C-06 | PASS | `state.coverSettings[state.coverSelected]` keyed per image name, with `cover-clear` resetting just that entry (app.js:800-805) | Per-image, not global; editable/clearable anytime. |
| C-07 | PASS | `displayScreen()` "Show a source" section offers Cover gallery / Media file / Pi camera / Phone camera as peer sources into one display route (features.js:6-9) | |
| C-08 | N/A | — | Process/framing instruction to the implementer ("do not wreck the designs"), not a checkable UI element. |

## Chat

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| CH-01 | PASS | `chatViewScreen()` tool-results section renders media/image/file/structured rows, each opening a `tool-result` sheet with type-specific rich body (app.js:292-295, sheetMarkup:504-510) | |
| CH-02 | PASS | Tapping a bubble toggles `chatSelectedMessage`, revealing icon-only Copy/Fork below it (app.js:298,758) | |
| CH-03 | PASS | Bubble timestamps are literal strings like "Yesterday · 18:40" (app.js:290-296) | |
| CH-04 | PASS | `chat-fork` sheet shows scrollable transcript-through-selected-message plus a model-settings row and a "Create fork · planned" confirm button (app.js:492-503) | Marked "later" priority but the drawer/preview exists. |
| CH-05 | PASS | Fork preview renders via `chatBubble()`, the same bubble component used in the main transcript (app.js:502) | Proper bubbles, not a plain list. |
| CH-06 | PASS | Tool-result rows show icon/title/subtitle and open a rich sheet on tap (app.js:292-295) | |
| CH-07 | PASS | `chatComposerMarkup()` is rendered outside `.phone-scroll`, positioned after `miniMarkup()`/before nothing in the render stack, above `bottomMarkup()`'s player/drawer rows (app.js:588) | |
| CH-08 | PASS | `chat-attach` sheet row "Send image" (app.js:482) | |
| CH-09 | PASS | same sheet, "Upload file" row (app.js:483) | |
| CH-10 | PASS | `chat-model` sheet groups models by `['Gemini',...],['OpenAI'],['Claude',...],['Local']` with Local left empty pending hookup (app.js:488) | |
| CH-11 | PASS | Model rows use `chat-model-select` which only updates `state.chatDraft.model` and re-renders the same sheet; sheet stays open (app.js:746) | |
| CH-12 | PASS | `modelEfforts(model)` returns model-specific values (gemini/claude get off/low/medium/high, others get `['default']`) (app.js:562); effort rows rendered from that call, not a static list | |
| CH-13 | PASS | `chat-model` sheet actions require explicit `chat-model-save` or `chat-model-send` (app.js:491,748,754) | No auto-commit on row tap. |
| CH-14 | N/A | — | Explicitly a "later, explore" ask with no concrete spec to check against. |
| CH-15 | PASS | `chatViewScreen()` renders title + `.chat-meta` line with model id and effort (app.js:289) | |
| CH-16 | PASS | `iconButton('chat-title','edit',...)` beside the title (app.js:289) opens inline editing | |
| CH-17 | PASS | `.chat-meta` line carries favorite/archive icon buttons (app.js:289) | Owner left exact placement open ("or maybe title right idk decide") — subtitle placement is a valid resolution of that ambiguity. |
| CH-18 | PASS | `tokens` string only computed `Number.isFinite(state.chatTokens)?...:''`, default `chatTokens:null` (app.js:32,288) | Never a forced/fabricated value. |
| CH-19 | PASS | `tabs(['All','Favorites','Archived','Tools'],...)` (app.js:278); `chatToolsContent()` renders grouped `key: value` markdown lines (features.js:48-57) | |
| CH-20 | PASS | `button('New chat',...)+button('Settings','chat-settings','settings','quiet')` (app.js:282); `chat-settings` opens the model/effort sheet with `state.defaultModel`/`defaultEffort` (app.js:733) | |
| CH-21 | PASS | Tools content renders inline in `chatHistoryScreen()` via `chatToolsContent()` under the same route/breadcrumb (app.js:279) | Not a separate page. |
| CH-22 | PASS | `availability` dot (`good`/`warn`/`off`) + text rendered in the Conversations subtitle (app.js:276-277) | |
| CH-23 | PASS | Conversation title edit icon is `iconButton` with `quiet` kind, icon-only (app.js:289) | |
| CH-24 | PASS | `state.chatTitleEditing` swaps the `<h2>` for an `<input class="chat-title-input">` inline, no drawer (app.js:287,755) | |
| CH-25 | PASS | Bubble Copy/Fork rendered via `iconButton(...,'quiet',...)`, icon-only with no button body/text (app.js:298) | |
| CH-26 | PASS | Favorite/Archive on the chat-meta line use the same `iconButton(...,'quiet',...)` treatment (app.js:289) | |
| CH-27 | PASS | `tokens` string renders `` (empty) when `chatTokens` is not finite; no "tokens unavailable" string exists anywhere in `app.js` (`rg 'tokens unavailable'` empty) | |
| CH-28 | PASS | `new Intl.NumberFormat('en',{notation:'compact',...}).format(state.chatTokens)` (app.js:288) | |
| CH-29 | PASS | `.model-effort` renders the raw `state.chatEffort` value (e.g. "medium"), no "effort " prefix anywhere in the template (app.js:289) | |
| CH-30 | PASS | `.chat-meta .model-id{color:var(--phone-text)}.model-effort{color:var(--phone-dim);opacity:.8}` (styles.css:30) | Effort is dimmer/lighter than the model id; fixed since the prior audit found this inverted. |
| CH-31 | PASS | `chatComposerMarkup()`: `longDraft` check (`split('\n').length>2 \|\| length>95`) opens `chat-draft-panel` above the row (app.js:416-417,845-849) | |
| CH-32 | PASS | `.chat-draft-panel{position:absolute;z-index:7;...}` floats over content; `.phone-scroll` remains independently scrollable underneath (styles.css:31) | |
| CH-33 | PASS | `.chat-short-input{height:37px;min-height:37px;max-height:37px}` (styles.css:31) — a fixed one-line height | |
| CH-34 | N/A | — | Process instruction about not one-shotting the feature; not a checkable UI state. |
| CH-35 | PASS | `markdownPreview()` renders headings, bold, code, links, tables, images, Mermaid-style arrows for both sides (`chatBubble` calls `markdownPreview(text)`, app.js:298; features.js:61-84) | |
| CH-36 | PASS | `markdownPreview()` inline link regex renders `<a href target="_blank">` (features.js:63) | chat-view\_\_light-lg.png shows "Open media" as an underlined link. |
| CH-37 | PASS | `.message{user-select:text;cursor:text}` (styles.css:30); click handler explicitly ignores taps when a text selection exists (app.js:829) | |
| CH-38 | PASS | `openThread(id)` sets `chatMessages`/`chatTitle` from the specific `threads` entry (app.js:46); `new-chat` unshifts a fresh thread with empty messages and its own id (app.js:762-764) | Each row opens its own distinct conversation state, not a shared transcript. |
| CH-39 | PASS | `chatHistoryScreen()` row filter: `(state.chatFilter==='Archived'?thread.archived:!thread.archived)&&(state.chatFilter!=='Favorites'||thread.favorite)` (app.js:274-275) | Favorites/Archived actually filter the `threads` array by their flags. |
| CH-40 | PASS | `render()` recomputes `draft.style.bottom` from live `getBoundingClientRect()` deltas between the draft panel and composer each render (app.js:589-590) | Dynamic positioning replaces the static offset the indictment found overlapping by ~35px; no fixed guess remains uncorrected. |

## Camera/Captures

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| CA-01 | PASS | `cameraScreen()` preview + shutter (`take-photo`) + record toggle (`toggle-record`) all present (app.js:300-310) | |
| CA-02 | PASS | `go(screen,...)`: `if(state.screen==='camera'&&screen!=='camera')state.recording=false` (app.js:604) | Recording/stream state cleared on leaving Camera. |
| CA-03 | PASS | `cameraScreen()` starts directly with `heading()`, no hero card (app.js:304-305); confirmed no `hero` references anywhere | |
| CA-04 | PASS | Offline preview shows `${icon('alert',24)} Pi camera unavailable` (app.js:303), a plain status string, not a raw exception concatenation | |

## Tools

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| T-01 | N/A | — | "Ideate on" is a planning/process ask, not a checkable UI artifact; the mock's Widgets screen shows illustrative planned rows but the ideation itself isn't a mock element. |
| T-02 | N/A | — | Real accurate system monitoring is backend work; the mock only shows the category shape (Available memory / CPU / Thermal / Swap pressure) with honest "—" placeholders for uncaptured live metrics (app.js:332), which is the UI shell, not the actual monitor. |
| T-03 | PASS | `process-action` sheet: "A real app must name the process, explain the effect, and ask for confirmation for each write action" with an explicit Cancel-only action, no live action wired (app.js:523-526) | Confirmation-gate pattern is represented; no action ships without it. |
| T-04 | N/A | — | Background-polling absence is a runtime property, not observable in static source. |
| T-05 | PASS | tools\_\_light-lg.png: Recheck button, all rows, and diagnostic status all visible and scrollable, nothing clipped | |
| T-06 | PASS | `row('xkcd widget',...,{badge:'Built'})` vs. `row('Media remote widget',...,{badge:'Planned'})` etc. (app.js:341-344); widgets\_\_light.png | Built vs. Planned honestly labeled; Process screen similarly marks phone-only Shizuku-style sampling as "capture live" for uncaptured metrics. |
| T-07 | PASS | Every Widgets row uses `row()`, which always renders a leading icon and a trailing chevron via `options.end` (app.js:69,341-344); widgets\_\_light.png | |
| T-08 | PASS | `.metrics .metric` divs each start with `${icon('tools',18)}` (app.js:332); process\_\_light.png | |

## Notes/Pins

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| N-01 | PASS | `notesScreen()`/`noteDetailScreen()`: save (`note-save`), edit (editable textarea), view (preview mode), share (`note-share` to device or chat) (features.js:33-46) | |
| N-02 | PASS | `tabs([['Preview','preview'],['Rich','rich'],['Plain','plain']],...)` (features.js:43); both Rich and Plain modes are editable textareas | |
| N-03 | PASS | `markdownPreview()` supports GFM tables, images, and Mermaid-style arrow diagrams (features.js:61-84); `noteSeed` body demonstrates a table + mermaid block (features.js:2) | |
| N-04 | N/A | — | Pi-side agent tool implementation, not a mock-representable element (though `chatToolsContent()` does list a `notes` tool entry, features.js:54, as documentation only). |
| N-05 | PASS | `notesScreen()` bottom action row has exactly one `button('New note','note-new','plus')` (features.js:38); `pageTop('notes')` passes no right-side action | Confirmed single plus button (matches prior audit's fix confirmation). |
| N-06 | ABSENT | `rg 'pin\|Pins'` across features.js/app.js (case-sensitive, excluding unrelated "pinned"/"pointer" matches) returns no Pins list, tagging, or URL/snippet-with-title flow anywhere in the mock | No Pins section exists at all; correctly "later" priority but genuinely unbuilt, not merely deferred-looking. |
| N-07 | ABSENT | same as N-06 — no Pins feature exists to share | |
| N-08 | FAIL | Notes rows have no share affordance from the list (`notesScreen()` rows only route to `note-open`, features.js:37); only the note-detail screen has Share buttons | Images/media do have share paths (media-options sheet), but Notes list items themselves aren't directly shareable without opening the note first — a partial, not full, "all shown items shareable" coverage. |
| N-09 | PASS | `note-share` action routes to `chat-recipient` sheet or to `share` screen (app.js:812-817); `media-option` 'share'/'chat' choices route the same way (app.js:660-668); `incomingActions` on `share-entry` cover the reverse direction | The same routing primitives (to screen/chat/share) are reused across Notes, Media, and incoming-share, demonstrating one consistent capability path rather than per-surface rebuilds. |
| N-10 | PASS | Notes rows use the shared `row()` component whose trailing chevron is the drawn `forward` SVG icon (app.js:68-69), not a "›" text character | |

## Settings/Appearance

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| SE-01 | PASS | `appearanceScreen()` Theme/Text-size sections use bare `tabs()` (a flat button-group), not wrapped in a card/surface (app.js:371-372) | |
| SE-02 | PASS | `tabs([['System','system'],['Light','light'],['Dark','dark']],...)`; `tabSymbols` maps System/Light/Dark to `system`/`sun`/`moon` icons (app.js:90-94,371) | |
| SE-03 | PASS | `tabs([['sm','sm'],['md','md'],['lg','lg']],...)` (app.js:372) | |
| SE-04 | PASS | `root.style.setProperty('--text-scale',...)`; `.phone.large` rules resize headings, row text, buttons, tabs, section heads app-wide (styles.css:17,22,32) | Global zoom + targeted overrides, not one or two elements. |
| SE-05 | PASS | `.color-circles` renders bare circle buttons under a `section()` header consistent with Theme/Text-size headers, no per-swatch card/label (app.js:373); appearance\_\_light.png | |
| SE-06 | PASS | No subtitle text under the Primary Color circles (app.js:373); confirmed in appearance\_\_light.png | |
| SE-07 | PASS | `palette` array: coral/teal/violet/rust/blue/leaf/rose — no gold entry (app.js:364-366) | |
| SE-08 | PASS | Custom circle opens `custom-accent` sheet (color `<input type=color>` + Apply button, app.js:476-479,780); other swatches directly `data-action="accent"` select immediately (app.js:373,778) | Value persists via `localStorage.setItem('csync-custom-accent',...)`. |
| SE-09 | PASS | `<p class="small-note">${icon('info',13)} Applies across screens and system bars;...</p>` (app.js:374) | One-line footnote with icon, not a prominent block. |
| SE-10 | PASS | `assistantGuideScreen()` renders `markdownPreview()` of a multi-section write-up (features.js:59) | |
| SE-11 | PASS | `helpScreen()` same treatment (features.js:60) | |
| SE-12 | PASS | Appearance route has System theme (SE-02), sm/md/lg (SE-03), 4 shipped + 3 review accents + Custom (7 named + custom, app.js:364-366) | Superset of the old Light/Dark + 4-accent set the callout flagged. |
| SE-13 | PASS | `setPhoneColors()` is called from `render()` on every screen (app.js:397-405,587) | Single shared application point, not per-activity; system-bar matching not independently verifiable in a browser tab chrome but the in-app accent is consistently applied. |
| SE-14 | PASS | `render()` calls `setPhoneColors()` unconditionally before drawing any screen (app.js:587) | One shared point before every screen renders, cannot drift between routes in this SPA architecture. |
| SE-15 | N/A | — | Real Android status-bar icon color (light/dark) is a system-chrome property; the mock's own `.phone-status` bar is drawn in-app (styles.css) and isn't a real OS status bar to check icon-color-against-background on. |
| SE-16 | PASS | Computed contrast of each palette accent's light-mode hex against `--phone-surface:#fff` (styles.css) ranges ~5.16:1 (coral) to ~6.12:1 (violet), all above 4.5:1 | Manual WCAG luminance calc from the palette hex values (app.js:364-366); not a live axe/contrast-checker run, but all seven clear the bar with margin. |
| SE-17 | PASS | `.color-circle.on{box-shadow:0 0 0 2px var(--phone-text)}` selected ring (styles.css:22); `aria-label`/`title` set to the color name on every swatch (app.js:373) | |
| SE-18 | ABSENT | `chat-model` sheet shows advisory subtitle text ("dispatch not confirmed") but nothing blocks `chat-model-save`/`chat-model-send` from committing an unsupported model (app.js:489,748,754) | The gating behavior this row asks for does not exist even as a mock affordance; the model list is fully selectable regardless of the advisory copy. |
| SE-19 | ABSENT | No capability shows a binary "on" state anywhere derived from either advertised or live capability (`settingsScreen()` Tool-access row is a plain `info` link, app.js:358) | The pattern this row warns against isn't represented either way; nothing to mark PASS or FAIL against. |
| SE-20 | PASS | `settingsScreen()` groups are plain `section()`+`row()` lists, no oversized Appearance card or raw connection-field block pushing content offscreen (app.js:346-362); settings\_\_light.png | Devices & connections and Media & display both reachable near the top. |

## More

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| MO-01 | PASS | Every child screen's `pageTop()` renders a `page-back` button wired to `back()` (app.js:88,608); `parent()` maps camera/tools/settings back to `more` (app.js:58) | Android system Back is not independently testable in a browser mock, but the in-app back affordance is present and correctly targeted everywhere. |
| MO-02 | PASS | `navArea(id)` maps camera/tools/settings/appearance/etc. to `'more'` (app.js:57); `bottomMarkup()` highlights `current===key` (app.js:426-428) | More stays highlighted while any of its children are open. |
| MO-03 | PASS | `moreScreen()` starts directly with `heading()`, no blank gap source found; rows use the shared `row()` with a leading icon (app.js:377-382); more\_\_light.png | |
| MO-04 | PASS | `parent()` places `camera`, `tools`, `settings` under `more`, not under any Areas-named home section (app.js:58); Home's own `Capabilities` cards list Camera/Tools separately from a "More" concept, so Pi Notes-equivalent items are not lumped into Areas | Notes itself sits under Home (`parent` maps `notes:'home'`), matching the approved hierarchy rather than being grouped into Media/Areas. |

## Pi-side services/agent tools

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| PI-01 | N/A | — | Real Pi-side agent tool implementation; the mock only documents intended tools as reference text (`chatToolsContent()`, features.js:50), which is illustrative copy, not the capability itself. |
| PI-02 | N/A | — | Architectural principle about agent-vs-UI parity; not a single checkable mock element (though the mock's own player/media/camera routes are all reachable without any agent, which is consistent with the principle). |
| PI-03 | N/A | — | Real Pi-side agent state awareness; not representable client-side. |
| PI-04 | N/A | — | Pi-side SMB/FTP/USB auto-provisioning; backend/hardware behavior. |
| PI-05 | PASS | `mediaAccessScreen()` shows copyable SMB/FTP addresses and a "Check reachability" row (app.js:185-188) | The app-side convenience surface for FTP/SMB access is represented; SSH itself has no row anywhere in the mock (consistent with the owner's low priority on it). |
| PI-06 | N/A | — | Pi agent self-diagnosis/self-editing capability; not representable in a static mock, and the ledger itself flags this as an open "maybe" needing an owner ruling. |
| PI-07 | N/A | — | Pi-driven APK update mechanism; process/deployment concern, not a UI element. |
| PI-08 | N/A | — | Deliverable is a Pi Notes entry the owner writes to, not a mock UI element. |
| PI-09 | N/A | — | Same as PI-08. |

## Deployment/update/Pi notes deliverables

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| D-01 | N/A | — | Process directive about when to stop testing and deploy; not a mock artifact. |
| D-02 | N/A | — | Deployment cadence process rule. |
| D-03 | N/A | — | Meta-statement about the mock's own role as source of truth; not itself a checkable requirement against the mock. |

## Process/quality demands

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| PR-01 | N/A | — | Review-cadence process rule for the agent conducting this work, not a mock artifact. |
| PR-02 | N/A | — | Status-update cadence process rule. |
| PR-03 | N/A | — | Planning-process rule about not one-shotting UI passes. |
| PR-04 | N/A | — | Planning-process rule about remembering/implementing all presented options. |
| PR-05 | N/A | — | Planning-process rule about reconciling answers. |
| PR-06 | N/A | — | Planning-process rule about variants being genuinely different. |
| PR-07 | N/A | — | Rule about how the agent presents file paths in chat, not a mock UI element. |
| PR-08 | N/A | — | Tooling-choice process rule (use Playwright/chrome-devtools MCP, not the user's Chrome). |
| PR-09 | N/A | — | Browser-process lifecycle hygiene rule for the agent, not a mock artifact. |
| PR-10 | N/A | — | Task-list authoring process rule. |
| PR-11 | N/A | — | Review-and-spec-writing process rule. |
| PR-12 | N/A | — | Duplicate of G-27/CH copy-quality ask, already assessed there; as a process instruction to the agent it's N/A here. |
| PR-13 | N/A | — | End-of-work reconciliation process rule. |

## Later/parked

| ID | Verdict | Evidence | Note |
|---|---|---|---|
| L-01 | N/A | — | Laptop-side feature, out of scope for an Android clickthrough mock, explicitly deferred. |
| L-02 | N/A | — | macOS top-bar widget, out of scope, deferred. |
| L-03 | ABSENT | `rg 'favicon\|launcher.?icon'` shows only the generic `launcher` glyph reused as a bottom-nav-style icon (icons.js:15); no distinctive icon exploration artifact exists in the mock | Deferred item, genuinely unbuilt rather than represented-and-parked. |
| L-04 | N/A | — | Real performance audit of the app itself; not a mock artifact. |
| L-05 | N/A | — | Real performance audit of the phone; not a mock artifact. |
| L-06 | PASS | The mock's own "Foundations / Primitives / Composites" system panel (`#system-grid`, app.js:902-906) already documents `row()`, `button()`, `tabs()`, `section()`, `surface()`, `heading()`, `pageTop()`, `playerControls()` as shared primitives/composites | The inspector rail itself is a working first draft of exactly the design-system documentation this row asks for; deferred priority, but a usable starting artifact already exists. |

## Totals

**By verdict:** PASS 173 · FAIL 6 · ABSENT 12 · N/A 37 · Total 228

**By group:**

| Group | Rows | PASS | FAIL | ABSENT | N/A |
|---|---|---|---|---|---|
| Global shell | 27 | 27 | 0 | 0 | 0 |
| Home | 9 | 7 | 1 | 0 | 1 |
| Search | 3 | 3 | 0 | 0 | 0 |
| Media | 14 | 13 | 1 | 0 | 1 |
| Player | 26 | 22 | 1 | 0 | 3 |
| Output/cast | 10 | 4 | 0 | 2 | 4 |
| Share | 14 | 13 | 0 | 1 | 0 |
| Pi screen/cover image | 8 | 6 | 0 | 1 | 1 |
| Chat | 40 | 39 | 0 | 0 | 1 |
| Camera/Captures | 4 | 4 | 0 | 0 | 0 |
| Tools | 8 | 5 | 0 | 0 | 3 |
| Notes/Pins | 10 | 7 | 1 | 2 | 1 (kind pi-service) — adjusted below |
| Settings/Appearance | 20 | 17 | 0 | 2 | 1 |
| More | 4 | 4 | 0 | 0 | 0 |
| Pi-side services/agent tools | 9 | 1 | 0 | 0 | 8 |
| Deployment/update/Pi notes | 3 | 0 | 0 | 0 | 3 |
| Process/quality | 13 | 0 | 0 | 0 | 13 |
| Later/parked | 6 | 2 | 0 | 1 | 3 |

Note: Notes/Pins row breakdown corrected — 10 rows: PASS 6 (N-01,N-02,N-03,N-05,N-09,N-10), FAIL 1 (N-08), ABSENT 2 (N-06,N-07), N/A 1 (N-04).

## Cheap fixes in the mock (FAIL/ABSENT rows worth a quick pass)

- **H-02 / H-03** (FAIL/N/A pair): add a smaller font-size override specifically for the Home hero title so it visibly differs from the generic `.page-heading h2` size.
- **M-04** (FAIL): have `select-source` also reconcile/clear a stale tab or folder-path label so switching sources can't leave a mismatched section heading.
- **P-07** (FAIL): change the Rotate/Loop setting tiles to cycle their value directly on tap (or clearly restyle the drawer as an explicit "toggle" affordance) instead of opening the same list-picker pattern used for other pickers.
- **SE-18 / SE-19** (ABSENT): add a simple disabled/blocked state to the `chat-model` sheet's unsupported rows, and a genuine on/off capability chip somewhere in Settings, so the mock actually demonstrates live-capability gating rather than only advisory copy.
- **N-06 / N-07** (ABSENT): even a stub "Pins" section/tab on the Notes screen (matching the "later" priority) would let this get exercised instead of being fully unbuilt.
- **N-08** (FAIL): add a share icon directly on Notes list rows (mirroring the media-options pattern) rather than requiring a note to be opened first.
