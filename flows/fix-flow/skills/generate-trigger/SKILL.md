# generate-trigger

Generate `trigger.sh` — the script that fires the integration flow.

## Steps

1. Read `/tmp/system-diagram.md` to understand the flow entry point.

2. Determine how to invoke the flow:
   - Local process (e.g. `pytest`, CLI command) → write a script that runs it directly
   - HTTP endpoint → write a script that calls it with `curl` or the appropriate client
   - Lambda → write a script that invokes it with `aws lambda invoke`
   - SQS message → write a script that sends the trigger message with `aws sqs send-message`
   - Other → derive the correct invocation from the system document

3. Write `trigger.sh` to `/tmp/fix-flow-orchestrator/scripts/trigger.sh`:
   - Must have a shebang: `#!/bin/bash`
   - Must exit 0 when the flow was successfully triggered
   - Must exit 1 if the invocation itself fails (e.g. Lambda not found, endpoint unreachable)
   - Must NOT wait for the flow to complete — just fires it and returns
   - Include a comment at the top explaining what it triggers and how

4. Make the script executable:
   ```bash
   chmod +x /tmp/fix-flow-orchestrator/scripts/trigger.sh
   ```

5. Confirm with the developer that the trigger command looks correct before returning.
