# Segments

Each moving part of csync, what it is, where its code and state live, and how to
poke it. Use this as a reference beside [architecture.md](architecture.md).

## Console CLI

- **Is**: the whole driver you run on your Mac.
- **Code**: `csync/` (Python). Entry `bin/csync` imports `csync.cli.main`. Verbs
  are argparse subparsers in `csync/cli.py`; each dispatches into a module
  (`invite.py`, `ops.py`, `tunnel.py`, `relay.py`, `teardown.py`, `doctor.py`).
- **State**: `~/.config/csync/` (keys, relay, per-host records, invite keys) and
  `~/.local/state/csync/audit.jsonl`.
- **Poke it**: `csync status`, `csync doctor`, `csync log`.

## Relay sshd

- **Is**: a small hardened sshd, separate from your system ssh, that the target's
  tunnel authenticates against.
- **Where**: `~/.config/csync/relay/` (config, host keys, `authorized_keys`, log),
  port 5122, launched by a LaunchAgent.
- **Auth**: one line per open invite, each pinned to `restrict`, one
  `permitlisten` port, and a forced `csync relay-hello <id>` command.
- **Poke it**: `lsof -nP -iTCP:5122`, `tail ~/.config/csync/relay/sshd.log`,
  `csync log --relay`.

## Route and Funnel

- **Is**: how the target reaches the relay. `lan` is a direct hop on 5122;
  `funnel` is TLS to the console's Funnel name on 10000 via `openssl s_client`.
- **Where**: Tailscale Funnel, set up by `csync init`.
- **Poke it**: `tailscale funnel status` should show `:10000` forwarding to
  `localhost:5122`.

## Target

- **Is**: the other machine, holding only what the paste installed, all reversible.
- **State**: `~/.csync/` (snapshot `state.env`, change ledger `changes.log`,
  `invite_key`, `known_hosts`, `gate.sh`, `teardown.sh`, `teardown-root.sh`).
- **Keeper**: a macOS LaunchAgent (`sh.csync.tunnel`) or a Linux user systemd
  unit (`csync-tunnel`) that keeps the reverse tunnel open.
- **Poke it**: on the target, `~/.csync/teardown.sh` reverses everything; the
  keeper log is the LaunchAgent stderr or `journalctl --user -u csync-tunnel`.

## Bootstrap and target scripts

- **Is**: the one-line entry (`bootstrap.sh`) and the reversible halves
  (`target/gate.sh`, `target/teardown.sh`, `target/teardown-root.sh`).
- **Fetched**: from the invite's `src` URL, each checked against a sha256 the
  token carries.
- **Poke it**: `csync invite --show-script` prints what the URL serves.

## Recipes

- **Is**: reviewed shell scripts the console streams to a target.
- **Where**: `recipes/*.sh`, each with a `# csync-recipe:`, `# os:`, `# summary:`
  header.
- **Poke it**: `csync recipes` lists them; `--dry-run` prints one before it runs.

## Mesh agent

- **Is**: a peer that syncs text, files, and images between your devices over the
  tailnet.
- **Code**: `agent/` (Go), port 8790, endpoints include `/whoami`, `/peers`,
  `/send`.
- **Trust**: the shared mesh token plus the tailnet.

## Assistant

- **Is**: a chat server with tools, backed by an extensible provider registry.
- **Code**: `assist/` (Go), port 8791, endpoints `/whoami`, `/capabilities`,
  `/providers`, `/config`, `/chat`, `/reset`.
- **Config**: `~/.config/csync/` on the Pi (`providers.json`, `assist.config.json`,
  key files). A new provider is a `providers.json` drop, no code change.

## Phone app

- **Is**: the Android front end for the mesh and the assistant.
- **Where**: a separate repo,
  [csync-hub](https://github.com/alcatraz627/csync-hub).
- **Talks to**: the agent on 8790 and the assistant on 8791, by device name over
  MagicDNS, with the mesh token.
