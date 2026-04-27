---
name: agent-loop-with-max-iterations
description: "Use this skill when writing an agent that must retry a blocking external check (CI, polling, review threads) in a loop — structure the loop with a named max-iteration guard, a BREAK-after-first-fix pattern, and re-entrance of upstream checks after downstream fixes."
user-invocable: false
---
## When to use

Any time you write or update an agent that contains a retry/watch loop over an external blocking check — for example: waiting for CI to pass, polling a deployment, re-checking after fixing review threads, or any pattern of the form "run check → fix failure → re-run check."

## Steps

1. Define a named constant for the iteration cap at the top of the pseudocode:
   ```
   MAX_<LOOP_NAME>_ITERATIONS = 5
   ```

2. Open the loop with the guard as its **first** statement:
   ```
   LOOP:
     if iterations >= MAX_<LOOP_NAME>_ITERATIONS:
       STOP with error "<loop name> exceeded MAX_<LOOP_NAME>_ITERATIONS"
   ```

3. After a successful fix attempt, **BREAK out of the inner fix loop immediately** and re-enter the outer watch loop. Do not continue processing remaining failures — the single fix commit may resolve all of them:
   ```
   if fixResult.fixed == true:
     BREAK   // re-watch from top; remaining items may already be fixed
   ```

4. Increment `iterations` at the **bottom** of the loop body, after the fix attempt, before `CONTINUE LOOP`.

5. When loops are nested (e.g., comment resolution wraps CI watch), the outer loop must **re-invoke the inner loop** after each round of fixes, before checking for new outer items:
   ```
   // After resolving all threads in this round, re-check CI before checking for more threads
   ciResult = ciWatchLoop(pr_url)
   if ciResult is error:
     STOP with error ciResult.message
   ```

6. Always give each loop and its error/success outputs distinct named types in the plan's `## Flows` section (e.g., `CIWatchLoopOutput`, `CIWatchLoopError`) so callers can pattern-match on the result.

## Notes

- The terse numbered-step form ("go back to step 3") is ambiguous about when the iteration counter increments and what happens to remaining items after the first fix. Always use explicit pseudocode for loops.
- `quota exhaustion` is a special-case non-fix: when `resolve-pr-issue` returns `skipped: true` for a CI failure caused by API quota exhaustion, treat it as a pass and return immediately — do not increment iterations or attempt further fixes.
- `gh pr checks <pr_url> --watch` blocks until all checks complete **or one fails**. After `--watch` exits with failure, use `gh pr checks <pr_url> --fail-fast` to collect the specific failing run IDs.
- The max-iteration guard prevents infinite loops in adversarial cases (e.g., a fix that breaks CI in a new way each time). Five iterations is the established default in this codebase.
