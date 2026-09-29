# csync Android: recon findings and working order

Written 2026-09-28 after three read-only recon passes. Inputs sit beside this file:
`requirements-ledger.md` (228 owner asks), `mock-audit.md` (clickthrough, 77 shots),
`native-audit.md` (installed 2.32 on emulator-5554, 20 screens).

## What the recon found

**The ledger.** 228 atomic asks, every one quoting the owner. Chat (40), Global shell
(27), Player (26) and Settings/Appearance (20) carry most of the weight. 4 later
messages override earlier ones; 5 asks are genuinely open (listed at the end).

**The mock is close to done.** Most 09-27 feedback items pass, and it has a real
shared primitive layer (`row()`, `tabs()`, `pageTop()`, app.js:60-238). Defects: the
Conversations tab strip overlaps at large text (own override, styles.css:45-47), the
full Player shows a duplicate mini row, "This phone" uses the Home icon, the Home
title was never made smaller, and there is dead code from earlier rounds (`.hero`
CSS, unused rotate/loop handlers).

**The native app is structurally ported but not faithful.** Every main screen
exists on 2.32 and most show live Pi data with no crashes. The sub-agent graded
13 of 20 as MATCH; the parent's own side-by-side read of Home, Player and Chat
says CLOSE at best, and that gap is what the owner sees:

- (Corrected 2026-09-29: type scale is NOT larger. Measured as a fraction of
  screen width the heading is 5.6% mock vs 5.4% native, a device row 15% vs 14.6%;
  page_home_v2.xml sets 22sp/14sp, matching the mock's px. The earlier claim came
  from comparing a 390px mock image to a 1080px device image.)
- Icon identities collide: Chat and Notes share one glyph, Media and Pi display
  share another; the 5th nav tab shows sliders instead of the menu icon.
- Home capability cards lack the status dot subtitle; device rows lack icon tiles.
- The Player seek bar uses the default Material purple, not the theme color.
- Chat's composer has a chevron where the attach "+" belongs; bubbles carry a
  stray chevron; the breadcrumb icon differs from the mock.

**Why it drifted.** `MainActivity.java` is 2,728 lines and builds most views in
Java; there is no `styles.xml` and no shared component layer. Each page restyles
itself, so a cross-app fix has to be repeated per page, and it was not. Five dead
pre-`_v2` layouts remain.

## Working order

1. **Ledger status sweep.** Mark each of the 228 rows mock PASS/FAIL and native
   PASS/FAIL/UNBUILT, from screenshots and code. This is the checklist for the rest.
2. **Mock fix pass, once.** The 10 fixes from `mock-audit.md` plus the Home title
   size. No new variant rounds.
3. **Native kit.** One theme and styles layer (type scale matched to the mock,
   color tokens, spacing), plus shared components: top bar with breadcrumb,
   bottom nav, bottom sheet, list row, section header, chip/tab strip, icon
   button, status dot, one icon set with one glyph per identity. Material
   components where they exist. Built and screenshotted once.
4. **Page ports onto the kit.** Home, Media + Player, Chat, Share, Camera,
   Notes/Pins, Settings/More, Search/Tools. Each page is done when its emulator
   screenshot sits beside the mock route and its ledger rows are ticked. Delete
   the dead layouts as each page moves.
5. **Unbuilt features** from the ledger: Android share-target routing, notification
   player, cover gallery, chat attach drawer and model picker, fork, Pi notes CRUD
   tools, and whatever step 1 shows as UNBUILT.
6. **Review and ship.** One adversarial pass against the ledger, 2.33 to the Pi,
   the in-app update proven on the emulator, the two Pi Notes rewritten short.

## Status 2026-09-29 (steps 1 to 3 done, step 4 started)

- **Step 1.** `ledger-status.md` marks all 228 asks for mock and app (regenerate with
  `merge_ledger.py`). Mock: 171 pass, 2 fail, 9 unbuilt, 46 n/a. App: 103 pass,
  64 fail (unconfirmed counted as fail), 21 unbuilt, 40 n/a.
- **Step 2.** Mock fixed in one pass: the audit's 10 items plus the Home title
  size and tap-to-toggle Rotate/Loop. Backup of the pre-fix mock is in the session
  scratchpad (clickthrough-backup-20260929).
- **Step 3.** App shared layer: `Kit.java`, `res/values/kit.xml`, `res/layout/kit_*.xml`,
  66 `csi_*` icons generated from the mock by `icons_to_vectors.py`.
- **Step 4 (partial).** Home, Media (Files, History, Access, drawers), Player and
  Chat (list, conversation, + drawer, message tap) rebuilt on the kit. Pairs in
  `side-by-side/`. Share, Camera, Notes, Settings, More, Search and Tools are not.
- **Known gaps on the rebuilt pages:** Player idle state keeps the last title where
  the mock says "No media selected"; Player tiles show label and value on one line;
  Favorite is still disabled; Rotate/Loop/Volume/Speed drawers are code-verified only
  (Pi idle during the run); the half-height mini player, the media notification,
  chat image and file attach, and the explicit model Save button are not built.
- **Not done:** nothing committed; 2.33 not built as a release or staged to the Pi.

## Open asks needing an owner ruling (from the ledger)

1. CH-17: favorite/archive placement, owner wrote "idk decide".
2. Whether Devices and Pick up keep the round-4 collapse behaviour on Home.
3. P-19: multiple drawers, owner asked to be told if it is a problem.
4. PI-06: should the Pi agent edit its own code.
5. O-07/O-08: VLC control and native Cast depend on a hardware choice.
