# Assistant provider availability, 28 September 2026

The Pi's provider registry listed Gemini and Claude, but `/Users/alcatraz627/Code/Claude/csync/assist/main.go` routed `/chat` only to Gemini. Android Settings let the owner select and save Claude through `/config`. That saved choice would make later chat requests return HTTP 501. The installed Settings capture `/private/tmp/csync-settings-v5-assistant-light.png` showed both providers without an availability label.

`/Users/alcatraz627/Code/Claude/csync/assist/providers.go` now defines `chatProviderSupported`, currently true only for Gemini. `/providers` reports `chatSupported` for each registry entry. `/config` rejects an unsupported provider with HTTP 400 before saving it. `/chat` uses the same predicate. The Android UI agent received the live contract and is updating Settings to show unsupported providers honestly.

`gofmt -w main.go providers.go` ran in `/Users/alcatraz627/Code/Claude/csync/assist`. `go test -count=1 ./...` exited 0 (`ok` in 0.558s). `git diff --check` exited 0. A static Linux ARM64 build exited 0 with SHA-256 `f6f02894f20314be4a5a7bda7799ede598000b10ed34ac6f65fe34893c344318`.

The Pi's old assistant binary hash was `26d14a55b04e486b7a5581878d71fdf90bf4b8b764f2da1fc8f2101d9228be76`. I copied it to `/home/alcatraz627/.local/bin/csync-assist-before-provider-support-20260928`, verified the copy, atomically installed the uploaded ARM64 binary, and restarted `csync-assist.service`. `systemctl --user show` reported `ActiveState=active` and `SubState=running`.

Authenticated live `GET /providers` returned HTTP 200 with active provider Gemini, `gemini.chatSupported=true`, and `claude.chatSupported=false`. Authenticated `POST /config` with a Claude selection returned HTTP 400 and `claude provider is not available for chat`. A second `GET /providers` still reported Gemini active. No chat message was sent. Android's unsupported-provider display and Apply behavior remain UNRUN until its source revision is installed.
