#!/usr/bin/env python3
"""
Metrics command: Display ranked list of slowest and most token-intensive agents/skills
"""

import csv
import os
import sys
from pathlib import Path
from typing import List, Tuple

def read_metrics_csv(csv_path: str) -> List[dict]:
    """Read and parse metrics.csv file."""
    rows = []
    try:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Skip rows with zero values for both metrics
                avg_runtime = float(row.get('avg_runtime', 0))
                avg_tokens = float(row.get('avg_tokens', 0))
                
                if avg_runtime == 0.0 and avg_tokens == 0.0:
                    continue
                
                rows.append({
                    'name': row.get('agent', row.get('skill', 'Unknown')).strip() or 'Unknown',
                    'avg_runtime': avg_runtime,
                    'avg_tokens': avg_tokens,
                    'runs': int(row.get('runs', 0)),
                    'sum_runtime': float(row.get('sum_runtime', 0)),
                    'sum_tokens': float(row.get('sum_tokens', 0)),
                })
    except FileNotFoundError:
        print(f"Error: metrics.csv not found at {csv_path}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Error reading metrics.csv: {e}", file=sys.stderr)
        return []
    
    return rows

def format_table(headers: List[str], rows: List[Tuple], col_widths: List[int]) -> str:
    """Format data as a simple ASCII table."""
    lines = []
    
    # Header
    header_line = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    lines.append(header_line)
    lines.append("-" * len(header_line))
    
    # Rows
    for row in rows:
        row_line = " | ".join(str(v).ljust(w) for v, w in zip(row, col_widths))
        lines.append(row_line)
    
    return "\n".join(lines)

def main():
    """Main entry point."""
    # Find project root (metrics.csv should be there)
    # Start from current directory and work up
    current = Path.cwd()
    metrics_csv = None
    
    # Try common locations
    for attempt in [current, current.parent, Path.home() / "github" / "dark_factory" / "dark_factory"]:
        candidate = attempt / "metrics.csv"
        if candidate.exists():
            metrics_csv = candidate
            break
    
    if not metrics_csv:
        # Fallback to env var or current dir
        metrics_csv = Path(os.environ.get('DARK_FACTORY_METRICS_CSV', 'metrics.csv'))
    
    # Read metrics
    rows = read_metrics_csv(str(metrics_csv))
    
    if not rows:
        print("No metrics data available.")
        return
    
    # Sort by runtime (slowest first)
    slowest = sorted(rows, key=lambda r: r['avg_runtime'], reverse=True)
    
    # Sort by tokens (highest first)
    most_tokens = sorted(rows, key=lambda r: r['avg_tokens'], reverse=True)
    
    # Display slowest
    print("\n=== SLOWEST AGENTS/SKILLS (by avg_runtime) ===\n")
    headers = ["Agent/Skill", "Avg Runtime (ms)", "Avg Tokens", "Runs", "Total Runtime (ms)", "Total Tokens"]
    col_widths = [40, 18, 12, 6, 18, 14]
    
    slowest_rows = [
        (
            row['name'][:39],
            f"{row['avg_runtime']:.0f}",
            f"{row['avg_tokens']:.1f}",
            str(row['runs']),
            f"{row['sum_runtime']:.0f}",
            f"{row['sum_tokens']:.0f}",
        )
        for row in slowest[:15]  # Top 15
    ]
    
    print(format_table(headers, slowest_rows, col_widths))
    
    # Display most tokens
    print("\n\n=== HIGHEST TOKEN USAGE (by avg_tokens) ===\n")
    most_tokens_rows = [
        (
            row['name'][:39],
            f"{row['avg_runtime']:.0f}",
            f"{row['avg_tokens']:.1f}",
            str(row['runs']),
            f"{row['sum_runtime']:.0f}",
            f"{row['sum_tokens']:.0f}",
        )
        for row in most_tokens[:15]  # Top 15
    ]
    
    print(format_table(headers, most_tokens_rows, col_widths))
    print()

if __name__ == '__main__':
    main()
