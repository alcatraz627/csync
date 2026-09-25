# Android UI direction 2: put the task first

This is a **proposal**, not an implemented app or an accepted design. The [eight-screen mock](../assets/android-ui-direction-2.svg) and [five critical states](../assets/android-ui-direction-2-states.svg) use example content. Their numbers, media names, reachability, and playback state do not describe the owner's devices.

## Request and provenance

The owner asked: "you've spammed so many full expanding buttons, let's make it sleeker. Maybe we show a mini player on top of the app when running that allows quick acccess to pause / play / stop, and a link to the full control screen." After the first mock, the owner said: "The mocks are erm, bad. Do you have a local model via lm you can use to ideate better on mocks? Your mocks are actually making the app worse."

The Android source checkout was at `82794741d9883318e7448dfe8d5eddfd7dc6d33b` when this was written, with uncommitted UI and Media changes. The screenshots under [assets/ui-current](../assets/ui-current/) were taken from the installed v2.11 emulator app on 2026-09-25. Home, Share, Chat, and Camera were taken from its light theme; Media was taken from its dark theme during a muted Pi YouTube playback test. These screenshots are the baseline, not the mock. The Pi player test is reported in [media operations](media-operations.md).

## What cannot disappear

| Existing surface | User-visible behavior to preserve | Evidence |
|---|---|---|
| Home | Named device reachability, entry to sharing, assistant and Media, and tool explanations | [Home screenshot](../assets/ui-current/home.png), [inherited brief](/Users/alcatraz627/Code/csync-hub/docs/ui-design-brief.md) |
| Share | Pick a named recipient, send text/clipboard/files, view the inbox and received items | [Share screenshot](../assets/ui-current/share.png), [inherited brief](/Users/alcatraz627/Code/csync-hub/docs/ui-design-brief.md) |
| Chat | Conversation list and history, assistant status, new conversation, search, background reply notifications | [Chat screenshot](../assets/ui-current/chat.png), [inherited brief](/Users/alcatraz627/Code/csync-hub/docs/ui-design-brief.md) |
| Media | Pi drive browse/search, History, SMB/FTP access, Pi and phone playback, wallpaper, YouTube and phone-file casting, immediate Stop | [Media screenshot](../assets/ui-current/media-playing.png), [Media source](/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/MediaActivity.java) |
| Camera | Pi preview only while visible, photo, recording, saved captures | [Camera screenshot](../assets/ui-current/camera.png), [Camera source](/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/CameraController.java) |
| Tools and Settings | Process view and widget utilities; device, assistant, receiver, theme and accent controls | [Inherited brief](/Users/alcatraz627/Code/csync-hub/docs/ui-design-brief.md), [main activity](/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/MainActivity.java) |

The original five destinations, Home, Share, Chat, Tools, and Settings, were ratified in the inherited brief. Camera and Media arrived later. Direction 2 proposes a navigation change for review; it does not erase any of those surfaces.

## Rejections and observed problems

| Evidence | Design consequence |
|---|---|
| The owner rejected the [first mock](../assets/android-ui-mocks.svg), recorded in [the redesign brief](android-ui-redesign.md). It flattened distinct tasks into repeated cards. | Keep Share, Chat, Media, Camera, Tools, and Settings visually and functionally distinct. |
| The owner's latest complaint names oversized full-width buttons and asks for a mini player. | Give one primary action per screen. Move playback controls to a compact active-state bar and a full player. |
| The [Media screenshot](../assets/ui-current/media-playing.png) shows four orange section pills, three orange setup pills, and six orange control pills. Pause and Resume appear together. | Use text tabs for sections, ordinary rows for files, one transport state, and one-tap Stop. |
| The [Home screenshot](../assets/ui-current/home.png) places a long assistant-tool manual before useful actions. | Put device state, browse, share, chat, resume, and camera in the first viewport; move tool reference to Tools. |
| The [Camera screenshot](../assets/ui-current/camera.png) gives controls the same pill treatment as Media and exposes a raw "Camera: null" error. | Let preview dominate, distinguish photo from record, and translate missing errors into human text. |
| The [inherited brief](/Users/alcatraz627/Code/csync-hub/docs/ui-design-brief.md) specifies a light default with slate neutrals and coral, teal, violet, or rust accents. | Keep that language. Do not impose a dark default or a terminal dashboard style. |

I used `lm see --ui` on the Home and Media screenshots for element inventory. A local `lm q --big` ideation pass suggested more large cards and pills, so I rejected its layout advice. The screenshot readings and current source, not the model's taste, ground this proposal.

## Proposed direction

**Task first, controls in context.** Home shows the reachable Pi and the few actions the owner came to perform. Media gives the library most of the viewport. A session bar appears above navigation only while playback is active; it shows the real target, title, observed state, Pause or Resume, and Stop. Tapping the body opens the full player. Share remains a sender and inbox. Chat remains a conversation space. Camera gives the preview priority. Tools is a compact diagnostics list, and Settings holds persistent choices.

The [mock sheet](../assets/android-ui-direction-2.svg) proposes five labeled bottom destinations: Home, Media, Share, Chat, and More. More opens separate Camera, Tools, and Settings screens; Home also offers a Camera entry. This is the open navigation decision. It moves Tools and Settings from the original bottom bar, so their discoverability must be checked with real use before implementation. The alternative is a four-item bottom bar plus a visible utility menu in the header; both need a narrow-screen and large-font test. Neither changes the actual jobs of Share or Chat.

Accent means primary action or selected location. Green means observed reachability, not a decorative badge. Stop is always available in the active mini player and full player, and cannot be hidden in More. Pi playback starts muted; the full player exposes a deliberate volume control. No mock implies that Pi and phone are synchronized. If both have sessions, the bar needs a target switcher or two compact session rows.

## Two critique and revision rounds

The owner said the second direction was "a LOT better" and requested two more gripe, planning, and improvement rounds before building it. The [initial sheet](../assets/android-ui-direction-2-before-rounds.svg) and [round-one sheet](../assets/android-ui-direction-2-after-round1.svg) preserve the visual changes. `lm see diff` reports were saved at `/Users/alcatraz627/Code/local-models/outputs/see/20260925T182055Z-diff-android-ui-direction-2-before-rounds.svg` and `/Users/alcatraz627/Code/local-models/outputs/see/20260925T182438Z-diff-android-ui-direction-2-after-round1.svg`. I read both rendered sheets as well as the difference reports; the model inventories changes, while the design judgments below are mine.

| Round | Gripe grounded in the rendered sheet | Planned change | Result in the new mock |
|---|---|---|---|
| 1: playback and navigation | The mini player's square Stop glyph could be mistaken for another control, and the full player showed Pause twice. Five destinations also lacked a selected-state cue. | Give Pause and Stop text in the mini player, add progress and a body affordance to open the full player, remove the duplicate overlay control, label the active destination. | The mini player names **Pi screen**, playback state, title, Pause, and Stop. The full player says where Pi video appears and keeps one transport control. The navigation shows an active underline. |
| 2: task hierarchy and media states | Home treated Media as a dominant hero even though Share and Chat are core. Media's **All files** area mostly showed folders and did not explain output choice. Camera's Photo and Record actions looked like one ambiguous control. | Make Home's three core jobs equal-weight rows; show playable file rows and an explicit output choice; separate shutter and record controls. Mock share handoff, copying progress, missing drive, and concurrent Pi/phone sessions. | [Main sheet](../assets/android-ui-direction-2.svg) has task rows and file examples. [State sheet](../assets/android-ui-direction-2-states.svg) shows a YouTube-app handoff without URL entry, Pi/phone output choice, transparent full-file transfer, disconnected Elements with History retained, and two individually controlled sessions. |

The local-model difference reports confirmed the intended control-label and layout changes. They do not establish that the proposal is usable on a real phone.

The owner then singled out **Home and Media hierarchy** and clarified that shared primitives, variants, and composites should guide the mock rounds as well as the later Android build. The [UI system proposal](android-ui-system.md) now defines each screen's job, real component callers, state variants, and cross-screen checks. In the latest [main sheet](../assets/android-ui-direction-2.svg), Home starts with a named device roster, then one media continuation entry and short actions. Media starts with the selected drive, scoped search, Files/History/Connections, and actual file rows. The active film appears in the persistent mini player, not in a second large Media block. This is another design revision, not owner acceptance or a shipped app change.

## What the mocks have not proved

The sheets are layout sketches. The main sheet is light with active Pi playback; the two-player state uses a dark variant. They do not yet cover an alternate accent, narrow phone, large text, idle playback, buffering, failed command, camera recording, or an upload that actually fails. They do not prove touch targets, accessibility semantics, or Android navigation behavior. The mock's Cancel upload control is planned; the current app does not offer it.

The [UI system proposal](android-ui-system.md) inventories existing Android styles and layouts and names the primitives, variants, and composites used by the revised mocks. Its drift checks are also the implementation checks. The current Android app has not been migrated to those components.

Playback reliability remains the first implementation priority. The visual redesign must not hide lag or failed casting behind a polished loading state.
