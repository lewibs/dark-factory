"""
tests/test_mermaid_to_image.py

Tests for scripts/mermaid_to_image.py
"""

import subprocess
import sys
import os
from unittest.mock import MagicMock, patch
import pytest

# Ensure scripts/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from mermaid_to_image import extract_mermaid_from_plan, generate_mermaid_ink_url, validate_mermaid_syntax

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "scripts", "mermaid_to_image.py")


# ---------------------------------------------------------------------------
# Flow: extractMermaidFromPlan
# ---------------------------------------------------------------------------

def test_extractMermaidFromPlan_success_block_1(tmp_path):
    # Plan path: extractMermaidFromPlan.success-block-1
    plan = tmp_path / "plan.md"
    plan.write_text("```mermaid\ngraph TD\n  A --> B\n```\n")
    result = extract_mermaid_from_plan(str(plan), block_index=1)
    assert "graph TD" in result

def test_extractMermaidFromPlan_success_block_2(tmp_path):
    # Plan path: extractMermaidFromPlan.success-block-2
    plan = tmp_path / "plan.md"
    plan.write_text(
        "```mermaid\ngraph TD\n  A --> B\n```\n\nsome text\n\n```mermaid\ngraph LR\n  C --> D\n```\n"
    )
    result = extract_mermaid_from_plan(str(plan), block_index=2)
    assert "graph LR" in result

def test_extractMermaidFromPlan_not_found(tmp_path):
    # Plan path: extractMermaidFromPlan.not-found
    plan = tmp_path / "plan.md"
    plan.write_text("No mermaid here.\n")
    with pytest.raises(ValueError, match="No mermaid block found"):
        extract_mermaid_from_plan(str(plan))

def test_extractMermaidFromPlan_index_out_of_range(tmp_path):
    # Plan path: extractMermaidFromPlan.index-out-of-range
    plan = tmp_path / "plan.md"
    plan.write_text("```mermaid\ngraph TD\n  A --> B\n```\n")
    with pytest.raises(ValueError, match="out of range"):
        extract_mermaid_from_plan(str(plan), block_index=5)

def test_extractMermaidFromPlan_file_missing():
    # Plan path: extractMermaidFromPlan.file-missing
    with pytest.raises(FileNotFoundError):
        extract_mermaid_from_plan("/nonexistent/path/to/plan.md")

def test_extractMermaidFromPlan_zero_index(tmp_path):
    # block_index=0 must raise ValueError, not silently return the last block
    plan = tmp_path / "plan.md"
    plan.write_text("```mermaid\ngraph TD\n  A --> B\n```\n")
    with pytest.raises(ValueError, match="block_index must be >= 1"):
        extract_mermaid_from_plan(str(plan), block_index=0)

def test_extractMermaidFromPlan_negative_index(tmp_path):
    # block_index < 0 must raise ValueError
    plan = tmp_path / "plan.md"
    plan.write_text("```mermaid\ngraph TD\n  A --> B\n```\n")
    with pytest.raises(ValueError, match="block_index must be >= 1"):
        extract_mermaid_from_plan(str(plan), block_index=-1)


# ---------------------------------------------------------------------------
# Flow: generateMermaidInkUrl
# ---------------------------------------------------------------------------

def test_generateMermaidInkUrl_success():
    # Plan path: generateMermaidInkUrl.success
    url = generate_mermaid_ink_url("graph TD\n  A --> B")
    assert url.startswith("https://mermaid.ink/img/")

def test_generateMermaidInkUrl_empty_input():
    # Plan path: generateMermaidInkUrl.empty-input
    with pytest.raises(ValueError, match="empty mermaid input"):
        generate_mermaid_ink_url("")


# ---------------------------------------------------------------------------
# Flow: validateMermaidSyntax
# ---------------------------------------------------------------------------

def test_validateMermaidSyntax_success():
    # Plan path: validateMermaidSyntax.success
    mock_result = MagicMock()
    mock_result.returncode = 0
    with patch("subprocess.run", return_value=mock_result):
        valid, err = validate_mermaid_syntax("graph TD\n  A --> B\n")
    assert valid is True
    assert err == ""

def test_validateMermaidSyntax_parse_error():
    # Plan path: validateMermaidSyntax.parse-error
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "Parse error on line 1"
    mock_result.stdout = ""
    with patch("subprocess.run", return_value=mock_result):
        valid, err = validate_mermaid_syntax("not valid mermaid |||")
    assert valid is False
    assert "Parse error" in err

def test_validateMermaidSyntax_npx_not_found():
    # Plan path: validateMermaidSyntax.npx-not-found
    with patch("subprocess.run", side_effect=FileNotFoundError):
        valid, err = validate_mermaid_syntax("graph TD\n  A --> B\n")
    assert valid is False
    assert "npx not found" in err


# ---------------------------------------------------------------------------
# Flow: cliEntryPoint
# ---------------------------------------------------------------------------

def _run_cli(*args):
    """Helper: run mermaid_to_image.py as a subprocess, return (stdout, stderr, returncode)."""
    env = {**os.environ, "MERMAID_SKIP_VALIDATE": "1"}
    result = subprocess.run(
        [sys.executable, SCRIPT_PATH] + list(args),
        capture_output=True,
        text=True,
        env=env,
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def test_cliEntryPoint_success_default(tmp_path):
    # Plan path: cliEntryPoint.success-default
    plan = tmp_path / "plan.md"
    plan.write_text("```mermaid\ngraph TD\n  A --> B\n```\n")
    stdout, stderr, rc = _run_cli(str(plan))
    assert rc == 0
    assert stdout.startswith("https://mermaid.ink/img/")

def test_cliEntryPoint_success_block_n(tmp_path):
    # Plan path: cliEntryPoint.success-block-n (--block flag)
    plan = tmp_path / "plan.md"
    plan.write_text(
        "```mermaid\ngraph TD\n  A --> B\n```\n\n```mermaid\ngraph LR\n  C --> D\n```\n"
    )
    stdout, stderr, rc = _run_cli(str(plan), "--block", "2")
    assert rc == 0
    assert stdout.startswith("https://mermaid.ink/img/")

def test_cliEntryPoint_success_block_n_positional(tmp_path):
    # Plan path: cliEntryPoint.success-block-n (positional second arg)
    plan = tmp_path / "plan.md"
    plan.write_text(
        "```mermaid\ngraph TD\n  A --> B\n```\n\n```mermaid\ngraph LR\n  C --> D\n```\n"
    )
    stdout, stderr, rc = _run_cli(str(plan), "2")
    assert rc == 0
    assert stdout.startswith("https://mermaid.ink/img/")

def test_cliEntryPoint_no_block(tmp_path):
    # Plan path: cliEntryPoint.no-block
    plan = tmp_path / "plan.md"
    plan.write_text("No mermaid here.\n")
    stdout, stderr, rc = _run_cli(str(plan))
    assert rc == 1
    assert "Error" in stderr or "error" in stderr.lower()

def test_cliEntryPoint_index_out_of_range(tmp_path):
    # Plan path: cliEntryPoint.index-out-of-range
    plan = tmp_path / "plan.md"
    plan.write_text("```mermaid\ngraph TD\n  A --> B\n```\n")
    stdout, stderr, rc = _run_cli(str(plan), "--block", "99")
    assert rc == 1
    assert "Error" in stderr or "error" in stderr.lower()

def test_cliEntryPoint_file_missing():
    # Plan path: cliEntryPoint.file-missing
    stdout, stderr, rc = _run_cli("/nonexistent/path/to/plan.md")
    assert rc == 1
    assert "Error" in stderr or "error" in stderr.lower()
