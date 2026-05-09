#!/usr/bin/env python3
"""
batch-queue-manager.py

Orchestrates batch job submission and status tracking for dark-factory manufacture flow.
Manages the lifecycle of batch jobs from creation through polling.

Usage:
  python3 batch-queue-manager.py \
    --command submit \
    --agent update-documentation-agent \
    --agent-args '{"planFilePath": "/path/to/plan.md"}' \
    --work-dir /path/to/work_dir
    
  python3 batch-queue-manager.py \
    --command poll \
    --job-id batch_123... \
    --work-dir /path/to/work_dir \
    --timeout 120
"""

import json
import sys
import argparse
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional


def submit_batch_job(
    agent_name: str,
    agent_args: Dict[str, Any],
    work_dir: str,
    scripts_dir: str,
) -> Dict[str, Any]:
    """
    Submits a batch job request via batch-request-builder.
    
    Returns: {jobId, customId, requestPath}
    """
    # Prepare temporary request file
    batch_jobs_dir = Path(work_dir) / "batch-jobs"
    batch_jobs_dir.mkdir(parents=True, exist_ok=True)
    
    request_file = batch_jobs_dir / f"{agent_name}-request.json"
    
    # Call batch-request-builder
    try:
        result = subprocess.run(
            [
                sys.executable,
                os.path.join(scripts_dir, "batch-request-builder.py"),
                "--agent", agent_name,
                "--agent-args", json.dumps(agent_args),
                "--work-dir", work_dir,
                "--output", str(request_file),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": f"batch-request-builder failed: {result.stderr}",
            }
        
        # Parse the request to extract custom_id
        with open(request_file, "r") as f:
            request_payload = json.load(f)
        
        custom_id = request_payload.get("custom_id", "unknown")
        
        return {
            "success": True,
            "jobId": custom_id,  # Will be replaced by actual Batch API ID
            "customId": custom_id,
            "requestPath": str(request_file),
        }
    
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "batch-request-builder timed out",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to submit batch job: {str(e)}",
        }


def poll_batch_job(
    job_id: str,
    work_dir: str,
    scripts_dir: str,
    timeout: int = 60,
) -> Dict[str, Any]:
    """
    Polls batch job status via batch-poll-manager.
    
    Returns: {status, result, error}
    """
    batch_jobs_dir = Path(work_dir) / "batch-jobs"
    batch_jobs_dir.mkdir(parents=True, exist_ok=True)
    
    result_file = batch_jobs_dir / f"{job_id}-result.json"
    
    try:
        result = subprocess.run(
            [
                sys.executable,
                os.path.join(scripts_dir, "batch-poll-manager.py"),
                "--job-id", job_id,
                "--timeout", str(timeout),
                "--output", str(result_file),
            ],
            capture_output=True,
            text=True,
            timeout=timeout + 10,  # Allow extra time for script overhead
        )
        
        # Parse the result file regardless of return code
        if result_file.exists():
            with open(result_file, "r") as f:
                poll_result = json.load(f)
            
            return {
                "success": poll_result.get("status") == "completed",
                "status": poll_result.get("status"),
                "result": poll_result.get("result"),
                "error": poll_result.get("error"),
            }
        else:
            return {
                "success": False,
                "status": "error",
                "result": None,
                "error": f"batch-poll-manager failed: {result.stderr}",
            }
    
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "status": "timeout",
            "result": None,
            "error": "Polling timed out",
        }
    except Exception as e:
        return {
            "success": False,
            "status": "error",
            "result": None,
            "error": f"Failed to poll batch job: {str(e)}",
        }


def main():
    parser = argparse.ArgumentParser(
        description="Manage batch job submission and polling"
    )
    parser.add_argument(
        "--command",
        required=True,
        choices=["submit", "poll"],
        help="Command to execute",
    )
    parser.add_argument(
        "--work-dir",
        required=True,
        help="Work directory path",
    )
    
    # Submit-specific args
    parser.add_argument(
        "--agent",
        help="Agent name (required for submit)",
    )
    parser.add_argument(
        "--agent-args",
        help="JSON string of agent arguments (required for submit)",
    )
    
    # Poll-specific args
    parser.add_argument(
        "--job-id",
        help="Job ID to poll (required for poll)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout for polling (default: 60)",
    )
    
    args = parser.parse_args()
    
    # Get scripts directory (parent directory of this script)
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    
    if args.command == "submit":
        if not args.agent or not args.agent_args:
            print("ERROR: --agent and --agent-args required for submit command", file=sys.stderr)
            sys.exit(1)
        
        try:
            agent_args = json.loads(args.agent_args)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in --agent-args: {e}", file=sys.stderr)
            sys.exit(1)
        
        result = submit_batch_job(
            args.agent,
            agent_args,
            args.work_dir,
            scripts_dir,
        )
        
        print(json.dumps(result))
        sys.exit(0 if result.get("success") else 1)
    
    elif args.command == "poll":
        if not args.job_id:
            print("ERROR: --job-id required for poll command", file=sys.stderr)
            sys.exit(1)
        
        result = poll_batch_job(
            args.job_id,
            args.work_dir,
            scripts_dir,
            timeout=args.timeout,
        )
        
        print(json.dumps(result))
        sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
