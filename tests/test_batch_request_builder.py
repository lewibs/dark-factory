"""
test_batch_request_builder.py

Unit tests for batch-request-builder.py
"""

import json
import tempfile
import subprocess
import sys
import os
from pathlib import Path


def test_build_update_documentation_request():
    """Test building a batch request for update-documentation-agent"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "request.json"
        script_path = Path(__file__).parent.parent / "agents/dark-factory/scripts/batch-request-builder.py"
        
        # Build request
        result = subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--agent", "update-documentation-agent",
                "--agent-args", json.dumps({"planFilePath": "/tmp/plan.md"}),
                "--work-dir", "/tmp/test",
                "--output", str(output_file),
            ],
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert output_file.exists(), "Request file not created"
        
        # Verify request structure
        with open(output_file, "r") as f:
            request = json.load(f)
        
        assert "custom_id" in request
        assert "params" in request
        assert request["params"]["model"] == "claude-3-5-sonnet-20241022"
        assert request["params"]["max_tokens"] == 8000
        assert "update-documentation-agent" in request["params"]["system_prompt"]


def test_build_skill_update_request():
    """Test building a batch request for skill-update-agent"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "request.json"
        script_path = Path(__file__).parent.parent / "agents/dark-factory/scripts/batch-request-builder.py"
        
        # Build request
        result = subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--agent", "skill-update-agent",
                "--agent-args", json.dumps({
                    "planFilePath": "/tmp/plan.md",
                    "workDir": "/tmp/work",
                    "taskSummary": "test task",
                }),
                "--work-dir", "/tmp/test",
                "--output", str(output_file),
            ],
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert output_file.exists(), "Request file not created"
        
        # Verify request structure
        with open(output_file, "r") as f:
            request = json.load(f)
        
        assert "custom_id" in request
        assert "skill-update-agent" in request["params"]["system_prompt"]


def test_invalid_agent():
    """Test that invalid agent names are rejected"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "request.json"
        script_path = Path(__file__).parent.parent / "agents/dark-factory/scripts/batch-request-builder.py"
        
        # Try to build request with invalid agent
        result = subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--agent", "invalid-agent",
                "--agent-args", json.dumps({"test": "args"}),
                "--work-dir", "/tmp/test",
                "--output", str(output_file),
            ],
            capture_output=True,
            text=True,
        )
        
        assert result.returncode != 0, "Should fail for invalid agent"
        assert not output_file.exists(), "Should not create file for invalid agent"


if __name__ == "__main__":
    test_build_update_documentation_request()
    test_build_skill_update_request()
    test_invalid_agent()
    print("All tests passed!")
