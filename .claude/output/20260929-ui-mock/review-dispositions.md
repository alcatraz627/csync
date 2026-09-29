<!-- sessions: csync-ui-7c@2026-09-29 -->
# What was done with each review finding

The review is `/Users/alcatraz627/Code/Claude/csync/.claude/output/20260929-ui-mock/review-opus.md`
(38 findings, written by an independent opus reviewer on 2026-09-29).
"Changed" means the mock changed and `runChecks()` passed afterwards on
846 of 846 frames. "Ruled" means the mock stays and the reason is recorded in
`/Users/alcatraz627/Code/Claude/csync/docs/android-app-decisions.md`.

| # | Finding, in short | Disposition |
|---|---|---|
| 1 | The same item offers different actions on each surface | Changed. One list, `itemActions()`, draws every item sheet and the From another app page. Table in app model section 7a. |
| 2 | Only dark frames existed, one large-text frame | Changed. All 141 frames rendered in light and at Large. Every light frame read; 24 Large frames read. |
| 3 | Sheets commit on a row tap | Changed and ruled. App model section 5 now says which sheets commit on tap and which need a button. Send to a device got a Send button. Send to a conversation never sent: it attaches, and now says so. |
| 4 | "Tools" names two things | Ruled, D7. Different icons; the guide opens the list as a sheet. |
| 5 | Status words outside the vocabulary | Changed. Vocabulary extended in section 7 and enforced by a check. A failed command no longer turns the session red. Recording is green. |
| 6 | Offline drawn two ways | Changed. One notice with Open Connection on every screen. Notes tile goes grey. Media offers This phone. |
| 7 | "Browsing Pi USB" on History, Access, Videos | Changed. Shown on Files and while searching only. |
| 8 | Send to a device jumps to Share | Changed. It is a sheet with the device list and Send. |
| 9 | Back from an incoming share goes to Share | Changed. Back returns to the app the item came from. |
| 10 | Captures behind an unlabelled thumbnail | Changed. Named rows under the shutter: Captures, Show on Pi screen. |
| 11 | Buttons wrapping to three lines | Changed. Short verbs. |
| 12 | Search's fifth scope cut | Changed. Fits at Small; scrolls with a fade at larger sizes. |
| 13 | Settings pages commit four ways | Changed. Toggles and pickers apply at once; typed fields have Save at the end. Assistant lost its duplicate Thinking control. |
| 14 | Rich was not a rich editor | Changed. Rich edits the formatted note; Plain edits Markdown. |
| 15 | Own colour had nothing to pick with | Changed. Hue, colour code, and a contrast reading. |
| 16 | Busy output not named in the item sheet | Changed. "Playing on Pi screen, Open the player". |
| 17 | Tool results in the present tense | Changed. "Started on Pi screen", "Read at 18:41". |
| 18 | Media search matched videos only | Changed. Every kind and folder in the source. |
| 19 | Skip length shows no value | Changed. "10 s" under the icon, in the page and the panel. |
| 20 | One icon, several meanings | Changed. Table of icons in the design system. |
| 21 | Share heading looked tappable and was not | Changed. The recipient is a row that opens the list. |
| 22 | Home said 123 videos, Videos said 6 | Changed. Both read the same list. |
| 23 | Loop had three states | Changed and ruled, P3. On or Off. |
| 24 | Accent on some row icons | Changed. Row icons are neutral. |
| 25 | No words on Pause and Stop in the panel | Changed for the panel. The mini row keeps spoken names only; it has no room for words at 48 wide. |
| 26 | "applying" was plain text | Changed. Amber dot. |
| 27 | Time shown only on tap | Changed. Every message shows its time. |
| 28 | Rotate row gave an instruction; no framing preview | Changed. |
| 29 | "6:29 left" and "stopped at 6:29" | Changed. One phrasing, and sample data that does not collide. |
| 30 | App sheet drawn over the wrong state; two refresh verbs | Changed. |
| 31 | The update row was never on screen | Changed. "Tools, end of the page" frame added. |
| 32 | Empty states with no action | Changed. |
| 33 | Favorite and Archive on an empty conversation | Changed. Hidden until the first message. |
| 34 | Sun icon for reveal; unclear hint | Changed. |
| 35 | "A file from Media" opens the parent | Changed. Named "Browse Media". |
| 36 | Widgets had "Add" as text and no detail | Changed. Each row opens a detail with Add or Remove. |
| 37 | Pi dot in the heading, not on rows | Ruled, P2. |
| 38 | Starts muted was never recorded | Ruled, P1. It is now also a setting. |

## Asks the review said had no screen

| Ask | State |
|---|---|
| SH-05 local video shared in | Now the default From another app frame. |
| SH-03 clipboard image | Frame "Sheet: Clipboard, an image". |
| N-08, M-10 share to another app | On every item sheet. |
| CH-10 OpenAI group | In the model sheet, marked not set up. Local is left out until a local model exists. |
| P-16 drag the panel to the full page | Works in the mock by dragging the handle up. A still frame cannot show it. |
| T-02 trends | One line per reading. A chart is not designed. |
| T-07 widget detail | Done. |
| CH-37 select part of a bubble | Works in the mock; text is selectable. A still frame cannot show it. |
| O-09 phone camera to the Pi screen | Not shown. Owner ruling P4. |
| Large text and light theme | Done, see finding 2. |

## Rulings the review wanted changed

| Ruling | Outcome |
|---|---|
| B13 and T-06 | New row B14 records the rule for native. |
| A4 and the word "Areas" | Sections renamed. Marked for the owner to look at. |
| Three unrecorded product choices | Recorded as P1, P2, P3. |
