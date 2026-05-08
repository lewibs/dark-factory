# Deprecated: destroy-factory Command Evolution (Previously destroy-factories)

## Metadata

- Date: `2026-04-28`
- Status: `resolved-by-redesign`
- Severity: `N/A (superseded)`
- Related issue/ticket: `N/A`
- Owner: `N/A`

## About

**Overview**:
This is a historical bug report documenting issues with an older implementation of the destroy-factories command. The command has been renamed to `destroy-factory` and completely redesigned to avoid the architectural issues described below.

**Context**:
- The old `destroy-factories.sh` attempted to kill all other Claude terminals running on the system by enumerating process trees.
- On GNOME desktops, `gnome-terminal` windows are all managed by a single shared daemon `gnome-terminal-server`, causing a PID collision issue where the script could not distinguish between different terminal windows.
- The new `destroy-factory` command takes a different approach: it only closes the current terminal/session, never attempting to kill other terminals.

**Previous Technical Issue**:
- When `destroy-factories.sh` ran, it called `find_claude_terminals()` which identified the calling terminal's own ancestor PID via `find_terminal_ancestor($$)`. 
- On GNOME, all gnome-terminal windows are children of the same `gnome-terminal-server` PID. 
- `find_terminal_ancestor($$)` returned the `gnome-terminal-server` PID as the "own ancestor."
- Then in the kill loop, every terminal emulator PID found by `all_terminal_emulator_pids()` matched `own_ancestor_pid` and was skipped.
- Result: zero terminals were killed.

**Resolution**:
- The command has been completely redesigned to eliminate this architectural issue.
- New `destroy-factory` command: closes only the current terminal/session by reading its own vte-spawn cgroup scope from `/proc/$$/cgroup` and stopping that scope.
- No terminal enumeration, no process tree walking for other terminals, no terminal killing — just self-close.
- This eliminates all issues with GNOME shared daemons and PID collisions.

## Resources

- Old implementation: `scripts/destroy-factories.sh` (removed)
- New implementation: `commands/destroy-factory.md`, `scripts/destroy-factory.sh`, `scripts/close-factory.sh`
- New tests: `tests/test_destroy_factory.py`, `tests/test_destroy_factory_kills_other_windows.py`

## Verification

- [x] Old implementation archived in this bug report
- [x] New implementation designed to avoid root cause (no terminal enumeration)
- [x] New tests verify self-close-only behavior
- [x] Command renamed from `destroy-factories` to `destroy-factory` to reflect behavior change
