<div align="center">
  <img src="assets/cover.svg" alt="csync" width="112">
</div>

<h1 align="center">csync</h1>

<p align="center">
  Drive another laptop from this one after a single pasted line there, and leave
  it exactly as you found it when you are done.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/console-python%203.12%2B-3776AB" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/targets-macOS%20%C2%B7%20Linux%20%C2%B7%20Android-46C46A" alt="Targets">
  <img src="https://img.shields.io/badge/transport-Tailscale%20%C2%B7%20reverse%20SSH-4C9BE8" alt="Transport">
</p>

---

## What it is

csync turns your Mac into a console that can operate another laptop over a tunnel
that the other laptop opens itself. The other laptop installs nothing. It pastes
one line, presses Enter, and types its password once. From then on you run one
command each to copy files either way, run setup recipes, take screenshots, read
hardware, and pull logs. Every command has a `--json` form, so an agent can drive
it as well as a person.

When the session ends, `csync teardown` reverses every change and proves it. The
target keeps no admin rights after the first minute, a timed backstop tears the
session down even if your Mac disappears, and every command is logged on both
ends.

There are three parts. The **console** is your Mac: the `csync` CLI, a small
hardened relay sshd, and a Tailscale Funnel that publishes it. The **target** is
the other laptop: its own sshd listening on loopback only, plus a keep-alive
reverse tunnel back to the console. The **route** between them is a direct LAN
hop when both are on the same network, and TLS through Tailscale Funnel otherwise.

## Requirements

On the console (your Mac): macOS 15 or newer, Python 3.12 or newer, and Tailscale
for the Funnel route. On a target: macOS 13+, a systemd Linux including a
Raspberry Pi, or an Android phone running Termux. A target needs only `bash`,
`curl`, `ssh`, and, for the Funnel route, `openssl`, all of which it already has.

## Install

csync runs straight from the repo. Clone it, put `bin/` on your `PATH`, then
initialise the console once.

```bash
git clone https://github.com/alcatraz627/csync.git
cd csync
export PATH="$PWD/bin:$PATH"     # add to your shell profile to keep it

csync init                        # generates keys, installs the relay, publishes Funnel
csync doctor                      # confirms every piece is up, with a fix for anything that is not
```

`csync init` is a one-time setup. `csync doctor` is safe to run any time and
`csync doctor --fix` starts Tailscale or the relay if either has stopped.

## Quick start

A whole session, from your Mac. Replace `rahul-mbp` with any name you like for the
other machine.

```bash
csync invite rahul-mbp            # prints ONE line to send them
# they paste that line in their terminal, press Enter, type their password once
csync wait rahul-mbp             # returns when the tunnel is up, about 30 seconds

csync shot rahul-mbp             # screenshot, saved under ~/csync/rahul-mbp/shots/
csync pull rahul-mbp ~/Library/Logs/DiagnosticReports
csync recipe rahul-mbp install-steam
csync run rahul-mbp --allow-write 'sw_vers'

csync teardown rahul-mbp --verify  # removes everything, restores their sshd, proves it
```

The other laptop only ever pastes the one invite line. Everything after that is a
command on your Mac.

## Commands

| Command | What it does |
|---|---|
| `csync init` | one-time console setup: keys, relay sshd, Funnel |
| `csync doctor [--fix]` | re-check everything init set up, and optionally start what stopped |
| `csync invite <name> [--route auto\|lan\|funnel] [--src URL]` | mint an invite and print the one paste line |
| `csync wait <name> [--timeout 10m]` | block until the target's tunnel is up |
| `csync status` | every host with its state, expiry, and last action, plus relay and Funnel health |
| `csync ls` | open invites and their expiries |
| `csync run <name> [--allow-write] <cmd>` | run a command on the target through the tunnel |
| `csync pull <name> <src>… [dst]` | copy files from the target |
| `csync push <name> <src>… [dst]` | copy files to the target's `~/Downloads/csync/` |
| `csync shot <name> [--display N] [--open]` | screenshot the target |
| `csync recipe <name> <recipe> [--dry-run]` | stream a reviewed setup script to the target |
| `csync recipes` | list the recipes in this repo |
| `csync persist <name> on\|off\|status` | turn the target's always-on behaviour on or off |
| `csync log [name] [--last 20] [--relay]` | read the audit journal or the relay log |
| `csync teardown <name> [--verify] [--yes]` | reverse every change on the target and confirm |
| `csync forget <name>` / `csync revoke --all` | drop a used name, or close every open invite |

An agent driver (a non-TTY caller, or `CLAUDECODE` set) gets the reading verbs by
default. Each writing verb needs `--allow-write` on that call, which the journal
records, and `--force` is never available without a real terminal.

## Serving the bootstrap to a remote target

The invite bakes a source URL the target fetches `bootstrap.sh` and the teardown
scripts from. When the repo is a clean, pushed commit, csync uses the pinned
GitHub raw URL automatically, so a target anywhere can pair. When the tree is
dirty or unpushed, csync falls back to a `file://` path that only works on this
machine, and warns you. Two ways to pair a genuinely remote target:

- Commit and push, so the pinned raw URL applies. This is the intended flow.
- Serve the repo over your tailnet and pass it explicitly, which serves the exact
  local files:

  ```bash
  python3 -m http.server 6242 --directory "$PWD" --bind 0.0.0.0
  csync invite air --route funnel --src http://<your-tailnet-ip>:6242 --allow-write
  ```

## The mesh and the assistant

Beyond driving a laptop, this repo also carries a small mesh layer: a peer
**agent** for syncing text, files, and images between your devices over the
tailnet, and an **assist** server (Gemini backed, provider-extensible) that
answers over the same wire with tools for home-server health, peer listing, and
gated shell commands. The phone side of all this is a separate Android app,
[csync-hub](https://github.com/alcatraz627/csync-hub).

## Recipes

Recipes are plain shell files under `recipes/`, each with a three-line header
(`# csync-recipe:`, `# os:`, `# summary:`). They run from the pinned commit, never
from a dirty tree without `--dev`, and `--dry-run` prints the exact script before
anything runs. `recipes/hello.sh` proves the path; `recipes/install-steam.sh`
installs Steam into `~/Applications` with no admin rights.

## Safety in one glance

The target listens on no network interface; the console only walks through the
tunnel the target opened. The invite key expires (one hour by default) and can
bind one loopback port, never a shell. A root timer tears the session down at its
deadline even if the console vanishes, and it can only run the exact teardown
script whose hash was recorded. `csync teardown --verify` lists anything left and
exits non-zero until nothing remains.

## Tests

```bash
python3 -m unittest discover -s tests    # token and JSON surface
bash tests/loopback.sh                    # end-to-end on one machine
```

## Documentation

| Document | What it covers |
|---|---|
| [docs/spec.md](docs/spec.md) | the full definition: routes, the token, the bootstrap steps, the security model, and the teardown guarantee |
| [examples/pihub](examples/pihub) | a small hub example served on a Pi |
