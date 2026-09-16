# csync

csync lets this Mac drive another laptop after one pasted line on that laptop,
and leaves that laptop exactly as it found it when the session ends. The other
laptop installs nothing: it reaches back to this Mac over a reverse SSH tunnel
using the ssh client it already has, and this Mac then copies files either way,
runs setup recipes, takes screenshots, reads hardware, and pulls logs through
that tunnel with one command each. Every command has a `--json` form so an agent
can drive it as well as a person.

Status: definition, before build. Build plan and parity ledger:
`.claude/output/20260905-2044-csync-change/plan.md`.

## What a session looks like

Three situations this is for, in the owner's words: operating "my other laptop"
from the big monitor; "helping my friends out" with a game or a widget on their
machine; and "find and copy and transfer logs or hardware features" without
clicking around sixteen times.

```
console (this Mac)                                  target (the other laptop)
──────────────────                                  ─────────────────────────
csync invite rahul-mbp ──► one line, sent by chat ──► paste, Enter, sudo password
csync wait rahul-mbp   ◄── tunnel comes up ◄────────── bootstrap finishes (≈30 s)
csync shot rahul-mbp
csync pull rahul-mbp ~/Library/Logs/DiagnosticReports
csync recipe rahul-mbp install-steam
csync teardown rahul-mbp --verify ──────────────────► everything removed, sshd as found
```

Every arrow is a command on the console or a paste on the target. There is no
menu to click on either machine.

## The three parts

| Part | Machine | What it is | What it holds |
|---|---|---|---|
| Console | this Mac | the `csync` CLI, a small hardened relay sshd, a Tailscale Funnel publishing that sshd | the only long-lived private key; host records; audit log; pulled files |
| Target | any Mac or Linux laptop | its own sshd, listening on loopback only, plus a keep-alive reverse tunnel to the console | one authorized-key line, one sshd drop-in, one state file, one teardown script |
| Route | the network between them | LAN direct when both are on the same network; otherwise TLS through Tailscale Funnel | nothing; it carries bytes |

```
            target                                          console
  ┌──────────────────────────┐                   ┌──────────────────────────────┐
  │ sshd  127.0.0.1:22       │                   │ relay sshd  0.0.0.0:5122     │
  │   ▲                      │   reverse tunnel  │   key-only · forced command  │
  │   │ localhost            │ ════════════════► │   permitlisten 127.0.0.1:52NN│
  │ ssh -R 52NN:localhost:22 │                   │        ▲                     │
  │   (LaunchAgent, KeepAlive)│                  │        │ csync ssh/rsync to  │
  └──────────────────────────┘                   │        │ 127.0.0.1:52NN      │
          │ route                                 └────────┼─────────────────────┘
          ├─ lan:    tcp  → console-lan-ip:5122            │
          └─ funnel: tls  → <console>.tail905820.ts.net:10000 ─► tailscale funnel
                            (openssl s_client as ProxyCommand)     → localhost:5122
```

The target never listens on any network interface. The console never connects
outward to the target; it only walks through the tunnel the target opened.

## Zero-click ledger

The owner's bar: if onboarding, launching, or connecting needs a click on either
side, it is still bad. Each step below states its cost honestly.

| Step | Where | Clicks | Typing | How often |
|---|---|---|---|---|
| `csync init` | console | 0, except Funnel's first enablement, which opens one browser approval | one command | once ever |
| Tailscale running on console | console | 0 while this Mac stays logged in to the tailnet; a browser login only if it has been logged out | none | once ever |
| `csync invite <name>` | console | 0 | one command | per session |
| Send the paste line | any chat app | n/a | paste | per session |
| Run the paste line | target | 0 | paste, Enter, the target's sudo password | per session |
| `csync wait`, then drive | console | 0 | commands | per session |
| `csync teardown --verify` | console | 0 | one command | per session |
| Screen Recording permission for remote screenshots | target, macOS only | 1 toggle in System Settings, first time only, only if screenshots are wanted | none | once per target `[VERIFY]` spike S1 |

The last row is the one exception, and it is an operating system rule: macOS
does not let a shell grant Screen Recording. Spike S1 settles whether macOS 26
still needs it and which binary to grant it to. Everything else is zero clicks
on both sides once `csync init` has run.

## Why the target installs nothing

Tailscale was the obvious tunnel and it fails the zero-click bar on the target
side, so it stays on the console only.

| Tailscale on a macOS target | Zero-click? | Source |
|---|---|---|
| App Store build | no, and it "cannot be a Tailscale SSH server" | tailscale.com/kb/1065, variant table |
| Standalone `.pkg` build | no: first launch asks the user to approve a VPN configuration and a system extension `[VERIFY]` | recollection; vendor page is silent on dialogs |
| Open-source `tailscaled` | yes if Homebrew already exists; the vendor recommends it "only for unattended installs managed by experienced macOS system administrators" | tailscale.com/kb/1065 |
| Any build on Linux | yes, `curl … install.sh` then `tailscale up --auth-key` | tailscale.com/kb/1031 |

A reverse SSH tunnel needs only `ssh`, which ships on macOS and on every desktop
Linux, and `openssl`, which ships on both, for the TLS hop through Funnel. On
the console, Tailscale is already installed (CLI 1.102.3 and the app), and
Funnel is the zero-configuration way to give this Mac a public TLS port:
`tailscale funnel --tls-terminated-tcp=10000 tcp://localhost:5122`
(tailscale.com/kb/1311). Funnel traffic "is subject to non-configurable
bandwidth limits" and passes through Tailscale's relays (tailscale.com/kb/1223),
which is why csync prefers the LAN route whenever the target can reach the
console directly.

## Routes

| Route | When | Target reaches | Cost | Version |
|---|---|---|---|---|
| `lan` | both on one network (helping a friend at their place, the second laptop at home) | `<console-lan-ip>:5122` directly | full LAN speed | v1 |
| `funnel` | anywhere else | `<console>.tail905820.ts.net:10000` over TLS, then the relay sshd | Funnel bandwidth cap, fine for shells, logs, screenshots | v1 |
| `tailnet` | the owner's own machines, permanently | direct WireGuard, no tunnel | one-time Tailscale install with its approval prompts, acceptable on a machine the owner sits at | v2 |

`csync invite` defaults to `--route auto`: the token carries both the LAN
address and the Funnel address, the bootstrap probes the LAN address first and
falls back to Funnel. The console's ssh configuration is the same either way,
because it always connects to a loopback port that the tunnel owns.

## The paste line and the token

```
bash <(curl -fsSL https://raw.githubusercontent.com/alcatraz627/csync/3f9c2e1/bootstrap.sh) eyJ2IjoxLCJpZCI6…
```

| Piece | Purpose |
|---|---|
| raw URL pinned to a commit | the target runs exactly the reviewed script; a later push cannot change what a sent invite does |
| `bash <(curl …)` | keeps stdin free, so `sudo` can ask for the password on the terminal |
| token, base64url | everything the bootstrap needs, so it asks nothing |

Token contents, plain `key=value` lines under the base64 so bash 3.2 can read
them without python or jq:

| Key | Value | Why it travels |
|---|---|---|
| `v` | 1 | format version |
| `id` | invite id, 8 hex | names the authorized-key lines and the state file on both ends |
| `name` | `rahul-mbp` | the host alias on the console |
| `route` | `auto`, `lan`, `funnel` | see Routes |
| `exp` | unix time, default invite + 1 h | after this the token is refused by the relay |
| `ttl` | seconds, default 4 h | when the target tears itself down if the console never does |
| `lan` | `192.168.1.20:5122` | LAN route endpoint |
| `funnel` | `aakarshs-macbook-pro.tail905820.ts.net:10000` | Funnel route endpoint |
| `relay_hostkey` | `ssh-ed25519 AAAA…` | pins the console's relay host key, so no prompt and no MITM |
| `port` | 5201 | the loopback port on the console this target's tunnel binds |
| `console_pub` | `ssh-ed25519 AAAA…` | the console's long-lived public key, installed on the target |
| `invite_key` | OpenSSH ed25519 private key, one per invite | the target's credential into the relay sshd |

The token is about 900 characters. It is meant to be sent as a message, never
read aloud. The private key in it is single-purpose: it can only open one
reverse listener on one fixed port on the console, it cannot get a shell, and
the console deletes its line at teardown or at `exp`, whichever is first. Two
machines pasting the same token cannot both connect, because the second cannot
bind the same port. A v1.1 hardening that keeps private keys off the wire is in
the plan's appendix.

## What the bootstrap does on the target

Ordered, and every step that changes the machine is recorded in
`~/.csync/state.env` (plain `key='value'` lines, so bash 3.2 can source it)
and `~/.csync/changes.log` before it runs, so teardown can reverse exactly what
happened. Each step prints one line. The steps that need root are gathered
into one generated script and run under a single `sudo`, so the password is
asked once.

| # | Step | macOS | Linux | Recorded |
|---|---|---|---|---|
| 1 | Refuse unsupported hosts | Darwin 13+ on arm64 or x86_64 | a distro with apt, dnf, or pacman | os, version, arch |
| 2 | Decode the token, check `exp` | | | id, name, port |
| 3 | Snapshot prior state | Remote Login on or off, members of `com.apple.access_ssh`, sshd drop-in present | sshd installed, enabled, active | the snapshot |
| 4 | Turn on sshd | `sudo systemsetup -setremotelogin on`, or `launchctl bootstrap system …/ssh.plist` `[VERIFY]` S2 | `apt install openssh-server` if absent, `systemctl enable --now ssh` | what was changed |
| 5 | Confine sshd to keys and one user | drop-in `/etc/ssh/sshd_config.d/000-csync.conf`: `PasswordAuthentication no`, `KbdInteractiveAuthentication no`, `AllowUsers <me>`. launchd owns the port-22 socket on macOS, so the drop-in cannot move it to loopback; the `from=` on the key and keys-only auth do that job | same path, plus `ListenAddress 127.0.0.1`, which sshd honours there | drop-in written, whether one existed |
| 6 | Restrict Remote Login to this account | done by `AllowUsers` in the drop-in; the `com.apple.access_ssh` group is left alone | same | |
| 7 | Install the console's key behind the gate | append `restrict,pty,from="127.0.0.1,::1",command="$HOME/.csync/gate.sh" ssh-ed25519 … # csync:<id>` to `~/.ssh/authorized_keys` | same | marker line, whether the file existed |
| 8 | Write the invite key, the pinned host key, and the three scripts | `~/.csync/invite_key`, `~/.csync/known_hosts`, `~/.csync/gate.sh`, `~/.csync/teardown.sh`, `~/.csync/teardown-root.sh`, each fetched from the pinned commit and checked against the sha256 carried in the token | same | paths and hashes |
| 9 | Probe the route | LAN endpoint first, 2 s; else Funnel | same | route chosen |
| 10 | Start the tunnel under a supervisor | LaunchAgent `sh.csync.tunnel`, KeepAlive, `ssh -N -R 127.0.0.1:<port>:localhost:22 … 'hello …'` | `systemd-run --user --unit csync-tunnel` | unit name |
| 11 | Arm the TTL backstop | root LaunchDaemon `sh.csync.ttl` runs `teardown-root.sh` every 15 s; it acts at the deadline, or as soon as `~/.csync/teardown.requested` appears, then removes itself | root timer `csync-ttl-<id>` every 15 s, same script | unit name, deadline |
| 12 | Print the change ledger | every line from state.json, for the friend to read | same | |

Step 10 is not `ssh -N`. The tunnel session carries a command string that the
relay's forced command reads as `SSH_ORIGINAL_COMMAND`:

```
hello v=1 id=3f9c2e1a user=rahul host=Rahuls-MacBook-Pro os=darwin osver=26.6.2 arch=arm64 sshd_hostkey=ssh-ed25519_AAAA… deadline=1757104800
```

That one line tells the console the login name to use, the target's sshd host
key to pin, and when the target will tear itself down. The session staying open
is the liveness signal; the LaunchAgent reconnects when it drops.

Nothing in the bootstrap needs python, brew, Xcode tools, or a browser. On a
macOS target the whole script must run under bash 3.2.

## Console commands

| Command | Does | Prints |
|---|---|---|
| `csync init` | generates the console key and relay host keys, writes the relay sshd config, installs its LaunchAgent, publishes Funnel, checks Tailscale | a readiness table, then the one thing left to do if any |
| `csync doctor [--fix]` | re-checks everything `init` set up; starts Tailscale and the relay if stopped | pass or fail per check with the fixing command |
| `csync invite <name> [--route auto\|lan\|funnel] [--ttl 4h] [--expires 1h]` | mints the invite key, writes the relay authorized-key line, builds the token | the paste line, alone on its own line |
| `csync wait <name> [--timeout 10m]` | blocks until the hello arrives and `ssh true` succeeds | the host row |
| `csync ls` | all hosts: name, os, user, route, online, expires | a table |
| `csync status` | hosts with state glyphs, expiry, last action; relay, Funnel, Tailscale health | one screen |
| `csync log [name] [--last 20] [--relay]` | reads the audit journal, or the relay log | time, host, verb, outcome per line |
| `csync sh <name>` | interactive shell, recorded on the target, terminal title set to the host | |
| `csync run <name> [--force] -- <cmd…>` | runs a command, streams output; `--force` lifts the target's refusals and needs a TTY | the output, then the remote exit code |
| `csync push <name> <src>… [dst] [--overwrite] [--dry-run]` | rsync to the target, default `~/Downloads/csync/`, refuses an existing path without `--overwrite` | progress, then the remote paths |
| `csync pull <name> <src>… [dst]` | rsync from the target, default `~/csync/<name>/inbox/` | progress, then the local paths |
| `csync shot <name> [--display N] [--open]` | screenshot to `~/csync/<name>/shots/<ts>.png` | the path |
| `csync info <name> [section…]` | hardware and device summary; sections: system cpu memory disk battery displays usb bluetooth network audio camera | a table per section |
| `csync logs <name> [--since 1h] [--app X] [--crash]` | system log slice, crash reports, app logs, bundled to `~/csync/<name>/logs/<ts>.tar.gz` | a one-screen digest and the bundle path |
| `csync recipe <name> <recipe> [--dry-run] [-- args]` | streams `recipes/<recipe>.sh` to the target's bash | the recipe's output |
| `csync recipes` | lists recipes with their `# summary:` and `# os:` headers | a table |
| `csync open <name> <url\|app\|path>` | `open` on macOS, `xdg-open` on Linux, on the target's screen | |
| `csync say <name> "<text>"` | a notification on the target's screen | |
| `csync persist <name> [on\|off\|status]` | turns the target's always-on behaviour on or off without ending the session; on Android that is the wake-lock and the boot script | what changed, and the settings intent for the battery grant |
| `csync teardown <name> [--verify] [--yes] [--dry-run] [--no-receipt]` | shows what will be removed and asks, runs the target's teardown script through the tunnel, copies the session log home, leaves the receipt, then removes the console side | a residue table, empty when clean |
| `csync forget <name>` | drops a host record whose tunnel is already gone | |
| `csync` | with no arguments, a picker: host, then command | |

Recipes are plain shell files in the repo with a three-line header
(`# csync-recipe: install-steam`, `# os: darwin`, `# summary: …`). They never
live on the target; the console streams them. `--dry-run` prints the script so
the owner can read what will run on a friend's machine.

The no-argument picker uses the `std::claude::tui` library (`tui_pick_one`),
so it degrades from fzf to gum to a numbered prompt and never hangs when there
is no terminal.

## Machine surface

An agent drives csync from a shell, so the CLI is the API. There is no daemon
to query and no MCP wrapper to maintain.

| Obligation | How csync meets it |
|---|---|
| Structured output | every command takes `--json`; the human table is rendered from the same object |
| Never prompt when blind | with `--json` or a non-TTY stdout, nothing asks; destructive verbs need `--yes` and otherwise exit 2 with the flag named |
| Waits live inside actions | `csync wait` exists, and `run`, `push`, `pull`, `shot` wait up to `--timeout` for a reconnecting tunnel before failing |
| Errors propose the fix | every non-zero exit carries `fix:` with the exact next command (`csync doctor --fix`, `csync invite <name>` again, `csync forget <name>`) |
| Output budgets | `info` and `logs` print digests and write the full payload to a file whose path is in the output; `run` truncates after 200 lines unless `--full` |
| Deltas, not silence | `push` and `pull` list what moved; `teardown` lists what was removed and what remains; an empty result says `nothing matched` |
| Journal | every command appends one line to `~/.local/state/csync/audit.jsonl`: time, host, verb, args, actor, exit, duration, files moved |
| Least power by default | an agent actor (stdout not a TTY, or `CLAUDECODE` set) gets the reading verbs; each writing verb needs `--allow-write` on that call, and `--force` is never available without a TTY |

Exit codes:

| Code | Meaning |
|---|---|
| 0 | done |
| 2 | usage, or a flag a blind caller must add |
| 3 | unknown host |
| 4 | host offline after the timeout |
| 5 | remote command failed; the remote code is in the JSON |
| 6 | console prerequisite missing; `csync doctor` names it |
| 7 | invite expired or already used |
| 8 | teardown left residue; the table lists it |

## Trust: logging, guardrails, visibility

Confidence comes from three things being true at once: everything that
happened is written down where each party can read it, the accidents that
matter are refused before they run, and the state is visible in one line
without asking.

### Four records, one per reader

| Record | Where | Written by | Holds | Read with |
|---|---|---|---|---|
| Console audit journal | `~/.local/state/csync/audit.jsonl` | every `csync` command, including failures | time, host, verb, full args, actor (human or agent), exit, duration, files moved, bytes | `csync log [name] [--last 20] [--json]` |
| Target session log | `~/.csync/session.log` on the target | `gate.sh`, the forced command in front of every SSH session | every command the console ran, as the target saw it, with a plain-language note beside the streamed verbs; interactive shells recorded with `script` to `~/.csync/shell-<ts>.log` | the friend, any time; copied to `~/csync/<name>/session/` at teardown |
| Relay log | `~/.config/csync/relay/sshd.log` | the relay sshd at `LogLevel VERBOSE` | tunnel up and down, refused keys, hello lines | `csync log --relay` |
| Receipt | `~/Desktop/csync-receipt-<date>.txt` on the target | teardown, unless `--no-receipt` | the change ledger, every command run, files moved in and out, and the verification that everything else was removed | the friend, after the session |

The receipt is the one file teardown leaves behind on purpose. The bootstrap
says so in its closing lines, so the friend expects it.

`gate.sh` is how the target keeps its own record. The console's key on the
target carries `command="$HOME/.csync/gate.sh"`, so sshd hands every session
to the gate first. The gate logs `SSH_ORIGINAL_COMMAND`, applies the refusals
below, then runs it: a command, an `rsync --server`, the `sftp` subsystem, or
a recorded login shell when the command is empty. Because the gate sits in the
key line, it holds even when someone bypasses `csync` and uses raw `ssh`. The
one command it does not write down is the bare `true` the console sends as a
liveness probe before each verb.

A verb that streams a script arrives as `bash -s`, which tells the person
reading the log nothing, so the console prefixes `CSYNC_OP=<name>` and the gate
turns that key into a phrase of its own: `shot` reads as "took a screenshot".
The console supplies the key and never the words, the raw command stays on the
line beside the phrase, and a key that is not a bare lowercase name is dropped.
So a console that lied about which verb it was running would still have its
actual command written down, which is the property that makes the log worth
reading.

### What is refused before it runs

| Accident | Guard | Where it lives |
|---|---|---|
| Acting on the wrong laptop | every verb prints the host row before doing anything; there is no default host, the name is always typed; `csync sh` sets the terminal title to the host name; a name cannot be reused until `csync forget` | console |
| Destroying the target | the gate refuses `rm -rf` aimed at `/`, `~`, or `*`, and `mkfs`, `diskutil erase`, `dd of=/dev`, `shutdown`, `reboot`, `launchctl bootout system`, and writes under `/System`; `csync run --force` lifts it for one command, and `--force` needs a TTY | target |
| Admin rights that outlive the session | csync holds no sudo on the target after the bootstrap; the root TTL daemon can only run the `teardown.sh` whose hash is in `state.json`; a recipe that needs admin prints the command for the friend to type at their own keyboard | target |
| Overwriting the friend's files | `push` lands in `~/Downloads/csync/` and refuses an existing path without `--overwrite`; rsync never runs with `--delete`; `pull` never removes anything on the target | console |
| Running a recipe nobody reviewed | recipes run from the pinned commit, never from a dirty working copy without `--dev`; `--dry-run` prints the exact script | console |
| Tearing down the wrong host | `teardown` shows the host row and what will be removed, then asks; `--yes` from a script, `--dry-run` to see it | console |
| An agent doing more than it was asked | an agent actor gets `ls`, `status`, `log`, `wait`, `pull`, `shot`, `info`, `logs` by default; `run`, `push`, `recipe`, `open`, `say`, `teardown` need `--allow-write` on that call, which the journal records; `--force` is never available without a TTY | console |
| Too many doors open | at most 5 open invites; `csync ls` shows every expiry; `revoke --all` closes everything in one command | console |

The console-side guards stop accidents. The target-side gate stops
destruction even if the console is bypassed. The friend's account having no
sudo bounds what any of it can reach.

### What you see without asking

| Moment | What appears | Where |
|---|---|---|
| Any command starts | one line: `rahul-mbp · rahul@Rahuls-MacBook-Pro · macOS 26.6 · funnel · online 12m · ends in 3h41m` | console, first line of output |
| Any command ends | one line: what changed and the next command, or the `fix:` line | console, last line |
| Tunnel comes up, drops, or reconnects | a macOS notification: `csync: rahul-mbp connected (funnel)` | console, opt-out in config |
| TTL is 10 minutes away | a notification naming the host and the deadline | console |
| "Is everything fine?" | `csync status`: hosts with 🟢 online, 🟡 reconnecting, 🔴 gone, ⏳ waiting for the paste, each with expiry and last action; relay, Funnel, and Tailscale health under it | console, one screen |
| Bootstrap finishes | six lines on the target: who is connected, what he can do (run commands as you, copy files, take screenshots, read device info), what he cannot (admin, your passwords), when it ends, where the log is, how to end it now (`~/.csync/teardown.sh`) | target |
| Session connects or ends | a notification on the target's screen | target |
| Session ended | the receipt on the Desktop | target |

## Files and state

Console:

| Path | Holds |
|---|---|
| `~/.config/csync/config.json` | tailnet hostname, ports, defaults |
| `~/.config/csync/id_ed25519`, `.pub` | the console's long-lived key, generated by `init` |
| `~/.config/csync/relay/` | relay sshd config, its host keys, `authorized_keys` with one line per open invite, pid file |
| `~/.config/csync/ssh_config` | one `Host csync-<name>` block per host; plain `ssh -F` works too |
| `~/.config/csync/known_hosts` | target sshd host keys, pinned from the hello |
| `~/.config/csync/hosts.json` | host records: name, id, user, os, route, port, deadline, last hello |
| `~/.local/state/csync/audit.jsonl` | the journal |
| `~/csync/<name>/inbox`, `shots`, `logs` | pulled files, screenshots, log bundles |
| `~/Library/LaunchAgents/sh.csync.relay.plist` | keeps the relay sshd running |

Target, all of it removed by teardown:

| Path | Holds |
|---|---|
| `~/.csync/state.env`, `changes.log` | the snapshot and the change ledger |
| `~/.csync/teardown.sh` | self-contained reversal, needs no network; the friend can run it any time |
| `~/.csync/teardown-root.sh`, copied to `/Library/Application Support/csync/<id>/` or `/etc/csync/<id>/` | the root half: drop-in removal and Remote Login restore, run by the TTL unit only |
| `~/.csync/tunnel.sh` | the reverse-tunnel loop the supervisor keeps alive |
| `~/.csync/gate.sh` | logs and screens every SSH session before it runs |
| `~/.csync/session.log`, `shell-<ts>.log` | the target's own record; copied to the console, then removed |
| `~/.csync/invite_key`, `known_hosts` | the tunnel credential and the pinned relay host key |
| `~/Library/LaunchAgents/sh.csync.tunnel.plist` or `csync-tunnel.service` | the tunnel supervisor |
| `/Library/LaunchDaemons/sh.csync.ttl.plist` or `csync-ttl.timer` | the backstop |
| `/etc/ssh/sshd_config.d/000-csync.conf` | keys-only, one user; loopback-only on Linux |
| one line in `~/.ssh/authorized_keys` | tagged `# csync:<id>` |

## Security model

| Threat | Answer |
|---|---|
| The paste line leaks later | the relay refuses the invite key after `exp` (1 h default); the key can only bind one loopback port, never a shell |
| A friend's machine as a way into the console | the relay sshd is a separate process with its own config: keys only, `UsePAM no`, `PermitTTY no`, forced command, `AllowTcpForwarding remote`, `permitlisten` pinned to one port. It is not the console's Remote Login sshd |
| A friend's machine as a way into the tailnet | it is never on the tailnet |
| Someone on the friend's network reaches their sshd | passwords off, one user allowed, and the console's key only works from `from="127.0.0.1,::1"`, which is where the tunnel delivers it. On Linux sshd also binds 127.0.0.1 only. On macOS launchd owns the port-22 socket on every interface, so the port answers on the LAN but nothing can authenticate on it |
| Someone on the console's network reaches the relay | key-only, no shell, no pty, forced command that only records a hello; port 5122 carries nothing else |
| A tampered bootstrap | the URL is pinned to a commit over TLS; `csync invite --show-script` prints the script that URL serves |
| Console laptop lost | keys sit under FileVault; `csync revoke --all` deletes every relay line and every open invite |
| Secrets in the public repo | the repo carries no keys; tokens are minted locally and never written to the repo |
| The owner's own reach on a friend's machine | sudo is used for exactly the steps in the bootstrap table, each recorded, and the change ledger is printed to the friend at the end |
| A stuck session | the TTL backstop tears down without the console; `csync ls` shows every deadline; the friend can run `~/.csync/teardown.sh` themselves |
| Admin rights left on the target | none after the bootstrap ends; the only root path is the TTL daemon, and it can only run the recorded `teardown.sh` |
| An agent misusing the console | reading verbs by default, writing verbs need `--allow-write` per call, `--force` needs a TTY, and every call is in the journal with `actor: agent` |

The console's own `/etc/ssh/sshd_config`, `~/.ssh/config`, and
`~/.ssh/authorized_keys` are never touched. The tailnet policy file is never
edited by the tool; `doctor` prints what to paste when Funnel is not yet
allowed.

## Teardown guarantee

`csync teardown <name> --verify` runs the target's `teardown.sh` through the
tunnel, then removes the console side, then proves the result.

| Removed on the target | Restored to the snapshot |
|---|---|
| the `# csync:<id>` line in `authorized_keys` | Remote Login on or off as it was |
| `/etc/ssh/sshd_config.d/csync.conf`, sshd reloaded | `com.apple.access_ssh` membership as it was |
| the tunnel LaunchAgent or unit, unloaded and deleted | |
| the TTL LaunchDaemon or timer, unloaded and deleted | |
| `~/.csync/` | |

| Removed on the console | Verified how |
|---|---|
| the relay `authorized_keys` line for the invite | `ssh -i <invite_key> … ` is refused |
| the `Host csync-<name>` block and the known_hosts entry | `csync run <name>` exits 3 |
| the host record | `csync ls` no longer lists it |

`--verify` prints a residue table; a clean run prints an empty one and exits 0.
Anything left prints with the command that removes it and exits 8. Pulled
files under `~/csync/<name>/` stay, because they are the owner's. On the
target, the receipt on the Desktop is the one deliberate leftover, and the
residue check knows to ignore it; `--no-receipt` removes even that.

## Operating systems

| Role | Supported | Notes |
|---|---|---|
| Console | macOS 15+ (this Mac runs 26.6.2) | Python 3.12+ from the system or Homebrew, Tailscale app or CLI |
| Target | macOS 13+ | bash 3.2, no python needed |
| Target | Debian, Ubuntu, Fedora, Arch with systemd | `openssh-server` installed if missing. A Raspberry Pi running Raspberry Pi OS is this row, with no Pi-specific code |
| Target | Android 9+ under Termux | no root and no sudo at any point. Termux installed once from F-Droid, then the same paste line. sshd on 8022, wake-lock and a Termux:Boot script for always-on, both removed by teardown or by `csync persist <name> off` |
| Target | Windows 10+ | planned: `bootstrap.ps1`, OpenSSH Server capability, `ssh.exe` for the tunnel. The architecture already fits; only the bootstrap differs |

### The Android target in detail

Everything structural is unchanged: the same token, relay, reverse tunnel, gate,
and teardown. What differs is below, and the whole `sudo` half of the bootstrap
disappears, because Termux is an unprivileged sandbox with no system service to
toggle and nothing privileged to restore.

| Concern | Laptop | Android under Termux |
|---|---|---|
| Prerequisites | ssh and curl are preinstalled | Termux from F-Droid, then the bootstrap runs `pkg install openssh rsync termux-api` itself |
| Interpreter | `/bin/bash` | `$PREFIX/bin/bash`; the bootstrap resolves it, because `/bin` does not exist |
| sshd port | 22 | 8022, which is what a non-root process may bind. The target picks this itself, so the console needs no flag |
| Privilege | one `sudo` for the service and the TTL daemon | none at all |
| Staying alive | LaunchAgent or systemd unit | `termux-wake-lock` plus `~/.termux/boot/csync-<id>.sh`, needing the Termux:Boot app |
| Turning always-on off | not applicable | `csync persist <name> off` releases the lock and deletes the boot script while the session continues; teardown does both anyway |
| Screenshot | the real screen | a camera frame, front or back. A real screen capture needs root or the ADB mode, and `csync shot` says so rather than returning something misleading |
| Logs | the system log | only this app's own logcat lines, which Android enforces without root. The digest says so |
| Extra `info` sections | none | `telephony`, `location`, `sensors`, on top of the usual ones, through Termux:API |

Battery optimisation is the one grant a script cannot revoke, because Android
routes it through a system settings page. `csync persist <name> on` prints the
exact intent that opens the page, and `off` prints the one that reopens it, so
the grant stays as easy to withdraw as it was to give.

**Confirmed on hardware, 2026-09-06**, a Redmi Note 10 Pro on Android 13 with
F-Droid Termux 0.118.3: the bootstrap, the tunnel, `run`, `info`, `push`,
`pull`, `logs`, `say`, `shot`, `recipe`, `persist`, and teardown all work, and
the gate refuses a destructive command even over raw ssh. What that run taught,
which no loopback could:

| Finding | Consequence |
|---|---|
| The Play Store Termux carries no matching Termux:API or Termux:Boot | F-Droid is the build to install, and the three apps must come from the same source so their signatures match |
| Android 12+ kills long-running child processes of an app | the tunnel needs `settings put global settings_enable_monitor_phantom_procs false`, which is one ADB command and survives until a factory reset |
| `/proc/uptime` is unreadable | the `system` section leaves uptime blank on Android rather than failing |
| Termux may already be running its own sshd | the bootstrap records whether it started sshd, and teardown stops it only if csync did. Otherwise csync would kill a service the owner started |
| A remote path is shell-quoted, so `~` never expands | remote defaults are home-relative (`Downloads/csync/`), never `~/...`, which otherwise creates a directory literally named `~` |
| The phone has no `~/Desktop` | the receipt lands in the home directory instead |

### What a phone can and cannot tell you about itself

Measured on the same device, over csync with ADB disconnected. The limits are
Android's, not csync's, and they are worth knowing before promising a diagnosis.

| Question | Over csync, no root | Notes |
|---|---|---|
| How much memory is in use | yes | `/proc/meminfo` is world-readable, so totals, available, swap and cache all come back |
| Which processes are heavy | no | Android hides other processes from an unprivileged app, so a process listing shows only csync's own |
| Load average, page faults, memory pressure | no on this device | MIUI denies `/proc/loadavg`, `/proc/vmstat` and `/proc/pressure` as well |
| Storage, network, battery, telephony, sensors | yes | through `df` and Termux:API |
| csync's own footprint | yes | about 18 MB resident: the tunnel's ssh, sshd, and the keeper shell |

The ADB mode closes exactly this gap: `top` and `dumpsys meminfo` over ADB
return the full per-process table with no root. That is the second reason to
build it, alongside screen capture.

### The phone as a build machine

`examples/jot` is a tasks app with a home-screen widget that was written on the
console, pushed over csync, and compiled on the phone with `aapt`, `ecj`, `d8`
and `apksigner` from Termux. No Gradle and no Android SDK on the Mac. Three
edit, rebuild and reinstall cycles ran entirely through csync, each build taking
seconds, producing a signed 17 KB APK.

Installing an APK is the one step Termux cannot do, so it needs ADB or a tap on
the phone's package installer. Everything up to that point, and everything
after, runs over the tunnel.

## The development channel to a phone

`tools/adb-dev.sh` is scaffolding, not a csync feature. It pushes a dev key to a
phone over ADB, forwards the phone's 8022 to this Mac, and then everything is
ordinary ssh, so csync's Android path can be built and tested without a person
holding the phone. The phone side is three lines pasted into Termux once, and
`adb-dev.sh phone-lines` prints them. The proper long-running ADB mode, the one
that would give a real screen capture and the full system log, is separate and
later.

## csync mesh: your own devices

Everything above is about driving a laptop you do not own and leaving no trace.
The mesh is the opposite case: your own always-on devices, which trust each
other and stay set up. Where a target never listens, a mesh peer always does.
Where the console reaches through a tunnel the target opened, any peer sends
straight to any other. It shares the tailnet, the token idea, and the
`~/csync/inbox` convention, and it is a separate component, not a mode of the
borrow-a-laptop flow.

```
                 Tailscale tailnet  (identity · encrypted P2P · the boundary)
  ┌───────────┬───────────────┬────────────────┬───────────────┬────────────────┐
  │   Mac      │  Raspberry Pi  │  Android (hub) │ iPhone (later) │ remote server   │
  │ csync-agent│  csync-agent   │  app + service  │  share-ext     │  csync-agent    │
  │  listen ▲  │  listen ▲      │  listen ▲       │  (send only)   │  listen ▲       │
  │  send  ─┼─►│  send  ─┼─────►│  send  ─┼──────►│  send  ─┼─────►│  send  ─┼─────► │
  └─────────┼──┴─────────┼──────┴─────────┼───────┴────────┴──────┴─────────┼───────┘
        every device speaks ONE contract:   /whoami  ·  /send  ·  /peers
              peer scan  =  `tailscale status`  ∩  /whoami probe
```

The agent is `agent/`, a single Go binary with no dependencies, so one build
drops onto a Mac, a Pi, a Linux box, or a remote server and runs. It listens on
this device's tailnet IP, never on the LAN or the internet, and every request
carries a shared token, so there are two gates: the tailnet, then the token.

| Endpoint | What it does |
|---|---|
| `GET /whoami` | this device's name, platform, version, and what it accepts; also the liveness probe |
| `POST /send` | receive text, a file, or an image into `~/csync/inbox/<from>/`; text also lands on the clipboard, and every arrival raises a notification |
| `GET /peers` | this agent's tailnet view, so a device without the `tailscale` CLI (a phone) can still discover its neighbours |

Identity and reachability come from Tailscale, so nothing is reinvented: a peer
scan is the tailnet's own device list intersected with which of them answer
`/whoami`. Discovery is not a hardcoded address list.

The wire is plain HTTP, not HTTPS, on purpose. The tailnet is already encrypted
end to end by WireGuard, so a second TLS layer would add self-signed-certificate
pain on Android for no real gain. The token, not the transport, is what proves
a sender is one of your devices.

| Command | What it does |
|---|---|
| `csync-agent serve` | start the receiver (binds to this device's tailnet IP) |
| `csync-agent peers` | list tailnet peers and which run an agent |
| `csync-agent send <peer> --text "..."` | send text; lands on the peer's clipboard on macOS |
| `csync-agent send <peer> <file>...` | send files or images |
| `csync-agent token` | print the shared token, minting one on first run |

Install it with `agent/install-macos.sh` (a LaunchAgent that keeps it running)
or `agent/install-linux.sh <binary>` (a per-user systemd service). The same
token file, `~/.config/csync/mesh.token`, must be copied to every device you
trust.

The phone side is the `csync-hub` Android app, which folds the earlier test apps
into one: an xkcd page and its home-screen widget, a Shizuku system monitor, and
a Devices page that scans peers, sends, and runs the receiver. The app also
registers in the system share sheet, so "Share → csync" pushes text, an image,
or a file straight to a chosen device over the tailnet.

## Not in v1

Own-machine persistent `tailnet` route. Windows targets. The csync ADB mode for
screen capture and full logs. Remote GUI control
(macOS Screen Sharing already works over a tailnet with `open vnc://` when the
target is one of the owner's machines). sshfs mounts. Clipboard sync. A web or
phone client. Enrollment that keeps private keys off the wire (v1.1, in the
plan appendix).

## Unknowns to settle before building

Each is one experiment on the owner's second laptop, before any real code.

| Spike | Question | Settles it | Result, 2026-09-05 |
|---|---|---|---|
| S1 | Does `screencapture` over SSH on macOS 26 return the real screen, and if not, does granting Screen Recording to `sshd-keygen-wrapper` fix it | run it, open the PNG, then grant, then run again | open. Through a test sshd started from a terminal it fails with "could not create image from display", which says nothing about the real launchd sshd |
| S2 | Which shell command turns on Remote Login on macOS 26 without a Full Disk Access prompt, and is `sshd_config.d` honoured | `systemsetup -setremotelogin on` vs `launchctl bootstrap`, then `sshd -T` | open; needs sudo on a real target. The include line is present in this Mac's `sshd_config` |
| S3 | Does `openssl s_client -quiet` work as a ProxyCommand through Funnel from a non-tailnet network | publish, then ssh from a phone hotspot | see the loopback record below |
| S4 | Does an unprivileged sshd run on the console without a firewall dialog | start it, connect, watch for the prompt | confirmed: `/usr/sbin/sshd -f` as the user daemonises, listens, no dialog |
| S5 | Do `permitlisten` and the forced-command hello behave | a permitted port binds, a second port is refused, a command is replaced | confirmed on this Mac; the sleep and reconnect half stays open |
| S6 | Does a root LaunchDaemon fire the TTL teardown and restore Remote Login | ttl 3m, wait, check state | open; needs sudo on a real target |
| S7 | Linux: systemd user unit for the tunnel, a root timer for TTL, a screenshot under Wayland | one Ubuntu VM | open |
| S8 | Funnel throughput for a 200 MB pull versus the LAN route | time both | open |

Also settled by the loopback run: macOS ships openrsync, which rejects GNU
rsync's `--info` flags, so csync only adds progress flags when it sees rsync 3;
a macOS target's login shell is zsh, whose failed globs abort a command, so
remote commands that glob run under `bash -c`.

## Decisions the owner still holds

| Id | Question | Default if silent |
|---|---|---|
| G1 | Do any friends' machines the owner expects to help soon run Windows | no; Windows is v2 |
| G2 | Publish the hardened relay port from this Mac to the internet through Tailscale Funnel at `aakarshs-macbook-pro.tail905820.ts.net:10000` | yes; the alternative is a small VPS relay |
| G3 | Public repo `github.com/alcatraz627/csync` with the raw-URL bootstrap pinned by commit | yes; a private repo cannot serve the paste line without a token |

Defaults applied without asking: Python 3 standard library for the console;
bash 3.2 for the bootstrap; remote operations streamed as shell, never stored
on the target; ports 5122 (relay), 10000 (Funnel), 5200 to 5299 (per-target
loopback); invite expiry 1 h; session TTL 4 h; the target's sshd confined to
loopback in every route.
