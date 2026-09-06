#!/bin/bash
# csync-recipe: hello
# os: darwin,linux,android
# summary: prints who and where it ran; proves a recipe streams and executes
printf 'hello from %s@%s (%s), args: %s\n' "$(id -un)" "$(hostname -s 2>/dev/null || hostname)" "$(uname -s)" "$*"
