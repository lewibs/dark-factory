---
name: documentation
user-invocable: false
description: Create or update a system documentation file in docs/docs/ using the documentation template. Use when documenting an existing system or validating that existing docs match the code.
---

## Required

Use this skill whenever a system needs to be documented in `docs/docs/`.

1. Start from `templates/documentation-template.md`. Do not invent alternate section order.
2. If a doc file already exists for this system, read it first and validate each section against the actual code before updating.
3. Complete each section from code evidence — never fill sections from assumptions.
4. Save the file to `docs/docs/<system-name>.md`.

## Context

- `docs/docs/` is the source of truth for how systems work. It describes what exists, not what is planned.
- `docs/plans/` is for active task planning — not source of truth.
- `docs/bugs/` is a log of fixed bugs — use it to cross-reference known failure modes.

## Template

Use `templates/documentation-template.md` as the required scaffold for all documentation files.
