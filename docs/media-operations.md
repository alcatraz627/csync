# Pi media operations

This runbook covers the deployed Pi media service and Android Media screen as of 2026-09-25. After the earlier HDMI failures, the owner confirmed moving video on the ARZOPA from an app-driven Pi Play. Pause, Mute, Volume, Stop, YouTube link playback, persistent screen-image storage, and phone-file upload were exercised through the Pi API or emulator app. Screen-image pixels, sound, the Elements HDD, the owner's phone HDMI path, and authenticated SMB/FTP clients remain unconfirmed.

## Routes and state

| Component | Address or path | Purpose |
| --- | --- | --- |
| Pi SSH | `ssh 100.65.188.9` | Works through Tailscale; `raspberrypi.local` did not resolve during this session. |
| Media API | `http://100.65.188.9:8792` | Token-gated browse, byte streams, Pi and phone player state, history, camera, and diagnostics. |
| Assistant | `http://100.65.188.9:8791` | Chat and tools that call the same media API. |
| Media code | `/home/alcatraz627/.local/share/csync-media/media/` | Deployed copy of this repository's `media/` package. |
| Media config | `/home/alcatraz627/.config/csync/media.json` | Drive IDs, capture directory, mpv command. Do not print the mesh token beside it. |
| Media service | `/home/alcatraz627/.config/systemd/user/csync-media.service` | User service. |
| Playback history | `/home/alcatraz627/.local/state/csync/media.db` | SQLite progress per item and target. |
| mpv log | `/home/alcatraz627/.local/state/csync/mpv.log` | Recent decoder and output errors. |
| Camera captures | `/home/alcatraz627/csync-media/` | Photos and converted MP4 clips. |
| Persistent screen image | `/home/alcatraz627/.local/state/csync/wallpaper.jpg` | The phone-picked JPEG reappears after Stop and media-service restart. |
| Phone-file casts | `/srv/media/shared/csync-casts/` | Files selected in the Android Media screen are saved to the SanDisk USB drive before Pi playback. |
| Android update APK | `/home/alcatraz627/.local/state/csync/csync-hub-update.apk` | Token-protected `/v1/app/apk`; Tools → Update csync from Pi downloads and asks Android to install newer signed builds. |

The Android Media screen uses the same token as the mesh peer. It browses and plays without Chat. `PhonePlaybackService` owns phone playback after the Media screen closes and polls the same command queue used by the assistant. It keeps video on a separate Android presentation display while the phone shows other tabs. Mirrored HDMI needs the Media screen visible for full-screen video. Pi playback uses mpv on the Pi's DRM output. The Camera tab subscribes to the Pi stream only while the tab is visible and polls recording state while open.

## Check a report of no video

1. Run `ssh 100.65.188.9 'systemctl --user is-active csync-media.service; cat /sys/class/drm/card1-HDMI-A-1/status; wc -c /sys/class/drm/card1-HDMI-A-1/edid; vcgencmd get_throttled'`.
2. Open Media in the Android app, select a known playable file, choose **Play on Pi projector**, and read its player state. A moving position proves decoding or clock progress, not visible HDMI output.
3. The current cable is connected from Pi micro-HDMI0 to the ARZOPA mini-HDMI input, and the monitor shows the Pi console. The earlier USB-C-only adapter could not carry Pi video; that wiring problem has been corrected. Check `mpv.log` and whether a DRM framebuffer is active during play. The console alone does not prove mpv can take over the display.
4. If the display shows video but is silent, check the Pi HDMI audio output and the monitor volume with a file that has an audio track. Do not change the video mode to fix audio without first reading the mpv log.

Those initial MP4 attempts showed only the console. Later, the HDMI digital-restore service and direct DRM playback produced moving color bars visible to the owner, including an app-driven Play. The media API waits for the requested file to reach a playing state and returns HTTP 503 `PLAYER_UNAVAILABLE` if it does not; it leaves history unchanged. Playback starts muted. The Media screen's Pause, Mute, Volume, and Stop controls call the immediate Pi API. A live silent-clip test held the paused position, set actual volume to zero, changed volume to 10%, and stopped to idle. The emulator file-cast journey selected a 2.5 MB MP4, uploaded it to the USB drive with a matching SHA-256, started Pi playback at volume zero, and stopped it. These API and emulator observations do not establish sound or the exact pixels on the monitor during the latest cast. The camera currently points away from the monitor. `vcgencmd get_throttled=0x50005` still reports active undervoltage and throttling. The supply label says 5 V, 3 A, but delivered voltage or USB load may still be inadequate; test with a known-good direct Pi supply and a powered USB hub before heavy two-drive use.

## Check a drive or share

| Check | Command on the Pi | Expected or action |
| --- | --- | --- |
| USB identity | `lsblk -o NAME,LABEL,UUID,FSTYPE,MOUNTPOINTS` | SanDisk UUID is `e3e443f3-040b-4c46-a2c1-62816bc9f682`. Record Elements' actual UUID when connected. |
| Existing USB | `findmnt -n -o TARGET,SOURCE,UUID /srv/media` | `/dev/sda1` under `/srv/media` on the last live check. |
| Elements | `findmnt -n -o TARGET,SOURCE,UUID /srv/elements` | Currently absent. The automount returns `No such device`; do not treat its empty mount directory as online. |
| SMB | `testparm -s` and `systemctl is-active smbd` | Shares include `sandisk` and `seagate-elements`. A client login and read/write check are still required. |
| FTP | `systemctl is-active vsftpd` and `findmnt /home/alcatraz627/FTP/Media` | `/Media` binds to `/srv/media`; `/Elements` binds to `/srv/elements`. A client login is still required. |
| Media API | Open the app's Drives screen or ask the assistant to run `media_diagnose` | The current USB is online; absent Elements reports `DRIVE_ABSENT`. |

`/etc/fstab` has a provisional `LABEL=Elements` automount. Replace that with the HDD's UUID after attaching and inspecting it; a duplicate label must not select the wrong drive. Before editing `/etc/fstab` or Samba, compare `/etc/fstab.csync-media-20260925.bak` and `/etc/samba/smb.conf.csync-media-20260925.bak`. Keep the older `[media]`, `[files]`, and `[raspi-shared]` shares intact.

The existing FTP service has TLS disabled. Use it only within a trusted route; SFTP is available through SSH when Tailscale authorization allows it. The app's Access screen copies SMB, FTP, and SFTP addresses but does not store file-service passwords.

## Check playback, camera, and assistant

| Symptom | First check | Next action |
| --- | --- | --- |
| Media screen cannot reach Pi | `systemctl --user status csync-media.service` and `journalctl --user -u csync-media.service -n 50 --no-pager` | Check Tailscale route and token pairing. Restart the service only after capturing its error. |
| Pi player unavailable | Assistant `media_diagnose`, `/home/alcatraz627/.local/state/csync/mpv.log`, and `vcgencmd get_throttled` | Read DRM, power, decoder, and audio errors. HTTP 503 `PLAYER_UNAVAILABLE` means the requested file did not reach a confirmed player state within five seconds; no history entry is saved. |
| Phone command queued | Phone player state and command result | Queued means the phone has not applied it. Keep the app's playback service running or choose Pi output. |
| Camera preview black | Camera status, lens direction, and a lit subject | Direct and service photos showed the room on 2026-09-25. Recheck framing and exposure if a later preview is dark. |
| Camera recording stops | Camera status `recordingError`, free space, captures directory | The recorder reserves 512 MB, caps raw capture at 512 MB or 30 minutes, and keeps raw MJPEG if conversion fails. A successful conversion removes the raw copy. |
| Assistant cannot diagnose | `systemctl --user status csync-assist.service` | The app's Media and Camera surfaces still use the media API directly. |

The assistant exposes `media_drives`, `media_search`, `media_status`, `media_play`, `media_pause`, `media_seek`, `media_resume`, `media_stop`, `media_volume`, `media_speed`, `media_cast_youtube`, and `media_diagnose`, plus the shared `camera` tool. Its phone commands are scoped to the observed phone session and generation. `media_play` currently starts Pi output; phone playback starts from the app. `media_cast_youtube` appears in the deployed assistant's live capability list; a full model-driven invocation of that new tool remains untested.

## Roll back a service change

The source files deployed before the adversarial fixes were copied on the Pi to sibling names ending in `.reviewfix-backup-20260925`. The newer media play-readiness change has `/home/alcatraz627/.local/share/csync-media/media/server.py.play-readiness-20260925.bak`. Restore a file with `cp` from its backup, then run `systemctl --user restart csync-media.service` or `systemctl --user restart csync-assist.service` as appropriate. Earlier Pi backups also exist for `/etc/fstab`, `/etc/samba/smb.conf`, and the assistant binary. Inspect a backup before restoring it because restoration would also discard later intentional changes.

The local source checkouts remain uncommitted. No Git history or remote was changed. The Android debug APK is at `/Users/alcatraz627/Code/csync-hub/app/build/outputs/apk/debug/app-debug.apk`, version 2.11/code 13, SHA-256 `14c1fc4f1625192a9d4698745b1ee7e42428a70a74e85e319db2458e32e2e5c8`. The same APK is staged on the Pi and installed on the owner's phone through paired wireless ADB after Shizuku restored it. Discover the current phone port with `adb mdns services`; the last observed address was `192.168.1.102:41957`. The APK fixes pending Stop and output handoff, a MediaPlayer preparation-state error, assistant Stop delivery while loading, and an early bookmark save that could replace a resume position with zero. Its Android share target now offers a Pi-screen cast for a single audio/video file or YouTube URL alongside the prior peer-send action. Emulator in-app upgrades from code 3 through 8 succeeded; the real phone's Tools → Update csync from Pi downloaded the staged code-9 APK and reported "csync is already up to date" without opening install settings. A future newer in-app update on the real phone may require Android's one-time "Allow from this source" grant, which is currently off. On the real phone, Media browsed Pi USB, streamed a silent WAV locally to completion, and stopped its foreground service in earlier tests. A slow-preparation resume test remains unrun. A later Pi-service correction cleared inherited pause before each new load; the real phone then observed the Pi file playing at zero volume, paused, resumed with advancing position, and stopped to idle. The Camera tab rendered live Pi camera frames. The share-sheet cast chooser and invalid-URL error were exercised on the real phone. Successful share-sheet file casting, phone HDMI playback, projector sound, and latest wallpaper pixels remain untested. An earlier emulator YouTube attempt stopped phone playback correctly but the Pi returned `PLAYER_UNAVAILABLE`; the app showed this failure. A subsequent muted public-video test succeeded as recorded below. Diagnose intermittent failures and sustained Pi power before relying on YouTube playback.

## Casting and performance probes, 2026-09-25

The Pi media service is a **user** service: `systemctl --user is-active csync-media.service` returned `active`. A system-wide `systemctl is-active` returned `inactive` because no system service has that name. Do not treat that result as a media outage.

The owner reported lag and intermittent non-playback. The first measured phone-to-Pi unauthenticated HTTP requests took 0.127 and 0.058 seconds end to end; local Pi health, search, player state, and a 1 MiB Range read took 0.030, 0.043, 0.005, and 0.035 seconds in one sample. These samples do not measure upload time, decoder stalls, or screen output. Android file casting currently copies the whole selected file to `/srv/media/shared/csync-casts/` and syncs it before Pi playback. A connection reset during one phone upload appears in the Pi user-service journal; it raised `UPLOAD_FAILED`, followed by a broken pipe while reporting the error. There is no resumable upload or live phone-file relay yet. Large files therefore wait for the complete transfer and may fail if the phone disconnects.

A real Pi-state defect was reproduced: the API reported an old film as playing while mpv had changed to `wallpaper.jpg`. `media/server.py` now reconciles the observed mpv path for active sessions and returns `unavailable` with no current item after an outside replacement. The focused regression and all 24 media-service tests passed; on the Pi a silent WAV was replaced with the wallpaper through mpv IPC and the API reported `unavailable` with no item. The deployed copy is backed up as `/home/alcatraz627/.local/share/csync-media/media/server.py.before-path-reconcile-20260925.bak`.

Pi `yt-dlp` resolved the public test video `jNQXAC9IVRw`. A muted Pi API cast then reached `playing` in 6.23 seconds with position advancing after four seconds. Android v2.11/code 13 accepts a shared YouTube title followed by one validated URL. An emulator `ACTION_SEND` with that shape opened the csync cast choice, selected Pi output, showed playing at 0% volume, and Stop returned the Pi API to `idle`. This exercised the emulator app and real Pi service. A tap from the native YouTube app, sustained screen pixels, and sound are still unconfirmed. The current Pi still reports `vcgencmd get_throttled=0x50005`, including active undervoltage.
