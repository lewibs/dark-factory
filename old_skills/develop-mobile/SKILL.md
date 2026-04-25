---
name: develop-mobile
description: Use this skill when writing code, running tests, or inspecting the React Native mobile application in `main/app`. Trigger phrases: "write mobile code", "debug app", "add UI component", "fix screen".
---

## Required

You must add the following steps to your current task checklist or implementation plan:

1.  **Navigate**: Go to `main/app`.
2.  **Install**: Run `npm install` if `package.json` changed.
3.  **Verify State**: Run `npm test` to verify existing behavior.
4.  **Implement**: Write your code, adding Unit and Integration tests for new features.
5.  **Format**: Run `jj fix` before committing to handle formatting.

## Context

I develop the mobile app using React Native (Expo) and TypeScript.

- **Testing**: `npm test` uses Jest. New features MUST have tests. Follow the **Frontend Testing** section in the [TDD skill](../test-driven-development/SKILL.md) — integration-first, behavior over implementation, mock at network boundary only.
- **Test coverage per screen**: At minimum — happy path, API error state, and empty/no-data state.
- **No test theater**: Write tests from requirements, not from reading code. A test that confirms what the code currently does (rather than what it should do) encodes bugs as correct behavior. See the [TDD skill](../test-driven-development/SKILL.md) for examples.
- **Navigation**: I use `expo-router` (file-based).
- **Images**: I use `expo-image` for caching.
- **State**: I prefer local state or Zustand.
- **Linting**: I run `npm run lint` to check for issues.

## Examples

### Good Component

```tsx
// main/app/components/Profile.tsx
// Using expo-image and local state
import { Image } from "expo-image";
import { useState } from "react";

export default function Profile() {
  const [active, setActive] = useState(false);
  return <Image source="..." />;
}
```

### Bad Component

```tsx
// Using React Native Image and global context unnecessarily
import { Image } from "react-native";
import { useContext } from "react";
```
