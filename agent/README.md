# csync mesh agent

The trusted-device half of csync. A small peer that each of your own machines
runs, so any device can send text, files, and images to any other over the
Tailscale tailnet. This is distinct from the borrow-a-laptop csync CLI: mesh
peers are persistent and symmetric, they always listen, and they trust each other.

One Go binary, no dependencies. Discovery rides on Tailscale; the wire is plain
HTTP over the tailnet (WireGuard already encrypts it), gated by a shared token.

## Build

```
./build.sh          # cross-compiles every target into dist/
go build -o csync-agent .   # just this host
```

Targets: `darwin-arm64`, `darwin-amd64`, `linux-arm64` (Raspberry Pi), `linux-amd64`, `linux-armv6`.

## Install

```
./install-macos.sh                          # LaunchAgent, keeps it running
./install-linux.sh dist/csync-agent-linux-arm64   # run ON the Linux device; systemd --user
```

Copy `~/.config/csync/mesh.token` to every device you trust; that shared secret
is the second gate on top of the tailnet.

## Use

```
csync-agent serve                          # receiver (binds to this device's tailnet IP)
csync-agent peers                          # tailnet peers and which run an agent
csync-agent send <peer> --text "hello"     # text (lands on the peer's clipboard on macOS)
csync-agent send <peer> ~/a.pdf ~/b.png    # files and images
csync-agent whoami                         # this device's identity
csync-agent token                          # print/mint the shared token
```

`<peer>` is a tailnet name (`raspberrypi`, `aakarshs-m5-pro`) or an IPv4 literal.

## Contract

| Method | Path | Body / headers | Result |
|---|---|---|---|
| GET | `/whoami` | none | `{name, platform, version, caps}` |
| GET | `/peers` | `X-Csync-Token` | tailnet roster with per-peer agent reachability |
| POST | `/send` | `X-Csync-Token`, `X-Csync-From`, `X-Csync-Kind` (text/file/image), `X-Csync-Name`; raw body | saved to `~/csync/inbox/<from>/`; receipt JSON |

Received text is copied to the clipboard on macOS. Every arrival raises a
desktop notification.

## Files

- `main.go`: CLI dispatch
- `server.go`: the receiver and its handlers
- `client.go`: sender and peer scan
- `config.go`: token, inbox paths, Tailscale identity and reachability
- `build.sh`, `install-macos.sh`, `install-linux.sh`: build and install

The Android peer is the `csync-hub` app at `~/Code/csync-hub`.
