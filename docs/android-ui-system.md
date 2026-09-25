# Android UI system proposal

This is a design and implementation contract for the next csync Android UI pass. It is not an implemented component library. The [revised screen sheet](../assets/android-ui-direction-2.svg) and [state sheet](../assets/android-ui-direction-2-states.svg) show the intended hierarchy; the Android resource files remain the source for shipped colors and themes.

## Screen jobs and hierarchy

| Screen | First thing to understand | Main content | Secondary path |
|---|---|---|---|
| Home | Which named devices are reachable | Device roster and one useful next action | Share, camera, diagnostics |
| Media | Which storage is being browsed | Search, Files, History, and file rows | Connections, output choice, full player |
| Full player | What is playing, where, and whether it is responding | Position, Pause or Resume, seek, volume, Stop | Tracks and speed |
| Share | Who will receive the item | Message/file composer and inbox | Recipient change |
| Chat | Which conversation is open | Conversation list or messages | Search and new conversation |
| Camera | Whether the Pi preview is live | Preview, Photo, Record | Saved captures |
| Tools | What needs attention | Device and app diagnostics | Detail and safe actions |
| Settings | What choice will persist | Connection, playback, theme settings | Device roster |

Home must not turn into a second bottom navigation. Its device rows answer reachability; its shortcuts reflect the current context. When an active session is already in the mini player, Home does not repeat that session as a large media card. Media must show actual browse results in the first viewport. A selected storage source is explicit; Files, History, and Connections are separate destinations. A tapped file opens an output choice before playback. History is available even if a removable drive is disconnected, with the missing source stated when Resume cannot proceed.

## Existing foundations

The current palette lives in [`colors.xml`](/Users/alcatraz627/Code/csync-hub/app/src/main/res/values/colors.xml) and its dark counterpart in [`values-night/colors.xml`](/Users/alcatraz627/Code/csync-hub/app/src/main/res/values-night/colors.xml). [`themes.xml`](/Users/alcatraz627/Code/csync-hub/app/src/main/res/values/themes.xml) defines a Material 3 DayNight base and Coral, Teal, Violet, and Rust accents. Use those semantic resource names in Android; the mock's hex values are illustrative, not a new palette. The current Home, Share, and Chat layouts already use some Material buttons, while [`activity_media.xml`](/Users/alcatraz627/Code/csync-hub/app/src/main/res/layout/activity_media.xml) repeats plain full-width buttons. `MediaActivity.row()` uses raw pixel padding at [`MediaActivity.java:274`](/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/MediaActivity.java:274); the capture row does the same at [`CameraController.java:184`](/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/CameraController.java:184). Those dynamic rows need density-aware dimensions when rebuilt.

| Token | Current source or proposed rule | Use |
|---|---|---|
| Background, surface, surface2, text, dim, border | Existing `@color` resources in both themes | Page, raised item, muted item, copy, supporting copy, divider |
| Accent | Existing theme `colorPrimary`; default Coral | Selected tab and one leading action, never every row |
| Online, offline, danger | Existing `@color` resources | Observed device state and destructive action |
| Type roles | Proposed: page title, row title, supporting text, section label | Shared roles; preserve Android font scaling instead of fixed-height text containers |
| Spacing | Proposed: one density-aware scale for inset, row padding, gap, and section break | Define Android `dimen` resources when the first shared layouts are built; no raw pixel padding |
| Touch area | Proposed: at least 48dp for interactive controls | Icons and compact transport buttons need a full hit area |

## Primitives with callers

| Primitive | Variants and states | Real caller |
|---|---|---|
| Page heading | title; title with contextual subtitle or trailing action | Home, Media, Share, Chat, Camera, Tools, Settings |
| Labeled row | device, folder, file, history, diagnostic; optional supporting line and trailing state | Home roster, Media library, Share recipient/inbox, Tools |
| Action | primary, quiet, destructive; enabled, busy, failed | Share Send, Camera Record, player Pause/Resume and Stop |
| Status text | observed online/offline, connecting, unavailable, error | Device roster, Pi media connection, Camera preview |
| Selection tab | selected, idle, disabled | Media Files/History/Connections, Chat filters |
| Transport control | Pause **or** Resume, seek, Stop; pending and failed command states | Mini player and full player |

These are roles, not a mandate to wrap every screen in cards. A row can be plain with a divider. The action role does not make every item a full-width button. Add a primitive to code only when two real callers need the same behavior or when a single caller needs a stateful control that should be centralized.

## Composites and behavior

| Composite | Parts | Contract |
|---|---|---|
| Navigation shell | Destinations, current location, optional mini player | The mini player sits above navigation only for an active session; its body opens full controls. The exact destination set remains open for owner review. |
| Mini player | Target, title, observed state, progress, Pause/Resume, Stop | Target and state match the full player. Stop stays one tap away. Pending commands show progress and failure; no optimistic false pause. |
| Full player | Media identity, target, position, seek, volume, transport, Stop | State comes from the active Pi or phone player, not a local button label. Pi starts muted; a changed volume is visible. |
| Media library | Source selector, search, Files/History/Connections, file rows | Drive disappearance preserves history, clears stale browse results, and explains Resume failure. |
| Output chooser | File identity, Pi screen, phone/phone HDMI, availability | A file tap chooses an output. Only available targets are actionable, and failure returns to the file rather than losing context. |
| Camera capture bar | Preview state, Photo, Record/Stop record | Recording state is unmistakable; leaving Camera closes the preview stream. |

Share's composer and inbox, Chat's conversation list, and Tools' diagnostics use shared primitives but remain distinct workflows. The agent may read player and library state and call the same media actions; it does not own these UI surfaces.

## Drift checks for each UI round and implementation

1. Compare the whole rendered Home and Media screens against the screen jobs above. Home must show named device reachability and a useful next action. Media must reveal source, search, Files, History, and real rows without scrolling past a setup panel.
2. Check the same semantic state across Home, Media, mini player, full player, output chooser, and the agent-facing player state. Target, title, position, volume, pending command, and error must agree or show why they differ.
3. In light and dark themes and each accent, check selected state, contrast, row grouping, overflow, and which action draws the eye first. Accent is a role, not a decoration quota.
4. Render a narrow phone and enlarged system font. Preserve readable labels, 48dp hit areas, and visible Stop without overlapping navigation or the mini player.
5. Exercise idle, buffering, playing, paused, failed command, offline Pi, disconnected drive, failed upload, and simultaneous Pi and phone playback. Capture screen images and test the action, not only the layout.
6. Before merging any new component, name its two callers or its unique stateful reason. Compare sibling screens and remove duplicated one-off styling. Use Android color and dimension resources rather than copying SVG colors or raw pixels.

The current mocks have only been visually inspected as static concepts. None of these runtime, accessibility, narrow-screen, theme, or failure-state checks is complete for a redesigned Android app.
