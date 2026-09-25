# Android app screen redesign

The [first ten screen mocks](../assets/android-ui-mocks.svg) were rejected by the owner on 2026-09-25 because they made the app worse. Keep them only as a record of what to avoid. A replacement design must follow the app's actual screens, real media behavior, and owner feedback before UI implementation.

A [second direction](android-ui-direction-2.md) now uses actual emulator screenshots and the owner's rejection record. Its [eight-screen visual sheet](../assets/android-ui-direction-2.svg) is a proposal for review, not an accepted implementation. The local `lm` model supplied element inventories; its generic card-and-pill redesign advice was rejected.

## Existing app and visual language

The inherited [UI brief](/Users/alcatraz627/Code/csync-hub/docs/ui-design-brief.md) defines csync as the phone's way to reach the owner's devices: Share and Chat are core, while the widget and system monitor are utilities. Its five original destinations were Home, Share, Chat, Tools, and Settings. Camera was added as a sixth tab; Media was added as a separate activity reached from Home or Tools. The light and dark themes use slate backgrounds, white/dark cards, readable secondary text, and selectable coral, teal, violet, or rust accents. Preserve the named-device model, the Share inbox, chat history, background replies, and the Camera lifecycle.

The Media activity currently uses wide primary-colored buttons for section switching, wallpaper, YouTube, file casting, player commands, volume, and settings. On a real phone these occupy most of the first screen while file results get a small middle area. The fixed player controls are useful during playback but dominate the screen when idle. The current six unlabeled bottom icons also hide Media behind other pages.

## Navigation and control hierarchy [REWORK]

The rejected mock proposed **Home, Media, Share, Chat, Camera, More** and repeated the same card pattern on every screen. Do not implement that navigation or layout without a new design review. The inherited Home, Share, Chat, Tools, Settings, and Camera surfaces must retain their different jobs and established behavior. Media needs easier access, but the destination count and grouping need a better solution than tiny labels or indiscriminate merging.

One mini player appears above the bottom bar when either Pi or phone playback has an active item. It shows the title, output, observed state, short progress, and **Pause/Resume** and **Stop**. Tapping its body opens the full player. It disappears after Stop or completion; a finished item remains in History. When the phone is offline, stale state is visibly marked and controls do not claim success. Pi control reads the Pi service; phone control reads the foreground playback service. Both use the existing command and acknowledgement paths. The mini player must not guess which target is active when both have sessions; it must show a target chooser or both sessions.

The full player holds seeking, output choice, safe volume, speed, audio/subtitle tracks when supported, errors, and diagnostics. Its first row shows the current target. Playback starts muted on the Pi until the user deliberately sets a volume. **Stop** remains one tap from the mini player and full player, and restores the saved Pi wallpaper.

## Screen inventory [REWORK]

| Screen | Main content | Primary action |
|---|---|---|
| Home | Device reachability, continue watching, recent activity | Resume, browse, send, or ask Pi |
| Media library | Search across connected drives, folder list, video/audio rows, absent-drive guidance | Choose a file and output |
| Full player | Playback image/state, progress, transport, output and settings | Pause/Resume, seek, or Stop |
| History | Recent files, target, position, disconnected-drive state | Resume or start over |
| File access | SMB, FTP, and SFTP addresses with share health | Copy address or diagnose |
| Share | Named recipient, composer, file action, inbox and recent transfers | Send to selected peer |
| Chat | Conversations, assistant status, media-aware result actions | Send message or use a surfaced media action |
| Camera | Live Pi preview, photo, record, captures, output choice | Capture or show on screen |
| Tools | Updater, system monitor, media diagnostics, widget help | Run the named utility |
| Settings | Devices, assistant, playback defaults, appearance, access | Adjust a preference |

## States to mock and test before implementation

The rejected visual sheet shows only the light coral theme with playback active and uses generic cards too uniformly. Use the local `lm` tools for critique and alternative concepts, but judge them against the inherited brief and app behavior: a local model suggested merging Share with Chat, a dark default, and a synchronized Pi-and-phone mode, none of which is supported by current requirements. The next mock round needs actual app screenshots, dark and alternate-accent renders, narrow-screen and large-font layouts. Draw and test idle, loading, paused, buffering, ended, offline, failed-output, disconnected-drive, and concurrent Pi/phone sessions. A visible error must state whether a command applied, queued, failed, or timed out. Camera preview must close on tab exit even while the mini player stays. The share-sheet cast picker must retain **Send to peer**.

The mocks include camera-to-screen and richer playback settings as intended destinations. Those capabilities are still being built; the current app must not expose dead controls. The mock's sample media names and status numbers illustrate layout only, not a live library or acceptance result.
