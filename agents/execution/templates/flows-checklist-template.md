# Flows Checklist

- Plan: `{{PLAN_PATH}}`
- Generated: `{{DATE}}`

## Flows

| Flow | Test File(s) | Core File(s) | Test Written | Test Failing | Implemented | Test Passing |
|------|-------------|--------------|:------------:|:------------:|:-----------:|:------------:|
| `{{FLOW_NAME}}` | `{{TEST_FILES}}` | `{{CORE_FILES}}` | `[ ]` | `[ ]` | `[ ]` | `[ ]` |

Legend: `[ ]` = not done · `[x]` = done · `N/A` = explicitly waived in plan

## Deviations

| Flow | Blocker | Resolution | Status |
|------|---------|------------|--------|
| — | — | — | — |

## Notes

- Phase 2 gate: every non-N/A flow must have Test Written `[x]` and Test Failing `[x]` before Phase 3 begins.
- Phase 3 gate: every flow must have Implemented `[x]` and Test Passing `[x]` before reporting success.
- A flow is only marked Implemented after its test passes — not when code is written.
