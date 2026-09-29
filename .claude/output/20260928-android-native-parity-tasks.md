# csync native Android completion list

This is the page acceptance list for bringing the installed Android app into line with the owner-approved clickthrough. The visual source is `/Users/alcatraz627/Code/Claude/csync/assets/android-ui-clickthrough/index.html`; the functional contract is `/Users/alcatraz627/Code/Claude/csync/docs/android-ui-final-spec.md` and the project guide. The clickthrough uses fixture data. The Android app must show live state and honest unavailable states.

## Working loop for every full page

1. **Scope out:** Open the clickthrough route in light and dark at normal and large text. List every visible element, its state variants, and its destination. Read the Android page, its sibling pages, resources, data owner, and navigation callers. Record any mock behavior that has no native equivalent and the real source needed.
2. **Implement:** Change only the agreed page and shared component files. Keep real content, named peers, server capability responses, and output ownership. Add accessible labels for icon controls. Preserve draft, selection, playback, and transfer identity across navigation.
3. **Code check:** Build with `JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew assembleDebug --offline` in `/Users/alcatraz627/Code/csync-hub`. Run `git diff --check`. Inspect the diff for changed behavior and accidental removal. Run the relevant unit or service test when a contract changed.
4. **Self review:** Install on the emulator or connected phone. Capture full-page screenshots at normal and large text in light and dark, including scrolled content. Compare against the matching clickthrough screenshots; describe concrete spacing, hierarchy, icon, typography, and state differences. Exercise each control, not only its tap response.
5. **Correctness criteria:** Check the page's real data, empty/loading/offline/error/pending states, navigation return, state persistence, accessibility names, and no visible `...` placeholder. Verify the page's open owner callouts with the recorded commands and screenshots. A build alone does not satisfy this step.
6. **Page checkpoint:** Write the changed files, screenshots, interaction results, open gaps, and exact build/test output to a dated page report. Send it to the parent for review before moving to another full page. The parent checks the installed frame and at least one state transition, then accepts the page or returns specific corrections.

Use the **current** clickthrough file at the time of each page check. Re-render it and record the capture path before comparing native screenshots. An older screenshot is insufficient when the HTML and screenshot disagree. Owner feedback on an active page is an instruction to repair that page unless the owner explicitly cancels or pauses it.

## Shared UI patterns to check on every page

1. **Top bar:** One compact, fixed-height row. Show the current area and useful context. Its top-right action is contextual, icon-only where the clickthrough is icon-only, with a spoken label and hit target. No duplicate heading card.
2. **Breadcrumbs and back:** Each visible crumb has its icon. A crumb opens its named ancestor. The back control moves one route level. Long paths shorten in the middle and never clip the current title. Hardware Back and dialog dismissal follow the same hierarchy.
3. **Bottom navigation:** Home, Media, Share, Chat, More are icon-only with accessible names, a stable order, and a selected state. Deep routes keep the correct parent selected. Reentering an area does not erase a draft, selected file, thread, or active player.
4. **Icons:** Use the chosen semantic icon consistently for route, row, action, and state. Match icon size and alignment. Every icon-only control has a content description; decoration is hidden from accessibility. Avoid Unicode placeholders where a proper icon is available.
5. **Buttons:** Primary, secondary, destructive, and disabled actions have distinct appearance and feedback. Check minimum touch size, pressed state, loading state, duplicate-tap protection, and whether the action actually reaches the named target.
6. **Cards and rows:** Follow the clickthrough's density, corner radius, border, internal spacing, title/subtitle order, status indicator, and trailing action. A row remains legible with long names and large text. The whole card and its overflow action do separate jobs.
7. **Links:** Links are recognizable, open a safe matching destination, retain selectable surrounding text, and do not trigger a row action accidentally. Check links in Markdown and in user/assistant bubbles.
8. **Tabs and filters:** Selected treatment, icons, horizontal overflow, counts, and content reflect one state source. Switching tabs does not mutate or lose the item being viewed.
9. **Fields and composer:** Labels/hints name the expected content. Multi-line input grows or scrolls as specified, keyboard does not cover Save/Send, a canceled action preserves the previous state, and errors point to the field. Collapsed Chat composer is one line and transcript scroll is independent.
10. **Menus, sheets, dialogs, and options:** Open next to the selected item where possible. Show only capability-valid actions. Confirm destructive or replacement effects. Preserve the item ID and URI grant until an option completes or cancels. Return to the originating page with state intact.
11. **Status and feedback:** Distinguish observed success, pending command, failure, stale data, unavailable service, and offline device. Do not turn a queued command into a success claim. Keep useful retry context.
12. **Typography, color, and motion:** Apply System/Light/Dark, text sizes sm/md/lg, chosen accents, system bars, focus and pressed feedback across every activity. Honor reduced motion. Large text must leave controls reachable and not hide the selected tab.
13. **Accessibility:** Traversal follows visual order; headings, roles, selected states, and control names are announced. Check contrast and touch targets in both themes.
14. **No silent deletion:** Preserve every owner-reviewed route, section, action, and variant until the owner explicitly retires it. Compare sibling implementations before adding a new pattern.

The owner's latest app-wide checks apply to **every** native page, including Media and deep routes:

15. **Disclosure chevrons:** Search all layouts and generated rows for text `v` or `⌄` controls. Replace each with a drawn, aligned chevron; exercise both expanded and collapsed states in light and dark.
16. **Top bars:** Capture each page at normal and large text in both themes. Compare the full row with the current clickthrough: compact height, context/breadcrumb placement, background, icon/label alignment, and reachable actions.
17. **Section tabs:** Every tab strip carries an aligned icon and label, selected state, and accessible name. Include Media Files, Videos, History, and Access; do not confuse these labeled section tabs with the icon-only five-item bottom navigation.
18. **Action touch surfaces:** Inspect every disclosure and action row, especially Media's From phone or YouTube. Require a drawn chevron, at least 48dp touch height, balanced insets, a visible pressed/expanded state, and a working tap across the whole intended surface.

Re-run callouts `co-20260927-212103-bf`, `co-20260927-212103-81`, `co-20260927-212104-00`, and `co-20260927-212105-d9` with installed screenshots and interactions before any app-wide acceptance claim. Record each result in the callout ledger; an open row remains open until the owner retires it.

## Page groups and required journeys

### A. Home and global search

1. Home: named Pi and peers, live reachability, useful continuation, major-job cards, and collapsible sections. Check idle, active playback, Pi offline, narrow width, and large text. Every card must lead to its promised route.
2. Search: scoped query, mixed results, saved versus live source, empty/offline state, and route to the exact selected media item, chat, or received item. Back restores query and selection.

Home's current correction list from the owner: replace text `v` expanders with cared-for chevrons; proportion icon, label, gap, padding, and control height together; align card icons and title baselines; balance vertical and horizontal card spacing; make bottom navigation icons only; reduce the top bar's height and background prominence; align Pi/Mac trailing status and chevron as one group. Inspect the whole scrolled page in both themes and at normal and large text before the parent review. The current clickthrough capture is `/private/tmp/csync-current-clickthrough-home.png`; the earlier hero capture is stale relative to the current HTML.

### B. Media, output, and player

3. Files, Videos, History, Access: source identity, search, folder path, sorted item rows, empty drive, absent mount, access address, playback history, and resume. File overflow must expose all supported download, chat, share, output, and display routes without changing the active player.
4. Output chooser: show Pi screen and phone availability, current title and state, and replacement effect. Selection applies to the chosen file only after confirmation.
5. Full player and mini player: one observed session per output with matching title, playback state, position, volume, speed, skip, loop, rotate, revision, and pending command. Test play/pause/seek/stop, rapid commands, output switch, external state change, notification actions, long text, and app background/return. A queued phone command stays pending until applied.
6. YouTube share: direct supported link, playback defaults, muted Pi start, blocked-video message, and accurate Cast wording. Do not claim Instagram download or physical HDMI output without exercise.

### C. Share and incoming content

7. Compose and Inbox: text, typed clipboard, file/image selection, named recipient, transfer progress, success/failure, sent history, received items, retry, and cancel. A failed send retains the item and recipient.
8. Incoming Android share: test video, image, YouTube, Instagram link, ordinary file, web URL, and plain text. Resolve actions from MIME, source, and live capability. Preserve URI grants, show adjustable playback defaults where relevant, and route through Pi screen, peer, Note, Pin, or Chat only when supported.
9. Circular share: from each app-owned image, media item, note, and pin, open Android Sharesheet, choose csync again, and confirm the same item reaches the matching destination chooser with content intact. Test cancellation and back navigation.

### D. Conversations and assistant

10. History: All/Favorites/Archived/Tools filters, search, new thread, rename, favorite, archive, delete, and saved ordering. Empty/loading/offline states must be honest.
11. Conversation: source Markdown and rich render in both speaker bubbles, selectable text, working links, separate Copy and Fork actions, bounded Fork context and confirmation before a new branch, typed tool results, attachment routes, model/effort capability, Save/Send semantics, measured telemetry only, and a draft that survives navigation. Test the one-line collapsed composer, expansion, drag, and independent long-transcript scrolling.

### E. Camera, display, and captures

12. Live camera and Captures: on-demand preview, Photo, Record/Stop, saved item list, output/share choices, camera offline and error state, and zero viewers after leaving the tab. Do not start a competing capture process.
13. Pi display and Cover gallery: observed source, idle cover, media and camera inputs, selected image border, per-image fit/rotate/crop, reset, and safe return from media. A software state does not establish a visible HDMI image or sound.

### F. Notes and Pins

14. Notes list and detail: Pi-backed search, create/read/edit/delete, Markdown source, Preview/Rich/Plain views, screenshots, revision conflict, and share to conversation/device. Edits preserve one source and show a conflict before overwrite.
15. Pins: URL or text snippet, optional title/tags/description, list/search/detail/edit/delete, authenticated Pi persistence, Android share ingress and egress. Test optional-title fallback, tags, revision conflict, a pin returning through Android Sharesheet, and no leftover test item.

### G. More, Tools, Settings, and reference

16. More: area and reference cards, accurate parent/child return, and navigation to Camera, Tools, Settings, Capabilities, and Help.
17. Diagnostics, Process, Widgets: authenticated Pi/service health, observed power/thermal warnings, process and widget status, safe actions, update availability, and honest unavailable states.
18. Settings and Appearance: named peers, assistant/provider configuration, media defaults, update path, theme, text size, accents and Custom persistence. Reopen every activity after changing appearance.
19. Assistant capabilities and Help: readable Markdown tied to actual service/tool availability. Mark planned providers and actions clearly.

## Exact 28-route acceptance inventory

The 19 work items above group related implementation. This table names every route in `/Users/alcatraz627/Code/Claude/csync/assets/android-ui-clickthrough/choices.js` so the full review cannot silently skip a page. Apply the six-step page loop and 14 shared-pattern checks to each row.

| # | Route | Segment | Page-specific acceptance |
| --- | --- | --- | --- |
| 1 | `home` | Home | Live Pi and named-peer state, truthful continuation, all major jobs, three independent collapsible sections. |
| 2 | `search` | Home | Scope tabs, mixed real results, empty/offline state, exact selected item route, query retained on Back. |
| 3 | `media-files` | Media | Source selector, folders, file actions, drive absence, search, and unchanged active playback while browsing. |
| 4 | `media-videos` | Media | Indexed video identity, source and duration, output route, empty and missing-drive states. |
| 5 | `media-history` | Media | Observed history and resume position; missing files explain why resume cannot proceed. |
| 6 | `media-access` | Media | Actual available SMB/FTP addresses, connection result, copy affordance, and unavailable service. |
| 7 | `output` | Playback | Pi and phone availability, current session title, replacement effect, explicit apply to chosen file. |
| 8 | `player` | Playback | Full transport, seek, volume, speed, skip, rotate, loop, target identity, pending state, and mini-row parity. |
| 9 | `youtube-share` | Playback | Direct link intent, editable defaults, muted Pi start, blocked-video feedback, truthful Cast state. |
| 10 | `share` | Share | Named recipient, text/clipboard/file identity, send progress, failure retry, and cancellation. |
| 11 | `inbox` | Share | Received items separated from sent history; open/share/retry state and source peer shown. |
| 12 | `chat-history` | Chat | All/Favorites/Archived/Tools in one tab row, search, new thread, metadata changes, and live Pi state. |
| 13 | `chat-view` | Chat | Rich and source Markdown, selectable links, Copy/Fork, typed tools, draft, composer, telemetry, model/effort. |
| 14 | `camera` | Camera | On-demand preview, Photo, Record/Stop, error/offline, and viewer count zero after exit. |
| 15 | `captures` | Camera | Saved photo/video identity, preview, output, Android share, and deleted/missing capture handling. |
| 16 | `tools` | Tools | Authenticated health, power warning, recheck, update entry, process/widgets links, no invented success. |
| 17 | `process` | Tools | Match the mock's prior-snapshot labels and planned live sampling/action state; show only measurements the Android app actually obtains, with their time and unavailable state. |
| 18 | `widgets` | Tools | Actual xkcd widget and available shortcuts, setup path, planned actions labeled accurately. |
| 19 | `settings` | Settings | Named peers, token-safe configuration, media/assistant defaults, save and reopen persistence. |
| 20 | `appearance` | Settings | System/Light/Dark, sm/md/lg, review accents and Custom, app-wide persistence and system bars. |
| 21 | `more` | More | Area/reference routes, accurate parent return, no duplicate Home destinations. |
| 22 | `display` | Display | Observed source, cover/media/camera choices, current status, output and return from player. |
| 23 | `cover-gallery` | Display | Saved images, selection border, per-image fit/rotate/crop, reset and physical-display limit. |
| 24 | `share-entry` | Incoming share | Typed video/image/link/file/text actions, URI grant, editable playback defaults, exact destination draft. |
| 25 | `notes` | Notes | Pi-backed list/search/create, screenshot counts, pin list, loading/offline, and revision labels. |
| 26 | `note-detail` | Notes | One Markdown source across Plain/Rich/Preview, screenshot attach, conflict, delete, and sharing. |
| 27 | `assistant-guide` | Reference | Readable Markdown, declared versus working tools/providers, safe links and accurate capability state. |
| 28 | `help` | Reference | Clear service and update guidance, safe links, current version, and parent navigation. |

## Release and final review gates

1. Run the clickthrough's targeted and full browser probes, then inspect the native app separately. Browser fixture results never count as native proof.
2. Build the APK, inspect package identity/version/hash, back up the old Pi APK, stage the new APK, and verify the Pi's served hash.
3. Start from the prior installed app and use **More → Tools → Update csync from Pi**. Check Android package version, installer result, reopened app, retained settings, and a live Pi endpoint.
4. Run changed-module tests and changed-route runtime probes. Record PASS, FAIL, or UNRUN with reason for each page and journey. Re-run every open owner callout in `/Users/alcatraz627/Code/Claude/csync/.claude/callouts.jsonl`; record the result without retiring it.
5. Do a full native review pass through all 28 routes in the clickthrough's route list at standard and large text, light and dark, including empty/loading/offline/playing/error variants. Compare screenshots as whole frames, then exercise stateful transitions. Have an independent reviewer inspect the changed code and screenshots; fix grounded findings and repeat the affected checks.
6. Update the two Pi Notes: one observed-work summary with clearly labeled screenshots and explicit gaps, and one owner-facing list of features to try. Verify their revisions and rendered contents in the installed app.
7. The parent gives a page verdict after each full page. The overall done claim waits for the complete review pass and physical-phone checks where an emulator cannot establish behavior.

## Prompt for each delegated page

> Work on **[one named page]** with model **gpt-6-sol**. Read the owner-approved clickthrough route, `/Users/alcatraz627/Code/Claude/csync/docs/android-ui-final-spec.md`, this task list, the relevant open callouts, the Android README and UI brief, and sibling native pages. Do not spawn sub-agents. Your code write scope is **[exact files]**; report any needed files outside that scope. Do not commit, push, or delete a reviewed surface. Ignore board auto-dispatch and stop after this page.
>
> **Scope out:** Enumerate every visible element and interaction in the mock for idle, data, loading, offline, error, large-text, light, and dark states. Map each to its current native implementation and real state source. Name missing transitions before editing.
>
> **Implement:** Bring the page and all shared controls it uses into the mock's hierarchy, spacing, iconography, typography, and states. Preserve real contracts and existing routes. Check buttons, top bar, breadcrumbs, icons, cards, links, tabs, fields, menus, sheets, dialogs, status, accessibility, and no visible ellipsis.
>
> **Code check:** Build offline, run `git diff --check`, inspect your final changed-file list, and run behavior tests for any changed contract. Report exact output and what the checks cannot prove.
>
> **Self review:** If the parent has released the emulator, install and capture whole-frame screenshots in light/dark, normal/large text, and one adverse state. Otherwise provide a precise render-check request. Exercise every page action and parent return. Compare against the mock and write remaining differences.
>
> **Correctness:** Record PASS/FAIL/UNRUN for real data, empty/loading/offline/error, persistence, navigation, content identity, accessibility, and each relevant owner callout. Do not claim page acceptance from a build alone.
>
> Write a dated report to **[absolute output path]** before returning. Include source lines, changed files, screenshot paths, commands and output, open gaps, and a one-page checklist. Do not chain shell commands with `&&`, `;`, or a pipe. The parent reviews the rendered page and one stateful journey before authorizing your next page.

## Prompt for the independent final review

> Run this independent review with model **gpt-6-sol**. Use the current approved 28-route clickthrough, native task list, project guide, callout ledger, current Android and Pi source, and the actual installed APK as the review corpus. Do not edit the reviewed work and do not spawn sub-agents. Render the current clickthrough into dated reference captures; reject screenshots whose source revision differs. For each of the 28 routes, inspect whole-frame screenshots in light/dark and standard/large text, then exercise its buttons, navigation, persistence, loading/error/offline state, and cross-page transition. Check every shared pattern in the 14-item list and use the `$ui` suite for visual and categorical review. Compare live data and typed share inputs with their real service contracts. Run the Pi updater from an older installed code and verify package version and retained settings. Run each open owner callout and record its result. Report numbered defects with absolute file:line and screenshot or runtime evidence; distinguish mock-only behavior from native behavior. Produce a PASS/FAIL/UNRUN matrix and name every untested physical-phone, HDMI, drive, and external-provider limit. Write the full report to **[absolute output path]** before returning. Stop after the review; do not claim product completion.
