---
name: manage-database
description: Safe lifecycle management for PostgreSQL and pgvector schema changes.
---

Use this skill when I ask you to create a migration, modify the schema, or update vector embeddings configuration.

## Required

You must add the following steps to your current task checklist:

1. Check current database connection status.
2. Create a safety backup (or ask me to confirm a snapshot exists).
3. Generate the migration script (e.g., using Alembic/Prisma).
4. Review the raw SQL.
   - **Note**: Look specifically for destructive actions like `DROP TABLE` or `ALTER COLUMN` that require downtime.
5. If `pgvector` is involved:
   - Verify dimension alignment (e.g., ensuring vector(1536) matches the model).
6. Apply the migration locally.
7. Verify the schema table reflects the new version.
