---
name: error-handling
description: Use this skill ONLY when adding try/catch blocks, exception logic, or error responses. Do NOT use for general coding.
---

<!-- TODO audit this, it should probably be in a python specific skill -->

## Required

You must add the following steps to your current task checklist or implementation plan:

1. Use custom exception classes from `core/exceptions.py`.
2. Log errors with context (use `structlog` or JSON format).
3. Distinguish between user-facing and internal errors.
4. Never expose stack traces or internal details to users.
5. Include error codes for programmatic handling.

## Context

I handle errors consistently and safely.

- **Custom Exceptions**: Use `InvalidInputError`, `NotFoundError`, `AuthError` from `core/exceptions.py`.
- **Logging**: Always log with context: `logger.error("action_failed", user_id=user.id, reason=str(e))`.
- **User Messages**: Generic and helpful, never technical.
- **Internal Messages**: Detailed for debugging, logged only.
- **Error Codes**: Use `ERROR_CODE` format for client handling.

## Examples

## Good Example

```python
from core.exceptions import InvalidInputError
import structlog

logger = structlog.get_logger()

def process_order(order_id: str) -> None:
    try:
        order = get_order(order_id)
    except OrderNotFoundError:
        logger.warning("order_not_found", order_id=order_id)
        raise InvalidInputError(
            code="ORDER_NOT_FOUND",
            message="We couldn't find that order."
        )
```

## Bad Example

```python
def process_order(order_id):
    try:
        order = get_order(order_id)
    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}  # Exposes internals
```
