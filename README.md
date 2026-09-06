# csync

Drive another laptop from this one after a single pasted line there, and leave it
exactly as you found it when you are done.

```
csync init                      # once, on this Mac
csync invite rahul-mbp          # prints one line; send it
csync wait rahul-mbp            # returns when their laptop connects
csync shot rahul-mbp            # screenshot
csync pull rahul-mbp ~/Library/Logs/DiagnosticReports
csync recipe rahul-mbp install-steam
csync teardown rahul-mbp --verify
```

The other laptop installs nothing. It turns on its own sshd for one user, keys
only, and opens a reverse SSH tunnel back to a small hardened relay on this Mac,
over the LAN when it can and through Tailscale Funnel otherwise. Every command
you run there is logged on their side, a handful of destructive ones are refused,
and teardown restores their machine and proves it.

Definition: `docs/spec.md`. Build plan and parity ledger:
`.claude/output/latest-change-plan.txt` points at it.

Requires on this Mac: macOS 15+, Python 3.12+, Tailscale (for the Funnel route).

Targets: macOS 13+, a systemd Linux including a Raspberry Pi, or an Android phone
running Termux. Android needs Termux installed once from F-Droid and then takes
the same paste line, with no root and no sudo at any point. What a phone gives
you is every verb except a real screen capture, which Android does not allow
without root, so `csync shot` returns a camera frame and says so.

Always-on behaviour on a phone, the wake-lock and the boot script, is granted
and withdrawn with `csync persist <name> on|off` and is removed by teardown
either way.

Tests: `python3 -m unittest discover -s tests` for the token and JSON surface,
`bash tests/loopback.sh` for the end-to-end run on one machine.
