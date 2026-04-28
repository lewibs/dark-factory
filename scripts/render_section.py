#!/usr/bin/env python3
"""
Render markdown sections with ASCII table formatting.

Converts raw markdown with pipe-delimited tables into formatted ASCII tables
with proper column alignment and borders.
"""

import sys


def parse_pipe_row(row: str) -> list[str]:
    """
    Parse a pipe-delimited row into cells.

    TODO: renderTable flow
    """
    # Strip leading/trailing pipes and split
    row = row.strip()
    if row.startswith('|'):
        row = row[1:]
    if row.endswith('|'):
        row = row[:-1]
    # Split by pipe and strip whitespace from each cell
    cells = [cell.strip() for cell in row.split('|')]
    return cells


def is_separator_row(cells: list[str]) -> bool:
    """
    Check if a row is a markdown separator row (| --- | --- |).

    TODO: renderTable flow
    """
    # A separator row has all cells containing only dashes (and possibly colons for alignment)
    for cell in cells:
        stripped = cell.strip()
        if not stripped:
            continue
        # Check if it's all dashes, colons, or combinations
        if not all(c in '-:' for c in stripped):
            return False
    return True


def render_table(rows: list[str]) -> list[str]:
    """
    Render a markdown table to ASCII format with borders.

    Takes a list of pipe-delimited markdown rows and returns formatted ASCII
    table lines with padded columns and +-+- borders.

    TODO: renderTable flow
    """
    # Parse cells from each row
    cells = [parse_pipe_row(r) for r in rows]

    # Filter out separator rows (| --- | --- |)
    data_cells = [c for c in cells if not is_separator_row(c)]

    if not data_cells:
        return []

    # Compute column widths
    ncols = len(data_cells[0])
    widths = [max(len(row[i]) if i < len(row) else 0 for row in data_cells) for i in range(ncols)]

    # Render table
    result = []
    border = '+' + '+'.join('-' * (w + 2) for w in widths) + '+'
    result.append(border)

    for i, row in enumerate(data_cells):
        rendered_row = '| ' + ' | '.join(
            (row[j] if j < len(row) else '').ljust(widths[j]) for j in range(ncols)
        ) + ' |'
        result.append(rendered_row)

        if i == 0:  # After header
            result.append(border)

    result.append(border)
    return result


def is_in_code_fence(line_index: int, lines: list[str]) -> bool:
    """
    Determine if a line is inside a code fence (``` or ~~~).

    TODO: passthroughContent flow
    """
    in_fence = False
    for i in range(line_index):
        if lines[i].startswith('```') or lines[i].startswith('~~~'):
            in_fence = not in_fence
    return in_fence


def render_markdown_to_ascii(content: str) -> str:
    """
    Convert markdown content with pipe-delimited tables to ASCII formatted tables.

    Detects contiguous table rows, renders them with borders and proper column
    widths, and passes through non-table content unchanged. Content inside code
    fences is never treated as tables.

    Args:
        content: Raw markdown text (may contain pipe-delimited tables, code blocks, headers)

    Returns:
        Rendered text with ASCII tables replacing pipe-delimited markdown tables
        Other content (headers, code blocks, text) passes through unchanged

    TODO: renderTable flow, passthroughContent flow
    """
    lines = content.split('\n')
    result = []
    i = 0

    while i < len(lines):
        # Check if we're in a code fence
        if is_in_code_fence(i, lines):
            result.append(lines[i])
            i += 1
        elif lines[i].startswith('|') and not is_in_code_fence(i, lines):
            # Collect all contiguous table rows
            table_lines = []
            while i < len(lines) and lines[i].startswith('|') and not is_in_code_fence(i, lines):
                table_lines.append(lines[i])
                i += 1

            # Render table
            result.extend(render_table(table_lines))
        else:
            # Non-table content passes through
            result.append(lines[i])
            i += 1

    return '\n'.join(result)


def main():
    """
    Read markdown from stdin, render it, and write to stdout.

    Usage: python3 render_section.py < input.md > output.txt
    """
    content = sys.stdin.read()
    rendered = render_markdown_to_ascii(content)
    sys.stdout.write(rendered)


if __name__ == "__main__":
    main()
