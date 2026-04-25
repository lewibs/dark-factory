import json
import os
import sys
import unittest
from unittest.mock import patch

# Add scripts directory to path to import the script module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))
import fix_stacked_prs


class TestFixStackedPRs(unittest.TestCase):

    def setUp(self):
        self.mock_nodes = [
            {"id": "commit3", "bookmarks": ["stack-3"], "parents": ["commit2"]},
            {"id": "commit2", "bookmarks": ["stack-2"], "parents": ["commit1"]},
            {"id": "commit1", "bookmarks": ["stack-1"], "parents": ["root"]},
            {"id": "root", "bookmarks": ["main"], "parents": []},
        ]
        self.node_map = {n["id"]: n for n in self.mock_nodes}

    def test_find_parent_bookmark_success(self):
        # stack-3 parent is stack-2
        current = self.node_map["commit3"]
        parent = fix_stacked_prs.find_parent_bookmark(current, self.node_map)
        self.assertEqual(parent, "stack-2")

        # stack-2 parent is stack-1
        current = self.node_map["commit2"]
        parent = fix_stacked_prs.find_parent_bookmark(current, self.node_map)
        self.assertEqual(parent, "stack-1")

    def test_find_parent_bookmark_root(self):
        # stack-1 parent is main
        current = self.node_map["commit1"]
        parent = fix_stacked_prs.find_parent_bookmark(current, self.node_map)
        self.assertEqual(parent, "main")

    def test_find_parent_bookmark_orphaned(self):
        # commit with unknown parent
        orphan_node = {"id": "orphan", "bookmarks": ["orphan"], "parents": ["unknown"]}
        parent = fix_stacked_prs.find_parent_bookmark(orphan_node, self.node_map)
        self.assertIsNone(parent)

    @patch("fix_stacked_prs.run_command")
    def test_get_pr_info_success(self, mock_run):
        mock_run.return_value = '{"baseRefName": "main"}'
        base = fix_stacked_prs.get_pr_info("stack-2")
        self.assertEqual(base, "main")
        mock_run.assert_called_with(
            ["gh", "pr", "view", "stack-2", "--json", "baseRefName"], check=False
        )

    @patch("fix_stacked_prs.run_command")
    def test_get_pr_info_failure(self, mock_run):
        mock_run.side_effect = FileNotFoundError("GH CLI not found")
        base = fix_stacked_prs.get_pr_info("stack-2")
        self.assertIsNone(base)

    @patch("fix_stacked_prs.run_command")
    @patch("builtins.print")
    def test_main_flow_update_needed(self, mock_print, mock_run):
        # Setup mocks
        # 1. get_jj_graph -> returns JSON lines
        jj_output = "\n".join([json.dumps(n) for n in self.mock_nodes])

        # 2. Mock PR info calls.
        # Sequence:
        # - jj log ... (returns jj_output)
        # - gh pr view stack-3 (returns main -> Incorrect, update needed)
        # - gh pr edit stack-3 ...
        # - gh pr view stack-2 (returns stack-1 -> Correct)
        # - gh pr view stack-1 (returns main -> Correct)
        # - gh pr view main (returns None)

        def side_effect(cmd, check=True):
            if cmd[0] == "jj":
                return jj_output
            if cmd[0] == "gh":
                if "view" in cmd:
                    bookmark = cmd[3]
                    if bookmark == "stack-3":
                        return '{"baseRefName": "main"}'  # Requires update to stack-2
                    if bookmark == "stack-2":
                        return '{"baseRefName": "stack-1"}'  # Correct
                    if bookmark == "stack-1":
                        return '{"baseRefName": "main"}'  # Correct
                    return ""
                if "edit" in cmd:
                    return "Updated"
            return ""

        mock_run.side_effect = side_effect

        # Run main
        # We need to patch argparse to avoid reading sys.argv
        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value.dry_run = False
            fix_stacked_prs.main()

        # Verify stack-3 was updated
        mock_run.assert_any_call(["gh", "pr", "edit", "stack-3", "--base", "stack-2"])

        # Verify stack-2 was NOT updated (already correct)
        call_args_list = mock_run.call_args_list
        edit_calls = [
            c for c in call_args_list if "gh" in c[0][0] and "edit" in c[0][0]
        ]
        self.assertEqual(len(edit_calls), 1)
        self.assertEqual(edit_calls[0][0][0][3], "stack-3")


if __name__ == "__main__":
    unittest.main()
