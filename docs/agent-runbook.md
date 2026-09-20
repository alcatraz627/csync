# Agent runbook

For an agent (or a person) who has to fix csync when it misbehaves. It assumes
nothing and points at exact files, ports, and commands. Read
[architecture.md](architecture.md) once first so the names below mean something.

## Orient in ten seconds

- Console code: `csync/` (Python). Entry is `bin/csync`, which imports
  `csync.cli.main`. Verbs are argparse subparsers in `csync/cli.py`.
- Console state: `~/.config/csync/`. Relay under `~/.config/csync/relay/`.
- Relay sshd log: `~/.config/csync/relay/sshd.log` (LogLevel VERBOSE).
- Audit journal: `~/.local/state/csync/audit.jsonl`.
- Target state: `~/.csync/` on the target.
- Ports: relay sshd 5122, Funnel 10000, per-host reverse-forward 52xx, mesh agent
  8790, assistant 8791.

Run these first for any pairing or connection issue:

```bash
csync status                    # every host, plus relay, Funnel, Tailscale health
csync doctor                    # what init set up, with a fix per failure
lsof -nP -iTCP:5122             # relay listening?
tailscale funnel status         # Funnel forwarding :10000 to localhost:5122?
```

## How registration actually works

A host flips from `invited` (shown as "waiting for the paste") to `online` only
when the target's tunnel authenticates to the relay and the relay's forced
command `csync relay-hello <id>` runs. That command is pinned in the relay
`authorized_keys` line for the invite key. `csync wait` polls for the flip, it
does not cause it. The code path: `relay.hello_main` in `csync/relay.py`, which
reads the hello from `SSH_ORIGINAL_COMMAND`, matches the id, and writes
`status: online`.

So "target says connected but console still says waiting" always means the
tunnel is not authenticating or not landing. It is never a `wait` problem.

## Playbook: a host is stuck at "waiting for the paste"

Work top to bottom. Each step tells you the next.

1. **Is the reverse-forward port up?** The invite baked a port, seen in `csync ls`
   or the `permitlisten` in the relay authorized_keys.

   ```bash
   lsof -nP -iTCP:5203            # replace with the host's port; empty = no tunnel
   ```

   Empty means no tunnel established. Continue.

2. **Read the relay log for that target's attempts.**

   ```bash
   tail -40 ~/.config/csync/relay/sshd.log
   ```

   A target on the Funnel route logs as `127.0.0.1` because Funnel forwards to
   localhost. Look for the pattern for the invite key:

   - `Accepted key ... found at authorized_keys:N` then `Failed publickey` then
     `Connection closed [preauth]`: the key matches but auth fails. Go to step 3.
   - No connection at all: the tunnel never reached the relay. Check Funnel
     (`tailscale funnel status`) and the target's keeper log. Go to step 5.
   - `Accepted` then the forced command runs but errors: auth is fine, the hello
     or the console-side `relay-hello` is failing. Check the python path in the
     authorized_keys `command=`.

3. **Prove whether the key or the path is at fault, from the console.** The
   console keeps its own copy of every invite key under
   `~/.config/csync/invites/<id>/id_ed25519`. Its fingerprint must equal the one
   in the relay log.

   ```bash
   ssh-keygen -lf ~/.config/csync/invites/<id>/id_ed25519
   ```

   Then authenticate that key straight to the relay with a deliberately wrong
   hello id, so the forced command exits without changing any state:

   ```bash
   ssh -v -F none -T -i ~/.config/csync/invites/<id>/id_ed25519 \
     -o IdentitiesOnly=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
     -p 5122 alcatraz627@127.0.0.1 "hello v=1 id=diagtest"
   ```

   - `Authenticated ... using "publickey"` and `csync relay: this key only carries
     a hello`: the key, the authorized line, and sshd are all fine. The fault is
     the target's installed key copy or its route. Go to step 4.
   - `Permission denied (publickey)`: the fault is server-side, reproducible here.
     Inspect the authorized_keys line for that id and `relay.authorized_line` in
     `csync/relay.py`.

4. **Test the target's installed key over the tailnet, bypassing the Funnel and
   the openssl proxy.** On the target:

   ```bash
   ssh -v -F none -T -i ~/.csync/invite_key -o IdentitiesOnly=yes \
     -o StrictHostKeyChecking=no -p 5122 alcatraz627@<console-tailnet-ip> "hello v=1 id=diagtest"
   ```

   - Authenticates: the installed key is good and the Funnel or the `openssl
     s_client` ProxyCommand is the culprit. Move the host to a direct route to the
     relay over the tailnet.
   - `Permission denied`: the installed key is corrupt. This is a bootstrap
     key-install bug; check `b64d` and the invite-key write around
     `bootstrap.sh:124`, fix, and re-mint.

5. **Funnel or keeper failure.** Confirm Funnel forwards `:10000` to
   `localhost:5122` with `tailscale funnel status`. On the target, read the keeper
   log (the LaunchAgent stderr on macOS, `journalctl --user -u csync-tunnel` on
   Linux) for `ExitOnForwardFailure`, a refused forward (port mismatch against
   `permitlisten`), or an `openssl s_client` error.

## Clean slate

When invites have piled up or the state is confused, reset and mint once:

```bash
csync revoke --all              # drop every open invite line on the relay
csync forget <name>             # release the host name
# on the target: run ~/.csync/teardown.sh
csync invite <name> --route funnel --allow-write   # one fresh invite
```

## Common failures and their cause

| Symptom | Likely cause | Where to look |
|---|---|---|
| stuck at "waiting for the paste", relay log shows Failed publickey | target's installed key is corrupt, or a server-side key/line bug | step 3, then step 4 |
| target says connected, relay log shows no inbound at all | Funnel down or keeper not dialing | `tailscale funnel status`, keeper log |
| `file://` in the paste line and a warning | csync tree is dirty or unpushed | commit and push, or serve the repo and pass `--src` |
| forced command errors after auth | the `command=` python path moved | the authorized_keys `command=` field |
| `run`/`push` refused with exit 2 | agent actor without `--allow-write` on that call | add `--allow-write` |

## Rules for touching csync as an agent

- Never bypass a gate to make something pass. If a verb refuses, the refusal is
  usually correct; find why.
- Prefer reading state files directly (the relay log, `~/.config/csync/`) over
  running mutating csync verbs while a human or another agent is driving the same
  console.
- Reproduce a failure locally before changing code. The console holds copies of
  the keys and can talk to its own relay, as step 3 shows.
- When you change bootstrap or the target scripts, remember the token carries
  their sha256; a change means a re-mint, and a dirty tree means the pinned URL
  falls back to `file://`.
