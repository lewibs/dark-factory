# generate-fetch-logs

Generate `fetch-logs.sh` — the script that pulls all logs relevant to debugging the flow.

## Steps

1. Read `/tmp/system-diagram.md` to identify all log sources for this flow.

2. Identify where logs live:
   - CloudWatch log groups → use `aws logs filter-log-events`
   - Local stdout/stderr captured to a file → `cat` or `tail` the file
   - DynamoDB / database records → query the relevant table for the run
   - Local pytest output → capture from the test runner output file
   - Multiple sources → fetch all of them and concatenate

3. Write `fetch-logs.sh` to `/tmp/fix-flow-orchestrator/scripts/fetch-logs.sh`:
   - Must have a shebang: `#!/bin/bash`
   - Must print all logs to stdout (the debugger reads stdout)
   - Must include a header before each log source so the debugger knows where each section came from:
     ```
     === <source name> ===
     <log content>
     ```
   - Should fetch logs from the most recent run only (not all historical runs)
   - Exit 0 on success, exit 1 if a log source is unreachable (with a clear error message)
   - Include a comment at the top listing all log sources it fetches from

4. Make the script executable:
   ```bash
   chmod +x /tmp/fix-flow-orchestrator/scripts/fetch-logs.sh
   ```

5. Confirm with the developer that all relevant log sources are covered before returning.
