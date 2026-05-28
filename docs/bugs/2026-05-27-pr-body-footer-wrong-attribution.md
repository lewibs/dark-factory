# Bug: PR body footer shows wrong attribution

**Date:** 2026-05-27
**Status:** Fixed

## Symptom

PRs opened by pr-agent never include "Generated with dark factory" in the footer. Instead the body sometimes shows "Generated with [Claude Code](https://claude.com/claude-code)" — the default Claude Code commit attribution — rather than the correct dark factory attribution from the template.

## Root Cause

The pr-agent instructions for Step 1 said:

> Read agents/pr/templates/pr-template.md for structure.

The phrase "for structure" signaled to the Haiku model that the template is a structural reference, not a verbatim scaffold. When writing the PR body from scratch, the Haiku model fell back on its training-data knowledge of the standard Claude Code attribution footer instead of copying the footer from the template.

The template (`agents/pr/templates/pr-template.md`) has the correct footer:

```
🤖 Generated with [dark factory](https://github.com/lewibs/dark-factory)
```

But since the instruction didn't mandate verbatim copying of that line, the model substituted its own version.

## Fix

Updated `agents/pr/agents/pr-agent.md` in two places:

1. **Step 1 orchestration block** — changed "Read template for structure" to explicitly embed the required footer and state it must be copied verbatim. Added a negative example ("Generated with [Claude Code](...)" is WRONG) to make the constraint unambiguous.

2. **Rules section** — added a dedicated rule: "The PR body footer MUST always be exactly: `🤖 Generated with [dark factory](https://github.com/lewibs/dark-factory)` — never `Generated with [Claude Code]` or any other attribution."

## Files Changed

- `/home/lewibs/github/dark_factory/dark_factory/agents/pr/agents/pr-agent.md`
