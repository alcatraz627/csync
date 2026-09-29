<!-- sessions: csync-ui-7c@2026-09-29 -->
# csync phone app: the design system

This file says how the app looks and what it is built from. How the app is
organised is in `/Users/alcatraz627/Code/Claude/csync/docs/android-app-model.md`,
and this file follows it. The running reference is the mock at
`/Users/alcatraz627/Code/Claude/csync/assets/android-ui-mock/index.html`. Every
value below is read from the mock's `styles.css`, `data.js` and `kit.js`. When
the mock and this file disagree, fix this file.

This version replaces the 26 September proposal. That text described three
review treatments, eight accent samples including Gold, and an open set of
bottom-bar places. All three were settled afterwards and none of it applies.

## Colour

The phone draws with these values only. Native resources use the same names.

| Name | Dark | Light | Used for |
|---|---|---|---|
| bg | `#0F1014` | `#F4F2ED` | The page |
| surface | `#181A20` | `#FFFFFF` | Groups of rows, tiles, sheets, the bottom bar |
| surface2 | `#20232B` | `#ECE9E2` | Icon tiles in rows, the track of a segmented control |
| line | `#2A2E38` | `#DDD8CE` | Borders and dividers |
| text | `#F4F2EF` | `#1B1B1F` | Titles and body |
| dim | `#A7ACB5` | `#565B65` | Second lines, section labels, idle icons |
| faint | `#8B909A` | `#60656F` | Help text, chevrons |
| good | `#3CCB84` | `#1B7F4A` | Status dot: working |
| warn | `#F0B23E` | `#8A5D00` | Status dot and notice: needs attention |
| bad | `#F26A6F` | `#C0323A` | Status dot, notice, Stop, Delete |

Text, dim and faint all reach 4.5 to 1 on bg, surface and surface2 in both
themes (SE-16). The mock's `runChecks()` measures this on every run.

### The accent

Seven colours and one the owner picks (SE-07, SE-08, SE-12). Each has three
values, because a colour that works as a fill does not work as small text.

| Name | Fill, under white text | Text on dark | Text on light |
|---|---|---|---|
| Coral | `#CC4620` | `#FF8A66` | `#B23A17` |
| Teal | `#08796F` | `#70D9C7` | `#08695F` |
| Violet | `#6546D8` | `#AD9AFF` | `#5A3CCB` |
| Rust | `#B33B0B` | `#F8A47A` | `#A3330B` |
| Blue | `#2768B2` | `#8BBCF4` | `#235A99` |
| Leaf | `#287D45` | `#8FDFA7` | `#246C3D` |
| Rose | `#B23773` | `#F4A1C6` | `#982A62` |

The brand coral `#E4572E` stays in the app icon. It is not used as a fill
because white text on it measures 3.7 to 1.

The accent appears in four places and nowhere else: the one primary button on
a screen, the selected option in a control, the highlighted place in the
bottom bar, and links in text. Icons in rows and tiles are neutral. Working
state is green, not the accent. Warnings and faults are amber and red.

## Type

Roboto, the system font. Three sizes of the whole scale: Small is 1, Medium is
1.15, Large is 1.3 (SE-03, SE-04). Every size below is multiplied by that.

| Role | Size | Weight |
|---|---|---|
| Bar place name in the top bar | 17 | 650 |
| Path step in the top bar | 13.5 | 500, current step 650 |
| Page heading | 22 | 700 |
| State line at the top of a page | 18 | 650 |
| Row title, tile title | 15 | 600 |
| Body | 14.5 | 400 |
| Second line of a row | 13 | 400 |
| Section label | 13 | 600, in dim |
| Help text | 12.5 | 400, in faint |

Section labels are quieter than the rows they introduce. That, and the single
accent, is where the hierarchy comes from.

## Space and shape

| Thing | Value |
|---|---|
| Page inset | 16 |
| Gap between sections | 18 |
| Row | at least 60 tall, 12 padding |
| Icon tile in a row | 38 square, corner 11 |
| Group of rows | corner 16, one border, dividers between rows |
| Tile | corner 14 |
| Button | 44 tall, corner 13 |
| Icon button | 40 square |
| Top bar | 52 tall, always |
| Bottom bar | 62 tall |
| Sheet | top corners 24, at most 82 percent of the screen |
| Smallest thing that can be tapped | 34, checked by `runChecks()` |

## Parts

One part per job. The table of jobs is in the app model, section 9. The
names here are the function names in the mock's `kit.js`; the native shared
layer uses the same names.

| Part | What it takes | Rules |
|---|---|---|
| `topBar` | the place | Built from the map. A screen cannot pass its own path. |
| `head` | title, optional second line | Title wraps to two lines, then fades. |
| `section` | label, content, optional id | With an id it collapses and remembers. |
| `row` | icon, title, second line, status or value, what it does | Chevron only when it opens something. A trailing icon button is a direct action named by its icon. |
| `tile` | icon, title, status or a number | The same data as a row, for grids. |
| `seg` | options with an icon each, the chosen one | No two options in one control share an icon. Scrolls sideways when it must, with a fade on the right. |
| `btn` | label, icon, kind | Kinds: primary, plain, quiet, danger. One primary on a page. A disabled primary turns neutral. |
| `ibtn` | icon, spoken name | Always has a spoken name. |
| `field` | icon, hint, value | Hints never end in an ellipsis. |
| `status` | tone, words | Dot then words. Tones: good, warn, bad, idle. |
| `notice` | tone, one sentence, one action | For the state of the whole page. |
| `empty` | icon, title, one line, one action | Says what belongs here. |
| `sheet` | title, content, buttons | Handle, no close button. Buttons only when it changes something. |
| `facts` | pairs | Label on the left, value on the right. |
| `playerControls` | the output | The same controls at page and panel size. |

## What may never appear

These are checked on every screen, in both themes and all three text sizes,
by `runChecks()` in the mock.

- An ellipsis, in text, in a hint or as an icon.
- Text cut off without a fade.
- A label in capitals.
- A text character used as a chevron or a separator mark.
- More than two facts on one line.
- A value that was not measured, shown as a dash or as "unavailable".
- The words planned, prototype or fixture.
- A button with no spoken name, or smaller than 34.
- Two primary actions on one page.
- A path that does not fit the top bar, or a top bar that is not 52 tall.
- Anything wider than the phone.

## How the native app is checked against this

1. Each screen is captured on the emulator in dark and light at Small, and in
   dark at Large.
2. The capture is set beside the same frame from the mock's "Show every
   screen" wall.
3. The differences are listed by part, not by pixel: a row that is the wrong
   height is one finding however many rows there are.
4. A screen is done when its list is empty and its asks in the map are met.
