import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add scripts directory to path to import the script module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))


class TestFixBranchName(unittest.TestCase):
    """Tests for fix_branch_name.py - written BEFORE implementation (TDD)."""

    # ========== is_push_branch tests ==========

    def test_is_push_branch_positive_standard(self):
        """Should detect standard jj push-xxxx pattern (12 lowercase letters)."""
        import fix_branch_name

        self.assertTrue(fix_branch_name.is_push_branch("push-nlwynnupppzk"))
        self.assertTrue(fix_branch_name.is_push_branch("push-wrkkkvknltwt"))
        self.assertTrue(fix_branch_name.is_push_branch("push-ukkxmqporkkk"))

    def test_is_push_branch_negative_normal_names(self):
        """Should reject normal branch names."""
        import fix_branch_name

        self.assertFalse(fix_branch_name.is_push_branch("feat/user-auth"))
        self.assertFalse(fix_branch_name.is_push_branch("fix/null-token"))
        self.assertFalse(fix_branch_name.is_push_branch("main"))
        self.assertFalse(fix_branch_name.is_push_branch("master"))
        self.assertFalse(fix_branch_name.is_push_branch("stack-1"))

    def test_is_push_branch_negative_similar_patterns(self):
        """Should reject patterns that look similar but aren't jj-generated."""
        import fix_branch_name

        self.assertFalse(fix_branch_name.is_push_branch("push-abc"))  # Too short
        self.assertFalse(
            fix_branch_name.is_push_branch("push-ABCDEFGHIJKL")
        )  # Uppercase
        self.assertFalse(fix_branch_name.is_push_branch("push-123456789012"))  # Numbers
        self.assertFalse(fix_branch_name.is_push_branch("push-abcdef12ghij"))  # Mixed

    # ========== parse_commit_description tests ==========

    def test_parse_commit_description_conventional_commit(self):
        """Should extract prefix and title from conventional commits."""
        import fix_branch_name

        prefix, title = fix_branch_name.parse_commit_description("feat: Add user login")
        self.assertEqual(prefix, "feat")
        self.assertEqual(title, "Add user login")

        prefix, title = fix_branch_name.parse_commit_description(
            "fix(auth): handle null token"
        )
        self.assertEqual(prefix, "fix")
        self.assertEqual(title, "handle null token")

        prefix, title = fix_branch_name.parse_commit_description("docs: update README")
        self.assertEqual(prefix, "docs")
        self.assertEqual(title, "update README")

    def test_parse_commit_description_with_scope(self):
        """Should handle scoped conventional commits."""
        import fix_branch_name

        prefix, title = fix_branch_name.parse_commit_description(
            "feat(api): add new endpoint"
        )
        self.assertEqual(prefix, "feat")
        self.assertEqual(title, "add new endpoint")

        prefix, title = fix_branch_name.parse_commit_description(
            "chore(deps): bump version"
        )
        self.assertEqual(prefix, "chore")
        self.assertEqual(title, "bump version")

    def test_parse_commit_description_no_prefix(self):
        """Should default to 'feat' for non-conventional commits."""
        import fix_branch_name

        prefix, title = fix_branch_name.parse_commit_description(
            "Add user login feature"
        )
        self.assertEqual(prefix, "feat")
        self.assertEqual(title, "Add user login feature")

    def test_parse_commit_description_empty(self):
        """Should handle empty descriptions."""
        import fix_branch_name

        prefix, title = fix_branch_name.parse_commit_description("")
        self.assertEqual(prefix, "feat")
        self.assertEqual(title, "untitled")

    # ========== slugify_title tests ==========

    def test_slugify_title_basic(self):
        """Should convert title to URL-safe slug."""
        import fix_branch_name

        self.assertEqual(
            fix_branch_name.slugify_title("Add user login"), "add-user-login"
        )
        self.assertEqual(
            fix_branch_name.slugify_title("Handle NULL Token"), "handle-null-token"
        )

    def test_slugify_title_special_chars(self):
        """Should remove special characters."""
        import fix_branch_name

        self.assertEqual(fix_branch_name.slugify_title("feat: add API"), "add-api")
        self.assertEqual(
            fix_branch_name.slugify_title("fix(auth): handle error!"), "handle-error"
        )

    def test_slugify_title_truncate(self):
        """Should truncate long slugs."""
        import fix_branch_name

        long_title = (
            "This is a very long title that should be truncated to a reasonable length"
        )
        slug = fix_branch_name.slugify_title(long_title)
        self.assertLessEqual(len(slug), 40)  # Max length limit

    # ========== get_stack_position tests ==========

    def test_get_stack_position_single_commit(self):
        """Should return (1, 1) for non-stacked commits."""
        import fix_branch_name

        # Mock jj output for single commit (no parents with bookmarks)
        with patch.object(fix_branch_name, "run_command") as mock_run:
            # Single commit with no bookmarked ancestors
            mock_run.return_value = (
                '{"id":"abc123","bookmarks":["push-nlwynnupppzk"],"parents":["root"]}'
            )
            position, total = fix_branch_name.get_stack_position("push-nlwynnupppzk")
            self.assertEqual(position, 1)
            self.assertEqual(total, 1)

    def test_get_stack_position_middle_of_stack(self):
        """Should return correct position in a stack."""
        import fix_branch_name

        with patch.object(fix_branch_name, "get_stack_info") as mock_stack:
            # 3rd commit in a stack of 5
            mock_stack.return_value = (3, 5)
            position, total = fix_branch_name.get_stack_position("stack-3")
            self.assertEqual(position, 3)
            self.assertEqual(total, 5)

    # ========== generate_branch_name tests ==========

    def test_generate_branch_name_no_stack(self):
        """Should generate simple branch name for non-stacked commits."""
        import fix_branch_name

        name = fix_branch_name.generate_branch_name("feat", "user-auth", 1, 1)
        self.assertEqual(name, "feat/user-auth")

    def test_generate_branch_name_with_stack(self):
        """Should include position for stacked commits."""
        import fix_branch_name

        name = fix_branch_name.generate_branch_name("feat", "s3-upload", 3, 5)
        self.assertEqual(name, "feat/s3-upload-3")

    def test_generate_branch_name_sanitizes_prefix(self):
        """Should handle non-standard prefixes."""
        import fix_branch_name

        name = fix_branch_name.generate_branch_name("FEAT", "test", 1, 1)
        self.assertEqual(name, "feat/test")

    # ========== generate_pr_title tests ==========

    def test_generate_pr_title_no_stack(self):
        """Should generate PR title with topic for non-stacked commits."""
        import fix_branch_name

        title = fix_branch_name.generate_pr_title(
            "feat", "Add user login", "user-auth", 1, 1
        )
        self.assertEqual(title, "feat: [user-auth] Add user login")

    def test_generate_pr_title_with_stack(self):
        """Should include topic and position for stacked PRs."""
        import fix_branch_name

        title = fix_branch_name.generate_pr_title(
            "feat", "Added implementation for s3 MPU start", "raw-memory-upload", 4, 5
        )
        self.assertEqual(
            title,
            "feat: [raw-memory-upload][4/5] Added implementation for s3 MPU start",
        )


class TestFixBranchNameIntegration(unittest.TestCase):
    """Integration tests for the main flow."""

    @patch("fix_branch_name.run_command")
    @patch("builtins.print")
    def test_main_detects_and_renames(self, mock_print, mock_run):
        """Main flow should detect push-xxx and offer to rename."""
        import fix_branch_name

        def side_effect(cmd, check=True):
            if cmd[0] == "jj" and "log" in cmd:
                return '{"id":"abc","bookmarks":["push-nlwynnupppzk"],"description":"feat: Add user login","parents":["root"]}'
            if cmd[0] == "jj" and "bookmark" in cmd and "rename" in cmd:
                return ""
            return ""

        mock_run.side_effect = side_effect

        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = MagicMock(
                dry_run=True, bookmark=None, json=False, output=None
            )
            # Should not raise
            fix_branch_name.main()

    @patch("fix_branch_name.run_command")
    def test_main_skips_good_branches(self, mock_run):
        """Should skip already well-named branches."""
        import fix_branch_name

        mock_run.return_value = '{"id":"abc","bookmarks":["feat/user-auth"],"description":"feat: Add user login","parents":["root"]}'

        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = MagicMock(
                dry_run=True, bookmark=None, json=False, output=None
            )
            # Should not raise and should not attempt rename
            fix_branch_name.main()
            # Verify no rename was attempted
            rename_calls = [c for c in mock_run.call_args_list if "rename" in str(c)]
            self.assertEqual(len(rename_calls), 0)


class TestJsonOutput(unittest.TestCase):
    """Tests for JSON output mode."""

    @patch("fix_branch_name.run_command")
    @patch("fix_branch_name.get_stack_info")
    def test_json_output_includes_all_fields(self, mock_stack, mock_run):
        """JSON output should include branch, title, and topic."""
        import fix_branch_name

        mock_run.return_value = '{"id":"abc","bookmarks":["push-nlwynnupppzk"],"description":"feat: Add user login","parents":["root"]}'
        mock_stack.return_value = (1, 1)

        result = fix_branch_name.generate_pr_info("push-nlwynnupppzk")

        self.assertIn("branch", result)
        self.assertIn("title", result)
        self.assertIn("topic", result)
        self.assertEqual(result["branch"], "feat/add-user-login")
        self.assertEqual(result["title"], "feat: [add-user-login] Add user login")

    def test_output_to_file_writes_json(self):
        """Should write JSON to file when --output flag provided."""
        import json
        import tempfile

        import fix_branch_name

        test_data = {
            "branch": "feat/test",
            "title": "feat: [test] Test",
            "topic": "test",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            fix_branch_name.write_pr_info_to_file(test_data, temp_path)

            with open(temp_path, "r") as f:
                loaded = json.load(f)

            self.assertEqual(loaded["branch"], "feat/test")
            self.assertEqual(loaded["title"], "feat: [test] Test")
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()
