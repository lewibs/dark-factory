---
name: hook-env-var-file-path-fallback
description: "Resolve a file path in a hook script using a three-tier fallback: env var → positional arg → hardcoded default, so the hook works in both Yama-invoked and manual test contexts."
user-invocable: false
---
## When to use

When writing a bash hook script that operates on a file whose path may be supplied by Yama via an environment variable, by a caller as a positional argument, or needs a sensible default when neither is present (e.g., during local testing or if the hook fires at an unexpected lifecycle point).

## Steps

1. Declare the file path variable with a three-tier fallback:

   ```bash
   TARGET_FILE="${MY_ENV_VAR:-${1:-/tmp/default-filename.md}}"
   ```

   - Tier 1: `MY_ENV_VAR` — set by the manufacturing pipeline or agent orchestrator.
   - Tier 2: `$1` — positional arg, useful for manual invocation or testing.
   - Tier 3: `/tmp/default-filename.md` — hardcoded fallback matching the convention used in `allowed-tools` (e.g., `cat > /tmp/pr-body.md *`).

2. After resolving the path, guard against the file not existing before doing any work:

   ```bash
   if [[ ! -f "$TARGET_FILE" ]]; then
       exit 0  # graceful no-op; hook fired before file was created
   fi
   ```

3. Document the env var name in a comment at the top of the hook script so future agents know how to inject it:

   ```bash
   # File path is resolved from: $MY_ENV_VAR, then $1, then /tmp/default-filename.md
   ```

## Notes

- The hardcoded `/tmp/` fallback must match the path used in the agent's `allowed-tools` frontmatter entry (e.g., `Bash(cat > /tmp/pr-body.md *)`). If the allowed-tools path changes, update the fallback too.
- The env var name should follow the `DARK_FACTORY_*` prefix convention used throughout this codebase (e.g., `DARK_FACTORY_PR_BODY_FILE`, `DARK_FACTORY_WORK_DIR`).
- Never `set -e` before the file-existence check if you want the hook to exit 0 gracefully on missing files — or use `[[ -f ... ]] || exit 0` before any command that would fail.
