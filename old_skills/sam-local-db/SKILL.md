---
name: sam-local-db
description: Fix and run the Encache backend locally with AWS SAM + Docker Postgres. Use when local SAM invocations fail due to missing DB env vars, Docker network connectivity, warm container env drift, or missing DB schema.
---

# Sam Local DB

## Overview

Run the Encache SAM API locally with Docker Postgres and ensure Lambdas receive DB env vars and can reach the DB.

## Workflow

### 1. Confirm local env files

- Ensure `main/server/sam-env.local.json` exists and includes `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT` for the MPU functions (`MemoryMpuStartFunction`, `MemoryMpuPartFunction`, `MemoryMpuCompleteFunction`, `MemoryMpuAbortFunction`).
- Ensure `main/server/sam-container-env.local.json` exists and has the same DB\_\* vars for container-level overrides.

### 2. Ensure Docker network is used on Linux

- Determine the compose network for the Postgres container (usually `server_default`).
- Start SAM on that network:
  ```bash
  SAM_DOCKER_NETWORK=server_default ./scripts/start-local.sh
  ```

### 3. Force env refresh if errors persist

Warm containers can keep stale env.

- Stop SAM (`Ctrl+C`).
- Remove SAM containers:
  ```bash
  docker rm -f $(docker ps -q --filter 'ancestor=samcli/lambda-python:3.12-x86_64-ea35a2dafa693f01cf9de8ed7')
  ```
- Restart SAM with the network.

### 4. Verify env inside the running Lambda container

Check that the MPU container actually has DB\_\* env vars:

```bash
# find a MemoryMpuStartFunction container
ID=$(docker ps -q --filter 'ancestor=samcli/lambda-python:3.12-x86_64-ea35a2dafa693f01cf9de8ed7' | head -n 1)
docker exec "$ID" env | rg -n 'DB_(HOST|NAME|USER|PASSWORD|PORT)='
```

If DB\_\* is missing, SAM is not applying the env file. Re-check step 1 and 3.

### 5. Fix missing DB schema (UndefinedTable)

If you see `relation "memory_uploads" does not exist`, reset the local DB volume so init scripts run:

```bash
./scripts/db-local-teardown.sh
./scripts/start-local.sh
```

## Notes

- `start-local.sh` should pass `--env-vars` and `--container-env-vars` if the container env file exists.
- The SAM process should be run from `main/server` so relative paths resolve correctly.
- SAM Lambda containers can only reach Postgres when they share a Docker network.
