---
name: generate-wait-for-completion
description: Generates wait-for-completion.sh, a script that polls until the integration flow reaches a terminal state. Called by setup-wizard.
user-invocable: false
---

# generate-wait-for-completion

Generate `wait-for-completion.sh` — the script that blocks until the flow reaches a terminal state.

## Steps

1. Read `docs/plans/system-diagram.md` to understand the flow's terminal states and how to detect them.

2. Determine the terminal signal:
   - DB field (e.g. `processing_status = complete | failed`) → poll the DB
   - Process exit → just wait for the process PID or subprocess to finish
   - Log line appears → tail the log and grep for the terminal pattern
   - CloudWatch metric or alarm → poll via `aws cloudwatch`
   - GitHub Actions run → poll via `gh run watch`
   - Other → derive from system document

3. Write `wait-for-completion.sh` to `/tmp/fix-flow-orchestrator/scripts/wait-for-completion.sh`:
   - Must have a shebang: `#!/bin/bash`
   - Must poll on a reasonable interval (default: 5 seconds)
   - Must have a timeout (default: 5 minutes) — exit 1 with a clear message if exceeded
   - Exit 0 when the flow reaches a **success** terminal state
   - Exit 1 when the flow reaches a **failure** terminal state or times out
   - Print the current state on each poll so progress is visible
   - Include a comment at the top explaining what it is polling and why

4. Make the script executable:
   ```bash
   chmod +x /tmp/fix-flow-orchestrator/scripts/wait-for-completion.sh
   ```

5. Confirm with the developer that the polling logic looks correct before returning.
