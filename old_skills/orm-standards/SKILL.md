---
name: orm-standards
description: Standards for adding SQLAlchemy ORM models in main/server/layers/shared/python/shared/orm and testing them with setup_inmemory_test_db.
---

## Required

You must follow these steps when adding or modifying ORM models:

1. Add the model class in `main/server/layers/shared/python/shared/orm/`.
2. Import `Base` and `getSession` from `shared.orm.orm`.
3. Export new model/functions in `shared/orm/__init__.py`.
4. Register the model by importing it in `shared/orm/orm.py`.
5. Write integration tests using `setup_inmemory_test_db`.

## Context

I use SQLAlchemy for ORM management and in-memory SQLite for testing.

- **Models**: Defined with `__tablename__` and SQLAlchemy types.
- **Helpers**: Create/read helpers should live next to the model.
- **Testing**: Never use a real database in tests; use `setup_inmemory_test_db()`.

## Examples

## Good Example

```python
from sqlalchemy import Column, String
from .orm import Base, getSession

class Example(Base):
    __tablename__ = "examples"
    id: str = Column(String, primary_key=True)

def createExample(payload: dict[str, Any]) -> None:
    session = getSession()
    try:
        session.add(Example(id=payload["id"]))
        session.commit()
    finally:
        session.close()
```

## Testing ORM code

- Prefer integration tests under `main/server/tests/integration/`.
- Use the shared helper: `from tests.db import setup_inmemory_test_db`.
- Call `setup_inmemory_test_db()` before ORM operations.
