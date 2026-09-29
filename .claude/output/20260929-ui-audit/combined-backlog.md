# csync app: combined issue backlog

**Date:** 2026-09-29 · build 2.34 · author: csync-opus
Merges the structural map, the external UI audit, and the notes gap analysis
into one deduplicated, prioritized list. Sources are tagged: [struct] structural
map, [ui] UI audit, [gap] notes inventory. Screenshot evidence lives in
`screens/`. This is the backlog the next full-mock and rebuild works from.

Two items from the UI audit are NOT bugs and are excluded from the list:
"ReplyReply" (a test message csync-opus typed with a doubled word) and "bold did
not render" (a misread, bold renders, verified live). Everything below is real.

---

## Tier 0. Decide the skeleton first (everything else hangs on these)

1. **One navigation model, not two.** [struct] Media, Notes, and Search are
   separate Activities each with their own copy of the bottom nav; Home, Share,
   Chat, More, Camera, Tools, Settings are pages inside one Activity. The same
   five-icon bar means two different things. Pick one model and apply it. This is
   the root of the back-button and breadcrumb problems.
2. **Breadcrumbs must reflect real structure or be dropped.** [struct] They skip
   More (Tools shows `Home / Tools`), always root at Home, and are hand-passed at
   each call site, not derived. Either compute from the real back stack or remove
   them.
3. **One back behavior.** [struct] Back is hand-coded per page for show() pages
   and uses the real stack for Activities, so the gesture differs by screen.
   Falls out of item 1.

## Tier 1. Collapse the duplicated components (one concept, one component)

4. **One row component.** [struct] `kit_row`, `CsyncMoreRow`/`CsyncMoreNavRow`,
   and `kit_area_card` all render icon + title + subtitle + tap. Unify to one
   with variants, delete the others.
5. **One segmented selector.** [ui] The pick-one control is drawn five or six
   different ways: Chat (orange text, no fill), Media (solid orange fill), Search
   (orange text), Appearance (grey fill), Assistant, and the Note editor
   Preview/Rich/Plain. Standardize one spec everywhere. Screens 20, 40, 50, 55,
   64, 65.
6. **One detail pattern.** [struct][ui] Detail is a full page on Tools (60, 61,
   62) but a bottom sheet on Settings (54, 63, 64, 65) and Media (44, 45). Pick a
   rule (for example: quick pickers are sheets, full sub-screens are pages).
7. **One player.** [struct][ui] There are four player surfaces (phone fullscreen
   landscape, Pi-screen full player, mini bar, mini half-panel) and the play
   TARGET is hidden. The same Resume plays on the phone in-app or casts to the Pi
   and the user cannot tell which (owner confirmed: it played on the phone).
   One player surface, one mini player, a visible switchable target. Screens 45,
   51, 52, 53.

## Tier 2. Per-screen defects that read as broken

8. **Placeholder values shipped as UI.** [struct][ui] Process monitor shows four
   big tiles with a bare em-dash value and "live sample needed" / "planned"
   captions, three of them gated on Shizuku which is not running. Lead with the
   Shizuku state; never render a dash as a value. Screen 61.
9. **Dead rectangles, no skeleton.** [ui] Camera preview (31) and the player (51)
   show large empty dark frames with only small grey text and no spinner or
   shimmer, reading as a crash. Add a progress or skeleton state and a timeout to
   an explicit retry.
10. **Orange vs purple theme split.** [ui] Settings Provider and the thinking
    selector render PURPLE (the Gemini pill, the Medium segment) while the whole
    app is orange. A Material default is bleeding through. Retheme to the accent.
    Screens 64, 25.
11. **Last row clips at the fold app-wide.** [ui] Tools, Camera, Assistant
    capabilities, Chat tools, and Media all shear their final row against the
    bottom nav. Add bottom content padding equal to the nav height on every
    scroll view. Screens 23, 31, 32, 34, 41.
12. **Media list repeats the path and clips long names.** [ui] Rows print the
    filename, then the full path that repeats the same filename, wrapping to three
    lines; the last row is sheared. Show the folder without re-appending the name,
    cap to one line (no ellipsis, per the owner's no-"..." rule, so middle-clip or
    fade), give the list a definite scroll height. Screen 41.
13. **Mini-player bar blends into the nav.** [ui] The now-playing bar sits flush
    on the nav with a hard-truncated title and small icon-only transport. Add a
    divider or elevation, middle-clip the title, verify 48dp targets. Screens 52,
    53.
14. **Send to an offline device is fully enabled with no warning.** [ui] Compose
    targets "xiaomi-m2101k6p" which the picker marks Offline; Send is bright and
    ready. Disable or warn when the recipient is offline. Screens 10, 11.
15. **Accent-on-dark contrast is borderline.** [ui] Hero outline chips, disabled
    buttons rendered as dim-orange, and secondary grey text sit near or under WCAG
    AA. Raise weights and lift secondary grey. Screens 01, 60, 41, 31.
16. **Bottom-sheet scrim too light.** [ui] Background content stays clearly
    readable behind sheets, so modals feel like they float on live content.
    Darken the scrim. Screens 25, 26, 54, 60.
17. **Same tools named two ways.** [ui] Assistant capabilities vs Chat tools:
    "Pi health" vs "Home health", "Your devices" vs "List peers", "Send to a
    device" vs "Send to peer", "Pi commands" vs "Run command", and different card
    styles. One name and one style per tool. Screens 23, 34.
18. **Wrong empty-state copy.** [ui] Favorites shows "No matches." (implies a
    search) instead of "No favorites yet"; empty states are bare left grey text.
    Context-correct copy plus a centered icon. Screens 21, 22.
19. **Ambiguous Home section chevrons.** [ui] "Pick up" and "Do something" carry a
    down-chevron that reads as collapsible but is not obviously interactive.
    Clarify or remove. Screen 01.
20. **Unlabeled per-screen top-right icons.** [ui] Different corner icons per
    screen (search, phone, download-tray, device-switch, gallery) with no labels.
    Standardize the set and meanings. Screens 01, 10, 31, 40.
21. **Note inline code hash wraps badly.** [ui] A SHA-256 renders as a two-line
    grey highlight split mid-hash. Use a scrollable mono block. Screen 55.

## Tier 3. Known bugs and unbuilt (from the checkpoint and status file)

22. **Title fallback bug.** [gap] YouTube resume shows `YouTube i <id>` instead of
    the saved title (`MediaActivity.java:491`, `:409`). Not in any backlog.
23. **Half-height mini player** built and installed but render never confirmed;
    **MediaSession lock-screen notification** (P-20) deferred.
24. **Hardware-blocked and only in a checkpoint:** casting reliability, full and
    mini player parity, Pi-screen video are blocked by Pi undervoltage
    (`throttled=0x50005`, mpv "Failed to create KMS", USB drives disconnected).
    Needs a proper PSU or powered hub. Not marked blocked in the ledger or spec.
25. **Unbuilt features per the status file:** cover gallery with per-image framing
    (C-02..06), Instagram save/play (SH-09), fork with model settings (CH-04),
    Sharesheet circular routing (call-out 28), native Cast receiver (O-08),
    widgets beyond xkcd.

## Tier 4. Documentation debt (this is why the app drifts)

26. **No single "what the app is now" doc.** [gap] Version is scattered: final
    spec says 2.29, checkpoint says 2.33, audit says 2.34. Create one current-state
    doc (version, staged Pi APK hash, open list).
27. **The design-system doc predates every round 5 decision.** [gap]
    `docs/android-ui-system.md` has no breadcrumb rule, no drawer rule, no
    no-ellipsis rule, still lists the removed Gold accent, still calls Search a
    proposal. It is the file a new reader opens for the design language, and it is
    wrong. This directly enabled the drift.
28. **READMEs and the design brief are stale.** [gap] Both still say five surfaces
    Home/Share/Chat/Tools/Settings and never mention Media, Notes, Pins, Camera,
    or the Pi update flow. AGENTS.md still says "preserve six-tab navigation",
    which the shipped five-tab nav violates.
29. **The owner's asks are untracked and could be lost.** [gap] The
    requirements-ledger (228 asks) and `callouts.jsonl` (82 call-outs) are
    untracked files in `.claude/output`. If the working tree is lost, the record
    of what you asked for goes with it. Commit them.
30. **Call-out status is meaningless.** [gap] All 82 rows read `open` even when
    the last recheck passed. Fold the last recheck into a real status; 6 call-outs
    were never rechecked at all.
31. **Contradictions across docs** [gap]: accent set (three answers), tab count
    (five vs six), route count (28 vs 29), Search pick (B vs from-scratch), Home
    hierarchy naming. Each is resolved in the ledger only, not cross-referenced.

---

## Recommended fix order
Tier 0 (skeleton) and Tier 4 items 26 to 28 first, because the full HTML mock the
owner wants next should be built on a corrected design-system doc and a decided
nav model, not on the stale ones. Then Tier 1 (component consolidation) drives
most of the mock. Tier 2 is per-screen polish once the components exist. Tier 3
is feature and hardware work that is mostly independent. Commit the ledger and
callouts (item 29) today regardless.
