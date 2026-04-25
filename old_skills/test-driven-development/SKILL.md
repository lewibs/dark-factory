---
name: test-driven-development
description: Use this skill when writing code to ensure correctness through TDD and the Four Pillars of Testing.
---

## Required

You must add the following steps to your current task checklist or implementation plan:

1. **Discover "What"**: List the most likely logical edge cases in plain English before writing any code.
2. **Filter**: Delete fluff; keep only high-signal scenarios (e.g., skip 1+1=2, keep null/empty/massive).
3. **Write Failing Tests**: Write one test case for each specific scenario (prefer property-based tests).
4. **Implementation**: Write the minimum code to make those specific tests pass.
5. **Refactor & Prune**: Refactor while green. Apply the "Delete by Default" rule to any redundant tests.

## No Test Theater

Test theater is writing tests that confirm code does what it currently does, rather than verifying it does what it *should* do. These tests give false confidence — impressive coverage numbers that encode bugs as correct behavior.

**How it happens:** You read the code, see `return response.data?.answer ?? ""`, and write a test asserting the function returns `""` when answer is missing. The test passes. Coverage goes up. But returning empty string was the bug — the user sees a blank ghost bubble instead of an error message. The test *protects the bug from being fixed*.

**The test:** Ask yourself — "did I write this test from the spec/requirement, or from reading the code?" If you read the code first, you're writing a tautology.

**Rules:**
- Write tests from requirements, not from reading implementation.
- If a test passes immediately on first run, it's suspicious — you may be confirming existing behavior rather than specifying correct behavior.
- When fixing a bug, the failing test must be written BEFORE reading the fix. If you read the fix first, you'll write a test that confirms the fix, not one that catches the bug.
- A test that nobody would ever think to write by looking at requirements alone is probably theater.
- Coverage that encodes bugs is worse than no coverage — it actively resists fixes.

## Four Pillars of Testing

1. **Separate "What" from "How"**: Never mirror code. Define failure modes in plain English first. Test behavior — what the user sees and experiences — not internal state or method calls.
2. **Move Toward Property-Based Testing**: Test rules/contracts (using `Hypothesis` or `FastCheck`) rather than just checking specific inputs.
3. **Integration over Unit**: Spend the token budget on user flows. Simple utils get 1 happy path + 1 edge case.
4. **Delete by Default**: Prioritize signal-to-noise. If a test doesn't add unique confidence, delete it.

## Edge Case Categories

Systematically cover these four categories when discovering edge cases:

1. **Boundary inputs** — empty arrays, single items, max-length strings, zero, negative numbers.
2. **Timing and ordering** — response after unmount, racing requests, out-of-order callbacks.
3. **State transitions** — double-tap, navigate away mid-operation, rapid repeated actions.
4. **Permission and auth boundaries** — expired tokens, revoked permissions, partial access.

## Frontend Testing (React Native / Expo)

### Principles

- **Test behavior, not implementation.** Assert what the user sees — rendered text, visibility, navigation — not `setState` calls or internal method invocations. "Tapping capture shows a timer" is durable; "setState({capturing: true}) was called" is brittle.
- **Integration-first.** Default to screen-level integration tests that render with real hooks, context providers, and a mocked API layer. A single integration test catches more bugs than a dozen isolated unit tests. Reserve focused unit tests for complex pure logic only (e.g., `FrameUploadQueue`).
- **Mock at the network boundary, not deeper.** Use `axios-mock-adapter` to intercept the shared axios instance. Hooks, state management, and components all run with real code — only the server is faked. Never mock custom hooks, context providers, or React Query internals.
- **Test error and empty states explicitly.** Every screen test file must include at minimum: happy path + API error + empty data. Users spend significant time in non-happy-path states.
- **Fresh state for every test.** Create a new `QueryClient` per test. Reset navigation, auth context, and singletons in `beforeEach`. Shared cache between tests is the most common source of flaky React Query suites.

### Running Tests

```bash
cd main/app
npm test                    # all tests
npm test -- --coverage      # with coverage report
npm test -- --watch         # interactive watch mode
```

### Good Example

```tsx
// Screen integration test — tests behavior, mocks only HTTP
import MockAdapter from "axios-mock-adapter";
import { render, waitFor, fireEvent } from "@testing-library/react-native";

it("shows empty state when no memories exist", async () => {
  mock.onPost("/memories/feed").reply(200, { memories: [], cursor: null });
  const { getByText } = render(<MemoryFeedScreen />);
  await waitFor(() => expect(getByText("No memories yet")).toBeTruthy());
});

it("shows error banner when API fails", async () => {
  mock.onPost("/memories/feed").reply(500);
  const { getByText } = render(<MemoryFeedScreen />);
  await waitFor(() => expect(getByText(/something went wrong/i)).toBeTruthy());
});
```

### Bad Example — Implementation Details

```tsx
// Testing implementation details — brittle, breaks on refactor
it("sets loading state", () => {
  const { result } = renderHook(() => useMemoriesFeed());
  expect(result.current.isLoading).toBe(true); // testing React Query internals
});
```

### Bad Example — Test Theater

```tsx
// Test theater: read the code, saw `?? ""`, wrote test confirming it.
// This ENCODES THE BUG — empty answer should show an error, not a blank bubble.
it("returns empty string when answer is missing", async () => {
  mock.onPost("/memories/chat").reply(200, { data: {} });
  const result = await chatWithMemory("Hello");
  expect(result).toBe(""); // ← protects the bug from being fixed
});

// Correct: test from the REQUIREMENT (user should see an error)
it("throws when answer is missing from response", async () => {
  mock.onPost("/memories/chat").reply(200, { data: {} });
  await expect(chatWithMemory("Hello")).rejects.toThrow("No answer received");
});
```

## Backend Testing (Python)

### Running Tests

```bash
.venv/bin/python -m pytest ...   # Use repo venv, not system pytest
```

### Mocking

- **AWS**: Prefer `botocore.stub.Stubber` for boto3 clients.
- **E2E Motion Tests**: For scrubbed scroll animations (e.g., GSAP ScrollTrigger), prefer simulated user input (`page.mouse.wheel`) over `window.scrollTo` to trigger intermediate events.

### Good Example

```python
# Step 1: List edge cases
# 1. Negative numbers 2. Zero 3. Floating points 4. Invalid strings 5. Null

# Step 2: Property-Based Test
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_sort_invariant(xs):
    result = my_sort(xs)
    assert len(result) == len(xs)
    assert all(result[i] <= result[i+1] for i in range(len(result)-1))
```

### Bad Example

```python
# Mirroring code or writing low-signal tests
def test_add():
    assert add(1, 1) == 2
    assert add(2, 2) == 4
    # Testing 10 different pairs of integers for a simple math function.
```
