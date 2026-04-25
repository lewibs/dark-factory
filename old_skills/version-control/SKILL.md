---
name: version-control
description: Use this skill when you need to save code changes, create commits, navigate the revision history, or push to the remote repository.
---

## Required

You must add the following steps to your current task checklist or implementation plan:

1. Run `jj st` to check status and changed files.
2. Run `jj fix` to auto-format code.
3. Save changes: `jj describe` (new commit) or `jj squash` (existing commit).
4. Create a bookmark: `jj bookmark create type/short-desc`.
5. Push to remote: `jj git push`.

## Context

I use `jj` (Jujutsu) for version control.

- **Mental Model**: The working copy is always a commit.
- **Rules**:
  - I NEVER push directly to `master`.
  - I NEVER use `git add` or `git commit`.
  - I ALWAYS run `jj fix` before pushing.
  - I create pull requests using the `create-pull-request` skill.

## Examples

## Good Example

# Saving a new feature

```bash
jj describe -m "feat: add login"
jj bookmark create feat/login
jj git push
```

## Bad Example

# Using git commands

```bash
git add .
git commit -m "wip"
```
