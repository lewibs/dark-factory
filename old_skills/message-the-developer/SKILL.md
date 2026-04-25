---
name: message-the-developer
description: Run, validate, and troubleshoot the Discord question bot in `scripts/discord_bot`. Use when you want to ask the developer a question or update them on your current state. It has additional instructions if its not working on how to fix it.
---

<!-- TODO audit this, it just doesn't work most the time -->

# Discord Bot Runner

## Overview

Run and validate the Discord question bot in `scripts/discord_bot`, including environment setup, dependency installation, and guidance for messaging users in the target channel.

## Workflow

### 1. Confirm environment and venv

- Prefer an existing venv if one is already in the repo (example: `main/server/.venv`).
- If no suitable venv exists, create and activate one:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

- Verify the active interpreter before installing:

```bash
which python
python --version
```

### 2. Install dependencies

- Bot-only install:

```bash
python -m pip install -r scripts/discord_bot/requirements.txt
```

- If the task requires all repo Python dependencies, also install:

```bash
python -m pip install -r requirements.txt
```

### 3. Load environment variables

- Always use `TARGET_CHANNEL_ID` (channel mode only). Do not support DM mode.
- Use `scripts/discord_bot/.env` with at least `DISCORD_TOKEN` and `TARGET_CHANNEL_ID`.
- `TIMEOUT_SECONDS` is optional.
- Avoid printing the token in logs or messages. Redact if shown.

### 4. Run the bot

```bash
set -a
source scripts/discord_bot/.env
set +a
python3 scripts/discord_bot/ask.py "Your question here"
```

### 5. Validate behavior

- The bot sends one question to `TARGET_CHANNEL_ID` only.
- It accepts the first non-bot message in that channel.
- It exits `1` on timeout or error.

### 6. Troubleshoot quickly

- `ModuleNotFoundError: No module named 'discord'`: Install `scripts/discord_bot/requirements.txt` in the active venv.
- `python: command not found`: Use `python3` and `python3 -m pip`.
- `Target channel is not messageable`: Check bot permissions in that channel.

## Messaging the user

Use a direct, single-action request in the target channel. Keep it short and explicit about where to reply.
Do not ask for a response in this chat. Wait for the Discord response before acting.

Example message:

"Please reply in #<channel-name> from your computer with a single sentence answer. The bot will take the first response and exit."

If you need more detail, ask for one follow-up only after the first response returns.

After receiving the user's response, summarize it and immediately act on the request. Do not stop after logging the reply.
