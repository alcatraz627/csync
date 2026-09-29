# csync UI audit and rebuild groundwork (2026-09-29)

This folder is the consolidated research for rebuilding the csync Android app's
UI properly. It exists so the next session (owner plans a fable) can build ONE
full HTML mock of every screen against a corrected design language, then rebuild
the native app to match, without re-doing the investigation.

## Read in this order

1. `combined-backlog.md` is the deduplicated, prioritized issue list (31 items in
   5 tiers). This is the work list. Everything else is evidence for it.
2. `structural-map.md` covers how the app's navigation is actually built and why
   it feels arbitrary: two nav shells, imposed breadcrumbs, simulated back.
3. `ui-issue-report.md` is the external-designer UI audit of all 35 screenshots:
   17 ranked per-screen defects (purple/orange split, five segmented-control
   styles, dead tiles, clipping, and more).
4. `notes-inventory-and-gaps.md` shows what is already written down about the app
   versus what is only in a transcript or contradicts another doc. It answers
   "what am I not asking that already exists."
5. `codex-trail.md` is the forensic triage of the prior effort: what Codex and the
   Claude recon session did, what failed and why, and what is salvageable.
6. `screens/` holds 35 numbered screenshots, one per screen, tab, drawer, sheet,
   and detail state, on build 2.34.

Earlier this session for context: `../20260929-ui-diagnostic.md` (why the old UI
read as generic) and `../20260929-home-redesign/home.html` (the approved Home
direction, already shipped natively in 2.34).

## State of the project, one place (this did not exist before)

- Current build is **2.34** (versionCode 36), installed on emulator-5554 and
  deployed to the Pi. Served APK sha256
  `b1eee321de00e3e788ac83955088a351e67307aa6bd5c5abdf627d8e6400b21e`. Install on
  the phone via More, Tools & diagnostics, Update csync from Pi.
- Repos: `/Users/alcatraz627/Code/csync-hub` (Android, on main, latest commit
  `98231c9`, pushed). `/Users/alcatraz627/Code/Claude/csync` (services, on main).
- What 2.34 already fixed this session: the Home hub hero, a warmer dark palette
  app-wide, sentence-case section labels app-wide (the ALL-CAPS tell is gone), a
  branded app icon and splash, and the undervoltage warning coloured amber vs
  green instead of blending into the coral.
- The prior effort, corrected: two agents were involved, not one. Codex built the
  28-screen HTML mock, the design docs, and a drifting native port that never
  reached visual parity. A separate Claude session then ran the recon and the
  `Kit.java` shared-style rebuild that fixed the root cause, a 2728-line God
  Activity with no shared style layer. The "80 percent of weekly budget" figure
  is the owner's framing and is not in any doc. Full detail in `codex-trail.md`.

## The backbone you may not be asking about but already have

- `../20260928-recon/requirements-ledger.md` is the master capture of your asks:
  228 atomic requirements grouped by screen, each with your own quote, a source
  line, a kind, and a priority. This is the strongest restart asset, and the mock
  should be built to satisfy it.
- `../../callouts.jsonl` holds 82 of your review call-outs with the check for
  each. Its `status` field is stale (all read open). The last recheck is the
  truth (64 pass, 12 fail, 6 never rechecked).
- The 28-screen HTML clickthrough mock in
  `../../../assets/android-ui-clickthrough/` is a coherent design worth keeping as
  the base for the next full mock, per `codex-trail.md`.

## The most urgent non-UI item

The requirements ledger and `callouts.jsonl` are UNTRACKED files. If the working
tree is lost, the record of everything you asked for goes with it. They should be
committed. See `combined-backlog.md` item 29.

## Plan for next session (fable)

Build ONE full HTML mock of every screen, on a corrected design-system doc and a
decided navigation model (backlog Tier 0 and items 26 to 28 first). Then rebuild
the native app to match, screen by screen, verified on the emulator. The mock is
the contract, the ledger is what it must satisfy, the combined backlog is the
order of work.
