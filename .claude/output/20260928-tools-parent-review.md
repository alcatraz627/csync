# Tools, Process, and Widgets parent review, 28 September 2026

The installed Dark normal captures are `/private/tmp/csync-tools-current-dark.png`, `/private/tmp/csync-tools-current-scrolled.png`, `/private/tmp/csync-tools-process-current.png`, and `/private/tmp/csync-tools-widgets-current.png`. I compared their whole frames with `/private/tmp/csync-reference-20260928/tools-dark.png`, `/private/tmp/csync-reference-20260928/process-dark.png`, and `/private/tmp/csync-reference-20260928/widgets-dark.png` from the current clickthrough.

## Tools

The native page shows actual authenticated media reachability and a current Pi undervoltage warning. Its scrolled state exposes Process monitor, Widgets, and the working Update csync from Pi entry. The mock places an unboxed, compact issue headline and Recheck above Service health. Native has a large boxed PI HEALTH hero plus a separate Tools headline; this pushes Utilities below the first viewport. The visual hierarchy is open. Recheck and each destination need an installed action check after the revision.

## Process monitor

Native currently shows one tall, mostly empty card with Shizuku unavailable text. The mock has a 2×2 metrics grid, Processes rows, and Traces rows. The mock explicitly labels its values prior fixtures and live sampling as planned. Native should show only real measurements it obtains, and preserve the honest Shizuku state, while using the route structure and visible Planned labels. The current installed page fails that visual contract.

## Widgets and quick actions

Native currently has a single prose card. The mock separates a Current xkcd widget row from Ideas to test rows, with Built and Planned labels. The xkcd widget does exist in the Android manifest and source. The installed page does not expose the same scannable route hierarchy, so this visual check fails.

Verdict: **FAIL/open** for all three route visuals. The UI agent received specific repair feedback without a pause. Dark/light normal/large captures, row actions, breadcrumb/back, current service refresh, widget route behavior, and error/offline states remain UNRUN in this parent pass.

## V3 visual recheck while agent finishes page pass

I opened the original-resolution native `/private/tmp/csync-tools-v3-dark-normal.png`, `/private/tmp/csync-process-v3-dark-normal.png`, and `/private/tmp/csync-widgets-v3-dark-normal.png` against the same mock references. The Tools issue headline is now unboxed. Process has a 2×2 metric grid and separate Processes and Traces sections. Widgets has separate Current and Ideas to test sections with Built and Planned labels. These correct the three structural failures above. The native pages still have distinct typography and spacing, and Process metrics omit the mock's leading icons. The xkcd row uses a Home icon rather than the mock star; Widget rows omit trailing chevrons. Tap behavior, live refresh, and light/large matrices await the agent's handoff. **Page verdict remains open** until those checks and a fresh installed action pass finish.

I also inspected the original-resolution light large captures `/private/tmp/csync-tools-v3-light-large.png`, `/private/tmp/csync-process-v3-light-large-route.png`, and `/private/tmp/csync-widgets-v3-light-large-route.png`. Tools shows the five-icon bottom nav, but the Process and Widgets captures appear to end in blank content without it. The Widgets subtitle also appears to lose the first letter of its wrapped final line. These may be screenshot timing or route-state issues; the agent has been asked to reproduce them in the current install before any verdict.

Correction: the nav inference above was wrong. The agent reopened the two original 1080×1920 frames and found the five-icon nav above the gesture bar in both. Process metrics also have leading icons. The actual Widgets defect is the orphaned `re planned.` wrap at large text. I had let the rendered tool preview of a tall screenshot substitute for inspecting the full frame. The nav and metric-icon portions must be recorded PASS, not as missing UI.

The agent supplied `/Users/alcatraz627/Code/Claude/csync/.claude/output/20260928-appwide-tools-handoff.md` at 06:54 IST. It records a successful offline build and install for its page revision, dark/light normal/1.3 captures, and exercised Process/Widgets navigation and Back. Recheck showed live media reachability and Pi undervoltage; the Pi power row opened a status dialog. Shizuku live sampling, launcher xkcd behavior, app update, and other row dialogs were not run. The agent's Tools callout gate exited 0 with its two relevant rows freshly passed and still open. My page verdict remains **open** while the remaining tap and route differences are checked on the latest install.

The agent's 07:07 continuation added a star icon, trailing chevrons, and tap dialogs to Widget rows and shortened the subtitle. Its offline build exited 0, but the revised APK was not installed in the agent's handoff. The newer four Tools callouts include a PASS for metric icons and a FAIL for the old installed subtitle; star and tap behavior still need current-install checks. Parent page verdict remains **open** pending those checks and full action review.

The agent's 07:20 installed v4 continuation in `/Users/alcatraz627/Code/Claude/csync/.claude/output/20260928-appwide-tools-handoff.md` now supplies Dark/Light normal/1.3 Widget frames and four tapped row dialogs. I opened `/private/tmp/csync-widgets-v4-light-normal.png` and `/private/tmp/csync-widgets-v4-light-large.png` at original resolution. The star, row chevrons, and complete one-line subtitle are visible. The agent reran the four relevant Tools callouts and the Tools gate exited 0. This clears the specific Widgets repair request. A later installed Light Tools frame exposed `Past undervoltage · null`; the agent fixed its string handling in source and built successfully, but that fix is not installed or in the staged 2.30 APK. The Tools page remains **FAIL/open** for that visible data defect, untested Shizuku sample and launcher widget behavior, and the outstanding full action/state pass. No callout was retired.

## 07:38 installed null-value recheck

I opened the original 1080×1920 `/private/tmp/csync-tools-null-fix-installed-light.png`. The Tools issue headline now reads `Undervoltage is happening now; recheck power before playback`, and the Pi power row shows a useful current warning without a literal `null`. The Recheck control, service rows, utilities, and five-icon bottom navigation are visible. This clears the specific null-value defect in the installed emulator. The 2.30 APK staged on the Pi predates this source fix, so an in-app update to that checkpoint would currently restore the older text until a newer checkpoint is staged. The page verdict stays **open** for live Shizuku sampling, launcher xkcd behavior, remaining row actions, offline states, and final release recheck; no owner callout is retired.
