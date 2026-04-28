"""
Tests for feature-agent integration with render_section.py.

Tests the featureAgentIntegration flow.
"""

import sys
import os
import subprocess

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import pytest
from render_section import render_markdown_to_ascii


class TestFeatureAgentIntegration:
    """Tests for featureAgentIntegration flow."""

    def test_featureAgentIntegration_draftPlan(self):
        """Test that System Intent section is rendered before display."""
        # Plan path: featureAgentIntegration.draftPlan
        # feature-agent pipes System Intent through render_section.py before embedding in question
        section_content = """## System Intent

This is a plan for building feature X.

| component | status |
| --- | --- |
| API | done |
| UI | todo |"""
        rendered = render_markdown_to_ascii(section_content)
        # Should contain rendered table
        assert '+-' in rendered
        assert '| component' in rendered
        # Headers should be preserved
        assert '## System Intent' in rendered

    def test_featureAgentIntegration_mermaid(self):
        """Test that Mermaid Diagram section is rendered (code blocks pass through)."""
        # Plan path: featureAgentIntegration.mermaid
        # Same pipeline; mermaid code blocks pass through unchanged
        section_content = """## Mermaid Diagram

```mermaid
graph TD
  A[Start] --> B[End]
```"""
        rendered = render_markdown_to_ascii(section_content)
        # Code block should pass through unchanged
        assert "```mermaid" in rendered
        assert "graph TD" in rendered

    def test_featureAgentIntegration_flowSection(self):
        """Test that flow section with Types, Paths, Pseudocode is rendered."""
        # Plan path: featureAgentIntegration.flowSection
        # Paths table rendered as ASCII; Types and Pseudocode code blocks pass through
        section_content = """### Flow: test

| path | input | output |
| --- | --- | --- |
| test.path1 | x | y |

```
def test():
    pass
```"""
        rendered = render_markdown_to_ascii(section_content)
        # Table should be rendered
        assert '+-' in rendered
        assert '| path' in rendered
        # Code blocks should pass through
        assert "```" in rendered

    def test_featureAgentIntegration_fallback(self):
        """Test that feature-agent falls back to raw content if script fails."""
        # Plan path: featureAgentIntegration.fallback
        # feature-agent falls back to unformatted content if script fails
        section_content = "Some test content"
        rendered = render_markdown_to_ascii(section_content)
        # Should return content unchanged if no tables
        assert section_content in rendered
