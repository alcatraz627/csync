# Android Home checkpoint, revision 2

## Review result and correction

The owner installed the first Home build and captured `/private/tmp/csync-sol-home-render.png`. The frame still had a large standalone title, no hub hero, and capability cards whose icons sat beside both text lines. This revision adds the requested hero, places capability icons beside titles with supporting text below, and tightens the top context row. I read `/Users/alcatraz627/Code/Claude/csync/.claude/output/20260928-android-native-parity-tasks.md` before this correction.

There is a source discrepancy to resolve at parent review: the current `/Users/alcatraz627/Code/Claude/csync/assets/android-ui-clickthrough/app.js:113-130` renders a plain heading, while the owner reviewed a Home clickthrough frame with a distinct `YOUR HUB` hero, supporting text, and Browse media/Search buttons. This implementation follows the owner's explicit installed-frame correction and the reviewed hero frame. All native statuses continue to use real probes or saved state.

## Code changed

| File | Lines | Change |
| --- | --- | --- |
| `/Users/alcatraz627/Code/csync-hub/app/src/main/res/layout/page_home_v2.xml` | 6-60, 138-171 | Top row is 40dp with smaller context text. Added a compact hero with eyebrow, headline, supporting text, and Browse media/Search actions. Replaced each two-line TextView capability with a vertical card container. Previous named device rows, section toggles, Pick up, and all card IDs remain. |
| `/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/MainActivity.java` | 242-292, 398-405, 441-472 | Hero actions reuse existing Media and Search destinations. Hero colors derive from current surface, border, and accent resources. Supporting text changes with live Pi assistant and media reachability. Capability heading and supporting text are separate views, and the narrow/large-text one-column layout now accepts the new card containers. Existing Home handlers and live status probes remain. |

The earlier first-pass changes in these files also place section arrows at the trailing edge, show observed Pi/Mac status badges, and shorten row/card spacing. No mock counts or synthetic device values were added.

## Code checks

In `/Users/alcatraz627/Code/csync-hub`, `JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew assembleDebug --offline` exited 0. Output ended with `BUILD SUCCESSFUL in 1s` and `34 actionable tasks: 10 executed, 24 up-to-date`. `git diff --check` exited 0 with no output. The Home layout was already untracked when this pass started, so the Git whitespace check excludes it; Android resource compilation and packaging included it.

## Parent render and verdict needed

I did not use ADB or the emulator, as instructed. This revision has no installed screenshot yet. The parent needs to capture normal and large text in light and dark, compare hero height, card wrapping, top row density, and scrolled Pick up against the approved Home frame, then exercise both hero actions and section collapse. An offline or partial Pi state should keep the hero wording honest. Home callout `co-20260925-183101-cf` remains open pending installed Home and Media checks. Broader player and token parity callout `co-20260925-183101-d0` remains open. No APK was staged on the Pi from this scoped pass.
