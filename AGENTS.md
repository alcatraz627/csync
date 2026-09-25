# csync agent guide

## Purpose and layout

csync has three related services with different trust models. Read the relevant code before changing a contract.

| Part | Code | Job |
| --- | --- | --- |
| Console and temporary target | `csync/`, `bootstrap.sh`, `target/`, `ops/`, `recipes/` | The Python CLI invites a target, which opens a reverse SSH tunnel. The console drives it until teardown. |
| Mesh peer | `agent/` | A persistent Go peer sends and receives text, files, and images between trusted tailnet devices on port 8790. |
| Pi assistant | `assist/` | A persistent Go HTTP service on port 8791 handles chat, model tools, media, and provider configuration. |
| Pi media and camera | `media/` | A Python HTTP service on port 8792 browses mounted drives, streams files and the Pi camera, controls direct-DRM playback, and stores play history. |

The Android client is a separate repository at `/Users/alcatraz627/Code/csync-hub`. Its `MeshClient` talks to the mesh and assistant. `MainActivity` owns Home, Share, Chat, Tools, Settings, and Camera; `MediaActivity` browses Pi files and controls the chosen output; `PhonePlaybackService` owns local playback, telemetry, and queued commands after Media closes; `CameraController` owns the Camera tab's on-demand stream. `MeshService` receives peer items; `ChatService` keeps a chat running in the background; `ChatStore`, `PeerStore`, and `Prefs` hold local state. Read that repo's `README.md` and `docs/ui-design-brief.md` before changing its behavior. The product goal is to reach the owner's other machines from the phone, especially to share items and use the Pi assistant.

## Design constraints

- Keep the temporary target passive. It dials out and confines its SSH listener to loopback. Record each target change and its reversal in teardown. Hash-pin scripts it runs. See `docs/principles.md`, `docs/development.md`, and `docs/security.md`.
- Keep console verbs explicit about their host and effects. Agent actors get read verbs by default; each write needs `--allow-write`. Keep JSON output, actionable exit errors, and the audit journal when adding verbs.
- Treat the mesh and assistant as persistent services for the owner's trusted devices. They bind to a Tailscale address and use the shared mesh token. Do not silently carry the temporary-target rules into these services or weaken their token checks.
- Keep tokens, provider keys, and host state out of Git. Do not print their values during diagnosis. The provider list can advertise a backend before chat implements it; check the dispatch in `assist/main.go` before claiming a provider works.
- Preserve the phone's named-peer model and six-tab navigation unless the owner decides otherwise. Server capability and provider responses drive parts of its UI.
- Keep media browsing and playback independent of Chat. The Android app and assistant use the same token-gated media API; a queued phone command is not yet an applied command. Drive roots must resolve to the expected mounted volume before listing or streaming.
- Stop camera streaming when the Camera tab closes. The Pi camera service and assistant camera tool share capture files under `~/csync-media`; do not start a competing camera process while the app is previewing.

## Work and verification

1. Inspect `git status` and the relevant source before editing. Historical checkpoints and documentation can lag the current code and deployed binaries.
2. For console changes, use `python3 -m unittest discover -s tests` and the relevant shell test. `tests/loopback.sh` exercises a local pairing but does not prove another OS works.
3. For Go changes, run `go test ./...` in the changed module and exercise the service or endpoint that changed. Build scripts and `install-linux.sh` show the Pi deployment path.
4. For Android changes, build from `/Users/alcatraz627/Code/csync-hub` with `./gradlew assembleDebug`. Verify changed UI on the phone when it is connected; a build alone cannot prove rendering or interaction.
5. Compare the local contract with the Pi's live `/whoami` and relevant authenticated endpoints before declaring a deployment current. The mesh serves 8790; the assistant serves 8791. Use SSH for service status when Tailscale permits it.
6. For media changes, run `python3 -m unittest -v tests.test_media_service`, then verify the matching Pi service endpoint and Android behavior. The Pi uses `mpv` on DRM card1 HDMI0, with a forced kernel video mode while monitor EDID is absent. Software playback state does not prove a visible image or sound on the physical screen.

This repository has old session checkpoints at its root. The `_checkpoint.claude.md` link can point to a session older than later commits. Use it for history, then verify current state from Git, source, and live endpoints.
