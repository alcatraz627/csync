# Media from Pi drives to the projector

Status: implementation and acceptance plan, 2026-09-25. The owner approved Pi and phone deployment/testing. The owner later confirmed moving video on the ARZOPA from app-driven Pi playback. Android app version 2.11/code 13 is staged on the Pi and installed on the real phone through paired wireless ADB after Shizuku restored the connection. Pi audio, the latest wallpaper pixels, phone HDMI, and Elements remain unconfirmed.

| Capability | Current evidence | Remaining acceptance |
| --- | --- | --- |
| Pi library and current USB | The media service returns the SanDisk drive online, lists files, streams byte ranges, and rejects changed files. Its service and mount recovered after a Pi reboot. | Unplug/replug during an active stream and confirm the error on the app. |
| Elements | A stable `/srv/elements` automount, SMB path, FTP path, and offline app entry are configured. | Attach the HDD, check its UUID and filesystem, prove hotplug, identity, reading, and writes as intended. The label-only provisional identity must become a UUID. |
| Pi HDMI player | After the initial failed attempts, the owner confirmed moving video through micro-HDMI0, including an app-driven Play. A later real-phone test found mpv could inherit pause from a prior file; the service now clears pause before each load. The real phone then observed the silent file playing at volume zero, paused, resumed with advancing position, and stopped to idle. Stop restores the saved screen image. The Pi still reports undervoltage and throttling. | Confirm sound at a safe volume and visible wallpaper pixels; remedy power before sustained two-drive playback. |
| Phone-file cast | The emulator's system picker selected a 2.5 MB MP4, uploaded it to `/srv/media/shared/csync-casts/` on the Pi USB drive, and started Pi playback muted. Source and Pi SHA-256 matched; app Stop returned idle. | Test a real phone file and longer transfer, cancellation during upload, and projector pixels. |
| YouTube link | The Pi played the official Blender sample with progressing position and persisted history after a URL validation and isolated yt-dlp/Deno setup. The emulator's Media screen invoked the same cast route. | Confirm pixels and sound for YouTube on the screen; test expiry, unavailable videos, network loss, and agent invocation. |
| Screen image | Android's image picker uploaded a JPEG; the Pi stored it on SD and mpv loaded it after Stop and service restart. | Point the Pi camera at the display or inspect the monitor directly to confirm the chosen pixels and reboot persistence. |
| App updates | The app's Tools button downloads a staged, token-protected signed APK from the Pi. Emulator code 3→4→5→6→7→8 updates completed through Android's package installer without ADB; the first required Android's one-time unknown-source grant. The real phone received code 12 through paired ADB. Its Tools button on code 9 downloaded the same staged APK and reported "csync is already up to date" without opening install settings. A seven-day tailnet browser bootstrap link remains a fallback. | Test the next newer in-app update on the real phone; Android's one-time "Allow from this source" setting is still off there. Android may still require installation approval. |
| Android playback | The emulator browsed 105 files through Load more, played WAV and MP4, rendered full-screen landscape video, and applied an agent-style pause after leaving Media. A foreground media service kept audio playback and telemetry active. An emulator secondary display kept showing MP4 frames while the app returned to Home. Code 7 corrected a preparation-state error found in code 6; code 8 keeps assistant Stop polling alive while loading and rejects unsafe early controls. On the real phone, code 8 browsed the Pi USB, started and stopped a silent Pi file, streamed the same file locally with advancing position, and stopped the phone foreground service. | Exercise the owner's phone and HDMI adapter with video and sound, and determine whether its adapter exposes a separate display or only mirrors. Hold a real stream in preparation and exercise assistant Stop and direct controls. |
| Camera | Pi camera MJPEG preview, photo, MP4 recording, and idle shutdown ran on hardware. The emulator Camera tab showed the stream, closed it on tab switch, and reconciled its Record button after an external stop. A blackholed stream viewer was released within seven seconds. A fresh direct still and service photo showed the lit room. The real phone Camera tab rendered live Pi camera frames. Write failures clear recording state; the stream has a write timeout and recording limits. | The monitor is outside the camera view; visible screen output is unconfirmed. Verify real-phone photo/record capture and stream teardown on tab switch. |
| Camera to screen | No camera-to-screen action is implemented. The Pi camera can stream to the app, and the phone camera is not yet a csync media source. | Add **Show Pi camera on Pi screen** using a locally authenticated low-latency stream, explicit Stop, muted default, and recovery to wallpaper. Add **Show phone camera on Pi screen** using an app camera sender with foreground lifecycle, permission handling, bounded buffering, disconnect cleanup, and explicit target state. Test both on the real display. |
| General casting | The app can upload a picked phone media file to the Pi USB drive and paste a YouTube link for Pi playback. Android's existing csync share target now offers **Play on Pi screen** or **Send to peer** for one audio/video file or a YouTube link. A real-phone invalid-link exercise confirmed that the cast handoff opens Media and displays the URL error; a successful share-sheet media cast is unconfirmed. | Resolve supported non-YouTube web media to a Pi-playable stream, display unsupported/DRM errors, and keep one output/Stop contract. Arbitrary browser-tab or protected-service screen casting needs a separate receiver/protocol decision and is not implemented. The macOS menu-bar sender remains a later project. |
| Assistant | The deployed assistant invoked `media_drives` and `media_diagnose` in a live chat. It has media and shared-camera tools. | Exercise every command through chat against both targets and check observed effects. |
| SMB and FTP | Samba and vsftpd are active. The SanDisk appears through a bind mount inside FTP, and `testparm` accepts the share changes. The absent Elements mount and FTP bind both returned `No such device`, with no SD-card fallback listing. | Authenticate a real SMB and FTP client, verify reads/writes, and repeat absent/hotplug checks with the actual HDD. |

## Result to deliver

The existing csync Android app becomes the remote and library browser for media on the Pi's attached drives. It must work without opening Chat or asking a model. When the Pi is connected to the projector, the phone selects a file and controls playback on the Pi. When the phone is connected to the projector and supports video output, the same app streams from the Pi and plays locally. Search, playback state, resume history, drive health, and errors have one meaning across both routes. The Pi assistant can call the same media operations and explain their failures.

| Owner action | Visible result | Failure shown |
| --- | --- | --- |
| Plug in the existing USB drive or Elements | The drive appears by a stable name and available capacity; its folders are browsable in the app and through its configured SMB, FTP, and SFTP routes. | Unmounted, unreadable, or underpowered drives show a reason and a next check. |
| Open Media and search or browse | Files are listed by drive and folder, with type, size, and playable status. Search results identify their drive. | A removed drive remains identifiable as offline; its cached results cannot be played. |
| Choose **Play on Pi** | The Pi starts the selected item on its HDMI output; the phone shows playback state, position, duration, volume, and speed. [PLANNED] Add track and buffering state. | A player or file failure is reported. [PLANNED] Classify HDMI and audio-sink failures before play. |
| Choose **Play on phone** | The phone streams the file from the Pi and uses its HDMI output if the hardware exposes one. | The app says when no external display is detected and offers local playback or Pi playback. |
| Pause, seek, change volume or speed | The chosen player changes, and both the app and assistant see the new state. [PLANNED] Select audio/subtitle tracks. | Invalid commands return structured errors. [PLANNED] Explain unsupported controls in the UI. |
| Reopen a played item | The app offers Resume or Start over at the last confirmed position. | If the original drive or file is absent, history stays visible and says what to reconnect. |

The phone should be a **player and controller**, not a network relay that must stay awake when the Pi itself is projecting. For phone HDMI, media flows Pi to phone to projector. For Pi HDMI, media flows from the mounted drive to a Pi player; the phone sends control commands only.

**Play on Pi** is a cast-like action inside csync: the phone sends an item ID and the Pi plays its own file. It is not a general Google Cast receiver that other Android apps will discover. The Media screen now has **Send phone media to Pi screen**: Android's picker uploads a video or audio file to a bounded folder on the SanDisk USB drive, then starts Pi playback. It validates file type, length, mounted-drive identity, and free space; incomplete uploads are removed. Background transfer, cancellation, share-sheet entry, and broader website casting remain planned. Streaming a phone-local file live to the Pi would make playback depend on the phone staying awake and connected, so the current path uploads first.

## Current evidence and limits

| Finding | Evidence | Consequence |
| --- | --- | --- |
| A Pi mesh peer and assistant answer on the tailnet. | Live `/whoami` on ports 8790 and 8791, 2026-09-25; source in `/Users/alcatraz627/Code/Claude/csync/agent/server.go` and `/Users/alcatraz627/Code/Claude/csync/assist/main.go`. | Reuse the tailnet identity and token pattern, while keeping media usable without a model provider. |
| Samba responds on port 445; Jellyfin reports version 12.1.0 and a completed setup on port 8096. | Live TCP and Jellyfin public-info checks, 2026-09-25. | Preserve both. Jellyfin may serve a later transcoding fallback; it does not supply the requested phone remote for Pi HDMI by itself. |
| The existing ext4 USB partition is mounted read-write at `/srv/media`; Samba's `media` and `files` shares point inside it. Jellyfin and Samba are running. | SSH `lsblk`, `findmnt`, `testparm -s`, and `systemctl`, 2026-09-25. The drive is a SanDisk device, UUID `e3e443f3-040b-4c46-a2c1-62816bc9f682`. | Preserve this mount, both shares, and Jellyfin's library. Do not repartition the larger physical USB device. |
| Samba advertises `seagate-elements` at `/srv/elements` and `sandisk` at `/srv/media`. The Elements disk is absent. | SSH `testparm`, `findmnt`, and media `/v1/drives`, 2026-09-25. The previous share used a stale symlink to an SD-card directory; a backup of `smb.conf` remains on the Pi. | Verify the actual Elements UUID and a client login before calling that share usable. An absent volume must not look like empty SD storage. |
| `vsftpd` is active on port 21. It uses `/home/alcatraz627/FTP` as its local root, allows local-user writes, and has TLS disabled. The SanDisk is bind-mounted at `FTP/Media`; `FTP/Elements` is a prepared automount. | SSH service, socket, config, mount, and directory checks, 2026-09-25. | Test actual FTP login, reads, writes, and hotplug. Preserve other files in the FTP root. |
| The assistant's optional shell-execution flag is present on the Pi. | SSH checked flag existence only, 2026-09-25; `/Users/alcatraz627/Code/Claude/csync/assist/tools.go:253` defines the gate. | Media actions should use narrow media tools despite the current broad shell ability. Do not use model-driven shell edits as the repair path. |
| The Pi has `mpv` configured for direct DRM on HDMI0; LightDM is inactive. After HDMI digital restoration, the owner confirmed moving video on the ARZOPA, including app-driven Play. The Pi still reports active undervoltage and throttling despite a supply labeled 5 V, 3 A. | SSH DRM, mpv log, `vcgencmd`, app state, and owner observation, 2026-09-25. | Verify the power path and sound under load. Do not infer new screen pixels from player state alone. |
| The app has six tabs, including Camera, plus a dedicated Media activity. The old chat media modal remains separate. | `/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/MainActivity.java`, `MediaActivity.java`, and emulator screenshots, 2026-09-25. | Test the real phone and HDMI route; emulator video proves rendering in-app only. |
| Shizuku restored the phone's wireless-debugging advertisement; paired ADB at `192.168.1.102:41957` installed code 9 with `Success`. | Live install, app browse, local WAV playback, Pi Stop, and camera preview, 2026-09-25. | Phone HDMI behavior and real-device video/audio output remain unverified. The ADB port may rotate; rediscover it with `adb mdns services`. |
| The Pi currently reports undervoltage and throttling (`vcgencmd get_throttled=0x50005`); kernel logs show repeated detect/recovery events. | Live SSH checks, 2026-09-25. | Inspect cable, supply, and USB power draw before two-drive and video-load tests. The supply's 5 V, 3 A label does not prove delivered voltage. |

## Architecture

Keep media available when the assistant is down. Add a small `csync-media` service in `/Users/alcatraz627/Code/Claude/csync/media/`, independent of the Go assistant. The Android app calls it directly. Assistant media tools call the same API. The service owns the library, drive state, stream URLs, Pi player state, and play history. Implement it with the Pi's installed Python 3.11 standard library: a bounded threaded HTTP server, `sqlite3` for file names and history, and direct file streaming. Keep the SQLite database on the SD card under the csync state directory, outside every removable drive, with a documented backup path. The service must survive a missing drive and a model-provider failure.

```text
[USB drives] --mounted files--> [Pi media service :8792] --HTTP Range bytes--> [Android player] --video/audio--> [phone HDMI]
      |                             |                                      |
      +--mounted paths--> [SMB/FTP/SFTP] +--Unix socket commands--> [Pi player] --video/audio--> [Pi HDMI]
                                    |
[Android Media screens] --browse/control/status HTTP--> [Pi media service]
[Pi assistant tools] --same API operations--> [Pi media service]
```

The service binds to the Pi's Tailscale address for the app and to loopback for the local assistant. Every library, stream, player, history, camera, and diagnostic request requires the mesh token. Never place a token in a media URL or log it. The Pi player accepts commands only from a local Unix socket; the socket is not exposed on TCP. Media IDs are opaque and resolve only beneath configured drive roots. Open files through checked paths, reject traversal and escaping symlinks, and bound request bodies and search results.

The existing Jellyfin server remains available. Avoid building a second metadata scraper or transcoder in the first slice. The new service lists real folders immediately, indexes names for search, and streams source bytes with HTTP Range. If a source codec cannot play on a specific phone or the Pi, report the format and decoder failure. Add a Jellyfin transcoding path only after real unsupported samples establish the need; do not silently transcode every file.

## Drive and share contract

Identify each disk by filesystem UUID and, where needed, hardware serial. Give each a stable mount path and display label. Preserve the existing `/srv/media` mount. `/srv/elements` is provisionally keyed by the expected `Elements` label because the HDD is not attached. Replace the label selector with its observed UUID before accepting this route as safe against duplicate labels. The SanDisk automount survived a reboot. Elements hotplug remains untested; `nofail` alone does not prove a later plug will mount.

Before listing, streaming, or serving a share, verify that the expected filesystem is mounted at that root. An empty directory on the SD card must never appear as an empty USB drive or accept uploads meant for the absent drive. The app may keep cached names for history, but marks the drive offline. On unplug during playback, stop the stream, save the last confirmed position, and report `DRIVE_REMOVED`; on reconnect, verify the same drive and item before Resume.

The backing mountpoint must be owned by root and inaccessible for writes by SMB and FTP identities when unmounted. A share may expose the mounted filesystem only after UUID verification. Connection-time Samba hooks alone do not protect a session that was already open when a disk disappeared. Before enabling writable shares, exercise both a new client and an already-connected client against a disposable Linux mount, remove it, attempt writes, and inspect the backing directory. Repeat on the Pi after approved deployment. Until that behavior is proven, new Elements access stays read-only. Preserve the existing SanDisk share settings pending the same audit.

Preserve the existing SMB `media` and `files` shares. Repair `seagate-elements` after the incoming drive's UUID and filesystem are known. Its current target is an SD-card placeholder. Test that every drive-backed share refuses access when its disk is absent, so a write cannot land on the SD card. Verify authenticated reads from the Mac and Android before enabling app uploads.

Preserve the running FTP service and its existing root. Inspect its users and passive-port behavior with a real client before exposing drive folders inside that root. SFTP over Tailscale SSH is an additional file-transfer route, but the tailnet currently requires an interactive SSH check; test whether the chosen Android file client can complete it before promising easy SFTP access. FTP and SFTP are different protocols. The app should show both accurately, indicate whether each is reachable, and offer copyable addresses plus an external-app open action with a clear no-handler message. The app's own file browser uses the media API for all drive files and does not depend on either protocol. Keep current FTP clients working while deciding whether to enable FTP over TLS or restrict the listener to the tailnet; do not silently change authentication or delete unrelated FTP content.

## Target media service contract [PLANNED]

This table is the intended end state. The current service implements drive listing, folder pagination with numeric offset, bounded search, byte streaming, Pi and active-phone state, progress, camera routes, and partial diagnostics. Indexed search, rich track/output state, upload, and share-health probes remain planned.

Version every route under `/v1`. Return stable codes and a human `message`, `fix`, and retryable flag on errors. The assistant consumes codes; the app shows the message and repair action.

| Route | Purpose | Required details |
| --- | --- | --- |
| `GET /v1/health` and `/v1/drives` | Service and drive status | Online, mount identity, free space, filesystem, read/write ability, last error. |
| `GET /v1/items?driveId=&path=&cursor=` | Folder browser | Bounded pages; directories before files; opaque item ID, name, size, type, modified time, drive ID. |
| `GET /v1/search?q=&cursor=` | Cross-drive search | Index updates on insert, rename, remove, and periodic reconciliation; identify stale/offline hits. |
| `HEAD/GET /v1/items/{id}/stream` | Phone playback and download | Token header, byte ranges, correct `206`/`416`, length, MIME, ETag, cancellation, no whole-file buffering. |
| `GET /v1/player/{target}` | Pi or active phone playback | State, item ID, position, duration, buffering, speed, volume, available tracks, output, error, monotonically increasing revision. |
| `POST /v1/player/{target}/commands` | Play, pause, stop, seek, volume, speed, audio and subtitle selection | Validate target and expected revision; deduplicate retries by command ID; return actual resulting state or a precise failure. |
| `POST /v1/phone/sessions`, `GET /v1/phone/commands`, and `POST /v1/phone/commands/{id}/result` | Phone-player command delivery | Register a random session ID and generation with a short lease; poll only while the player is active; acknowledge applied, rejected, or expired with observed state. |
| `GET /v1/history` and `POST /v1/progress` | Resume across both targets | Item identity, target, last confirmed position, completion, timestamp; retain entries for absent drives. |
| `POST /v1/incoming` | Optional phone-local media handoff | Stream to a bounded Pi inbox with upload progress and cancellation; publish an item only after a complete, checked transfer. |
| `GET /v1/diagnostics` | Support and agent triage | Mounts, share health, index age, HDMI connector and audio sink, player health, last errors, safe suggested fixes. |

`mpv` is installed and controlled through JSON IPC on the Pi. The service currently translates play, seek, pause, stop, volume, and speed, and observes position, duration, pause, and EOF. Audio/subtitle selection is planned. Direct DRM output and the HDMI audio device are configured; actual picture and sound remain unproven because the attached monitor supplies no EDID.

Item IDs sign the configured drive ID, relative path, and a version from filesystem identity, size, and modification time. The configured drive ID maps to an expected UUID or provisional label. An open stream pins one file descriptor and version. Each new range request checks that version and honors `If-Range`; a replaced or modified file returns `ITEM_CHANGED` instead of mixing bytes. A rename requires reselection. This avoids full hashing of large videos on every request.

Android currently uses `MediaPlayer` with a token header in a foreground playback service. The emulator proved that audio playback and agent commands continue after leaving Media. A separate-display `Presentation` kept MP4 video visible while the app returned to Home. Media3, a media session, richer decoder/track state, and physical HDMI acceptance remain planned. The app reports local state and progress to the Pi service and receives queued agent commands while its player session is active. Phone commands expire quickly and cannot execute later after a reconnect. If the phone is offline, the assistant must not claim a control succeeded. A session has one explicit target.

Phone command submission returns `queued`, never `applied`. The server targets a particular registered phone playback session and generation. The app acknowledges a command only after the player emits the resulting state; retries with the same command ID return its stored terminal result. Expired leases and replaced generations reject late commands and state reports. A control revision changes on commands and media switches, while frequent position telemetry has its own monotonic sequence, so progress reports do not make every seek conflict. The assistant reports `queued`, `applied`, `rejected`, or `expired` accurately.

The app persists confirmed progress locally before showing it as saved, including while offline. It uploads ordered session-generation and sequence records when the Pi returns. The service rejects older records for the same or a replaced session. An intentional backward seek is valid, so reconciliation never chooses the maximum time position. Completion and Start over are explicit progress events. Test network loss, process death, delayed replay, and a new session starting before an old upload arrives.

## Android surfaces

The app now has six bottom tabs, including Camera. Home and Tools open a dedicated Media activity. Share, Chat, xkcd, monitor, and Settings remain accessible. The first [full-app screen mocks](../assets/android-ui-mocks.svg) were rejected by the owner; [the UI plan](android-ui-redesign.md) records the rework requirements. No navigation or mini-player redesign has been implemented.

The Media activity has Drives, Browse/Search, Now Playing, History, and Access sections. A file row opens an explicit **Pi projector** or **This phone** picker. Current controls are seek, pause/resume/stop, volume, and speed. History offers Resume and Start over. Access copies SMB, FTP, and SFTP addresses. [PLANNED] Add audio/subtitle tracks, an app-wide compact player control, connection reachability, and richer output errors. The foreground service keeps phone playback and agent controls active after leaving Media; if Android exposes a separate display, a `Presentation` keeps video there. The owner's exact phone-HDMI path still needs hardware acceptance.

The phone-HDMI route has a hardware gate. Test the exact phone, adapter, and projector with Android display enumeration and a video sample. If Android exposes a presentation display, render video there and keep controls on the phone. If it only mirrors, offer a full-screen mirrored player and explain that controls will also appear on the projector. If it exposes no video output, show an unsupported-output message and offer Pi playback or a compatible external receiver. Software cannot make an unsupported USB-C port output HDMI.

## Assistant integration

Add explicit tools such as `media_drives`, `media_search`, `media_status`, `media_play`, `media_pause`, `media_seek`, `media_settings`, and `media_diagnose` in `/Users/alcatraz627/Code/Claude/csync/assist/`. They call the media service, not shell commands or a separate media index. Each mutating tool names `target=pi|phone`, item ID, and expected state revision. The assistant may explain `DRIVE_ABSENT`, `NO_HDMI`, or `UNSUPPORTED_CODEC` using diagnostics and recommend the exact next check. It must report whether an action actually applied. Keep the current `run_command` gate; media tasks must not require using it.

Do not let the model edit its deployed binary or service files directly. Routine recovery can be explicit, narrow operations after testing, such as retrying a library scan or restarting a failed player. Code fixes go through this repository, tests, a build, and an observable deployment with rollback. This keeps the Pi able to diagnose itself without making a broken live system its own source of truth.

### Diagnostic codes and repair guidance

| Code | App and assistant report | Verification and repair |
| --- | --- | --- |
| `DRIVE_ABSENT` or `WRONG_VOLUME` | Name the expected drive and last seen time. | Check USB power and `lsblk`; remount only the matching UUID, then retry scan. Never use a label alone. |
| `MOUNT_UNREADABLE` or `MOUNT_READ_ONLY` | Show browse versus upload availability separately. | Inspect `findmnt`, filesystem logs, ownership, and free space; avoid a write probe on a suspect disk. |
| `SHARE_UNAVAILABLE` | Name SMB, FTP, or SFTP and the affected drive. | Check daemon state, share path, mount identity, client authentication, and protocol-specific logs. |
| `NO_HDMI` or `NO_AUDIO_OUTPUT` | Offer phone playback and show the chosen Pi connector or sink. | Check connector status, EDID, selected mode, and audio sink with the projector attached. Retry output setup without rebooting the media library. |
| `PLAYER_UNAVAILABLE` or `UNSUPPORTED_CODEC` | Preserve the selected file and position. | Check supervised player state and decoder output. Test the file directly; add a transcoding fallback only for a proven format gap. |
| `PHONE_OFFLINE` or `PHONE_OUTPUT_UNSUPPORTED` | Keep Pi playback available. | Check phone tailnet status, active player session, external-display enumeration, and adapter compatibility. |
| `AUTH_REQUIRED`, `RANGE_INVALID`, or `ITEM_CHANGED` | Reject the request without leaking a path or token. | Reconnect/pair, retry with a valid byte range, or reselect the changed file. |

The current `/v1/diagnostics` response has an observation time, mounted-drive state, Pi and phone player state, power bits, HDMI connector status and EDID length, and recent mpv error lines. [PLANNED] Add share health, audio-sink probes, explicit retry safety, and an app diagnostics page. The assistant can read current diagnostics and suggest checks; a queued phone command is not reported as applied.

If the media service cannot answer, the app distinguishes name resolution, connection refusal, and timeout. The assistant's `media_diagnose` checks the user service, power, current USB mount, HDMI connector state, and media diagnostics without `run_command`. `/Users/alcatraz627/Code/Claude/csync/docs/media-operations.md` covers service-down checks and rollback. [PLANNED] Add journal and protocol-specific share probes, automatic-restart policy, and full app-side authentication guidance.

## Failures to exercise

| Trigger | Expected behavior and check |
| --- | --- |
| Either drive absent at boot, inserted later, or two drives with the same label | Correct drive ID and mount state; no boot delay or wrong-drive browse. |
| Drive unplugged during scan, phone stream, Pi playback, or SMB access | Operation stops with a named drive error; history remains; no writes to the SD mount directory. |
| Filesystem is read-only, dirty, permission denied, nearly full, or slow to spin up | Browse when possible; uploads disabled when not; diagnostic names the failing layer. |
| Deep folders, duplicate names, non-ASCII names, symlinks, large videos, and concurrent browse/search | Stable pagination and no path escape, UI freeze, or whole-file memory load. |
| Seek near start/end, rapid repeated commands, app background/rotation, service restart | Player state converges; no old command controls a new session; progress survives. |
| Projector connected after player start, wrong HDMI port, no audio sink, or unsupported codec | Explicit output/decoder error, retry after connection, and no false “playing” state. |
| Phone cable attached with no external display, mirrored display, or separate display | Correct mode in UI; the direct-HDMI promise is made only in a proven mode. |
| Tailnet drops or phone sleeps | Pi playback continues; phone controls reconnect and refresh state; stale state is labeled. |
| Token missing/wrong, malformed range, traversal path, or unlisted root | Refusal with no file leak, no auth token in logs, and an actionable app error. |
| Old phone command after app restart, duplicate delivery, or two active sessions | Command is applied at most once to the named generation; queued is never reported as applied. |
| Offline phone progress, a later session, and a deliberate backward seek | Durable resume position follows ordered confirmed events, not the largest timestamp or position. |
| File replaced, renamed, or edited between two range requests | No mixed-version playback and no silent resume of replacement bytes. |
| Media service stopped, assistant alive, wrong token, or tailnet down | App and assistant classify what they can observe without claiming the stopped service diagnosed itself. |
| Second disk spins up during video playback on a historically undervolted Pi | Current/historical throttling and USB reset evidence is recorded; hardware remedy is suggested before repeated remounts. |
| Existing SMB, Jellyfin, mesh, chat, xkcd, and monitor flows | Their existing runtime checks still pass after the media addition. |

## Work order and proof

1. **Finish local acceptance.** Python HTTP and fault tests, Go assistant tests, Android build, and emulator journeys now cover 105-file browsing, audio/video playback, background audio command delivery, offline history, and Camera tab lifecycle. Repeat the final suite after the last code edit; full service-down and large-file stress tests remain.
2. **Close adversarial findings.** The review at `/Users/alcatraz627/Code/Claude/csync/.claude/output/20260925-0516-adversarial-review/indictment.md` found 13 gaps. Session targeting, wrong-item progress, cross-output control fallback, mpv framing and EOF state, camera write/stream bounds, pagination, removed-drive progress, background audio, and local history have code changes and targeted exercises. The final recheck at `/Users/alcatraz627/Code/Claude/csync/.claude/output/20260925-0516-adversarial-review/final-recheck.md` confirmed the narrow playback and camera corrections. Physical HDMI, phone HDMI, Elements, authenticated shares, and track selection remain open or planned. Separate-display video ran in the emulator; mirrored phone HDMI still needs a real-device test.
3. **Complete hardware acceptance where available.** Micro-HDMI0 now reaches the ARZOPA and the owner has seen moving video. Diagnose the active undervoltage, then confirm sound, screen-image pixels, and sustained playback. Attach Elements and replace the provisional label with its UUID; test hotplug, Samba, FTP, and removal during streaming. Once wireless debugging answers, install the latest phone APK and test its HDMI playback, Camera tab, and local-file picker. Record PASS, FAIL, or UNRUN for each route.
4. **Handover.** Keep the Pi deployment and Android emulator build observable, document backups and rollback commands, preserve the uncommitted source changes for review, and state any remaining physical tests without a ready claim.

The first three independent capabilities to ship are drive availability, a reliable Pi HDMI player controlled by the phone, and a native Android browser/player. Assistant control follows the same contract. No “ready” claim is earned from a build, unit test, or endpoint response alone; the projector and phone paths require observed video and audio on their actual hardware.

## Decisions still needed

The actual phone is a Nothing AIN065 on Android 16. Version 2.11/code 13 is installed; Shizuku running on the phone restored paired ADB. Future ADB ports may rotate, so use `adb mdns services` before connecting. The app's Pi-hosted updater is also installed; its next newer APK may require the one-time Android install-source grant. A live HDMI output test remains. Pi micro-HDMI0 reaches the ARZOPA and moving video has appeared. The app uploads selected media only into a dedicated folder on the identified SanDisk USB drive; general file writes and deletion remain outside its API. Existing Samba and FTP retain their earlier write settings. Elements must be attached to learn its UUID and filesystem.

## Technical references

- [Tailscale SSH check mode](https://tailscale.com/kb/1193/tailscale-ssh) explains the browser reauthentication observed during Pi SSH. It also affects generic SFTP clients.
- [Debian systemd automount](https://manpages.debian.org/bookworm/systemd/systemd.automount.5.en.html) and [udev rules](https://manpages.debian.org/bookworm/udev/udev.7.en.html) describe the supported hotplug mechanisms. Long-running mount work belongs in a service, not inside a udev rule.
- [Samba share controls](https://www.samba.org/samba/samba/docs/man/manpages/smb.conf.5.html) and [root preexec close](https://devel.samba.org/samba/docs/man/manpages/smb.conf.5.html) are candidates for refusing an absent drive; validate the exact behavior on this Pi before changing its shares.
- [mpv's command and JSON IPC interface](https://mpv.io/manual/stable/) supports observed playback state and remote commands. The Pi output backend still needs a real projector test.
- [Android Media3 HTTP customization](https://developer.android.com/media/media3/exoplayer/customization) supports token headers on range requests. [Media3 player events](https://developer.android.com/media/media3/exoplayer/listening-to-player-events) provide real state and seek observations.
- [Android external-display Presentation](https://developer.android.com/reference/android/app/Presentation) applies when the phone exposes a separate display; the exact phone and adapter determine whether it can be used.
- [Raspberry Pi HDMI configuration](https://www.raspberrypi.com/documentation/computers/configuration.html) covers display mode and audio-sink checks with the projector attached.
