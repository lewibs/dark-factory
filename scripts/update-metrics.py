#!/usr/bin/env python3
"""
update-metrics.py

Reads the metrics section from brain.json and upserts rows into a persistent
CSV at csv_path. Recomputes avg_runtime and avg_tokens from stored sums.

CLI args:
  --csv   <path>   Absolute path to the metrics CSV file (created if absent).
  --brain <path>   Absolute path to brain.json.

Non-fatal: any error is logged to stderr and the script exits 0 so that a
metrics failure never blocks a manufacture run.
"""

import argparse
import csv
import json
import os
import sys

CSV_FIELDNAMES = [
    "agent",
    "skill",
    "avg_runtime",
    "avg_tokens",
    "runs",
    "sum_runtime",
    "sum_tokens",
]


def read_csv(csv_path):
    """Return list of row dicts; empty list if file does not exist."""
    if not os.path.exists(csv_path):
        return []
    rows = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rows.append(
                    {
                        "agent": row.get("agent", ""),
                        "skill": row.get("skill", ""),
                        "avg_runtime": float(row.get("avg_runtime", 0) or 0),
                        "avg_tokens": float(row.get("avg_tokens", 0) or 0),
                        "runs": int(row.get("runs", 0) or 0),
                        "sum_runtime": float(row.get("sum_runtime", 0) or 0),
                        "sum_tokens": float(row.get("sum_tokens", 0) or 0),
                    }
                )
            except (ValueError, TypeError) as e:
                print(f"update-metrics | warning | skipping malformed CSV row: {e}", file=sys.stderr)
    return rows


def write_csv(csv_path, rows):
    """Write rows to csv_path, creating parent dirs if needed."""
    parent_dir = os.path.dirname(os.path.abspath(csv_path))
    os.makedirs(parent_dir, exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def find_row(rows, agent, skill):
    for row in rows:
        if row["agent"] == agent and row["skill"] == skill:
            return row
    return None


def upsert(rows, agent, skill, elapsed_ms, tokens, runs):
    existing = find_row(rows, agent, skill)
    if existing:
        existing["sum_runtime"] += elapsed_ms
        existing["sum_tokens"] += tokens
        existing["runs"] += runs
    else:
        rows.append(
            {
                "agent": agent,
                "skill": skill,
                "sum_runtime": elapsed_ms,
                "sum_tokens": tokens,
                "runs": runs,
                "avg_runtime": 0.0,
                "avg_tokens": 0.0,
            }
        )
    # Recompute averages for all rows after each upsert
    for row in rows:
        if row["runs"] > 0:
            row["avg_runtime"] = row["sum_runtime"] / row["runs"]
            row["avg_tokens"] = row["sum_tokens"] / row["runs"]


def main():
    parser = argparse.ArgumentParser(description="Flush brain.json metrics into a CSV.")
    parser.add_argument("--csv", required=True, help="Absolute path to the metrics CSV file.")
    parser.add_argument("--brain", required=True, help="Absolute path to brain.json.")
    args = parser.parse_args()

    try:
        with open(args.brain) as f:
            brain = json.load(f)
    except Exception as e:
        print(f"update-metrics | error | cannot read brain.json: {e}", file=sys.stderr)
        sys.exit(0)

    metrics = brain.get("metrics", {})
    if not metrics:
        print("update-metrics | flush | no metrics in brain.json, skipping", file=sys.stderr)
        sys.exit(0)

    try:
        rows = read_csv(args.csv)
    except Exception as e:
        print(f"update-metrics | error | cannot read CSV: {e}", file=sys.stderr)
        sys.exit(0)

    for key, data in metrics.items():
        # Key format: "agent/skill" or just "agent" (skill defaults to empty string)
        if "/" in key:
            agent, skill = key.split("/", 1)
        else:
            agent = key
            skill = ""

        elapsed_ms = float(data.get("elapsed_ms", 0))
        tokens = float(data.get("tokens", 0))
        runs = int(data.get("runs", 1))

        upsert(rows, agent, skill, elapsed_ms, tokens, runs)

    try:
        write_csv(args.csv, rows)
    except Exception as e:
        print(f"update-metrics | error | cannot write CSV: {e}", file=sys.stderr)
        sys.exit(0)

    print(
        f"update-metrics | flush | rows={len(rows)} csv={args.csv}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
