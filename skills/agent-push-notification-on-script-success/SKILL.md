---
name: agent-push-notification-on-script-success
description: "How to have an agent run a helper Python script, capture its stdout URL or value, and send a PushNotification only when the script succeeds — skipping silently on failure."
user-invocable: false
---
## When to use

When an agent instruction body needs to call an external helper script (Python or bash), capture its output, and conditionally push a notification to the developer's phone — without blocking the main flow if the script fails or produces no output.

## Steps

1. **Run the helper script via Bash** — use a Bash tool call or inline pseudocode:

   ```
   run: python3 scripts/<helper>.py <arg1> [--flag N]
   capture stdout as <value>
   capture exit code
   ```

2. **Gate on both exit code AND non-empty output** — check both conditions before sending the notification:

   ```
   if exit code == 0 and <value> is non-empty:
     call PushNotification with message: "<label>: <value>"
   else:
     log warning to stderr — skip push, continue
   ```

3. **Never block the main flow** — the push step is best-effort. If the script exits non-zero (e.g., no matching block found, file missing) or returns empty output, log a warning and continue to the next step of the agent's flow without raising an error.

4. **Document the skip branches in the plan** — in the plan's flow table, add a `branch` path for `script-failure` and `no-output` so the skip behavior is explicit and reviewers know it is intentional.

## Notes

- The planning-agent's `planningAgentPushesUrl` flow in `agents/featurework/planning/agents/planning-agent.md` is the canonical reference implementation of this pattern.
- The PushNotification tool is a Claude Code built-in and requires no setup. Invoke it with a `message` string.
- For the message format, prefer a short human-readable label followed by the URL or value so the notification is useful at a glance on the phone lock screen (e.g., `"Plan diagram: https://mermaid.ink/img/..."`).
- Do not add the PushNotification tool to an agent's `tools:` frontmatter unless the agent instruction body explicitly calls it — omitting it means it won't be available at runtime. See `declare-tools-in-agent-frontmatter` skill.
- **Do not treat stderr as a failure signal.** Many helper scripts (including `scripts/mermaid_to_image.py`) write progress or warning messages to stderr even on a successful run. The only reliable failure signals are: (a) non-zero exit code, and (b) empty stdout. Explicitly tell worker agents "check exit code only — do not treat stderr output as a failure on its own." Without this instruction, agents will often misinterpret diagnostic stderr lines as errors and incorrectly set url/value to null.
