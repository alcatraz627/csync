# csync Android UI audit

Reviewer: senior product designer, external. I did not build this app.
Scope: UI-only, per-screen and cross-screen. Navigation architecture is out of scope by request.
Evidence: the 35 PNGs in `/Users/alcatraz627/Code/Claude/csync/.claude/output/20260929-ui-audit/screens/`.

## Verdict up front

The app has a real, coherent visual language when it works: one accent orange, big bold screen titles, rounded cards, a consistent bottom nav with a pill highlight. That skeleton is good. The damage is in the details that a build passes but a human sees instantly: a duplicated word baked into a chat message, stat tiles that render a bare dash instead of a number, a camera and a player that show large dead black rectangles with no skeleton, one settings area themed purple while the whole rest of the app is orange, and the same "segmented selector" concept drawn five different ways. Several list screens clip their last row at the fold instead of scrolling cleanly. Fix the placeholder-as-UI cases and the orange/purple split first; those are the ones that read as broken rather than plain.

Note on the capture set: four files do not show the screen their name promises. `42-media-history.png` and `43-media-access.png` are pixel-identical to `41-media-videos.png` (the Videos tab), and `44-media-source-drawer.png` and `45-media-resume-sheet.png` are identical to `10-share-compose.png` (the Share compose screen). So the History tab, the Access tab, the media source drawer, and the resume sheet were not actually captured and I cannot audit them. Either those surfaces failed to open or the capture grabbed the wrong frame. Worth confirming those four routes render at all.

---

## Findings, ranked by user-facing damage

### 1. Chat: the user's own message is duplicated in-place ("ReplyReply")
Evidence: `24-chat-conversation.png`, `26-chat-attach-drawer.png`.
The outbound user bubble reads "ReplyReply with one bold word a two item bullet list and a link to example.com". The first word "Reply" is printed twice with no space. This is a text-echo or state-append bug rendering into the message itself, and it is the single most broken-looking thing in the set because it is content, not chrome. Anyone reading their own sent message sees the app corrupted their words.
Fix: find the send path that concatenates the prompt (likely an optimistic-echo appended to the streamed request). De-duplicate before render. Add a snapshot test that sends "Reply X" and asserts the bubble equals the input exactly.

### 2. Chat response formatting did not honor the request, and "Ready" reads as leftover status
Evidence: `24-chat-conversation.png`.
The prompt asked for "one bold word, a two item bullet list, and a link". The reply renders a large heading "Ready", then "First item / Second item", then the link. No word is bold anywhere, and "Ready" looks like an app status label that leaked into the message body rather than model content. Combined with two stacked "Thinking" collapsibles and a separate "Available skills / 21 available skills" expander at the top, the assistant turn is hard to read as a single answer.
Fix: confirm markdown bold actually renders in the chat markdown component (test `**word**`). Verify "Ready" is model content and not an injected status string sitting inside the bubble; if it is a status, move it out of the message container or drop it once streaming completes.

### 3. Process monitor: stat tiles are empty placeholders (icon + bare dash)
Evidence: `61-tools-process-monitor.png`.
Four large cards (Available, CPU, Thermal, Swap pressure) each show only a slider icon and a lone "—" where a number belongs, with captions "live sample needed" or "planned". This is the textbook "dead tile" defect: big cards, an icon column that carries no information, and a placeholder value shown as if it were real UI. Three of four also depend on Shizuku, which the panel below says is not running. The screen presents four broken gauges before telling you why they are empty.
Fix: when Shizuku is down, do not render the metric grid at all; lead with the "Shizuku is not running / start via ADB" state as the primary content. If you keep the tiles, replace the dash with a proper empty treatment (skeleton shimmer while sampling, or a muted "No sample" with a single Refresh affordance), and drop the redundant per-tile slider icon that says nothing.

### 4. Camera and Player show large dead black rectangles with no skeleton
Evidence: `31-camera.png`, `51-media-player.png`.
The camera preview is a roughly 1080x600 empty dark-grey rounded rectangle with "Connecting to Pi camera" in grey underneath and no spinner or shimmer. The player (`51`) is a full black landscape frame with only "This phone · loading" in small grey at the bottom and the filename wrapping to two lines. Both read as a crash or a frozen stream rather than a connecting state.
Fix: put a centered progress indicator or a skeleton shimmer inside the preview and the player frame during connect/load, plus a timeout to an explicit "Could not reach Pi camera / retry" state. Never leave a large empty container as the only feedback.

### 5. Settings > Provider and Thinking are themed PURPLE while the whole app is orange
Evidence: `64-settings-provider.png` (Gemini toggle and "Medium" thinking segment are purple), and the same purple in `25-chat-model-drawer.png` context. Every other screen uses orange as the single accent.
This is the most jarring cross-screen inconsistency. The selected "Gemini" pill and the selected "Medium" thinking segment are filled with a desaturated purple that appears nowhere else, which makes this one panel look like it belongs to a different app or an unthemed Material default that never got the brand color.
Fix: retheme the provider segmented control and the thinking selector to the app accent (orange selected fill or orange text, matching whichever pattern you standardize on in finding 6). Confirm no `colorPrimary`/`colorSecondary` default is bleeding through on these Material toggles.

### 6. The same "segmented selector" concept is drawn five different ways
Evidence, in order of how much they clash:
- Chat filter `20-chat-all.png`: pill container, icon+label, active = orange text, no fill.
- Media filter `40-media-files.png` / `41`: active = solid orange filled chip with white-on-orange.
- Search filter `50-search.png`: active = orange text, no fill (like chat).
- Appearance `65-settings-appearance.png`: Theme and Text size are segmented with a grey filled active segment and orange text.
- Assistant `64` and Note editor `55-note-detail.png` (Preview/Rich/Plain): yet another fill/tint.
A user moving between Media, Chat, Search, and Settings sees the "pick one of a row" control change shape, fill, and color each time.
Fix: pick one segmented-control spec (recommend: rounded track, selected segment gets an orange-tinted fill with orange label, unselected gets muted grey label) and apply it to all of these. This single normalization removes most of the "different screens feel like different apps" impression.

### 7. Media list: long filenames clip the last row at the fold and repeat the path
Evidence: `41-media-videos.png`.
Every row prints the display name ("Adjustable Bend.wmv") and then the full path which repeats the same filename again ("Pi USB · files/Macrame/TIAT/Adjustable_Bend.wmv"), wrapping to three lines. The last visible row, "Blackadder.S00E02.Blackadders.Ch..." is hard-clipped mid-title at the bottom edge with its second line sheared off, rather than scrolling cleanly. The trailing three-line glyph on each row reads as a drag handle but is a menu.
Fix: show the folder path without re-appending the filename (e.g. secondary line = "Pi USB · files/Macrame/TIAT"), cap it to one line with middle-ellipsis, and make sure the list has a definite scroll height so the final row is fully drawn. Swap the ambiguous three-line handle for a standard vertical-dots overflow icon.

### 8. Several list screens clip their final row at the fold instead of ending cleanly
Evidence: `32-tools.png` ("App updates / Use the Pi connection to install a newer csync" sheared), `31-camera.png` ("Pi display / Open screen and playback controls" sheared), `34-assistant-capabilities.png` ("Run command ... May be disabled by the owner; if" cut mid-sentence), `23-chat-tools.png` ("Saved skills" cut).
The content ends in a half-rendered line pressed against the bottom nav, which reads as a rendering fault. It is really a height/scroll-inset problem where the scroll area does not reserve room for the bottom nav.
Fix: add bottom content padding equal to the nav bar height (plus a small margin) to every scrollable screen so the last item clears the nav, and rely on the scroll fade rather than a hard clip.

### 9. Mini-player bar stacks on the nav and truncates the title hard
Evidence: `52-camera-captures.png`, `53-settings-top.png`.
A now-playing bar ("THIS PHONE · PLAYING / Blackadder.S00E02.Blackad") sits directly above the bottom nav. The title is cut with a hard truncation, the four transport icons (pause/stop/volume/speed) are small icon-only controls, and on `52` the bar overlaps the last capture row. Two stacked bars plus the status bar eat a lot of vertical space with no visual separation between the mini-player and the nav.
Fix: give the mini-player a clear top divider or elevation so it does not blend into the nav, use middle-ellipsis on the title, ensure the list above reserves space for it (same inset fix as finding 8), and confirm the transport icons meet 48dp.

### 10. Sending to an offline device is fully enabled with no warning
Evidence: `10-share-compose.png` + `11-share-inbox.png`.
Compose header says "Send to xiaomi-m2101k6p", but in the picker that device is marked "Offline", and Home (`01`) itself said "Mac offline · choose a device". The orange "Send text" button is fully enabled with no indication the current recipient is unreachable, so the primary action looks ready when the message will not land.
Fix: when the selected recipient is offline, either disable Send with an inline "recipient offline" note, or show a confirm. At minimum surface the recipient's online state next to the header, not only inside the picker.

### 11. Accent-on-dark contrast is borderline on hub chips, disabled buttons, and secondary text
Evidence: `01-home.png` (the Media/Assistant/Camera/Screen chips are thin orange outline with orange text on a near-black gradient card; "Mac, sharing receiver offline / Set up" is dim grey), `60-tools-power-detail.png` (the "Recheck" button behind the sheet is dim-orange text on dim-orange fill, clearly below contrast), path strings in `41`, "Preview live while this tab is open" in `31`.
Several orange-on-dark and grey-on-black pairings look under the WCAG AA line for their size.
Fix: raise the outline-chip label to full-weight orange or give the chips a subtle filled background; bump secondary grey one or two steps lighter; and make sure disabled buttons use a distinct, still-legible disabled token rather than a dimmed accent that reads as an active-but-faint control.

### 12. Bottom-sheet scrim is too light; background content bleeds through
Evidence: `25-chat-model-drawer.png`, `26-chat-attach-drawer.png`, `54-settings-device-detail.png`, `60-tools-power-detail.png`.
When a sheet opens, the content behind it stays fairly bright and readable (the chat's "Available skills / Thinking / Ready" and the Settings list are clearly legible behind the sheet). The weak scrim makes the modal feel like it is floating on top of live content rather than taking focus.
Fix: darken the modal scrim (raise the black overlay opacity) so the sheet clearly owns the foreground.

### 13. Same assistant capabilities named two different ways on two screens
Evidence: `23-chat-tools.png` vs `34-assistant-capabilities.png`.
The same underlying tools are labeled differently: "Pi health" vs "Home health", "Your devices" vs "List peers", "Send to a device" vs "Send to peer", "Pi commands" vs "Run command". The two screens also use different card styles. A user reading both will not know these are the same capabilities.
Fix: pick one name per tool and one card style, and reuse across both surfaces.

### 14. Empty-state copy is wrong for the context
Evidence: `21-chat-favorites.png` shows "No matches." under Favorites; `22-chat-archived.png` shows "No archived chats."
"No matches" implies an active search filter, but nothing is being searched; the correct empty state for an untouched Favorites tab is "No favorites yet" with a hint on how to favorite a chat. Both empty states are also bare left-aligned grey text with no icon, so they read as an error rather than a clean empty.
Fix: context-correct copy ("No favorite chats yet"), and give empty states a small centered icon plus one line of guidance for visual weight.

### 15. Section headers carry an ambiguous chevron affordance on Home
Evidence: `01-home.png`.
"Pick up where you left off" and "Do something" each have a down-chevron at the right end of the section title, which reads as a collapsible section, an unusual pattern for a home feed and not obviously interactive.
Fix: if the sections collapse, use a clearer disclosure (rotate on state, label it); if they do not, remove the chevron.

### 16. Unlabeled, per-screen top-right icons hurt discoverability
Evidence: top-right actions differ by screen with no labels: Home `01` has a search glass; Share `10` has a phone icon plus a download-tray icon; Media `40` has a search glass plus a device-switch glyph; Camera `31` has a gallery/image icon. Same corner, different meanings, no text.
Fix: standardize the icon set and meanings, and consider a short label or a long-press tooltip for the less obvious ones (the download-tray and device-switch glyphs are not self-evident).

### 17. Note detail: SHA-256 renders as a two-line grey highlight that breaks mid-hash
Evidence: `55-note-detail.png`.
The inline code hash gets a grey highlight background that wraps across two lines and splits the hash awkwardly inside a parenthetical, and the Preview/Rich/Plain control is a sixth variant of the segmented selector.
Fix: render long inline code in a horizontally scrollable or wrap-at-boundary mono block, and fold the segmented control into the finding 6 standard.

---

## Screens that are essentially fine (one line each)

- `30-more.png`: clean list, good icon+title+subtitle rhythm, consistent radii.
- `33-settings.png` / `53-settings-top.png`: well-grouped sections, good hierarchy (the only issue is the purple leaking into the child Provider screen, finding 5).
- `35-notes.png`: clear, good "New note" primary and revision metadata.
- `36-help.png`: readable, correct version footer ("csync 2.33"); a lot of dead space below but acceptable for an about screen.
- `52-camera-captures.png`: good list with size/type metadata; only the mini-player overlap (finding 9) hurts it.
- `62-tools-widgets.png`: clear "Built" vs "Planned" states, consistent rows.
- `63-settings-tailscale.png`: honest form; masked token, sensible Save/Start pairing; "tailnet not up" status shown.
- `65-settings-appearance.png`: good theme/size/color layout; folds into finding 6 only on the segmented style.
- `50-search.png`: solid unified search with type filters and a result count.

## Suggested fix order (highest damage first)

1. Kill the "ReplyReply" duplication (1) and confirm chat markdown renders (2).
2. Replace placeholder-as-UI on Process monitor (3) and add skeletons to Camera/Player (4).
3. Resolve the orange vs purple split (5) and unify the segmented control (6, 17).
4. Fix list clipping and bottom-nav insets everywhere (7, 8, 9).
5. Offline-send guard (10), contrast pass (11), scrim (12), naming/empty-state/copy cleanups (13, 14, 15, 16).
