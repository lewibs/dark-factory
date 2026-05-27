# Remove Duplicate /dark-factory:investigate Command

## System Intent

- **What is being built:** Remove the deprecated `/dark-factory:investigate` command (duplicate of `/dark-factory:investigation`) and update all references throughout the codebase to use the correct `investigation` command instead.
- **Primary consumer(s):** End users of the dark-factory Claude Code plugin.
- **Boundary:** This is a cleanup task that removes duplicate command files and updates documentation and help references.

## Changes

1. Delete `/commands/investigate.md` (duplicate command file)
2. Update `README.md` to reference `/dark-factory:investigation` instead of `/dark-factory:investigate`
3. Update `docs/docs/dark-factory-commands.md` to reflect the correct command name in diagrams and flows
4. Update `docs/docs/manufacture.md` to reference the correct command in deprecated references

## Acceptance Criteria

- All references to the deprecated `/dark-factory:investigate` command are updated to `/dark-factory:investigation`
- No broken links or references remain
- Documentation is consistent across all files
- The duplicate `commands/investigate.md` file is deleted
