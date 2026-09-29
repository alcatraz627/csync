# Codex trail: csync Android UI effort, forensic triage

Written 2026-09-29 for a clean restart. Sources read: the final Codex handback
(`_codex-handback-20260928-1252.claude.md`), the 39 dated Codex handbacks at the
repo root, the Claude recon folder
(`/Users/alcatraz627/Code/Claude/csync/.claude/output/20260928-recon/`), the
clickthrough mock source, the variants folder, and the design docs under
`/Users/alcatraz627/Code/Claude/csync/docs/`.

One correction to the framing up front. Two agents worked this, not one. Codex ran
25 to 28 September and produced the mock, the docs, and a native port that kept
missing parity. A separate Claude session ("csync-opus", session csync-57176d0a)
ran a recon on 28 September and a native "kit" rebuild on 29 September, on top of
Codex's work. The recon folder and the kit rebuild are Claude's, and they are the
most reusable assets in the tree. Where this matters for salvage I say who made
what.

## 1. Timeline and scope

The goal never changed: recover every csync conversation input, then make the
native Android app (`/Users/alcatraz627/Code/csync-hub`) match an approved HTML
clickthrough while keeping the real Pi, mesh, assistant, media, camera, notes, and
sharing functions live. The clickthrough is the visual source of truth; the live
services and project guide are the functional source.

Codex worked in numbered UI rounds, captured in the docs:

- Rounds 1 to 3 lived in `/Users/alcatraz627/Code/Claude/csync/assets/android-ui-variants/`
  (a variant explorer with `round1.html`, `variant-screens.js`, `review-system.js`).
  This was A/B/C option shopping per screen and per primitive. The owner's later
  note that "Search A/B/C were cosmetic" is a recorded rejection of this style of
  round.
- Round 4 (`docs/android-ui-round4-reconciliation.md`, 27 Sep) collapsed the
  variant picks into one decision map: 21 screen picks, 9 primitive picks, 9
  composite picks, 14 icon identities. This is where the design actually converged.
- Round 5 (`docs/android-ui-round5-plan.md`, 27 Sep) added 7 routes to reach the
  28-screen clickthrough and wrote the per-surface behavior contract. This is the
  binding spec.
- `docs/android-ui-final-spec.md` (28 Sep) and `docs/android-ui-system.md`
  (26 Sep) hold the visual contract, tokens, primitives, and drift checks.

Cadence is the clearest scope signal. Codex wrote 39 dated handback checkpoints in
four days: 7 on the 25th, 12 on the 26th, 11 on the 27th, 9 on the 28th, roughly
one every one to two waking hours. Each handback re-states goal, changed files,
verified, not-done, next. The volume of near-identical recovery records is itself
the trail of an effort that kept restarting rather than converging.

The final Codex state (28 Sep 12:52): the owner said "halt testing, finalize the
APK, and deploy it." Codex deployed release 2.32 (versionCode 34) to the Pi and
stopped. The whole-app parity goal was left open; both goals were kept open and
uncommitted.

## 2. Delivered vs failed, and the failure pattern

### Delivered

- The clickthrough mock. Coherent, 28 routes, a real shared-primitive layer. This
  is the strongest artifact. Detail in section 3.
- The design doc set: round4 reconciliation, round5 contract, final spec, UI
  system, improvement backlog. These capture the owner's decisions with quotes and
  per-surface acceptance criteria.
- Real backend and service work that does function: assistant provider changes
  (`assist/`), Pi media rotate/loop and Notes-body search (`media/server.py`,
  with 31 passing unit tests), two Pi Notes updated in place with screenshots, and
  the 2.32 APK built, staged to the Pi with a hash-checked backup, and served.
- A materially complete native app that runs without crashes and is wired to live
  Pi data on most screens. The Claude native audit graded 13 of 20 screens MATCH,
  5 CLOSE, 2 FAR, roughly 60 to 70 percent of the built-tier screens having a
  working data-backed counterpart. Appearance (live theme, text size, accent),
  History, Access, the full Player, Chat with real assistant traces, Captures,
  Tools diagnostics, Settings, and Notes are genuinely built, not stubs.

### Failed or never reached

- Visual parity with the mock. This is the recurring failure. Screens exist and
  work, but they do not look like the approved mock. The native audit and the
  recon working-order both grade Home, Player, and Chat as CLOSE at best, and that
  visual gap is exactly what the owner sees.
- Concrete parity defects the recon found: icon identities collide (Chat and Notes
  share one glyph, Media and Pi display share another, the 5th nav tab shows
  sliders instead of a menu icon); Home capability cards lack the status-dot
  subtitle and device rows lack icon tiles; the Player seek bar uses default
  Material purple, not the theme accent; the Chat composer shows a chevron where
  the attach "+" belongs.
- Two structural mismatches, not just cosmetic: Inbox is not a routable screen
  (it is a scrolled section of Compose), and Media Files gates all content behind a
  "Choose a drive" step the mock does not have.
- In-app update proof for 2.32 (owner halted testing), physical-phone rendering,
  and visible Pi HDMI/audio (the Pi is in undervoltage and mpv cannot create a KMS
  surface, so Pi-screen video never renders).
- The two Pi Notes were updated but never curated into the short final form the
  owner asked for.

### Why implementation kept failing

The root cause is architectural, and the recon names it precisely
(`native-audit.md` section 5, `working-order.md` "Why it drifted").
`MainActivity.java` is 2,728 lines and builds most views by hand in Java. There is
no `styles.xml` and no shared component layer. Programmatic view construction is
scattered: 82 hand-rolled `new View`/styling calls in MainActivity, 55 in
NotesActivity, 39 in MediaActivity, 15 in SearchActivity. Because every page
restyles itself, a cross-app visual fix (icon set, type scale, accent binding,
row/card grammar) has to be repeated per page by hand, and Codex never did that
consistently. So each new screen drifted from the mock in the same ways, and
fixing one screen did not fix the next. Five dead pre-`_v2` layout files were also
left behind (353 dead lines). One measurement error compounded the confusion: an
earlier claim that native type scale was "larger" was later corrected (working-
order line 25), it came from comparing a 390px mock image to a 1080px device image.

## 3. The HTML mock: keep it

The clickthrough is a coherent single design, not a pile of variants. Location:
`/Users/alcatraz627/Code/Claude/csync/assets/android-ui-clickthrough/`.

Size and structure:

- `app.js` 92 KB, `styles.css` 39 KB, `features.js` 11 KB, `icons.js` 6.5 KB,
  `choices.js` 5.9 KB, `index.html` 3.9 KB. Roughly 160 KB of source plus verify
  harnesses (`verify.mjs` 28 KB, `verify-audit.mjs` 10 KB, `capture-all.mjs`).
- 28 routes, listed in `choices.js`, every one rendering in light and dark with
  zero console errors when captured. The mock-audit captured 77 screenshots across
  both themes plus large-text and interactive states (drawers, expanded player,
  notification shade).
- A genuine shared-primitive layer: `row()`, `tabs()`, `pageTop()`, `heading()`,
  `areaCard()`, sheet markup, transport rows, all in `app.js`. Screens are
  composed from these primitives, which is why the mock is internally consistent in
  a way the native app is not.

Quality read from the mock-audit: most 27/28 September owner feedback items pass.
The known defects are minor and were largely fixed in the Claude mock-fix pass on
29 September: the Conversations tab strip overlapped at large text, the full Player
showed a duplicate mini row, "This phone" used the Home icon, the Home title was
never shrunk despite the ask, and there is dead code from earlier rounds (`.hero`
CSS, unused rotate/loop handlers in `app.js`). None of these undermine the design.

Verdict: keep and use this mock as the visual truth. Do not rebuild the full mock
from scratch. A fresh mock would throw away a converged 28-screen design and the
228 owner decisions baked into it, and would re-run the exact round-shopping the
owner already rejected. If anything is wanted, it is a small polish pass on the few
remaining defects, not a new mock.

## 4. Salvageable vs throwaway

### Salvage (high value)

- The clickthrough mock (whole `assets/android-ui-clickthrough/` folder). Visual
  truth. Keep.
- The design doc set: `docs/android-ui-round5-plan.md` (the binding behavior
  contract), `docs/android-ui-round4-reconciliation.md` (the decision map),
  `docs/android-ui-final-spec.md`, `docs/android-ui-system.md`,
  `docs/android-improvement-backlog.md`.
- The Claude recon folder,
  `/Users/alcatraz627/Code/Claude/csync/.claude/output/20260928-recon/`. This is
  the best restart asset. `requirements-ledger.md` captures 228 atomic owner asks
  each quoting the owner; `ledger-status.md` marks every ask mock PASS/FAIL and
  app PASS/FAIL/UNBUILT (mock: 171 pass, 2 fail, 9 unbuilt, 46 n/a; app: 103 pass,
  64 fail, 21 unbuilt, 40 n/a); `working-order.md` is a clean six-step plan;
  `mock-audit.md` and `native-audit.md` are grounded, file-line-cited audits.
- The native "kit" work from the 29 September Claude session
  (`_checkpoint-kit-20260929.claude.md`): `Kit.java`, `res/values/kit.xml`,
  `kit_*.xml` layouts, and 66 `csi_*` vector icons generated from the mock. This is
  the shared component layer the app was always missing, and several pages were
  already ported onto it (Home, Media, Player, Chat, Share, Camera, Notes, More,
  Settings, Search) and emulator-verified. If the restart keeps any native code,
  keep this. Note it is uncommitted in `/Users/alcatraz627/Code/csync-hub`.
- Working backend/service changes: `assist/attach.go` (chat attachments, tested and
  deployed), `media/server.py` rotate/loop and Notes search (31 tests pass), the
  branded app icon and 2.33 release plumbing.
- The requirements capture itself. Even if all native code is discarded, the
  228-row ledger plus the 28-screen mock is a complete, owner-approved spec for a
  clean rebuild.

### Throwaway or archive only

- The variants folder `/Users/alcatraz627/Code/Claude/csync/assets/android-ui-variants/`.
  Rounds 1 to 3 exploration, superseded by the clickthrough. Archive for history,
  do not build from it.
- The 39 Codex handbacks at the repo root. History only. The final one
  (`_codex-handback-20260928-1252.claude.md`) and the kit checkpoint
  (`_checkpoint-kit-20260929.claude.md`) are the only two worth keeping open; the
  rest can be swept.
- The five dead pre-`_v2` Android layouts (`page_home.xml`, `page_tools.xml`,
  `page_camera.xml`, `page_more.xml`, `page_share.xml`). Delete.
- Dead mock code (`.hero` CSS, unused rotate/loop handlers in `app.js`).
- The God-object structure of `MainActivity.java` as an approach. The lines that
  wire live Pi data are worth keeping; the hand-rolled per-page view building is
  the thing to stop doing, which the kit layer already replaces.

## 5. Budget and waste notes

The "roughly 80 percent of the weekly budget" figure is the owner's, from the task
brief. It is not stated in any doc I read; no handback or recon file records a
token, rate-limit, or budget number. What the docs do substantiate:

- 39 dated handback checkpoints in four days (25 to 28 September), a new full
  recovery record roughly every one to two hours. That volume of restart-and-
  re-verify is the concrete waste signature: effort spent re-establishing state
  rather than converging.
- Rounds 1 to 3 of variant shopping were later judged cosmetic by the owner
  ("Search A/B/C were cosmetic"), so a chunk of early effort produced options that
  were thrown away at round 4.
- The core inefficiency: Codex kept re-fixing individual native screens against the
  mock without first building the shared style/component layer, so the same visual
  drift reappeared per page and per handback. The Claude recon diagnosed this and
  the kit rebuild fixed the root cause in one session, which is the shape the
  restart should follow: one kit, then port pages onto it, not per-page restyling.

## Restart recommendation (one line)

Keep the mock and the docs as-is, start from the recon `working-order.md` and
`ledger-status.md`, build on the `Kit.java` shared layer rather than the God
Activity, and do not commission a new mock or new variant rounds.
