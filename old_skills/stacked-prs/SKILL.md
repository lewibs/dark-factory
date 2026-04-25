---
name: stacked-prs
description: Use this skill to ensure stacked PRs on GitHub correctly target their parent branches instead of main.
---

## Required

You must use this skill whenever you are creating or updating a "stack" of pull requests (multiple dependent branches).

1. **Verify Stack**: Check if the current PR depends on another active PR.
2. **Run Automation**: Execute `python3 .agent/skills/stacked-prs/scripts/fix_stacked_prs.py` after pushing.
3. **Verify Targets**: Confirm in the output that child PRs are retargeted to their parent branches.

## Context

I automate the management of stacked PRs to ensure clean diffs.

- **Problem**: GitHub defaults all PRs to target `main`, showing cumulative diffs for stacked changes.
- **Solution**: I run the `fix_stacked_prs.py` script to retarget child PRs to their parent PRs.
- **Timing**: Run this _after_ pushing bookmarks to GitHub (`jj git push`).

## Examples

### Good Example

# After pushing stack-1 and stack-2

$ python3 .agent/skills/stacked-prs/scripts/fix_stacked_prs.py

Updating PR for 'stack-2' to base 'stack-1'...
✅ Updated 'stack-2' base to 'stack-1'

### Bad Example

# Do not leave stacked PRs targeting main

PR #2 (stack-2) targets main.
Diff includes changes from PR #1 (stack-1) AND PR #2.
Reviewers are confused by large diffs.
