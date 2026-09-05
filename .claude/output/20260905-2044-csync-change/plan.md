# csync build plan

<!-- sessions: csync-plan-7c@2026-09-05 -->

This is the build plan for csync, the tool defined in
`/Users/alcatraz627/Code/Claude/csync/docs/spec.md`. The spec says what csync
is; this file says what must be true before anyone writes code, what must still
be true afterwards, and in what order the pieces land. Read the spec first.

## Why there is work to do

Class: **Capability**. Nothing in this account does this today.

| Evidence | Reading |
|---|---|
| `which csync` | `csync not found` |
| `/Users/alcatraz627/Code/Claude/csync` | empty directory, not a git repo |
| owner, verbatim | "click around 16 times to fetch / download / configure / execute, or worst find and copy and transfer logs or hardware features" |
| owner, verbatim | "the friction of doing various things manually is annoying" |

The cost is a manual routine repeated every time a friend needs help or the
second laptop needs something. No constraint is violated; this is a missing
capability with a repeated cost, which is enough.

## Problems, each with the check that flips

| # | Observation | Cost | Check |
|---|---|---|---|
| P1 | No way to reach another laptop without sitting at it and configuring sharing by hand | every session starts with clicking through System Settings on the other machine | `csync invite x` produces a line; pasting it on a fresh macOS user account brings `csync wait x` to a host row with no clicks on either side |
| P2 | Files, logs, and hardware details move by AirDrop, chat, or a USB stick | minutes per item, and logs are found by memory | `csync pull`, `csync logs`, `csync info` each land the artifact under `~/csync/<name>/` with the path printed |
| P3 | A remote screenshot on macOS may come back black under TCC | the one thing that shows what the friend sees is the one that silently fails | spike S1 result recorded in the spec; `csync shot` either returns a real screen or exits 5 with `fix:` naming the toggle |
| P4 | Any tunnel left behind is an open door on a machine the owner does not control | the owner's own words: "not leaving an exploitable path" | `csync teardown x --verify` exits 0 with an empty residue table, and the target's `~/.ssh/authorized_keys`, `sshd_config.d`, Remote Login state, and launch units match the pre-bootstrap snapshot byte for byte |
| P5 | Tailscale onboarding on a target needs OS approval clicks | fails the owner's zero-click bar (mid-turn ruling, 2026-09-05) | the bootstrap never invokes Tailscale; `rg tailscale bootstrap.sh` returns nothing |
| P6 | An agent driving the tool needs structured output and no prompts | the owner: "I foresee an agent being able to drive this as well" | every verb passes `--json` and, with stdout not a TTY, never blocks on input; a test runs each verb with stdin closed |

Watch, not chase: the console's Tailscale is currently stopped
(`tailscale status` → `Tailscale is stopped`). `csync doctor --fix` starts it;
if it turns out to be logged out, that is a one-time browser login and not a
csync defect.

## How this account already solves each shape

Swept `/Users/alcatraz627/Code` and `~/.claude` for the shapes this tool
touches. Rows marked new precedent have no prior answer in the tree.

| Decision | Existing answer | Evidence | Adopting or deviating |
|---|---|---|---|
| Reaching a machine off-LAN | Tailscale MagicDNS, tailnet `tail905820` | `~/Code/Personal/home-server/docs/remote-access.md:10-25` | adopting on the console only; deviating on the target for the zero-click reason in P5 |
| Trust model for tailnet peers | "Tailscale IS the auth layer"; a shared node has "full access to everything" | `~/Code/Personal/home-server/docs/security.md:32,39` | this is exactly why friends' machines never join the tailnet |
| Taking a macOS screenshot from a script | `screencapture -x -D "$n" "$out"` and a TCC probe that treats a tiny PNG as denied | `~/.claude/scripts/desktop.sh:74,301-312` | adopting both the flag set and the size-based denial check |
| Terminal picker | `tui_pick_one`, fzf → gum → read | `~/.claude/scripts/tui/pick.sh` | adopting for the no-argument picker |
| CLI help, pipe mode, `--json` | help structure, `[ -t 1 ]` detection, `NO_COLOR` | `~/.claude/conventions/cli-help-design.md` §Principles, §Pipe-friendly mode | adopting |
| Agent-driven tool obligations | deltas, budgets, fixes in errors, built-in waits, journal | `~/.claude/conventions/agent-first-tools.md` §The five obligations | adopting; the spec's Machine surface table is that table applied |
| Shell dialect for scripts | `#!/bin/bash` runs bash 3.2 on macOS, no associative arrays | `~/.claude/rules/shell.md` §Sentinel values | adopting for `bootstrap.sh` and `teardown.sh` |
| Deleting files | `trash`, never `rm` | `~/.claude/rules/shell.md` §Safe delete | console side adopts `trash`; the target's teardown uses `rm` on files it created, because `trash` does not exist there and the paths are its own |
| Tailscale CLI allowed for agents | `Bash(tailscale:*)` already in the allowlist | `~/Code/Claude/its-my-config/claude/settings.json:41-42` | adopting; `csync doctor` shells out to it |
| Reverse SSH tunnel into a dedicated relay sshd | no implementation; the owner's own notes cover the primitives | `~/Code/Personal/helper-docs/ssh/ssh.md:192` (`ssh -R`), `:327` (`-N` persistent tunnel); no `permitlisten` or `ForceCommand` use anywhere under `~/Code` | new precedent for the relay; the tunnel flags follow the notes |
| Invite token format | none | | new precedent, defined in the spec |
| Target state snapshot and change ledger | none | | new precedent, defined in the spec |

## What must still hold

Greenfield in the repo, so the parity ledger is about the machines, not the
code. Every row is something the tool must leave untouched or restore, with a
check that fails if it is lost. Rows are surfaces, not behaviours.

| Must still hold | Why | Check that catches its loss |
|---|---|---|
| Target `~/.ssh/authorized_keys` identical to the pre-bootstrap copy after teardown | a leftover key is the exploitable path | `diff` against the copy the bootstrap took in step 3 |
| Target Remote Login state identical to the snapshot | a friend's sshd left on is a door they did not have | `systemsetup -getremotelogin` equals the snapshot value |
| Target `com.apple.access_ssh` membership identical to the snapshot | same | `dseditgroup -o checkmember` per prior member, and no extras |
| No `/etc/ssh/sshd_config.d/csync.conf` on the target after teardown | a loopback-only drop-in left behind would break the friend's own later use of ssh | `test ! -e` |
| No `sh.csync.*` launch units on the target after teardown | a reconnect loop with no relay to reach is noise, and a TTL daemon that fires later is a surprise | `launchctl print system/sh.csync.ttl` and `gui/<uid>/sh.csync.tunnel` both fail |
| Target `~/.csync/` absent after teardown | the state file holds the change ledger, which is the friend's business only while the session lasts | `test ! -d` |
| The receipt is the only csync artifact left on the target, and only when not opted out | the friend gets a record; anything else left is residue | `find ~ -iname '*csync*'` lists exactly `~/Desktop/csync-receipt-*.txt`, or nothing with `--no-receipt` |
| No sudo path for the console's key on the target at any point | the blast radius is the friend's own account | `ssh csync-<name> sudo -n true` fails; `sudoers` unchanged from the snapshot |
| Console `/etc/ssh/sshd_config`, `~/.ssh/config`, `~/.ssh/authorized_keys` unchanged by any csync command | csync runs its own sshd and its own `ssh -F`; touching the owner's defaults is scope creep with security weight | sha256 of the three files before and after the full test suite |
| Tailnet policy file unchanged by csync | an ACL edit by a tool can lock the owner out of their own tailnet | `doctor` prints, never `PUT`s; a test asserts no `api.tailscale.com` call carries a body |
| Console Tailscale login state unchanged | csync may start the app and run `tailscale up`; it never logs out or switches accounts | `tailscale status --json` `.Self.UserID` equal before and after |
| Pulled files under `~/csync/<name>/` survive teardown | they are the owner's, and the reason the session happened | `ls` after `teardown --verify` |

## Directives, each with a check

Rows marked (parity) come from the ledger above.

| ID | Directive | Check |
|---|---|---|
| D1 | Settle spikes S1 to S8 on the second laptop before writing the CLI, and record each result in the spec's Unknowns table | the table has a result column with no empty cells |
| D2 | `bootstrap.sh` runs under `bash --posix` 3.2 with no python, brew, jq, or curl beyond the initial fetch | `shellcheck -s bash` clean; a run inside `bash-3.2` on the second laptop completes |
| D3 | The bootstrap snapshots before it changes, and writes `state.json` before each mutating step | kill the bootstrap after step 7; `teardown.sh` still restores the snapshot (parity) |
| D4 | The target's sshd is keys only and one user in every route, and loopback-only where the OS lets sshd own the socket | `sshd -T` on the target shows `passwordauthentication no`, `allowusers <user>`; on Linux also `listenaddress 127.0.0.1:22`; on macOS the launchd socket stays on all interfaces and the key's `from=` carries the loopback restriction |
| D5 | The relay sshd on the console runs unprivileged from its own config with `PermitTTY no`, `UsePAM no`, `AllowTcpForwarding remote`, and a forced command | `sshd -T -f <relay config>` shows each; `ssh -i <invite_key> -p 5122 localhost bash` is refused |
| D6 | Each invite's relay line carries `permitlisten` for exactly its port | a second connection with the same key fails to bind, logged as such |
| D7 | The hello carries user, os, sshd host key, and deadline; the console pins the host key before its first `ssh` | `known_hosts` gains one line before `csync wait` returns; no `accept-new` in `ssh_config` |
| D8 | Route `auto` probes LAN for 2 s then falls back to Funnel | on the same Wi-Fi `hosts.json` records `route: lan`; on a hotspot it records `funnel` |
| D9 | Every verb accepts `--json` and never prompts when stdout is not a TTY | a test loop runs each verb with `</dev/null` and `--json`, asserting valid JSON and no hang |
| D10 | Every non-zero exit carries a `fix:` line and one of the exit codes in the spec | the same loop asserts the field on forced failures |
| D11 | `info`, `logs`, and `run` obey output budgets, writing full payloads to files | `csync logs x --since 24h` prints under 40 lines and names a `.tar.gz` |
| D12 | `shot` treats a PNG under 5 KB as denied and exits 5 with the TCC toggle in `fix:` | cover the screen-recording case from S1 |
| D13 | `teardown --verify` restores every parity row and prints residue | run the parity checks as its implementation; a deliberately left drop-in makes it exit 8 (parity) |
| D14 | The TTL backstop tears down without the console | set `--ttl 3m`, kill the relay, wait, run the parity checks from a LAN shell (parity) |
| D15 | csync never edits the console's sshd config, `~/.ssh/config`, `~/.ssh/authorized_keys`, or the tailnet policy | sha256 before and after the suite; a network mock asserts no policy `PUT` (parity) |
| D16 | Recipes carry the three-line header and `--dry-run` prints them without connecting | `csync recipes` lists each; `--dry-run` works with the relay stopped |
| D17 | The no-argument form uses `tui_pick_one` and degrades to a numbered prompt | run with `PATH` lacking fzf and gum |
| D18 | The audit journal gets one line per command, including failures, with the actor | count lines before and after the suite equals the number of commands run; each line has `actor` |
| D19 | The target's key line carries `command="$HOME/.csync/gate.sh"`, and the gate logs every session before running it | `ssh csync-x true` appends one line to `session.log`; `rsync`, `sftp`, and `csync sh` each append one too |
| D20 | The gate refuses the deny-list and `--force` needs a TTY | `csync run x -- rm -rf ~` exits 5 with the refusal in `fix:`; `csync run x --force -- …` from `</dev/null` exits 2 |
| D21 | Every verb prints the host row first and the delta or `fix:` line last | a test captures each verb's first and last lines |
| D22 | An agent actor gets reading verbs only; writing verbs need `--allow-write` | with `CLAUDECODE=1`, `csync push x f` exits 2 naming the flag; with the flag it runs and the journal shows `actor: agent` |
| D23 | `push` refuses to overwrite without `--overwrite` and never passes `--delete` | push the same file twice; the second exits 2; `rg -- --delete csync/ops.py` is empty |
| D24 | Teardown copies the session log home, writes the receipt, and the residue check ignores exactly that file | after teardown, `~/csync/x/session/` exists and `find ~ -iname '*csync*'` on the target lists only the receipt (parity) |
| D25 | Tunnel up, down, and TTL warnings raise a console notification; `csync status` renders in one screen | kill the tunnel and watch Notification Center; `csync status` is under 44 lines with 5 hosts |
| D26 | csync never gains sudo on the target after the bootstrap | `ssh csync-x sudo -n true` fails; `rg sudo ops/ recipes/` shows only lines that print a command for the friend (parity) |

## The contract

Repository layout:

```
csync/
├── bootstrap.sh              # target side, bash 3.2, self-contained
├── bin/
│   ├── csync                 # console CLI, python3, stdlib only
│   └── csync-tui             # bash, sources ~/.claude/scripts/tui, execs csync
├── csync/                    # python package
│   ├── cli.py                # argparse, --json, exit codes, fix: lines
│   ├── state.py              # config.json, hosts.json, audit.jsonl
│   ├── keys.py               # console key, relay host keys, invite keys
│   ├── relay.py              # relay sshd config, LaunchAgent, hello handler
│   ├── funnel.py             # tailscale status / up / funnel wrappers
│   ├── invite.py             # token build and parse
│   ├── tunnel.py             # ssh_config blocks, known_hosts, wait
│   ├── ops.py                # run, push, pull, shot, info, logs, open, say
│   ├── recipes.py            # header parse, list, stream
│   ├── teardown.py           # both sides, residue table
│   └── doctor.py             # checks with fixing commands
├── ops/                      # shell streamed to targets, never stored there
│   ├── info.sh  logs.sh  shot.sh  open.sh  say.sh
├── target/                   # installed by bootstrap.sh from the same pinned
│   ├── gate.sh  teardown.sh  #   commit, sha256 of each embedded in bootstrap.sh
├── recipes/
│   ├── install-homebrew.sh  install-steam.sh  … (each with the header)
├── tests/
│   ├── test_token.py  test_cli_json.py  test_parity.sh  …
└── docs/spec.md
```

Shapes:

| Shape | Fields |
|---|---|
| token | `v id name route exp ttl lan funnel relay_hostkey port console_pub invite_key`, `key=value` lines, base64url |
| hello | `v id user host os osver arch sshd_hostkey deadline`, one line in `SSH_ORIGINAL_COMMAND` |
| hosts.json entry | `name id user os osver arch route port deadline last_hello hostkey created` |
| state.env (target, `key='value'` lines) | `id name h cs os osver user_name uid route route_used port target_port console_name created deadline no_root ak_existed tunnel_pid supervisor`; the root half keeps `rl_before dropin_existed` (Linux: `ssh_enabled_before ssh_active_before`) in its own state.env under a root-owned directory; `changes.log` holds the human-readable ledger |
| audit line | `ts host verb args exit ms` |
| relay authorized_keys line | `restrict,port-forwarding,permitlisten="127.0.0.1:<port>",command="<bin>/csync-relay-hello <id>" ssh-ed25519 <pub> csync-invite:<id>` |
| target authorized_keys line | `restrict,pty,from="127.0.0.1,::1",command="$HOME/.csync/gate.sh" ssh-ed25519 <console_pub> # csync:<id>` |
| gate.sh contract | reads `SSH_ORIGINAL_COMMAND`; appends `ts cmd` to `session.log`; refuses the deny-list unless `CSYNC_FORCE=1` is the first token; empty command runs `script -q shell-<ts>.log $SHELL -l`; `sftp` runs the sftp server; anything else runs `$SHELL -c` |
| receipt | plain text: change ledger, every session.log line, files in and out, residue check result |
| ssh_config block | `Host csync-<name>` / `HostName 127.0.0.1` / `Port <port>` / `User <user>` / `IdentityFile ~/.config/csync/id_ed25519` / `UserKnownHostsFile ~/.config/csync/known_hosts` / `StrictHostKeyChecking yes` / `IdentitiesOnly yes` |

Module boundaries: `cli.py` is the only module that prints; every other module
returns dicts and raises `CsyncError(code, message, fix)`. `ops.py` never
builds ssh argv itself; it asks `tunnel.py` for the base argv for a host. The
target never receives python; `ops/*.sh` are streamed with `bash -s`.

Ladder: reuse `ssh`, `rsync`, `openssl`, `launchctl`, `systemd-run`,
`screencapture`, `system_profiler`, `log show`, `journalctl`; then the Python
standard library (`argparse`, `json`, `subprocess`, `base64`, `secrets`); no
third-party dependency on either side.

## First running slice

LAN route, the owner's second laptop, no Funnel yet.

```
csync init --no-funnel
csync invite mbp2 --route lan --ttl 2h          # prints the paste line
# paste on mbp2, Enter, sudo password
csync wait mbp2 --timeout 5m
csync run mbp2 -- uname -a
csync teardown mbp2 --verify
```

Proof: `wait` prints a host row with `route lan`; `run` prints a `Darwin`
line and `exit 0`; `teardown --verify` prints an empty residue table and exits
0; on mbp2, `diff ~/.ssh/authorized_keys <snapshot>` is empty and
`systemsetup -getremotelogin` matches the snapshot. That slice exercises the
token, the bootstrap, the relay sshd, the forced-command hello, the ssh_config,
one verb, and the whole teardown. Everything after it is more verbs and one
more route.

## Sequence

| Milestone | Lands | Gate to pass |
|---|---|---|
| M0 | spikes S1 to S8, results in the spec | D1 |
| M1 | first running slice on the LAN route, with `gate.sh` logging in the key line from day one | the proof above, plus D19 |
| M2 | Funnel route: `init` publishes, `--route auto`, `openssl` ProxyCommand | D8 from a hotspot |
| M3 | `run`, `push`, `pull`, `info`, `logs`, `--json` everywhere; host row first, delta last; audit journal with actor; `log` and `status`; agent read-only default; the gate's deny-list | D9, D10, D11, D18, D20, D21, D22, D23 |
| M4 | `shot`, `open`, `say`, the TCC path from S1 | D12 |
| M5 | `teardown --verify`, TTL backstop, `revoke --all`, receipt and session-log copy, notifications | D13, D14, D15, D24, D25, D26 |
| M6 | `recipes`, `doctor --fix`, `csync-tui`, audit | D16, D17, D18 |
| M7 | Linux targets in `bootstrap.sh` and `ops/*.sh` | the slice proof on the Ubuntu VM from S7 |
| M8 (v2) | `tailnet` route for owned machines; `bootstrap.ps1` for Windows; enrollment that keeps private keys off the wire | out of this plan |

## Must not touch

The console's `/etc/ssh/sshd_config`, `~/.ssh/config`, `~/.ssh/authorized_keys`,
`~/.ssh/known_hosts`. The tailnet policy file. The console's Tailscale login.
On the target, anything outside `~/.csync/`, the one `authorized_keys` line, the
one sshd drop-in, the two launch units, and the Remote Login state. A friend's
shell rc files, dotfiles, and Homebrew are never read or written.

## Model plan

```
Model plan:
  spikes  → main agent (fable) · hands-on with the second laptop · no sub-agents
  build   → main agent (fable) · owner ruling 2026-09-01: fable does involved work itself
  review  → /skeptical-review fork, opus · medium · after M1 and after M5
  vision  → lm see on S1 screenshots · $0 second reader beside native read
```

## Appendix: considered and parked

| Idea | Why parked | Where it would return |
|---|---|---|
| Tailscale on the target | GUI variants need OS approval clicks; the App Store build cannot be an SSH server; `tailscaled` needs Homebrew | M8, owned machines only |
| Tailscale SSH instead of sshd | Linux-only in practice; two code paths in v1 | M7 if Linux sshd install proves annoying |
| A VPS or GCP micro relay instead of Funnel | a machine to patch and pay for; Funnel is zero-configuration and already on the console | G2 alternative if Funnel's bandwidth cap bites in S8 |
| Cloudflare Tunnel | needs `cloudflared` on the target, which is an install | never, under the zero-install rule |
| Enrollment over the tunnel so the target generates its own key | better security, more code; v1 has TTL and single-bind | M8 as v1.1 |
| sshfs mount, clipboard sync, VNC | not in the owner's list | when asked |

## Decisions the owner holds

G1, G2, G3 as listed in the spec, with the defaults that apply if silent.
