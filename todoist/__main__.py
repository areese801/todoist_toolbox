"""
CLI entry point for the todoist toolbox.

Usage:
    python -m todoist <recipe> [options]

Recipes:
    complete-overdue-recurring         Close overdue recurring tasks (dry-run by default)
    reschedule-overdue-nonrecurring    Reschedule overdue non-recurring tasks to today (dry-run by default)
    label-by-color                     Apply a label to all tasks under projects of a given color
    reschedule-work-to-monday          Reschedule overdue work tasks to next Monday (Friday evening)
    schedule-undated                   Apply a due date to undated tasks (dry-run by default)
"""

import argparse
import sys

from todoist_api_python.api import TodoistAPI
from todoist.todoist_tasks import _get_api_token
from todoist.recipes import complete_overdue_recurring
from todoist.recipes import reschedule_overdue_nonrecurring
from todoist.recipes import label_by_color
from todoist.recipes import reschedule_work_to_monday
from todoist.recipes import schedule_undated


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

    # label-by-color
    lbc_parser = subparsers.add_parser(
        "label-by-color",
        help="Apply a label to all tasks under projects of a given color.",
    )
    lbc_parser.add_argument(
        "--color",
        default=None,
        help="Project color to match (e.g., sky_blue). Falls back to TODOIST_LABEL_COLOR env var.",
    )
    lbc_parser.add_argument(
        "--label",
        default=None,
        help="Label name to apply (e.g., work). Falls back to TODOIST_LABEL_NAME env var.",
    )
    lbc_parser.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="Actually apply labels. Without this flag, only a dry-run is performed.",
    )
    lbc_parser.set_defaults(func=label_by_color.run)

    # reschedule-work-to-monday
    rwm_parser = subparsers.add_parser(
        "reschedule-work-to-monday",
        help="Reschedule overdue work tasks to next Monday (designed for Friday evening).",
    )
    rwm_parser.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="Actually reschedule tasks. Without this flag, only a dry-run is performed.",
    )
    rwm_parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Bypass the day/time check (normally only runs Friday evening or weekends).",
    )
    rwm_parser.set_defaults(func=reschedule_work_to_monday.run)

    # schedule-undated
    su_parser = subparsers.add_parser(
        "schedule-undated",
        help="Apply a due date to undated tasks (tomorrow, or next Monday if tomorrow is a weekend).",
    )
    su_parser.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="Actually apply due dates. Without this flag, only a dry-run is performed.",
    )
    su_parser.set_defaults(func=schedule_undated.run)

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
