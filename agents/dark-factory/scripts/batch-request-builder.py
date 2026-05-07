#!/usr/bin/env python3
"""
batch-request-builder.py

Constructs Anthropic Batch API requests for non-interactive dark-factory agents.
Converts standard agent invocation arguments into Batch API job payloads.

Usage:
  python3 batch-request-builder.py \
    --agent update-documentation-agent \
    --agent-args '{"planFilePath": "/path/to/plan.md"}' \
    --work-dir /path/to/work_dir \
    --output /path/to/request.json
"""

import json
import sys
import argparse
import uuid
from datetime import datetime
from typing import Dict, Any, Optional


# Agent configurations: model, system prompt template, required args
BATCHABLE_AGENTS = {
    "update-documentation-agent": {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 8000,
        "system_prompt": """You are update-documentation-agent. Your job is to update project documentation after a plan has been implemented.

You will be given a plan file path. Your task is to:
1. Read the plan and identify affected flows/components
2. Find and update existing docs or create new ones
3. Return a SkillUpdateOutput with the files written

Return JSON with this structure:
{
  "docsWritten": ["/absolute/path/to/file1.md", ...],
  "phase_complete": true
}

If you cannot complete, return:
{
  "error": "description of what went wrong"
}
""",
    },
    "skill-update-agent": {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 8000,
        "system_prompt": """You are skill-update-agent. Your job is to review completed work and identify reusable patterns.

Given a plan file path, work directory, and task summary, you will:
1. Review the completed work
2. Identify non-obvious patterns that are likely to recur
3. Write skill files to the skills/ directory
4. Return a SkillUpdateOutput

Return JSON with this structure:
{
  "skillsWritten": [
    {"path": "skills/pattern-name/SKILL.md", "action": "created"},
    ...
  ]
}

If no patterns qualify, return:
{
  "skillsWritten": []
}

If there's an error, return:
{
  "error": "description of what went wrong"
}
""",
    },
}


def build_batch_request(
    agent_name: str,
    agent_args: Dict[str, Any],
    work_dir: str,
) -> Dict[str, Any]:
    """
    Builds a single Batch API request payload for a dark-factory agent.
    
    Args:
        agent_name: Name of the agent (update-documentation-agent, skill-update-agent)
        agent_args: Arguments to pass to the agent
        work_dir: Working directory (used for custom_id generation)
    
    Returns:
        Dictionary ready to be serialized to Batch API request
    """
    if agent_name not in BATCHABLE_AGENTS:
        raise ValueError(f"Agent '{agent_name}' is not eligible for batching")
    
    config = BATCHABLE_AGENTS[agent_name]
    
    # Generate unique custom_id for batch job
    custom_id = f"{work_dir.split('/')[-1]}-{agent_name}-{uuid.uuid4().hex[:8]}"
    
    # Build user message content (serialize agent args as JSON)
    user_message = f"""Agent Input:
{json.dumps(agent_args, indent=2)}

Process the input and return your result in JSON format."""
    
    # Build the Batch API request payload
    request_payload = {
        "custom_id": custom_id,
        "params": {
            "model": config["model"],
            "max_tokens": config["max_tokens"],
            "system": config["system_prompt"],
            "messages": [
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
        },
    }
    
    return request_payload


def main():
    parser = argparse.ArgumentParser(
        description="Build Batch API request payloads for dark-factory agents"
    )
    parser.add_argument(
        "--agent",
        required=True,
        choices=list(BATCHABLE_AGENTS.keys()),
        help="Agent to batch",
    )
    parser.add_argument(
        "--agent-args",
        required=True,
        help="JSON string of agent arguments",
    )
    parser.add_argument(
        "--work-dir",
        required=True,
        help="Work directory path (for custom_id generation)",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output path for request JSON",
    )
    
    args = parser.parse_args()
    
    try:
        agent_args = json.loads(args.agent_args)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in --agent-args: {e}", file=sys.stderr)
        sys.exit(1)
    
    try:
        request_payload = build_batch_request(
            args.agent,
            agent_args,
            args.work_dir,
        )
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Write request to file
    try:
        with open(args.output, "w") as f:
            json.dump(request_payload, f, indent=2)
        print(f"Request written to {args.output}")
        print(f"Custom ID: {request_payload['custom_id']}")
        sys.exit(0)
    except IOError as e:
        print(f"ERROR: Failed to write request: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
