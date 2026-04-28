---
name: separate-open-only-from-reopen-scripts
description: "When a script both opens a new terminal and self-destructs the caller, never reuse it for open-only cases — create a dedicated open-only script instead."
user-invocable: false
---
## When to use

Any time you need to open a new terminal window (e.g. launching a remote-control session) without closing the calling terminal. This situation arises when adding a new command that spawns a factory but must leave existing factories and the calling session untouched.

## Steps

1. Identify whether the existing script you are about to call contains self-destruction logic — specifically: cgroup scope-stop (`systemctl --user stop "$SCOPE"`), or killing a claude ancestor process via process-tree walk.
2. If the existing script contains either of those patterns, do NOT reuse it for an open-only case. Reusing it will silently close the calling session and any factory windows in the same terminal scope.
3. Create a separate script (e.g. `scripts/build-factory.sh`) that contains only the `open_terminal` function and the launch + exit-code check. Do not include any cgroup, scope-stop, or process-kill logic.
4. Point the new command's `.md` file at the new open-only script.
5. Leave `reopen-remote-control.sh` (or equivalent) unchanged — it is intentionally destructive and is correct for its own use case (reopening a session after install, where the installer terminal must close).

## Notes

- `scripts/reopen-remote-control.sh` is purpose-built to close the calling session after reopening. Its teardown logic is not a bug — it is the intended behavior for the reopen case.
- The `open_terminal` function itself (gnome-terminal / x-terminal-emulator / xterm / konsole fallback chain) is safe to copy verbatim into a new open-only script.
- The bug is always the same: a command spec (`.md` file) delegates to `reopen-remote-control.sh` thinking it only opens a terminal, not realizing the script also kills the session that called it.
