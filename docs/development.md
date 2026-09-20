# Development: dos and do-nots

Guardrails for anyone, human or agent, extending csync, so future changes stay
aligned with what the project already is. These are about direction, not style.

## Do

- **Keep the target passive.** The target dials out and listens on nothing. Any
  new feature reaches the target through the tunnel it already opened. If a change
  wants the console to connect inward to the target, it is wrong.
- **Make every change reversible on the target.** Anything a session writes on a
  target is recorded in the change ledger and undone by teardown. A new step that
  touches the target adds its snapshot and its reversal in the same change.
- **Pin what the target runs to a hash.** The bootstrap and the target scripts are
  fetched against a sha256 the token carries. A new target-side script carries its
  own hash the same way.
- **Give every verb a `--json` form and honest exit codes.** An agent must be able
  to drive it. Errors carry a `fix:` with the exact next command.
- **Default an agent actor to the reading verbs.** A writing verb needs
  `--allow-write` on that call, and `--force` needs a real terminal. New verbs
  declare which side of that line they are on.
- **Log the change, not just the result.** Push and pull list what moved, teardown
  lists what was removed and what remains, and the journal gets one line per call.
- **Reproduce before you patch.** The console can talk to its own relay with its
  own copy of an invite key. Prove the fault before changing code.

## Do not

- **Do not add a default host.** The host name is always typed. There is no
  "current" target, because acting on the wrong machine is the worst failure.
- **Do not let the console hold admin on the target past the bootstrap.** The only
  privileged path is the root TTL backstop, and it can run only the one recorded
  teardown script.
- **Do not weaken a gate to make a test or a demo pass.** If a verb refuses,
  understand the refusal. A test-only exception to a safety rule is not allowed.
- **Do not run recipes or scripts from a dirty working tree in a real session.**
  Recipes run from the pinned commit. `--dev` exists for local work and says so.
- **Do not branch behaviour on the text of an error.** Carry a code or an exit
  status. Messages are for humans.
- **Do not commit secrets.** Tokens, keys, and `~/.config/csync` never enter the
  repo. The repo is public.

## Planned directions, so they land coherently

- **A first-class tailnet route.** When both machines are on the same tailnet, the
  target should reach the relay directly on the console's tailnet address, without
  the Funnel or the `openssl s_client` proxy. This is cleaner and faster than
  Funnel for the common case and removes a fragile dependency. It fits as a third
  route beside `lan` and `funnel`, choosing the console's tailnet address for the
  reverse dial.
- **A persistent, no-TTL session for a trusted own machine**, so a laptop you own
  does not re-paste each time. It stays opt-in and still fully reversible.
- **A run-in-GUI-session helper for macOS targets.** A plain `run` lands in a
  detached ssh session, which cannot receive GUI or HID events. A wrapper that
  runs a helper inside the logged-in Aqua session (via `launchctl asuser`) is
  needed for anything that reads controllers, the screen, or input.
- **Smart-home control as a peer capability.** Reaching your bulbs and switches is
  the same class of problem as reaching your laptops: bring the far device close.
  It belongs behind the same tailnet trust boundary, driven through the mesh, not
  as a bolt-on.
