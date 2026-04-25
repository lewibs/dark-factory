---
name: project-constraints
description: Use this skill to verify project boundaries, security rules, and performance targets before finalizing changes.
---

## Required

You must add the following steps to your current task checklist or implementation plan:

1. Verify no production data is modified.
2. Verify no unauthorized third-party API calls are made.
3. Check for any secrets in code or logs.
4. If schemas changed, confirm versioning is handled.
5. If state changes, confirm idempotency keys are used.
6. Verify performance targets (Glasses <100ms, Phone <5m, AWS <10m).

## Context

I adhere to strict project boundaries and constraints.

- **Independence**: I never touch production data or unapproved APIs.
- **Security**: I ensure no raw media in logs and no hardcoded secrets.
- **Architecture**: I respect the 3-layer boundary (Glasses -> Phone -> AWS).
- **CI/CD**: I wait for ALL CI checks (required or not) and fix any failures before merging.
- **Dependencies**: Keep `apps/landing-web` SvelteKit and Svelte versions aligned (SvelteKit 2.x requires Svelte 5+).
- **Motion**: For scroll-linked animations in `apps/landing-web`, keep mobile scroll distances close to desktop values to avoid disorientation.

## Examples

## Good Example

# Updating schema with versioning

```json
{
  "version": "v2",
  "data": { ... }
}
```

## Bad Example

# Hardcoding secret

```python
API_KEY = "sk-12345" # pragma: allowlist secret
```
