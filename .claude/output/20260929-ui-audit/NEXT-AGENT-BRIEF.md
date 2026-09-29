# Next-agent brief: rebuild the csync Android UI properly

You are picking up a UI rebuild that already has a lot of investigation behind
it. Read this brief fully. Everything you need is linked here so the owner does
not have to restate anything and you do not have to scour the repo. Paths are
absolute. When this brief says "the audit folder" it means
`/Users/alcatraz627/Code/Claude/csync/.claude/output/20260929-ui-audit/`.

---

## 1. Your mission

Build ONE full HTML mock of every screen of the csync Android app, on a corrected
and coherent design language, then rebuild the native app to match it screen by
screen, verified on the emulator. The mock is the contract. The requirements
ledger is what the mock must satisfy. The combined backlog is the order of work.

Do the two preconditions first (details in section 8): fix the stale
design-system doc and decide the one navigation model. Do not build the mock on
the old docs; they are why the app drifted.

## 2. What csync is (the product, current, not the ancient version)

csync is a personal device mesh for one owner. The phone app reaches the owner's
own machines over Tailscale and does real work with them:

- The **Raspberry Pi** is the hub. It runs three services the app talks to: a Go
  mesh peer (port 8790, sends and receives text, files, images between trusted
  devices), a Go assistant (port 8791, a Pi-hosted chat assistant with model
  tools, media, provider config), and a Python media service (port 8792, browses
  mounted drives, streams files and the Pi camera, controls direct-DRM playback on
  the Pi's HDMI screen, stores play history).
- The **Mac** is a sharing target and receiver.
- The phone app's job, in the owner's words from the product brief, is to reach
  those machines: **share items to them, use the Pi assistant, browse and play the
  Pi's media (on the phone or cast to the Pi's screen), see the Pi camera, keep
  notes and pins on the Pi, and manage it all.**

The app has these surfaces today: **Home, Media, Share, Chat, and More** in the
bottom nav, with More holding **Pi camera, Tools and diagnostics, Settings,
Notes, Pins, Search, Assistant capabilities, and Help**. (Note the doc conflict
in section 8: older docs say six tabs Home/Share/Chat/Tools/Settings/Camera; the
shipped app is the five above. The shipped set is the current reality.)

Authoritative product context, in order of usefulness:
- `/Users/alcatraz627/Code/Claude/csync/AGENTS.md` (the services, trust model,
  design constraints, and how to verify each part). Read this first.
- `/Users/alcatraz627/Code/csync-hub/docs/ui-design-brief.md` (the original
  Norman-style product brief; stale on surfaces but good on intent).
- `/Users/alcatraz627/Code/csync-hub/README.md` (build and code layout; stale on
  surfaces).
The Android app source is a separate repo: `/Users/alcatraz627/Code/csync-hub`.
The services are in `/Users/alcatraz627/Code/Claude/csync`.

## 3. The ask and the pain point (why this rebuild exists)

The UI has been through five design rounds and many native ports and it still
reads as generic and structurally incoherent. The owner's pain, stated plainly:

- The app "looks pretty ass": it was the generic dark SaaS-card template with
  every AI-design tell (identical flat cards, ALL-CAPS eyebrows, middle-dot meta
  strings, an accent that did nothing). See `../20260929-ui-diagnostic.md`.
- Deeper than looks, the STRUCTURE is a mess: inconsistent mental mapping,
  multiple ways of doing the same categorical pattern, unintuitive navigation and
  back button, breadcrumbs that are externally imposed rather than reflecting how
  the app is organized, and common segments done badly. These were bad in the
  mock and worse in the app. See `structural-map.md` and `ui-issue-report.md`.
- The prior effort wasted enormous budget building mocks and failing to implement
  them. The owner is explicit: do not repeat that. Build the mock, then actually
  ship it, and do not let the native app drift from it. See `codex-trail.md`.

The owner's chosen path: get the full mock right FIRST, then implement against it.
The owner will likely drive that with a fable-tier model.

## 4. Current state (build 2.34)

- 2.34 is built, installed on the emulator, and deployed to the Pi. Install on the
  phone via More, Tools and diagnostics, Update csync from Pi.
- What this session already fixed (visual, on top of the old skeleton): the Home
  screen is rebuilt as a Pi "hub hero" with a mesh motif that echoes the new app
  icon, live capability pills, and a green status dot; the dark palette is warmer
  app-wide; section labels are sentence-case app-wide (the ALL-CAPS tell is gone
  from Home, Media, Chat, More, Tools, Settings, Search); there is a branded
  adaptive app icon and a launch splash; the undervoltage warning is amber vs
  green instead of blending into the coral.
- These visual fixes sit ON TOP of the broken structural skeleton. The skeleton
  (sections 1 and Tier 0 of the backlog) is untouched and is the main remaining
  work.

## 5. Everything you need, linked

Work list and evidence (all in the audit folder):
- `combined-backlog.md` the 31 issues in 5 tiers. This is your work list.
- `structural-map.md` how navigation is actually built and why it feels arbitrary.
- `ui-issue-report.md` the 17 ranked per-screen UI defects (external designer).
- `notes-inventory-and-gaps.md` what is documented vs what is only in a transcript
  or contradicts another doc.
- `codex-trail.md` the forensic history of the prior effort and what is salvageable.
- `screens/` 35 numbered screenshots, one per screen, tab, drawer, sheet, detail.
- `README.md` the index and one-place state of the project.

The requirements and review record (the backbone, treat as source of truth for
what the owner asked):
- `../20260928-recon/requirements-ledger.md` 228 atomic asks with the owner's own
  quotes, grouped by screen, with priority. The mock must satisfy this.
- `../../callouts.jsonl` 82 owner review call-outs, each with a re-runnable check.
  Its `status` field is stale (all read open); the last recheck is the truth.
- `../20260928-recon/ledger-status.md` per-ask pass/fail/unbuilt status.

The existing design assets:
- `../../../assets/android-ui-clickthrough/` the 28-screen HTML mock. It is a
  coherent design and is the recommended BASE for your full mock. Do not start
  from zero; fix and complete this.
- `/Users/alcatraz627/Code/Claude/csync/docs/android-ui-system.md`,
  `android-ui-round4-reconciliation.md`, `android-ui-round5-plan.md`,
  `android-ui-final-spec.md` the design-system and decision docs (see section 8:
  the system doc is stale, the final spec is the most current).
- The approved Home visual direction, already shipped: `../20260929-home-redesign/home.html`.

## 6. Hard rules from the owner (do not relearn these the hard way)

- No "..." anywhere in the app, on any text or input (owner call-out 15). If you
  must truncate, middle-clip or fade, never a trailing ellipsis.
- No ALL-CAPS tracked eyebrows, no middle-dot meta strings as primary status, no
  placeholder values (dashes, "live sample needed") shown as real UI.
- The accent (coral #E4572E) marks the ONE primary action and live state per
  screen, nothing else.
- Keep the shared style layer. The root cause of the old failure was a 2,728-line
  single Activity with no shared components. A `Kit.java` shared layer now exists
  in `/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/Kit.java`;
  build on it, do not regress to per-screen styling.
- Build the mock to ship. Do not produce a mock the native app cannot match, and
  do not let the native app drift from the mock. Verify every screen on the
  emulator, not just by building.

## 7. Environment and how to work

- Emulator AVD is `csync-ui` (currently running windowed). adb device
  `emulator-5554`. Screenshot with `adb -s emulator-5554 exec-out screencap -p`.
  The tab bar row on MediaActivity is around y=428, not y=587 (a capture gotcha).
- Build:
  `env JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home /Users/alcatraz627/Code/csync-hub/gradlew -p /Users/alcatraz627/Code/csync-hub assembleDebug --offline --console=plain -q`.
  Install with `adb -s emulator-5554 install -r <apk>`.
- Deploy to the Pi (for the in-app updater): bump versionCode and versionName in
  `/Users/alcatraz627/Code/csync-hub/app/build.gradle`, build, then scp the APK to
  the Pi (`100.65.188.9:/home/alcatraz627/.local/state/csync/csync-hub-update.apk`)
  with a hash check and a backup of the current one, and verify the served
  `GET http://<assist-ip>:8792/v1/app/apk`. The guarded procedure is in
  `../20260928-android-232-pi-release.md`. SSH to the Pi works when it is up.
- Hardware blocker you cannot fix: the Pi is in undervoltage
  (`throttled=0x50005`), mpv cannot create KMS, and the USB drives are
  disconnected. So Pi-screen video playback, casting reliability, and full/mini
  player parity CANNOT be exercised until the owner fixes Pi power and display.
  Phone-local playback does work. Do not chase the Pi display; flag it and move on.

## 8. Do these before the mock

- Fix `docs/android-ui-system.md`, or put a banner at its top that the final spec
  overrides it. It predates every round-5 decision: it still lists the removed
  Gold accent, has no breadcrumb or drawer or no-ellipsis rule, and calls Search a
  proposal. It is the file a newcomer opens for the design language and it is
  wrong. See `notes-inventory-and-gaps.md` gaps 1, 2.
- Decide the ONE navigation model (backlog Tier 0 item 1). Right now Media, Notes,
  and Search are separate Activities with their own copy of the bottom nav while
  everything else is a page in one Activity. The mock and the rebuild both need
  this decided first.
- Refresh the stale surface lists in the READMEs and AGENTS.md, or the next reader
  will be misled about what the app even is (gap 3, 4).

## 9. Open decisions the owner still owes (present these, do not rediscover them)

From the ledger's open rulings and `../20260928-recon/working-order.md`:
- CH-17: favorite and archive placement in Chat.
- Whether Home's Devices and Pick-up sections keep the round-4 collapse behavior.
- P-19: whether one-drawer-at-a-time is acceptable.
- PI-06: whether the Pi agent may edit its own code.
- O-07 / O-08: whether a Cast-enabled HDMI device is an acceptable receiver.
Put these on one decision surface for the owner rather than asking them one by one.
