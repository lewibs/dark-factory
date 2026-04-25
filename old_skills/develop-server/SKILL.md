---
name: develop-server
description: Use this skill when writing Python code, running tests, or inspecting the AWS Lambda backend and PostgreSQL database in `main/server`. Trigger phrases: "write backend code", "debug server", "add API endpoint".
---

## Required

You must add the following steps to your current task checklist or implementation plan:

1.  **Navigate**: Go to `main/server`.
2.  **Venv**: Activate `main/server/.venv` (create it if missing) before installing or running Python tooling.
3.  **Verify State**: Run `pytest` to ensure the current state is stable.
4.  **Implement**: Write your code, ensuring you add Unit (`tests/unit/`) and Integration (`tests/integration/`) tests for new features.
5.  **Format**: Run `jj fix` before committing to handle formatting.

## Context

I develop the server using Python 3.x and AWS Lambda.

- **Testing**: `pytest` is mandatory for all changes.
- **Database**: PostgreSQL with `pgvector`. Connect via `psql` if needed.
- **Type Hints**: Required for all functions.
- **Exceptions**: Use `core/exceptions.py`.
- **Logging**: Use `structlog` or JSON formatting.

## Examples

### Good Code

```python
def process_data(data: dict) -> None:
    """Processes input data."""
    try:
        logger.info("processing_data", id=data["id"])
    except KeyError:
        raise InvalidInputError("Missing ID")
```

### Bad Code

```python
def process_data(data):
    # No type hints, print instead of log
    print(f"Processing {data['id']}")
```
