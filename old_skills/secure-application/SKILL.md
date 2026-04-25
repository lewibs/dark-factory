---
name: secure-application
description: Enforce security best practices for mobile and cloud infrastructure.
---

Use this skill BEFORE you create a commit involving API keys, authentication logic, or new database connections. Also use this when I explicitly ask for a security review.

## Required

You must add the following steps to your current task checklist:

1. Scan the staged changes for secrets/keys.
   - Run `git diff --cached` (or `jj diff`) and manually inspect for high-entropy strings.
2. Grep for forbidden mobile storage patterns.
   - Search for `AsyncStorage` usage for sensitive data (tokens/keys).
   - If found, suggest `SecureStore` alternatives immediately.
3. Verify API route security.
   - If new endpoints were added, ensure they have authentication middleware applied.
4. Check for `console.log` statements that might leak PII or auth tokens.

## Context

I enforce security best practices for mobile and cloud infrastructure.

- **Secrets**: I never commit plain text API keys or secrets.
- **Storage**: I use `SecureStore` for sensitive data on mobile.
- **Auth**: I ensure all new API routes are protected.
- **Privacy**: I avoid logging PII or sensitive tokens.

## Examples

## Good Example

"I found a call to AsyncStorage storing 'user_token'. I have added a task to refactor this to SecureStore."
