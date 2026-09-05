# Environment access in csync

Every read of an environment variable goes through `env(name, default)` in
`csync/envcfg.py`. The module lists each variable csync reads with a one-line
meaning, and `env()` refuses a name that is not on the list. New variables are
added to that list first, then read through `env()`.

Reason: the console CLI, the relay's forced command, and the tests all need
to agree on the same three roots (`CSYNC_HOME`, `CSYNC_STATE`, `CSYNC_DATA`),
and the forced command runs under sshd's minimal environment. One accessor
keeps the list visible and stops a stray read from landing in the wrong place.

The shell scripts on the target (`bootstrap.sh`, `target/*.sh`, `ops/*.sh`)
read only `HOME`, `SHELL`, `USER`, `SSH_ORIGINAL_COMMAND`, and the display
variables a Linux screenshot needs. They carry no csync-specific variables;
everything they need travels in the token or in `state.env`.
