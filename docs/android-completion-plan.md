<!-- sessions: catch-mock-d0@2026-09-30 -->
# csync phone app: the completion plan

This plan covers the owner's four asks of 2026-09-30 (night). It lists what
exists today with the file and line that shows it, what is proposed, and the
order of work. The app model in `docs/android-app-model.md` and the rulings in
`docs/android-app-decisions.md` still govern; nothing here overrides them.

Each stream is built the same way: read the siblings, build, run it on the
emulator, read the capture, then show it.

## Stream 1. Launcher presence: widgets, quick actions, icons, splash

### What exists today

| Surface | State | Evidence |
|---|---|---|
| Launcher widgets | One, the xkcd comic | `AndroidManifest.xml:94`, `XkcdWidgetProvider.java` |
| Quick Settings tiles | None | No `TileService` anywhere in `app/src/main` |
| App shortcuts (press and hold the icon) | None. The Tools page says they are "planned", which ruling B13 forbids | `MainActivity.java:354`, `page_tools_v2.xml:96` |
| Share menu entries | One, `csync`. No direct targets | `AndroidManifest.xml:53` |
| Icon | One mesh-hub vector, coral on dark | `drawable/ic_launcher_foreground.xml` |
| Splash | A static vector on a fixed dark colour | `themes.xml:15` to `17`, `drawable/splash_icon.xml` |

### What gets built

**Widgets (four, as the mock's Widgets page lists them).** Each follows the
xkcd widget's pattern: a provider for taps and a job for the network read,
because a receiver gets no background network.

| Widget | Shows | Taps |
|---|---|---|
| Media remote | What the Pi screen is playing, its state | Pause or Resume, Stop, open the player |
| Pi status | Online or offline, power, drives | Opens Tools |
| Camera glance | The latest still from the Pi camera | Refresh, open the camera |
| xkcd | Already built | Restyled to match the other three |

A fifth is proposed beyond the mock: **Ask the Pi**, a one-row widget that
opens a new conversation with the keyboard up. It is the shortest path to the
assistant from the home screen.

**Quick actions.** Three static app shortcuts (New chat, Send to a device,
Pi camera live) plus one dynamic shortcut per recent conversation. Four Quick
Settings tiles (Pi camera, Send the clipboard, Pi screen, Send the last
photo). Two more share-menu entries (Send to Pi screen, Send to your last
device) as direct share targets.

**Icon set.** Six launcher icons, each a full adaptive icon with a themed
(monochrome) layer, chosen under Settings, Appearance. Android switches a
launcher icon through activity aliases, so picking one makes the launcher
redraw and can drop the icon from a home-screen folder once; the picker says
so before it applies.

| Name | Idea |
|---|---|
| Hub | Today's mesh hub, cleaned up. The default |
| Orbit | The hub as a ring with three satellites, on a gradient |
| Signal | Concentric arcs leaving a node |
| Prism | A faceted shape, in the accent's gradient |
| Terminal | A prompt mark, for the chat-first user |
| Mono | One colour on black, no gradient |

**Splash.** An animated vector: the hub node pulses, the three links draw
outward, the device nodes pop in, in warm orange through violet on a fixed deep
background. It does not follow the chosen accent: Android draws the splash
before the app can read its settings. Under one second, then a short fade into
Home. On Android 11 and older the static icon stays, since the animated splash
needs Android 12.

### How it is verified

Each widget is added to the emulator launcher and captured in dark and light,
with the Pi reachable and with it off. Each shortcut and tile is fired and the
place it opens is captured. Each icon is selected and the launcher captured.
The splash is recorded as a short screen recording and frames are read back.

## Stream 2. Chat for a heavy Claude Code and ChatGPT user

### What exists today

| Capability | State | Evidence |
|---|---|---|
| Reply streaming | One block per step (thinking, tool call, text). No word-by-word text | `assist/main.go:189` |
| Stop a reply | Not possible. The request runs to the end | No cancel path in `assist/main.go:131` to `224` |
| Regenerate, edit and resend | Not possible. The Pi only appends to a conversation or forgets all of it | `assist/main.go:31`, `:44` |
| The Pi's memory of a conversation | In memory only. An assistant restart forgets it while the phone still shows it | `assist/main.go:31` |
| Tool calls | A collapsed text block per call, raw JSON inside | `MainActivity.java:2350` |
| Message actions | Copy and Fork | `MainActivity.java:2459` |
| Attachments | Image or file, 8 MB, sent with a line of text naming them | `MainActivity.java:1881`, `:2276` |
| Reply notification | Opens the app, not the conversation that replied | `ChatService.java:111` |
| Delete a conversation | Deletes at once, no confirmation | `MainActivity.java:2182` |
| Hidden long-press on the title | Opens a roadmap file | `MainActivity.java:1692` |
| Export | Not built | Mock `sheets.js` `export-chat` only |
| Conversations | Kept on this phone only | `ChatStore.java` |

### The proposed spec

Ordered by how much each changes the feel. The first group needs the Pi
assistant changed and redeployed; the second is phone only.

**Needs the Pi assistant**

1. **Words appear as they are written.** Text streams token by token for all
   three providers.
2. **Stop.** While a reply runs, Send becomes Stop. It cancels on the Pi, keeps
   what arrived, and marks the reply as stopped.
3. **Regenerate and edit.** Regenerate reruns the last reply, optionally with
   another model. Edit reopens your message in the box and reruns from there.
   Both need the Pi to rewind a conversation to a given message.
4. **Send while it works.** A message sent during a reply is queued and shown
   as queued, then sent when the reply ends. Stop clears the queue.
5. **The Pi remembers.** Conversations are saved on the Pi, so a restart does
   not orphan them, and a conversation started on the phone can be read from
   another device later.
6. **Usage per reply.** Tokens in and out and the time taken, shown quietly
   under a reply when tapped.

**Phone only**

7. **One work strip per reply.** Thinking and tool calls fold into one line,
   "Worked for 12 s, 3 tools", that opens to a timeline. Each tool shows a
   result card by kind (media, image, facts, file, note, devices), as the mock
   draws them, instead of raw JSON.
8. **Code that behaves like code.** Code blocks scroll sideways, carry a copy
   button and the language name, and never wrap mid-token.
9. **The slash menu.** Typing `/` lists saved skills from the Pi and the
   common tools (play, find, send, note, camera, health). Typing `@` offers
   devices, notes and recent files to mention.
10. **One message box.** The mock's composer: add, model pill, Send, all in
    one outlined box, growing to six lines, with a draft kept per
    conversation.
11. **Reading a long reply.** The view stops following when you scroll up, and
    a jump-to-latest button appears.
12. **Find in conversation**, and search across all conversations by content,
    not only by title.
13. **Notifications that work like a messenger.** The reply notification
    opens its conversation, lets you answer from the shade, and recent
    conversations appear as share targets and launcher shortcuts.
14. **Export** as Markdown or one tall image, per the mock.
15. **Housekeeping.** Delete asks first. The hidden long-press goes. Timestamps
    group by day. The bottom bar no longer rides above the keyboard.

Not proposed: voice in (the keyboard already offers it), and the assistant
editing its own code (ruling E4 stands).

## Stream 3. Every half-done capability

State words: **built** means it runs in the native app; **partial** means a
piece runs; **design** means the mock only; **unproven** means built and never
exercised.

| # | Capability | State | What is missing | Plan |
|---|---|---|---|---|
| 1 | Settings, one page | partial | Still the old multi-card page; picker does not read live models | Rebuild to the mock, ruling R2 |
| 2 | Providers | partial | Claude left off by ruling; OpenAI through ChatGPT sign-in landed after the last checkpoint and is not re-verified here | Verify OpenAI on the Pi, show honest state per provider |
| 3 | Conversation | partial | Stream 2 | Stream 2 |
| 4 | Share from another app | partial | Three different dialogs by kind, none with the five destinations; says "peer" | One page, five destinations, `ShareActivity.java:76` to `132` |
| 5 | Send to a device from any item | partial | Exists in Share only; no shared action list | One resolver from app model 7a |
| 6 | Widgets, tiles, shortcuts | partial | Stream 1 | Stream 1 |
| 7 | Player honesty | partial | No loading, finished or failed state; no pending command state | Build, then test both outputs at once |
| 8 | Rotate and Loop in the player | design | Pi holds both; no native control | Build |
| 9 | Media notification | unproven | Never exercised with real playback | Exercise on the emulator |
| 10 | Light theme, Large text | unproven | Dark status-bar icons wrong (`themes.xml:14`), accent text contrast, Tools at 1.5 scale | Fix and capture |
| 11 | Home | partial | Owner: too much focus on devices | Stream 4 |
| 12 | Process monitor | partial | Reads "used" memory, shows empty tiles | Build to the mock, goal row #16 |
| 13 | Notes attachments | design | Images only today | Build |
| 14 | Pi screen sources | design | Slideshow, a note, a link are small; screen and one-app share need a receiver on the Pi | Build the small three; spike the share, goal row #9 |
| 15 | Display sheet, per-display tuning | design | The Pi reports no display | Pi reports it, app reads it, ruling R6 |
| 16 | Covers sheet | partial | Wallpaper upload exists; framing does not | Build |
| 17 | Search | built | Content search of conversations missing | Stream 2 item 12 |
| 18 | In-app update | unproven | 2.35 to 2.36 through the app never run | Run it on the next build |
| 19 | Pi drives | unproven | Elements never attached; write protection unproven | Needs the drive plugged in |
| 20 | Pi HDMI picture and sound | unproven | Never verified by eye | Needs eyes on the screen |
| 21 | Pi cold boot with USB | unproven | Only a service restart was tested | Needs a power cycle |
| 22 | Camera error text | unknown | "Camera: null" reported in an old review, not re-checked | Check and fix |
| 23 | Gemini image tool | not started | | Build after stream 2 |
| 24 | Dead layouts | leftover | `page_home.xml`, `page_share.xml`, `page_more.xml`, `page_tools.xml`, `page_camera.xml` are inflated nowhere | Remove once confirmed |
| 25 | Stale records | leftover | `ledger-status.md`, `callouts.jsonl` status | Regenerate from captures at the end |

Rows 19 to 21 need something physical and cannot be finished from here. They
stay listed as waiting on the hardware.

## Stream 4. UI and usability suggestions

Ranked by what the owner meets most often.

1. **Home leads with doing, not with devices.** A "Pick up" card first (what
   was playing, the last conversation), then one row of four large actions
   (Play, Ask, Send, Camera), then status as one quiet line that opens Tools.
   Devices fold into a single row with a count.
2. **One sheet style for every choice.** Replace the remaining Android alert
   dialogs (share-in, custom accent, confirmations) with the kit sheet.
3. **Motion with a job.** A shared 150 ms fade-through between bar places, a
   sheet that springs, a pressed state on every row. Nothing decorative.
4. **Haptics on commit.** A light tick on Send, Save, toggle and transport.
5. **Empty and offline states everywhere.** Every list gets the mock's icon,
   one line and one action; every screen says "the Pi cannot be reached" the
   same way.
6. **Pull to refresh** on Home, Media, Received and Tools, replacing the
   refresh icons where the list is the page.
7. **Predictive back.** Opt in to Android's back preview so a child page peeks
   its parent.
8. **Edge to edge.** Draw behind the system bars with correct insets, which
   also fixes the bar riding above the keyboard.
9. **Readable accent text.** A darker accent shade for small text in light
   theme and a lighter one in dark, so every accent passes 4.5 to 1.
10. **Landscape and tablets.** The player page and a conversation use the
    width; the rest stay one column, centred.
11. **TalkBack pass.** Every icon button spoken, focus order checked, the
    status dot never the only signal.
12. **`MainActivity.java` is 2,799 lines.** Chat, Share and Settings move into
    their own classes as each is rebuilt. No behaviour change by itself, and
    it is what makes the rest of this list cheap.

## Order of work

1. Stream 1, because it is self-contained and needs no ruling.
2. Settings and the provider picker (stream 3 rows 1 and 2).
3. Stream 2, phone-only items first, then the Pi assistant items.
4. Share-in and the shared action list (rows 4 and 5).
5. Player rows 7 to 9, theme row 10.
6. Home and the stream 4 list.
7. The remaining rows, then the stale records.

A build is staged on the Pi after each numbered step, with a hash check.

## What waits on the owner

One decision page, `csync-completion`, carries the open calls: which chat
items to build, which UI suggestions to accept, and which half-done rows to
drop instead of finish. Every question arrives with a recommended answer, so
silence on a row means the recommendation stands.
