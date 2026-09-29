# csync app: structural map and UI component audit

**Date:** 2026-09-29 · author: csync-opus · app build 2.34
**Screenshots:** `/Users/alcatraz627/Code/Claude/csync/.claude/output/20260929-ui-audit/screens/`
(numbered, one per screen/tab/drawer). Captured on emulator-5554.

This document maps how the app is actually organized, inventories the UI
components, and catalogs the structural and mental-model problems so we can fix
them one at a time. It describes the app as built, not as the mock intended.

---

## 1. Navigation architecture (and why it feels arbitrary)

### The app is two bottom-nav shells pretending to be one
There is one bottom navigation bar with five items: Home, Media, Share, Chat,
More. But they do not all live in the same place.

- **Home, Share, Chat, More** are pages inside `MainActivity`, swapped with an
  internal `show(n)` call (MainActivity.java:100-106). No new screen is pushed;
  the same Activity just changes its body.
- **Media** is a whole separate Activity. Tapping the Media nav item runs
  `startActivity(MediaActivity)` and returns false so the nav item does not even
  select (MainActivity.java:103). `MediaActivity` then draws its **own** bottom
  nav bar that looks identical.
- **Camera, Tools, Settings** are also `show(n)` pages inside MainActivity
  (indexes 5, 3, 4), reached from the More page.
- **Notes and Search are separate Activities again** (`NotesActivity`,
  `SearchActivity`), reached from More and from the Home search icon.

So the same five-icon bar is sometimes MainActivity changing its body and
sometimes a different Activity with a copy of the bar. Media, Notes, and Search
break the model. This is the root cause of most of the navigation and
breadcrumb problems below.

### Back button is hand-written per page, not a real stack
`onBackPressed` (MainActivity.java:481-492) is a chain of special cases: if on
More with a detail open, close the detail; if on Settings with a detail, close
it; if on Tools with a detail, close it; if on Camera, ask the camera controller
to close a child page; if on Tools or Settings, go to More; else default. Because
the pages are not a real navigation stack, back has to be simulated, and it does
not always match how you got there. Crossing into MediaActivity, NotesActivity,
or SearchActivity uses the real Activity back stack instead, so back behaves
differently on those screens than on the show() pages.

### Breadcrumbs are imposed, not derived
Every screen paints a breadcrumb in its top bar (`kit_page_top`), for example
`Home / Tools / Process` (screen 61) or `Home / Settings` (screens 33, 54). The
crumb is passed in by hand at each call site, it is not computed from how you
actually navigated. Consequences:
- Tools lives **under More**, but its crumb says `Home / Tools`, skipping More.
  So the crumb claims a hierarchy the app does not have.
- The crumb root is always `Home` even when you arrived from a different tab.
- Tapping a crumb does not reliably retrace the path, because the path was never
  real. The crumb is decoration that asserts a structure the navigation does not
  implement. This is exactly the "externally imposed rather than reflective"
  feeling.

---

## 2. Screen inventory

Grouped by shell. Filenames are in the `screens/` folder.

**MainActivity pages**
- `01-home` Home (hub hero, devices, pick-up, capabilities).
- `10-share-compose` Share, compose mode. `11-share-inbox` Share, inbox mode
  (a top-right toggle swaps the two, another one-control-two-modes pattern).
- `20-chat-all` Chat list, All filter. `21` Favorites, `22` Archived, `23` Tools
  filters (same screen, four filter chips). `24-chat-conversation` a thread.
  `25-chat-model-drawer` the model and effort sheet. `26-chat-attach-drawer`
  the attach sheet.
- `30-more` the More index (Areas: Pi camera, Tools, Settings; Reference:
  Assistant capabilities, Pi Notes, Help).
- `31-camera` Pi camera (show(5)). `32-tools` Tools index (show(3)).
  `33-settings` Settings index (show(4)).
- `34-assistant-capabilities`, `36-help` reference pages.

**Tools sub-pages (all show() detail states)**
- `60-tools-power-detail` power health. `61-tools-process-monitor` process
  monitor. `62-tools-widgets` widgets and quick actions.

**Settings sub-details (bottom sheets, not pages)**
- `54-settings-device-detail` the Raspberry Pi row opens a **sheet** with Media
  and screen / Camera / Assistant settings / Connection details. `63` Tailscale,
  `64` provider and model, `65` appearance.

**MediaActivity (separate Activity, own bottom nav)**
- `40-media-files` Files tab. `41-media-videos` Videos. `42-media-history`
  History. `43-media-access` Access. `44-media-source-drawer` the add-source
  sheet. `45-media-resume-sheet` the resume choice sheet.
- `51-media-player` the phone fullscreen video player (lands in landscape).

**Separate activities**
- `35-notes` Notes (NotesActivity). `50-search` Search (SearchActivity).
- `52-camera-captures` captures.

**Player surfaces (there are four)**
- Phone fullscreen landscape video (`51`).
- Pi-screen full player (portrait: poster, transport, Volume/Speed/Rotate/Loop
  tiles), seen earlier this session.
- Mini-player docked bar (bottom of any screen during phone playback), seen on
  `61`.
- Mini-player expanded half-panel (title, transport, Volume/Speed/Full player),
  captured while playing.

---

## 3. Component inventory

### Shared building blocks (the intended kit)
- `kit_page_top` top bar with breadcrumb plus optional action icons.
- `kit_section_head` a collapsible section label: coral icon, label, chevron.
- `kit_row` a list row: leading icon tile, title, subtitle, trailing chevron or
  status. The workhorse.
- `kit_area_card` the 2-up capability tile: icon, title, status dot, subtitle.
- `Kit.sheet` a bottom sheet, used for pickers, menus, and some details.
- `Kit.Pill` new, hero only.
- Home hero new, Home only.

### The same job done more than one way (the real problem)
- **List rows exist in at least three parallel styles:** `kit_row` (Media,
  Chat, Home pick-up), `CsyncMoreRow` / `CsyncMoreNavRow` (More, Tools,
  Settings rows: screens 30, 32, 33), and `kit_area_card` (Home capability
  grid). Three components render "an icon, a title, a subtitle, and a tap
  target." They differ in height, icon treatment, and divider style, so the app
  looks subtly different screen to screen for no reason.
- **Section labels have several styles:** `Kit.Text.Section`,
  `CsyncAppearanceHeading`, and inline hardcoded TextViews. Casing and tracking
  were inconsistent until this session; the underlying styles are still
  duplicated.
- **Detail navigation is both a page and a sheet:** Tools details are full
  pages (60, 61, 62); Settings details are bottom sheets (54, 63, 64, 65); Media
  file and source details are sheets (44, 45). "Open the detail of X" has no one
  answer.
- **Stat tiles are their own pattern with placeholder values:** Process monitor
  and Tools show cards whose value is an em-dash and whose status reads "live
  sample needed" or "planned" (screen 61). These are the placeholder-underscore
  tell in a different costume, shipped as real UI.
- **Model list uses one identical icon for every row** (screen 25): every Gemini
  model has the same coral gauge glyph, so the icon column carries no
  information.
- **Two playback targets, four player UIs, no clear signal** (section 2). The
  same Resume action can play on the phone in-app or cast to the Pi screen, and
  the user cannot tell which they are about to get. Confirmed live: resuming a
  Pi USB item played it fullscreen on the phone, not on the Pi.

---

## 4. Structural and mental-model problems, ranked

1. **Two shells wearing one nav bar.** Media (and Notes, Search) are separate
   Activities with a duplicated bottom bar, while Home, Share, Chat, More,
   Camera, Tools, Settings are pages in one Activity. The user cannot build a
   stable mental model of "where am I" because the same bar means two different
   things. Fix direction: pick one model. Either everything is a destination in
   one nav graph, or the bottom bar is only ever top-level and details always
   push. Do not mix.
2. **Breadcrumbs assert a hierarchy the app does not implement.** They skip More,
   always root at Home, and are not tap-to-retrace. Fix direction: derive the
   crumb from the real back stack, or drop it and rely on one clear back
   affordance. A crumb that lies is worse than none.
3. **Back button is simulated and inconsistent.** show() pages need hand-coded
   back handling; Activities use the real stack. Same gesture, different
   behavior by screen. Fix direction follows from problem 1.
4. **Detail is sometimes a page, sometimes a sheet.** No rule. Fix direction:
   choose one (likely: quick settings and pickers are sheets, full sub-screens
   are pages) and apply it everywhere.
5. **Multiple row components for one concept.** kit_row vs CsyncMoreRow vs
   kit_area_card. Fix direction: one row component with variants, delete the
   others.
6. **Four player UIs and a hidden play target.** Fix direction: one player
   surface with a visible, switchable target (phone vs Pi screen), one mini
   player, one full player.
7. **Placeholder values shipped as UI.** Em-dash stat tiles, "live sample
   needed", "planned". Fix direction: hide a tile with no data, or show a real
   empty state, never a dash.
8. **Two-mode screens via a hidden toggle.** Share compose vs inbox, and the
   Media source sheet, hide a second mode behind a small top-right control. Fix
   direction: make the mode switch obvious or split the screens.

---

## 5. How to use this

Each numbered problem in section 4 is a work item. The screenshots in `screens/`
are the evidence. Suggested order: fix 1 and 2 first (they define the skeleton
everything else hangs on), then 4 and 5 (collapse the duplicated components),
then 6, 7, 8 (per-surface cleanups). The visual redesign from earlier today
(hub hero, warm tokens, sentence-case labels) sits on top of this skeleton and
does not depend on it, so structural fixes and visual fixes can proceed in
parallel.
