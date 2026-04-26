---
name: handle-idempotent-setup-script
description: "When a bash setup script fails because its target already exists, derive the expected output path from input context and continue rather than stopping with an error."
user-invocable: false
---
## When to use

When invoking a setup or initialization bash script (e.g., `init.sh`) and it fails with an error indicating the target directory or resource already exists. The script was designed to be run once, but the agent is being run on an already-initialized project. The agent must not stop — it must recover by deriving what the script would have produced and proceeding to the next step.

## Steps

1. Run the setup script normally and capture its exit code and stdout/stderr.
2. If the script succeeds, extract the output path/value from stdout (e.g., a line like `PROJECT_PATH=<value>`).
3. If the script fails with an "already exists" error (keywords: "already exists", "directory exists", "already initialized", non-zero exit with that message):
   a. Log: "Directory already exists — skipping script, proceeding to next phase."
   b. Derive the expected output path from the input you were given:
      - If a `github_url` was provided: `REPO_NAME = basename(github_url, ".git")`, then `DERIVED_PATH = REPO_NAME/REPO_NAME`.
      - If no URL (CWD-based): `DIRNAME = basename(CWD)`, then `DERIVED_PATH = DIRNAME/DIRNAME`.
   c. Use `DERIVED_PATH` as if the script had returned it successfully.
4. If the script fails for any other reason (not "already exists"), surface the error and stop.
5. Continue to the next phase with the resolved path.

## Notes

- The "already exists" recovery is only safe when the script is purely a setup/directory-creation step and its sole output is a predictable path derivable from the inputs. Do not apply this pattern to scripts that write configuration or perform network operations — check idempotency assumptions first.
- The dark factory `init.sh` script creates a two-level directory structure (`<repo>/<repo>/`). The derivation rule above is specific to that script. Adapt the derivation logic if applying this pattern to a different script with different path conventions.
- Always log the skip explicitly so future debugging has a clear audit trail of why the script was bypassed.
