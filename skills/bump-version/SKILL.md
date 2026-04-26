---
name: bump-version
description: "Increment the patch version in .claude-plugin/plugin.json, commit, and create a git tag using the dark-factory double-dash tag convention."
user-invocable: false
---
## When to use
When the dark-factory plugin needs a new release: increment the patch segment of the version in `.claude-plugin/plugin.json`, produce a commit, and apply the canonical git tag so the version is findable and push-ready.

## Steps

1. Read the current version from `.claude-plugin/plugin.json` (field `"version"`).
2. Split on `"."` into `[major, minor, patch]`; increment `patch` by 1 to get `newVersion`.
3. **Guard — check for duplicate tag before writing anything:**
   ```bash
   git tag -l "dark-factory--v<newVersion>"
   ```
   If the tag already exists, abort and surface `StandardError { message: "tag already exists: dark-factory--v<newVersion>" }`. Do not overwrite an existing tag.
4. Write `newVersion` back into `.claude-plugin/plugin.json`.
5. Stage and commit:
   ```bash
   git add .claude-plugin/plugin.json
   git commit -m "chore: bump version to <newVersion>"
   ```
6. Create the tag using the double-dash convention:
   ```bash
   git tag "dark-factory--v<newVersion>"
   ```
7. After local verification, push the tag separately:
   ```bash
   git push origin "dark-factory--v<newVersion>"
   ```
8. Re-register and update the locally installed plugin so the running Claude Code environment reflects the new version:
   ```bash
   DARK_FACTORY_ROOT=$(git worktree list | head -1 | awk '{print $1}')
   claude plugin marketplace add "$DARK_FACTORY_ROOT"
   claude plugin marketplace update dark-factory
   claude plugin update "dark-factory@dark-factory"
   claude plugin list   # confirm new version appears
   ```

## Notes

- The tag format is `dark-factory--v<version>` — two dashes between `dark-factory` and `v`. Using a single dash (`dark-factory-v1.1.5`) is wrong and will not match the convention already established by prior tags.
- Always run the duplicate-tag guard (step 3) before modifying any file. Writing the file and then discovering the tag exists leaves the repo in a dirty state with an uncommitted version change.
- Always use `git worktree list | head -1 | awk '{print $1}'` (not `$(pwd)`) to get the main repo root for marketplace registration. When this skill runs inside a git worktree, `$(pwd)` resolves to the worktree path — which gets deleted after cleanup — causing the marketplace registration to point to a dead path and the plugin to disappear on next restart.
- This skill covers patch bumps only. Minor and major bumps follow the same steps but increment the respective segment and reset lower segments to zero.
