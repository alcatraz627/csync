# Android UI system proposal

This is a design and implementation contract for the csync Android UI pass. It is not a complete component library. The [revised screen sheet](../assets/android-ui-direction-2.svg) and [state sheet](../assets/android-ui-direction-2-states.svg) show the intended hierarchy. [Emulator captures](../assets/android-ui-live/) show the first Home, Media, More, and mini player implementation. The Android resource files remain the source for shipped colors and themes.

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
| Navigation item | icon, selected mark, and spoken destination name | Main destinations and More children |
| Labeled row | device, folder, file, history, diagnostic; optional supporting line and trailing state | Home roster, Media library, Share recipient/inbox, Tools |
| Action | primary, quiet, destructive; enabled, busy, failed | Share Send, Camera Record, player Pause/Resume and Stop |
| Status text | observed online/offline, connecting, unavailable, error | Device roster, Pi media connection, Camera preview |
| Selection tab | selected, idle, disabled | Media Files/History/Connections, Chat filters |
| Input and search | scoped prompt, entry, and submit | Media search, Chat composer, global search proposal |
| Transport control | Pause **or** Resume, seek, Stop; pending and failed command states | Mini player and full player |
| Appearance choice | named primary color, selected marker, theme preview | Settings and every screen preview |

These are roles, not a mandate to wrap every screen in cards. A row can be plain with a divider. The action role does not make every item a full-width button. Add a primitive to code only when two real callers need the same behavior or when a single caller needs a stateful control that should be centralized.

## Composites and behavior

| Composite | Parts | Contract |
|---|---|---|
| Navigation shell | Destinations, current location, optional mini player | The mini player sits above navigation only for an active session; its body opens full controls. The exact destination set remains open for owner review. |
| Mini player | Target, title, observed state, progress, Pause/Resume, Stop | Target and state match the full player. Stop stays one tap away. Pending commands show progress and failure; no optimistic false pause. |
| Full player | Media identity, target, position, seek, volume, transport, Stop | State comes from the active Pi or phone player, not a local button label. Pi starts muted; a changed volume is visible. |
| Media library | Source selector, search, Files/History/Connections, file rows | Drive disappearance preserves history, clears stale browse results, and explains Resume failure. |
| Output chooser | File identity, Pi screen, phone/phone HDMI, availability | A file tap chooses an output. Only available targets are actionable, and failure returns to the file rather than losing context. |
| Share flow | Named recipient, text or file action, and inbox route | Keep receiver and delivery state visible. Failed upload retains context and offers a useful retry path. |
| Conversation | Thread identity, messages, media result, composer | A returned media item opens the matching controls without implying the assistant owns playback. |
| Camera capture bar | Preview state, Photo, Record/Stop record | Recording state is unmistakable; leaving Camera closes the preview stream. |
| Diagnostics | Observed status, cause, next check, and details | Tools names its evidence and separates observations from suggested actions. |
| Settings group | Persistent choice, current value, and scope | Theme, color, output, and assistant settings carry through their callers. |

The review page previews nine composite choices; its Navigation shell example contains the mini player, while the mini player retains its own behavior contract here. Share's composer and inbox, Chat's conversation list, and Tools' diagnostics remain distinct workflows. The agent may read player and library state and call the same media actions; it does not own these UI surfaces.

## Round 4 review contract

The [whole-app review page](../assets/android-ui-variants/index.html) is a visual proposal. Its screen chips cover Home, search, Media, output choice, player, Share, Chat, Camera, Tools, Settings, and More. The behavior coverage map points to open work in the [improvement backlog](android-improvement-backlog.md) and the [adversarial review](../.claude/output/20260926-0324-adversarial-review/indictment.md). A mock does not establish that a feature is built or reliable.

The review separates four decisions:

The screen treatments now differ in composition on every screen. A is a compact route list with the main actions close to the title. B groups work into sections and cards. C leads with one current task or device and gives its primary action a focused surface. These are review directions; a choice does not remove the other actions or states listed below. The small primitive and composite previews use the same three visual treatments, so each shared choice can be compared with its screen callers.

| Decision | Scope | Reconciliation rule |
|---|---|---|
| Screen layout A/B/C | One screen at a time | Preserve all screen picks, including untouched B defaults. A screen choice changes its hierarchy and density. |
| Primitive and composite A/B/C | Every caller of that shared role | Apply the selected role consistently across screens. A local screen choice does not silently replace the shared role. |
| Icon identity | Each named destination or feature concept | Use one selected identity at every caller. Action glyphs may be icon-only for transport and navigation when the control retains a spoken label; task actions use icon plus text. |
| Primary color and theme | All screens and activities | Keep the named choice and check both themes, readable text, system bars, selected state, and semantic status colors. |

Before Android implementation, turn the owner's full feedback string into a decision ledger. Include every screen, primitive, composite, icon, color, and written note. Record mixed A/B/C choices as intentional or unresolved after showing a combined preview; do not silently pick one treatment or discard an unmentioned screen. Reconcile conflicts with the owner before changing the shared code. The unselected visual alternatives remain review references rather than three parallel production interfaces.

### Color roles

The current Android app ships Coral, Teal, Violet, and Rust in `colors.xml`. The review adds Blue, Leaf, Rose, and Gold as proposed choices. The four additions are not yet Android settings or resources.

| Choice | Light fill | Light text | Dark preview fill | Status |
|---|---|---|---|---|
| Coral | `#E4572E` | `#AD3C1E` | `#FF9477` | Shipped fill; text and dark tuning proposed |
| Teal | `#0D9488` | `#087266` | `#61D4C6` | Shipped fill; text and dark tuning proposed |
| Violet | `#7C5CFF` | `#6241D4` | `#B39EFF` | Shipped fill; text and dark tuning proposed |
| Rust | `#C2410C` | `#A3330B` | `#F68A5F` | Shipped fill; text and dark tuning proposed |
| Blue | `#2768B2` | `#235A99` | `#80B8F4` | Proposed |
| Leaf | `#287D45` | `#246C3D` | `#80D69A` | Proposed |
| Rose | `#B23773` | `#982A62` | `#F390BF` | Proposed |
| Gold | `#8E6500` | `#795600` | `#E7BD64` | Proposed |

The fill, text, and on-fill roles are separate. The HTML preview darkens each light-theme action fill to 85% of its chosen color before placing white text on it; swatches and identity accents retain the named color. This is a contrast proposal, not an Android resource change. Measure actual rendered contrast before committing Android values; the adversarial review found small accent text below 4.5:1 with three shipped accents. Keep status colors semantic instead of recoloring errors or reachability with the chosen primary.

### Controls and behavior that survive a visual choice

Use a leading icon and a verb for Share Send, clipboard, Camera Photo/Record, output selection, retry, and playback Stop. Icon-only navigation and transport controls need a visible selected or pressed state, a spoken name, and a full touch target. Use SVG mock glyphs only as direction references; Android should use its chosen vector assets consistently.

Preserve the adversarial review's player and navigation requirements through every treatment: a mini-player row opens the same named output in full controls; loading, playing, paused, finished, pending, and failed states remain distinct; Stop stays immediate; More children return to More; source, section, search scope, and content agree; output choice names availability, muted Pi startup, and replacement effects. Home shows observed named-device state and a real next action. Tools remains usable with large text. Shared appearance must reach Media and system bars.

The backlog also remains in scope after a design pick: slow or failed cast/stream playback, Pi frame rate and power, rotation and loop, direct YouTube Share, native Cast receiver choice, disconnected drives and access, widgets and quick actions, launcher and notification identity, process monitoring, app performance, and phone performance. The HTML coverage map shows where each item enters the proposed UI. Hardware and runtime acceptance still require the separate checks listed in the backlog.

## Drift checks for each UI round and implementation

1. Compare the whole rendered Home and Media screens against the screen jobs above. Home must show named device reachability and a useful next action. Media must reveal source, search, Files, History, and real rows without scrolling past a setup panel.
2. Check the same semantic state across Home, Media, mini player, full player, output chooser, and the agent-facing player state. Target, title, position, volume, pending command, and error must agree or show why they differ.
3. In light and dark themes and each accent, check selected state, contrast, row grouping, overflow, and which action draws the eye first. Accent is a role, not a decoration quota.
4. Render a narrow phone and enlarged system font. Preserve readable labels, 48dp hit areas, and visible Stop without overlapping navigation or the mini player.
5. Exercise idle, buffering, playing, paused, failed command, offline Pi, disconnected drive, failed upload, and simultaneous Pi and phone playback. Capture screen images and test the action, not only the layout.
6. Before merging any new component, name its two callers or its unique stateful reason. Compare sibling screens and remove duplicated one-off styling. Use Android color and dimension resources rather than copying SVG colors or raw pixels.

The Home, Media, More, and mini player layouts have been inspected in a running emulator. Pi file browsing and the mini player's Pause, Resume, and Stop were exercised against the live Pi. The remaining screens, accessibility, narrow-screen, theme, phone, and failure-state checks are still open.

The 2026-09-26 installed-app check rendered Home and Media in both app themes. At 720×1280 with 1.3× font scale, Media clipped its search hint and later tabs; Home pushed its contextual action below the first viewport. These are open Android implementation defects. The HTML review page's narrow-width result does not clear them. Full mini/full-player target, title, state, action, and touch-area parity was not exercised in that run because no active player session was available.
