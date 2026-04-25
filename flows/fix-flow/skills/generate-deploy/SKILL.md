# generate-deploy (optional)

Generate `deploy.sh` — the script that deploys the current code to the target environment.

Only generate this script if the flow **cannot** be tested locally. If the flow runs entirely with local code (e.g. pytest against a local DB), skip this step and return without generating a script.

## Steps

1. Read `/tmp/system-diagram.md` to understand the deploy mechanism for this flow.

2. Ask the developer to confirm:
   - Is a deploy required to test fixes, or can changes be tested locally?
   - If local only → stop here, do not generate the script.

3. Determine the deploy mechanism:
   - SAM → `sam build && sam deploy`
   - Docker → `docker build && docker push`
   - Lambda direct → `aws lambda update-function-code`
   - Other → derive from system document

4. Write `deploy.sh` to `/tmp/fix-flow-orchestrator/scripts/deploy.sh`:
   - Must have a shebang: `#!/bin/bash`
   - Must deploy only the components relevant to this flow — not everything
   - Must wait for the deploy to complete before exiting
   - Exit 0 on successful deploy, exit 1 on failure
   - Include a comment at the top explaining what is being deployed and where

5. Make the script executable:
   ```bash
   chmod +x /tmp/fix-flow-orchestrator/scripts/deploy.sh
   ```

6. Confirm with the developer that the deploy command and target are correct before returning.
