"""
Tests for render_section.py.

Tests the renderTable and passthroughContent flows.
"""

import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import pytest
from render_section import (
    render_markdown_to_ascii,
    render_table,
    parse_pipe_row,
    is_separator_row,
    is_in_code_fence,
)


class TestRenderTable:
    """Tests for renderTable flow."""

    def test_renderTable_markdown(self):
        """Test rendering a standard markdown table with header and data rows."""
        # Plan path: renderTable.markdown
        # Detects contiguous rows, skips separator rows, computes column widths, renders table with borders
        input_content = """| name | value |
| --- | --- |
| foo | 123 |
| bar | 456 |"""
        result = render_markdown_to_ascii(input_content)
        # Should have ASCII table with borders
        assert '+-' in result
        assert '| name' in result
        assert '| foo' in result
        assert '| bar' in result

    def test_renderTable_singleRow(self):
        """Test rendering a table with only a header row."""
        # Plan path: renderTable.singleRow
        # Even with no data rows, renders table structure with borders
        input_content = "| col1 | col2 |"
        result = render_markdown_to_ascii(input_content)
        # Should have ASCII table with borders even for single row
        assert '+-' in result
        assert '| col1' in result


class TestPassthroughContent:
    """Tests for passthroughContent flow."""

    def test_passthroughContent_text(self):
        """Test that non-table lines pass through unchanged."""
        # Plan path: passthroughContent.text
        # Non-table lines pass through unchanged
        input_content = """# Header

Some plain text here.

More content."""
        result = render_markdown_to_ascii(input_content)
        assert "# Header" in result
        assert "Some plain text here." in result
        assert "More content." in result

    def test_passthroughContent_codeBlock(self):
        """Test that content inside code fences never treated as tables."""
        # Plan path: passthroughContent.codeBlock
        # Content inside code fences never treated as tables, passes through unchanged
        input_content = """```
| this | is | not | a | table |
```

| this | is | a | table |
| --- | --- | --- | --- |
| foo | bar | baz | qux |"""
        result = render_markdown_to_ascii(input_content)
        # The pipe content in code fence should be unchanged
        assert "| this | is | not | a | table |" in result
        # The actual table should be rendered
        assert '+-' in result
