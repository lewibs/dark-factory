"""
Tests for the claim-validator-agent.

Validates agent file structure for the claimValidation flow.

Flows covered:
- claimValidation.all-true
- claimValidation.some-false
- claimValidation.doc-not-found
"""

import os
import re

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLAIM_VALIDATOR_AGENT = os.path.join(
    REPO_ROOT, "agents", "documentation", "agents", "claim-validator-agent.md"
)


def read_file(path):
    with open(path, "r") as f:
        return f.read()


def parse_frontmatter(content):
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}
    frontmatter = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            frontmatter[key.strip()] = value.strip()
    return frontmatter


class TestClaimValidatorAgent:
    """Tests for claim-validator-agent file structure."""

    def test_claim_validator_agent_exists(self):
        """Plan path: claimValidation.all-true — agent file must exist."""
        assert os.path.exists(CLAIM_VALIDATOR_AGENT), (
            f"claim-validator-agent not found at {CLAIM_VALIDATOR_AGENT}"
        )

    def test_claim_validator_agent_has_name(self):
        """Agent must declare name: claim-validator-agent in frontmatter."""
        content = read_file(CLAIM_VALIDATOR_AGENT)
        fm = parse_frontmatter(content)
        assert fm.get("name") == "claim-validator-agent"

    def test_claim_validator_agent_has_read_tool(self):
        """Agent must have Read tool to read documentation files."""
        content = read_file(CLAIM_VALIDATOR_AGENT)
        fm = parse_frontmatter(content)
        tools = fm.get("tools", "")
        assert "Read" in tools

    def test_claim_validator_agent_references_all_verified(self):
        """Plan path: claimValidation.all-true — agent must return allVerified field."""
        content = read_file(CLAIM_VALIDATOR_AGENT)
        assert "allVerified" in content, (
            "claim-validator-agent must return allVerified in its result"
        )

    def test_claim_validator_agent_references_false_claims(self):
        """Plan path: claimValidation.some-false — agent must return falseClaims field."""
        content = read_file(CLAIM_VALIDATOR_AGENT)
        assert "falseClaims" in content, (
            "claim-validator-agent must return falseClaims for the orchestrator to feed back"
        )

    def test_claim_validator_agent_handles_doc_not_found(self):
        """Plan path: claimValidation.doc-not-found — agent must handle missing file."""
        content = read_file(CLAIM_VALIDATOR_AGENT)
        assert "not found" in content.lower() or "does not exist" in content.lower(), (
            "claim-validator-agent must handle the case where docPath does not exist"
        )
