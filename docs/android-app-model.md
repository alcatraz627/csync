<!-- sessions: csync-ui-7c@2026-09-29 -->
# csync phone app: the app model

This is the one description of how the phone app is organised. The mock, the
design-system doc and the native app all follow it. The owner's own words outrank
it: a rule here that drops or narrows something the owner asked for needs a recorded
owner ruling in the decisions doc.

The machine-readable copy of the place map lives in
`/Users/alcatraz627/Code/Claude/csync/assets/android-ui-mock/model.js` and the
mock builds its breadcrumbs, Back targets and bottom-bar highlight from it, so
the two cannot drift.

Owner asks are cited by their ledger id (for example G-02) from
`/Users/alcatraz627/Code/Claude/csync/.claude/output/20260928-recon/requirements-ledger.md`.
Where this model overrides something that shipped or an earlier doc, the
decision is recorded in
`/Users/alcatraz627/Code/Claude/csync/docs/android-app-decisions.md`.

## 1. What the app is for

The phone reaches the owner's own machines and does real work with them. The
Raspberry Pi is the hub. Other machines are named devices that can receive
things. Six jobs, in the order people reach for them:

1. Play something on the Pi screen or on this phone, and control it.
2. Send text, a file or a link to a named device, and see what arrived.
3. Talk to the Pi assistant.
4. Look through the Pi camera and keep captures.
5. Keep notes and pins on the Pi.
6. Check that everything is healthy, and set things up.

## 2. The things the app talks about

One name per thing. A screen never invents a second name for any of these.

| Thing | What it is | Words used in the app |
|---|---|---|
| Hub | The Raspberry Pi and its services | Raspberry Pi, or Pi in short labels |
| Device | A named machine on the tailnet, this phone included | Its own name, such as `studio-mac` |
| Source | Where media comes from | A drive name, This phone, YouTube |
| Output | Where media plays | Pi screen, This phone |
| Session | What one output is playing now | Playing, Paused, Loading, Stopped |
| Item | A file, folder, link or text being played or sent | Its title |
| Conversation | One thread with the Pi assistant | Its title |
| Note, Pin | Markdown and saved links or snippets kept on the Pi | Its title |
| Capture | A photo or recording from the Pi camera | Photo or Recording, with its date |

Three consequences follow from this table.

- There is no device called "Mac". The roster shows real names. The old "home
  peer" and "assistant peer" fields are connection details, named by what they
  do: the hub address, and an optional second address to find devices through.
- The Pi display is not a separate feature. It is the Pi screen output (C-07,
  C-08). Looking at it shows what is on the screen now: a session, or the cover
  image when idle.
- The assistant's tools carry the same names everywhere they appear (Chat's
  Tools view, the assistant guide, tool results in a conversation).

## 3. The map

Five places sit in the bottom bar. They are siblings. None of them is a child
of Home. Every other place has exactly one parent, and that parent never
changes with the route taken to get there (G-02).

The bar carries a sixth button before them, Quick, which is not a place: it opens
bar 1, the quick rail, upward over the bar, and a tap elsewhere closes it. The top
left corner shows the csync icon the owner picked for the launcher, and it goes
Home (owner, 2026-10-01).

```
Home                           hero · Pick up · capability cards in two tiers
├─ Search
├─ Raspberry Pi                Pi screen and camera links, then each part's health
│  └─ Pi camera
│     └─ Captures
└─ Notes                       views: Notes · Pins
   ├─ Note
   └─ Pin

Media                          views: Files · Videos · History · Access
├─ Pi screen                   the Pi output: player, or cover when idle
│  └─ Covers
└─ This phone                  the phone output: player, present while it plays

Share                          compose
├─ Received
└─ From another app            entered from the Android share sheet
   └─ A post from Instagram    its parts, saved one, some or all

Chat                           views: All · Favorites · Archived · Tools
└─ Conversation

More
├─ Process monitor             This phone
├─ Widgets                     This phone
├─ Settings
│  └─ Connection
├─ Assistant guide
└─ Help and about
```

Where a place lives is decided by what it is, not by the bar's five slots
(owner, 2026-10-01: "the bottom drawer is limited by 5 icons"). The Raspberry
Pi and Notes are capabilities in their own right and hang off Home; More holds
this phone's tools, the app itself and reading. Home is the map: every
capability has a card there, and no card repeats a bottom-bar place.

The deepest place is three levels. That is a design limit, not an accident: a
fourth level means the thing should have been a sheet or a view.

### Views are not levels

A view is a different look at the same place: Files, Videos, History and
Access are all Media. Switching view does not move you in the map, does not
change the breadcrumb, and is not undone by Back. Folder browsing inside Files
is content, not navigation: the folder path and its Up row are inside the list
(G-03).

## 4. Moving around

### The bottom bar

Five icons, no labels, each with a spoken name (G-21, G-14). The highlighted
icon is the bar place that owns the current place, so More stays highlighted
on Settings and on Appearance (MO-02). Tapping an icon opens that place's
root. One bar exists for the whole app; no screen draws its own copy.

### Back

There is one Back behaviour, for the arrow in the top bar and for the system
gesture alike.

| Where you are | Back does |
|---|---|
| A sheet is open | Closes the sheet |
| The player panel is open | Collapses the panel to the mini row |
| A child place | Opens its parent, one level up (G-02, MO-01) |
| From another app | Returns to the app the item was shared from |
| A bar place other than Home | Opens Home (system gesture only, no arrow) |
| Home | Leaves the app (system gesture only, no arrow) |

Back never stops playback, never walks folders and never changes a view (G-03).

### The top bar

One bar, one height, on every screen. It never scrolls and never grows (G-04,
G-05, G-22, G-26).

- On a bar place it shows that place's icon and name, and no arrow.
- On a child place it shows the arrow, then the path from the bar place to
  here, for example `More / Settings / Appearance`. Every step has its icon,
  always the same icon for the same place (G-06). Earlier steps are tappable.
- When the path does not fit, earlier steps keep their icons and drop their
  words, left to right. The current step always keeps its words. No step is
  ever removed and nothing is ever cut with an ellipsis (G-12).
- The right side holds up to two icon-only actions that belong to this place
  (M-02, SH-11). The same action always uses the same icon.

### The heading under the bar

The breadcrumb says where you are. The heading says what you are looking at.

- A bar place has no heading when its name is all there is to say. It has a
  one-line heading when it carries state, such as "Raspberry Pi is online".
- A child place uses the item's own title as its heading (the conversation
  title, the note title, the media title). When the breadcrumb already names
  the page and there is no item, there is no heading.
- A subtitle is kept only when it states scope or state, such as "Browsing
  Pi USB". A subtitle never gives instructions and never restates the title
  (G-15).

## 5. Page, sheet or inline

"Open the detail of X" has one answer, chosen by what the detail is.

| The detail is | It opens as | Examples |
|---|---|---|
| A place you stay in and work in | Page | Conversation, Note, Pi screen, Process monitor, Appearance |
| A choice among a few options, or actions on the thing you tapped | Sheet | Play on, Send to, Choose a source, file actions, model and effort |
| One value to adjust | Sheet with one control | Volume, Speed, Skip length |
| A confirmation before something is lost or replaced | Sheet with two buttons | Delete note, Replace Pi playback |
| Facts about one row | Sheet with labelled facts | Pi power, a transfer, a tool result |
| A setting with two or three states | Inline, in the row | Rotate, Loop, Receiving on this phone |

Sheet rules: a drag handle, no close button at the top or the bottom (G-09,
G-10). It closes by dragging down, tapping outside, or Back (G-11).

When a tap is enough and when a button is needed:

| The sheet | Commits by |
|---|---|
| Picks one of a list, stays on this phone, and is undone by picking again (source, recipient, skip length) | The tap on the row |
| Sends, deletes, replaces, installs or stops something | A named button. Rows only select. |
| Sets more than one thing together (model and thinking) | Save (CH-11, CH-13) |
| Adjusts one value with a slider | The slider itself (P-09) |

Send to a conversation adds the item to the message being written. Nothing
is sent until Send is pressed in that conversation. Only one sheet is open at a
time; opening another replaces it (P-19). The player panel is not a sheet, so
a sheet may open above it.

A row that opens something shows a chevron. A row that does something shows
no chevron. A row that does nothing is not tappable and looks it.

## 6. Playing things

### The target is always named before anything plays

The confirmed fault in 2.34 was that Resume on a Pi item played on the phone
with no warning. The rule that prevents it:

- Tapping a file opens its sheet. For something playable the first group is
  Play: one row per output, with the output in the row's words, whether it is
  available, and what it replaces if that output is busy (P-22). The other
  things the file can do follow in the same sheet (M-10).
- A row in History says where it last played. Its sheet offers "Resume on Pi
  screen from 6:29", "Start over on Pi screen" and "Play on this phone". The
  output is part of the button's words.
- Starting on an output that is already playing asks first, in a sheet.

### One player, three sizes

One session per output. Every size shows the same output name, title, state
and controls, read from the same session (P-10, P-21).

| Size | Where | Contents |
|---|---|---|
| Mini row | Above the bottom bar on every place, while a session is active | Output and state, title, Pause or Resume, Stop, Volume, Speed (P-18) |
| Panel | Floats to half height when the mini row is tapped, never scrolls | Handle, title, seek, transport, the four settings (P-13 to P-17) |
| Page | Media / Pi screen or Media / This phone | Picture or art, seek, transport, the four settings, output switch |

On the phone output, video fills the page's picture area and can go full
screen. Full screen is a mode of that page, not another player. The Android
media notification is the fourth surface of the same session (P-20).

Transport is one row: Favorite, Rewind, Pause or Resume, Forward, Skip
length, Stop (P-02, P-03). Pause or Resume is the one accent-filled control.
Below it a two by two grid: Volume, Speed, Rotate, Loop (P-04). Volume and
Speed open a slider sheet and apply at once (P-06, P-09). Rotate and Loop
change on tap and apply two seconds after the last tap, showing "applying"
until then (P-07, P-08). Stop cancels anything still waiting (P-11).

When the Pi screen has no session, its page shows the cover image and the
ways to put something on the screen. It never shows a row of dead controls.

## 7. Status

One vocabulary, always a coloured dot followed by words. Colour alone never
carries the meaning. The mock's `runChecks()` rejects any status word that is
not in this table.

| Dot | Meaning | Words |
|---|---|---|
| Green | Working | Online, Ready, Connected, Playing, Live, Recording, Delivered, Allowed, Added, or a count such as "6 videos" |
| Amber | Working, needs attention | Checking, Connecting, Loading, Low power, "applying" after a value, or a part count such as "1 of 2 connected" |
| Red | Did not work | Failed, Blocked |
| Grey | Not present, by design or for now | Offline, Disconnected, Paused, Stopped, Not set up, Not added, Showing the cover |

The line at the top of a page may say the same thing as a sentence, such as
"Raspberry Pi is online".

A command that fails does not change what is playing, so the session stays
Playing and a notice on the page says what failed and offers Try again.

When the Pi cannot be reached, every screen says so the same way: a grey
status, one notice, and one action that opens Connection.

A value that has not been measured is not shown. There is no dash, no
"unavailable" and no "planned" inside the phone (CH-18, CH-27, T-06). A
screen whose data needs something that is missing leads with that one fact
and the way to fix it.

## 7a. What each kind of item can do

One list, used by Media, Received, Captures, conversations, notes, pins and
From another app. The same item offers the same actions under the same names
wherever it appears (M-10, N-08, N-09). The mock builds every item sheet from
`itemActions()` in `sheets.js`.

| Action | Video, audio | Image | Document | Text | Link | Folder |
|---|---|---|---|---|---|---|
| Play on Pi screen, Play on this phone | yes | | | | yes | |
| Show on Pi screen | | yes | yes | yes | | |
| Open (look at it here) | | yes | yes | | | yes |
| Open in VLC | video | | | | | |
| Set as the Pi cover | | yes | | | | |
| Copy the text | | | | yes | | |
| Send to a device | yes | yes | yes | yes | yes | yes |
| Send to a conversation | yes | yes | yes | yes | yes | |
| Add to a note | yes | yes | yes | yes | yes | |
| Save as a pin | yes | yes | yes | yes | yes | |
| Save on this phone | yes | yes | yes | | | yes |
| Share with another app | yes | yes | yes | yes | yes | yes |

Every kind but a folder can go to five places: the Pi screen, a device, a
conversation, a note and a pin (owner, 2026-09-30). From another app shows
those five and leaves out Save on this phone, Open and Share with another
app, because the item came from this phone. File details is added for items
that live on a drive, Delete for captures, and Take out of this note for an
item inside a note. Share with another app opens Android's own share menu.

csync puts three entries in the share menu of other apps: csync (asks where
the item goes), Send to Pi screen (no question), and Send to your last
device. They are listed on the Widgets page with the widgets, tiles and
shortcuts.

## 8. Words on screen

- No ellipsis anywhere, as text, as a placeholder or as an icon (G-12). A long
  title wraps to two lines and then fades at the end of the second line.
- Titles are the readable name. The raw filename and path are in the item's
  facts sheet (M-13).
- Section labels are sentence case.
- A line under a title joins at most two short facts with a middle dot, such
  as "YouTube · 6:29 left" (H-09). Status is never written that way; it uses
  the dot and words from section 7.
- Text is what a person would say. No revision numbers, host types, internal
  names or advice about the app's own roadmap (G-27).

## 9. One component per job

| Job | Component | Used for |
|---|---|---|
| Say where you are | Top bar | Every screen |
| Name the page | Heading | Section 4 |
| Group a list | Section label, plain or collapsible | Every list; Home's three sections collapse (H-07, H-08) |
| Show one thing in a list | Row | Devices, files, conversations, settings, captures, transfers |
| Show one thing in a grid | Tile, the same data as a row | Home capabilities, player settings, measurements |
| Switch view or pick one of a few | Segmented control | Media views, Chat views, Search scope, Note mode, Theme, Text size, Fit |
| Act | Button: primary, secondary, quiet, danger | One primary per screen |
| Act from a bar or a row end | Icon button | Top bar actions, row actions, transport |
| Type | Field | Search, message, note, address |
| Choose or confirm | Sheet | Section 5 |
| Say how something is | Status | Section 7 |
| Warn about the page | Notice | Pi offline, drive missing, send failed |
| Say there is nothing | Empty state | Icon, one line, one action |
| Say it is coming | Loading state | Camera preview, player picture, lists |
| Confirm it happened | Toast | After every action that changes something |

Every tab and button has an icon on its left (G-13). The accent colour marks
the one primary action on a screen and the selected item in a control. Icons
in rows and tiles are neutral. Warnings are amber and faults are red, never
the accent.
