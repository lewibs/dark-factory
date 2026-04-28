---
name: kill-gnome-terminal-via-vte-cgroup
description: "How to cleanly close a GNOME terminal tab or window from a bash script by stopping its vte-spawn cgroup scope via systemctl --user, with a fallback to plain kill for non-GNOME environments."
user-invocable: false
---
## When to use

Any time a bash script needs to programmatically close a GNOME terminal window or tab — either the calling terminal (self-close) or another terminal identified by PID. This pattern appears in:
- Scripts that reopen a session in a fresh terminal and must close the installer/caller terminal afterward.
- Scripts that destroy all factory terminals before spawning a new one.

## Steps

### Closing another terminal (by PID)

1. Read the vte-spawn scope name from the target process's cgroup file:
   ```bash
   SCOPE=$(grep -oP 'vte-spawn-[^/]+\.scope' /proc/"$pid"/cgroup 2>/dev/null | head -1)
   ```
2. If a scope was found, stop it via systemctl:
   ```bash
   if [ -n "$SCOPE" ]; then
       systemctl --user stop "$SCOPE" 2>/dev/null || {
           echo "Warning: could not stop scope $SCOPE for PID $pid" >&2
       }
   else
       # Fallback for non-GNOME environments (xterm, konsole, etc.)
       kill "$pid" 2>/dev/null || echo "Warning: could not kill PID $pid" >&2
   fi
   ```

### Self-closing (closing the current terminal)

1. Read the current process's own scope:
   ```bash
   SELF_SCOPE=$(grep -oP 'vte-spawn-[^/]+\.scope' /proc/"$$"/cgroup 2>/dev/null | head -1)
   if [ -n "$SELF_SCOPE" ]; then
       systemctl --user stop "$SELF_SCOPE" 2>/dev/null || true
   fi
   ```
2. After stopping the scope, also kill the ancestor `claude` process so the session fully terminates (the scope stop closes the terminal but the claude process may linger):
   ```bash
   pid=$$
   while [ "$pid" -gt 1 ]; do
       ppid=$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d ' ')
       name=$(ps -o comm= -p "$pid" 2>/dev/null | tr -d ' ')
       if [ "$name" = "claude" ]; then
           kill "$pid" 2>/dev/null || true
           break
       fi
       ([ -z "$ppid" ] || [ "$ppid" -le 1 ]) && break
       pid=$ppid
   done
   ```

## Notes

- The `vte-spawn-*.scope` cgroup entry only exists on GNOME/VTE-based terminals (gnome-terminal). Other emulators (xterm, konsole, x-terminal-emulator) will not have this entry, so the plain `kill` fallback is required for portability.
- `systemctl --user stop <scope>` sends SIGTERM to all processes in the cgroup and waits for them to exit — cleaner than a raw `kill` on the terminal PID, which may leave child processes orphaned.
- Stopping the cgroup scope closes the terminal window but does not necessarily terminate the `claude` process that was running inside it. Always follow up with the process-tree walk to kill the `claude` ancestor when a full session teardown is needed.
- The grep pattern `vte-spawn-[^/]+\.scope` is anchored to extract only the scope name segment regardless of the full cgroup path format, which varies between kernel versions.
- Both `destroy-factories.sh` and `reopen-remote-control.sh` use this exact pattern — treat those files as authoritative references.
