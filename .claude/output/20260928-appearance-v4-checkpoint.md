# Appearance installed checkpoint, 2026-09-28 08:31 IST

## Source and build

- Android APK: `/Users/alcatraz627/Code/csync-hub/app/build/outputs/apk/debug/app-debug.apk`, modified 08:30:36 IST, 6,184,906 bytes, SHA-256 `bdd59e8a613a2f5c9989cf8d8a12b58be4806c6756969eaef0273c1502f65d24`.
- `JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew assembleDebug --offline --console=plain`: exit 0, `BUILD SUCCESSFUL in 997ms`, 34 tasks, 10 executed. `adb install -r /Users/alcatraz627/Code/csync-hub/app/build/outputs/apk/debug/app-debug.apk`: `Success`. `git diff --check`: exit 0.
- The APK is newer than the Pi-staged 2.30 APK. Do not use this checkpoint as proof of the Pi update path.

## Changed in this Appearance pass

- `/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/MainActivity.java`: selectors use independently rounded inset buttons, semantic icon tint, persisted selection; custom swatch is a palette on a rainbow circle; shared bottom nav uses the slate surface and no elevation.
- `/Users/alcatraz627/Code/csync-hub/app/src/main/res/layout/page_settings.xml`: semantic icons on all Theme and Text size choices; selectors are horizontal groups; custom swatch uses palette art.
- `/Users/alcatraz627/Code/csync-hub/app/src/main/res/drawable/ic_system_theme.xml`, `ic_sun.xml`, `ic_moon.xml`, `ic_text_size.xml`, `ic_palette.xml`: new Android vector icons.
- `/Users/alcatraz627/Code/csync-hub/app/src/main/res/values/colors.xml`, `/Users/alcatraz627/Code/csync-hub/app/src/main/res/values-night/colors.xml`, `/Users/alcatraz627/Code/csync-hub/app/src/main/res/values/themes.xml`: soft selected nav indicator on light and dark surfaces. The shared color/theme files also contain earlier uncommitted Appearance work.

## Installed results

| Check | Result | Evidence |
| --- | --- | --- |
| Appearance light, md, full frame | PASS for requested icons, segmented track, rounded white selected pill, rainbow Custom, soft bottom indicator | `/private/tmp/csync-appearance-v4-light-md.png` |
| Appearance dark, md, full frame | PASS for requested icons, slate nav instead of maroon, dark inset selected pill, nav indicator | `/private/tmp/csync-appearance-v4-dark-md.png` |
| Appearance dark, lg | PASS for controls and visible five-icon nav; text increases | `/private/tmp/csync-appearance-v4-dark-lg.png` |
| Light/Dark switching | PASS, tapped on installed page and inspected both rendered frames | same light/dark frames |
| Text size md→lg→md | PASS on Appearance; selection and size changed after recreation | dark md/lg frames |
| Custom RGB picker | PASS dialog opens; adjusting sliders and Apply changed active accent to green, selected Custom ring and nav icon | `/private/tmp/csync-custom-dialog-light.png`, `/private/tmp/csync-custom-applied-light.png` |
| Restore Coral after Custom | PASS, coral swatch and active icon returned to coral | `/private/tmp/csync-coral-restored.png` |
| System theme follows device mode | UNRUN | Emulator handoff due for parent's Notes test. |
| Small text, all six other named colors, persistence after full process restart, Media/Notes cross-activity rendering | UNRUN | Needs later Settings acceptance pass. |

The installed screenshot was compared to `/private/tmp/csync-reference-20260928/appearance-dark.png`. The selected pill and slate nav now match the reference shape and hue. Native still has a longer breadcrumb, larger fixed top spacing, and a real Android status/navigation bar, so whole-frame exact parity remains open.

## Owner categorical visual check

Using `/Users/alcatraz627/Code/Claude/csync/.claude/output/20260928-ui-categorical/patterns.md` on the installed v4 frames: text-glyph disclosure controls N/A on Appearance; icon/label proportion PASS for the two selector groups; aligned icon and text centers PASS; card rhythm N/A; icon-only five-item bottom nav PASS in light, dark, and large; compact top context PARTIAL because the native breadcrumb is longer and top gap differs from the mock; trailing device row alignment N/A on this route; current reference PASS with `app.js` SHA-256 `33afbce0354b03cf1d99268b2dc971a3dbeed00ea580b9f2c6ecc24c29efc81f`. The full Settings route remains open under the callout gate.

`bash /Users/alcatraz627/.claude/scripts/callouts/callouts.sh gate android-ui-settings`: exit 1. Open rows `co-20260927-235712-42` and `co-20260928-001940-bf` still require the full Settings action and Appearance persistence matrix. Do not retire them yet. Next: give emulator to parent for Notes; then finish the missing Settings checks and send a page verdict.

## Later source boundary

After the installed v4 captures, Main and Media began deriving the selected bottom-nav pill from the active accent over the slate or light nav surface. This lets a Custom color produce a matching soft indicator. Offline `assembleDebug --offline --console=plain` exited 0 (`BUILD SUCCESSFUL in 753ms`, 34 tasks, 4 executed). This newer indicator has **not** been installed or screenshot checked; the v4 captures above show the earlier static indicator.
