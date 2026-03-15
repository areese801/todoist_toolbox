"""
CLI entry point for the todoist toolbox.

Usage:
    python -m todoist <recipe> [options]

Recipes:
    complete-overdue-recurring         Close overdue recurring tasks (dry-run by default)
    reschedule-overdue-nonrecurring    Reschedule overdue non-recurring tasks to today (dry-run by default)
"""
import argparse
import sys

from todoist_api_python.api import TodoistAPI
from todoist.todoist_tasks import _get_api_token
from todoist.recipes import complete_overdue_recurring
from todoist.recipes import reschedule_overdue_nonrecurring


def build_parser() -> argparse.ArgumentParser:
    """
    Build and return the argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="python -m todoist",
        description="Todoist toolbox — CLI recipes for bulk task management.",
    )
    subparsers = parser.add_subparsers(dest="recipe", required=True)

    # complete-overdue-recurring
    co_parser = subparsers.add_parser(
        "complete-overdue-recurring",
        help="Close overdue recurring tasks that recur every 7 days or fewer.",
    )
    co_parser.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="Actually close tasks. Without this flag, only a dry-run is performed.",
    )
    co_parser.add_argument(
        "--clear-cache",
        action="store_true",
        default=False,
        help="Clear the cached recurrence intervals before running.",
    )
    co_parser.set_defaults(func=complete_overdue_recurring.run)

    # reschedule-overdue-nonrecurring
    ro_parser = subparsers.add_parser(
        "reschedule-overdue-nonrecurring",
        help="Reschedule overdue non-recurring tasks to today.",
    )
    ro_parser.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="Actually reschedule tasks. Without this flag, only a dry-run is performed.",
    )
    ro_parser.set_defaults(func=reschedule_overdue_nonrecurring.run)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    # Create a shared API instance
    token = _get_api_token()
    api = TodoistAPI(token)

    args.func(args, api=api)


if __name__ == "__main__":
    main()
