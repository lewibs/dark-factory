#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from typing import Dict, List, Optional, Tuple


def run_command(command: List[str], check: bool = True) -> str:
    """Runs a command and returns its stdout."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=check)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(command)}: {e.stderr}", file=sys.stderr)
        if check:
            raise
        return ""


def get_jj_graph() -> List[Dict]:
    """Retrieves the jj commit graph for bookmarks."""
    # Construct a JJ template to output the commit graph as JSON.
    # The template builds a JSON object for each revision:
    # { "id": "<change-id>", "bookmarks": ["<name>", ...], "parents": ["<parent-change-id>", ...] }
    template = (
        r'"{\"id\":\"" ++ change_id ++ "\", \"bookmarks\": [" ++ bookmarks.map(|b| "\"" ++ b ++ "\"").join(",") ++ "], \"parents\": [" ++ parents.map(|p| "\"" ++ p.change_id() ++ "\"").join(",") ++ "]}"'
        + "\n"
    )

    # Query the graph for all revisions reachable by bookmarks.
    # This assumes the stack structure is fully bookmarked (common for stacked PRs).

    output = run_command(
        ["jj", "log", "-r", "bookmarks()", "-T", template, "--no-graph"]
    )

    nodes = []
    for line in output.splitlines():
        if line.strip():
            try:
                nodes.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"Failed to parse line: {line}", file=sys.stderr)
    return nodes


def get_node_by_id(nodes: List[Dict], change_id: str) -> Optional[Dict]:
    """Finds a node in the graph by its change_id."""
    for node in nodes:
        if node["id"] == change_id:
            return node
    return None


def find_parent_bookmark(
    current_node: Dict, all_node_map: Dict[str, Dict]
) -> Optional[str]:
    """
    Finds the nearest parent bookmark for a given node.

    This implementation looks at the immediate parent commit. If the parent
    revision has a bookmark, it is returned as the parent bookmark.
    """
    # Iterate through parents to find one that exists in our bookmarked node map.
    for parent_id in current_node["parents"]:
        if parent_id in all_node_map:
            parent_node = all_node_map[parent_id]
            # Return the first bookmark name found on the parent node.
            # JJ 0.37+ bookmarks are simple strings.
            if parent_node["bookmarks"]:
                return parent_node["bookmarks"][0]

        # Note: Intermediate non-bookmarked commits are skipped in this view.
        # A robust solution would require full graph traversal, but this suffices
        # for standard stacked PR workflows where every step is bookmarked.

    return None


def get_pr_info(bookmark_name: str) -> Optional[str]:
    """
    Checks if there is an open PR for the branch/bookmark.
    Returns the current base branch of the PR if found.
    """
    # gh pr view <branch> --json baseRefName
    try:
        output = run_command(
            ["gh", "pr", "view", bookmark_name, "--json", "baseRefName"], check=False
        )
        if output:
            data = json.loads(output)
            return data.get("baseRefName")
    except (ValueError, FileNotFoundError):
        pass
    return None


def update_pr_base(bookmark_name: str, new_base: str, dry_run: bool = False):
    """Updates the PR base branch."""
    print(f"Updating PR for '{bookmark_name}' to base '{new_base}'...")
    if not dry_run:
        run_command(["gh", "pr", "edit", bookmark_name, "--base", new_base])
        print(f"✅ Updated '{bookmark_name}' base to '{new_base}'")
    else:
        print(f"[Dry Run] Would run: gh pr edit {bookmark_name} --base {new_base}")


def main():
    parser = argparse.ArgumentParser(
        description="Retarget stacked PRs in GitHub based on jj bookmarks."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print actions without executing them."
    )
    args = parser.parse_args()

    print("Fetching jj graph...")
    # Assume the user has a linear stack of bookmarks (e.g., Main -> FeatA -> FeatB).
    # FeatB's parent is FeatA; FeatA's parent is Main.

    nodes = get_jj_graph()
    node_map = {n["id"]: n for n in nodes}

    print(f"Found {len(nodes)} bookmarked revisions.")

    for node in nodes:
        bookmarks = node["bookmarks"]
        if not bookmarks:
            continue

        current_bookmark = bookmarks[0]  # Handle first bookmark for now

        # Determine intended base
        parent_bookmark = find_parent_bookmark(node, node_map)

        if not parent_bookmark:
            # If no parent bookmark found, it likely sits on main or something un-bookmarked.
            # We skip.
            continue

        # Check current PR status
        current_base = get_pr_info(current_bookmark)
        if not current_base:
            # No open PR or failed to fetch
            # Quietly skip if no PR
            continue

        if current_base == parent_bookmark:
            continue

        # Update
        print(
            f"PR for '{current_bookmark}' targets '{current_base}', but should target '{parent_bookmark}'"
        )
        update_pr_base(current_bookmark, parent_bookmark, args.dry_run)


if __name__ == "__main__":
    main()
