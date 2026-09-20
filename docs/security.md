# Security model

What protects a csync session, stated plainly, and what each protection assumes.
The normative detail is in [spec.md](spec.md); this is the reasoning behind it.

## The trust boundary

A session rests on two things: the network it runs over, and the mesh token or
invite key. On the drive-a-laptop path, the target reaches the console over a LAN
hop or a Tailscale Funnel, and authenticates with a per-invite key. On the mesh
and assistant paths, the boundary is the tailnet plus the shared mesh token.
Nothing here trusts the public internet on its own.

## What the target exposes: nothing inbound

The target turns its sshd on but binds it to loopback only, keys only, one user.
It never listens on any network interface. The console never connects toward the
target. Instead the target dials out and opens a reverse tunnel, and the console
walks through that tunnel. So there is no port on the target for anyone to find or
attack.

## The invite key

Each invite mints its own ed25519 key. Its public half goes into the relay's
`authorized_keys` on one line, pinned to a forced command
(`csync relay-hello <id>`), a single permitted listen port, and nothing else. Its
private half travels once, inside the token the target pastes. The key expires
(one hour by default) and after that the relay refuses it. It can bind one
loopback port and can never open a shell.

## The forced command

The relay never gives an invite key a session it chose. Every connection runs the
one forced command, so a leaked key can do exactly one thing: send a hello. It
cannot run commands, forward arbitrary ports, or read files.

## Admin rights end with the bootstrap

The bootstrap asks for the password once, to turn on the SSH service and arm the
cleanup. After that the console holds no privilege on the target. The only
privileged path is a root TTL timer, and it can run only the exact teardown script
whose hash was recorded, nothing else.

## The backstop

Even if the console disappears, a root timer on the target tears the session down
at the deadline, restores the SSH service to its prior state, and removes itself.
The friend can also run `~/.csync/teardown.sh` at any moment, with no network.

## Integrity of what the target runs

The bootstrap and the target scripts are fetched against a sha256 that the token
carries, from a commit-pinned URL. A tampered or swapped script fails the hash
check and the bootstrap stops. `csync invite --show-script` prints exactly what
the URL will serve.

## The audit trail

Every console command appends one line to the journal with the actor marked human
or agent. The target's forced command logs every verb the console ran, in the
target's own words, and teardown leaves a receipt on the target listing every
change and proving the rest was removed.

## What an agent actor may do

An agent driving the console gets the reading verbs by default. Each writing verb
needs `--allow-write` on that call, which the journal records, and `--force` is
never available without a real terminal. This keeps an automated driver from doing
more than it was asked without a trace.

## What this model does not defend against

- A compromised console. It holds the long-lived key under FileVault; if the
  console itself is owned, `csync revoke --all` closes every open door, but a
  live attacker on the console is outside the model.
- A target whose owner is coerced into pasting a malicious line. csync proves what
  a real invite does; it cannot judge intent.
- The endpoints themselves. csync secures the path and the session, not the
  security posture of either machine.

## Reporting

If you find a weakness in the session model, the key handling, or the teardown
guarantee, raise it privately with the repository owner rather than in a public
issue.
