# AGENTS.md

hypercaffeinated: a macOS installer (`install.sh`) that sets up a root LaunchDaemon, which keeps
the Mac awake with the lid closed whenever `~/NoSleep/state` says `on`.

## Layout
- `install.sh`: the whole product. It writes three things inline via heredocs:
  the daemon (`/usr/local/sbin/hypercaffeinatedd`), the user helper (`~/NoSleep/nosleep`) and the
  LaunchDaemon plist (`/Library/LaunchDaemons/local.hypercaffeinated.plist`).
- `README.md`: user-facing docs, including the safety warnings. Keep them in step with the code.

## Rules
- Target `/bin/bash` 3.2 (the macOS system bash): no `mapfile`, associative arrays, `${x,,}` etc.
- The daemon runs as root and reads a user-owned file. It must only ever compare that file's
  contents to `on`/`off`: never execute, source, `eval` or interpolate them into commands. Keep the
  symlink and ownership checks.
- Never run `install.sh` or `pmset` changes without the user's explicit go-ahead: they need sudo
  and change system power settings.
- Check: `bash -n install.sh`, plus `shellcheck install.sh` if available.
