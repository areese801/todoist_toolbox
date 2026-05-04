"""
Recipe: schedule-undated

Finds open tasks with no due date and assigns them a sensible default so they
surface in Today/Upcoming views. The chosen due date is tomorrow if tomorrow
is a weekday (Mon-Fri); otherwise the following Monday. The "now" reference
is computed in the project's configured timezone.

Tasks tagged with the configured no-due-date label (default: "_NoDueDate") or
the project-wide no-robots label (default: "_no_robots") are skipped.
"""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from todoist.config import get_config
from todoist.todoist_tasks import get_active_tasks, _task_link


def _now_in_tz(tz_name: str) -> datetime:
    """
    Return the current datetime in the given timezone.
    """
    return datetime.now(ZoneInfo(tz_name))


def _next_business_day(from_date: date) -> date:
    """
    Return the next business day strictly after from_date.

    Tomorrow if tomorrow is a weekday (Mon-Fri); otherwise the following
    Monday.
    """
    d = from_date + timedelta(days=1)
    if d.weekday() >= 5:  # Saturday (5) or Sunday (6)
        d += timedelta(days=7 - d.weekday())
    return d


def run(args, api=None):
    """
    Execute the schedule-undated recipe.

    Args:
        args: argparse.Namespace with an execute attribute.
        api: A TodoistAPI instance.
    """
    config = get_config()
    no_due_date_label = config["no_due_date_label"]
    no_robots_label = config["no_robots_label"]
    timezone = config["timezone"]

    target_date = _next_business_day(_now_in_tz(timezone).date())
    target_str = target_date.isoformat()

    print("Fetching open tasks with no due date...")

    all_tasks = get_active_tasks(api=api)

    undated = [t for t in all_tasks if t.due is None]

    skipped_no_due = [t for t in undated if no_due_date_label in t.labels]
    skipped_no_robots = [
        t
        for t in undated
        if no_robots_label in t.labels and no_due_date_label not in t.labels
    ]
    eligible = [
        t
        for t in undated
        if no_due_date_label not in t.labels and no_robots_label not in t.labels
    ]

    if skipped_no_due:
        print(
            f"Skipping {len(skipped_no_due)} task(s) with '{no_due_date_label}' label."
        )
    if skipped_no_robots:
        print(
            f"Skipping {len(skipped_no_robots)} task(s) with '{no_robots_label}' label."
        )

    if not eligible:
        print("No undated tasks to schedule.")
        return

    if args.execute:
        _execute(api, eligible, target_str)
    else:
        _dry_run(eligible, target_str)


def _dry_run(tasks, target_date: str):
    """
    Print what would be scheduled without making changes.
    """
    print(f"DRY RUN: {len(tasks)} task(s) would be scheduled for {target_date}:\n")
    for task in tasks:
        print(f"  - {_task_link(task)}")
    print("\nTo execute, re-run with --execute")


def _execute(api, tasks, target_date: str):
    """
    Apply the target due date to each eligible task.
    """
    scheduled = 0
    failed = 0
    for task in tasks:
        try:
            api.update_task(task.id, due_date=target_date)
            print(f"  Scheduled for {target_date}: {_task_link(task)}")
            scheduled += 1
        except Exception as ex:
            print(f"  FAILED: {_task_link(task)} -- {ex}")
            failed += 1

    total = len(tasks)
    print(
        f"\nScheduled {scheduled} of {total} task(s) for {target_date}. "
        f"{failed} failure(s)."
    )
