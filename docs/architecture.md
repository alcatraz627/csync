# Architecture

How csync is put together, from the pieces down to the bytes on the wire. The
full normative definition lives in [spec.md](spec.md); this is the map you read
first.

## The whole picture

```
   YOU, at the console                                A target laptop
   ┌───────────────────────────┐                      ┌──────────────────────────┐
   │ csync CLI (Python)        │                      │ its own sshd, loopback   │
   │ relay sshd  *:5122        │ ◄── reverse tunnel ──┤ ssh -R 127.0.0.1:52NN    │
   │ Tailscale Funnel :10000   │     (target dials)   │ keeper (LaunchAgent /    │
   │ audit journal + keys      │                      │  systemd user unit)      │
   └───────────────────────────┘                      └──────────────────────────┘
        console reaches the target only through the tunnel the target opened
```

There are three roles. The **console** is your Mac. The **target** is the other
machine. The **route** is whatever network carries the tunnel between them.

## The console

The `csync` CLI (Python, under `csync/`) is the whole driver. It owns:

- The only long-lived private key, at `~/.config/csync/id_ed25519`.
- A small hardened **relay sshd** on port 5122, configured under
  `~/.config/csync/relay/`. It accepts only the console user, only by key, and
  each invite key is pinned to one forced command and one listen port.
- A **Tailscale Funnel** that publishes the relay on `:10000` for targets that
  are not on the same LAN.
- The audit journal at `~/.local/state/csync/audit.jsonl` and per-host state under
  `~/.config/csync/`.

## The target

The target installs nothing permanent that csync did not write, and everything it
writes is reversed by teardown. After the one paste it holds:

- Its own sshd, turned on and confined to loopback, keys only, one user.
- A **keeper**: a LaunchAgent on macOS or a user systemd unit on Linux that keeps
  a reverse SSH tunnel open back to the console relay. The keeper dials out; the
  console never dials in.
- A snapshot of prior state, a change ledger, and a self-contained teardown
  script, all under `~/.csync/`.
- A root TTL backstop that runs teardown at the deadline even if the console
  vanishes.

## The route

The token an invite carries names two ways to reach the relay, and the target
picks one:

- **lan**: a direct TCP hop to the console's address on port 5122. Fast, used when
  both machines are on the same network.
- **funnel**: TLS to the console's Funnel name on port 10000, then on to the
  relay, using `openssl s_client` as an SSH ProxyCommand. Used when the target is
  elsewhere.

Both machines being on the same tailnet is a third, cleaner case: the relay
listens on all interfaces, so the target can reach the console's tailnet address
on 5122 directly. A first-class tailnet route is a planned addition (see
[development.md](development.md)).

## How a target registers

This is the step people trip on, so it is worth stating exactly.

1. The target's keeper connects to the relay with its invite key and passes a
   **hello** string as the SSH command, and a reverse forward `-R 127.0.0.1:52NN`.
2. The invite key in the relay's `authorized_keys` is pinned to a forced command,
   `csync relay-hello <invite-id>`. On a successful connection that command runs
   on the console.
3. `relay-hello` reads the hello from `SSH_ORIGINAL_COMMAND`, and if the id
   matches it flips the host from `invited` to `online` and holds the session open
   so the reverse listener stays up.

The state only flips through that forced command. `csync wait` does not cause the
flip, it polls for it. So if a host is stuck at "waiting for the paste" while the
target says it connected, the tunnel is not authenticating or not landing, not
that `wait` has not noticed. The runbook has the exact checks.

## The mesh and the assistant

Layered on top of the same tailnet trust are two more services, used by the phone
app and each other rather than by the drive-a-laptop flow:

- The **agent** (`agent/`, Go) is a peer that syncs text, files, and images
  between your devices over the tailnet, on port 8790.
- The **assist** server (`assist/`, Go) answers chat with tools (home health, peer
  listing, gated shell) over port 8791, backed by an extensible provider registry.

The phone side is a separate app,
[csync-hub](https://github.com/alcatraz627/csync-hub). These share the mesh token
and the tailnet as their trust boundary, the same as the console and target.

## Where state lives

| Path | Whose | What |
|---|---|---|
| `~/.config/csync/` | console | keys, relay config, per-host state, invite keys |
| `~/.local/state/csync/audit.jsonl` | console | every command, with actor and outcome |
| `~/csync/<name>/` | console | pulled files, screenshots, session logs |
| `~/.csync/` | target | snapshot, change ledger, teardown scripts, invite key |
| `~/.config/csync/` | Pi and phone | mesh token, assist provider config |
