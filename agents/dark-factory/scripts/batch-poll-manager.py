#!/usr/bin/env python3
"""
batch-poll-manager.py

Polls Anthropic Batch API for job status and retrieves results.

Usage:
  python3 batch-poll-manager.py \
    --job-id batch_abc123... \
    --timeout 120 \
    --output /path/to/results.json
"""

import json
import sys
import argparse
import time
from typing import Dict, Any, Optional


def poll_batch_status(
    job_id: str,
    timeout_seconds: int = 60,
    poll_interval: int = 5,
) -> Dict[str, Any]:
    """
    Polls Anthropic Batch API for job completion.
    
    Args:
        job_id: Batch job ID from API
        timeout_seconds: Maximum time to poll
        poll_interval: Seconds between polls
    
    Returns:
        Dictionary with status, result, and error fields
    """
    try:
        from anthropic import Anthropic
    except ImportError:
        return {
            "jobId": job_id,
            "status": "error",
            "result": None,
            "error": "anthropic SDK not installed. Install with: pip install anthropic",
        }
    
    client = Anthropic()
    start_time = time.time()
    
    while (time.time() - start_time) < timeout_seconds:
        try:
            batch_status = client.beta.batches.retrieve(job_id)
            
            # Check if batch is complete
            if batch_status.processing_status == "completed":
                # Retrieve and parse results
                results = []
                try:
                    result_lines = client.beta.batches.results(job_id)
                    for result in result_lines:
                        if hasattr(result, 'result') and result.result:
                            try:
                                # Parse the message content
                                if hasattr(result.result, 'message'):
                                    msg = result.result.message
                                    if hasattr(msg, 'content') and msg.content:
                                        # Extract JSON from content
                                        content_text = msg.content[0].text if msg.content else ""
                                        # Try to parse JSON from the response
                                        try:
                                            parsed = json.loads(content_text)
                                            results.append({
                                                "custom_id": result.custom_id,
                                                "output": parsed,
                                            })
                                        except json.JSONDecodeError:
                                            # If not JSON, store as text
                                            results.append({
                                                "custom_id": result.custom_id,
                                                "output": content_text,
                                            })
                            except (AttributeError, IndexError, TypeError):
                                continue
                except Exception:
                    # If we can't retrieve results details, at least return completed status
                    pass
                
                return {
                    "jobId": job_id,
                    "status": "completed",
                    "result": results if results else None,
                    "error": None,
                }
            
            # Check for failure
            if batch_status.processing_status == "failed":
                error_msg = ""
                if hasattr(batch_status, 'request_counts'):
                    counts = batch_status.request_counts
                    if hasattr(counts, 'errored'):
                        error_msg = f"Batch API reported {counts.errored} failed requests"
                
                return {
                    "jobId": job_id,
                    "status": "failed",
                    "result": None,
                    "error": error_msg or "Unknown batch failure",
                }
            
            # Still processing, wait and retry
            time.sleep(poll_interval)
        
        except Exception as e:
            return {
                "jobId": job_id,
                "status": "error",
                "result": None,
                "error": f"Batch API error: {str(e)}",
            }
    
    # Timeout reached
    return {
        "jobId": job_id,
        "status": "timeout",
        "result": None,
        "error": f"Job {job_id} did not complete within {timeout_seconds}s",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Poll Anthropic Batch API for job completion"
    )
    parser.add_argument(
        "--job-id",
        required=True,
        help="Batch job ID to poll",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout in seconds (default: 60)",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=5,
        help="Polling interval in seconds (default: 5)",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output path for results JSON",
    )
    
    args = parser.parse_args()
    
    # Poll for completion
    result = poll_batch_status(
        args.job_id,
        timeout_seconds=args.timeout,
        poll_interval=args.poll_interval,
    )
    
    # Write results to file
    try:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"Status: {result['status']}")
        if result['error']:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"Results written to {args.output}")
            sys.exit(0)
    except IOError as e:
        print(f"ERROR: Failed to write results: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
