"""Tests for the CLI entry point (__main__.py)."""
import sys
from unittest.mock import patch, MagicMock


class TestCLIEntryPoint:
    """Tests for python -m todoist CLI dispatch."""

    def test_complete_overdue_recurring_subcommand_dispatches(self):
        """'complete-overdue-recurring' subcommand should parse and default to dry-run."""
        from todoist.__main__ import build_parser

        parser = build_parser()
        args = parser.parse_args(["complete-overdue-recurring"])

        assert args.execute is False  # default is dry-run
        assert hasattr(args, "func")

    def test_complete_overdue_recurring_with_execute_flag(self):
        """--execute flag should set args.execute=True."""
        from todoist.__main__ import build_parser

        parser = build_parser()
        args = parser.parse_args(["complete-overdue-recurring", "--execute"])

        assert args.execute is True

    def test_complete_overdue_recurring_clear_cache_flag(self):
        """--clear-cache flag should set args.clear_cache=True."""
        from todoist.__main__ import build_parser

        parser = build_parser()
        args = parser.parse_args(["complete-overdue-recurring", "--clear-cache"])

        assert args.clear_cache is True

    def test_complete_overdue_recurring_clear_cache_default(self):
        """--clear-cache should default to False."""
        from todoist.__main__ import build_parser

        parser = build_parser()
        args = parser.parse_args(["complete-overdue-recurring"])

        assert args.clear_cache is False

    def test_reschedule_overdue_nonrecurring_subcommand_dispatches(self):
        """'reschedule-overdue-nonrecurring' subcommand should parse and default to dry-run."""
        from todoist.__main__ import build_parser

        parser = build_parser()
        args = parser.parse_args(["reschedule-overdue-nonrecurring"])

        assert args.execute is False
        assert hasattr(args, "func")

    def test_reschedule_overdue_nonrecurring_with_execute_flag(self):
        """--execute flag should set args.execute=True."""
        from todoist.__main__ import build_parser

        parser = build_parser()
        args = parser.parse_args(["reschedule-overdue-nonrecurring", "--execute"])

        assert args.execute is True

    def test_no_subcommand_exits_with_error(self):
        """Running with no subcommand should exit with a SystemExit."""
        from todoist.__main__ import build_parser

        parser = build_parser()
        try:
            args = parser.parse_args([])
            # If parse succeeds with required=True, this won't be reached
            assert False, "Should have raised SystemExit"
        except SystemExit:
            pass  # Expected: argparse exits when required subcommand missing
