"""
Recipe: reschedule-work-to-monday

Finds overdue non-recurring tasks with a specific label (default: "Work")
and reschedules them to the following Monday. Designed to run Friday evening
so leftover work tasks get a clean start next week.

Guardrails: only runs on Friday after the configured cutoff hour, or on
Saturday/Sunday. Use --force to bypass.
"""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from todoist.config import get_config
from todoist.todoist_tasks import get_overdue_non_recurring_tasks, _task_link


def _now_in_tz(tz_name: str) -> datetime:
    """
    Return the current datetime in the given timezone.
    """
    return datetime.now(ZoneInfo(tz_name))


def _next_monday(from_date: date) -> date:
    """
    Return the date of the next Monday strictly after from_date.
    """
    d = from_date + timedelta(days=1)
    while d.weekday() != 0:  # 0 = Monday
        d += timedelta(days=1)
    return d


def _is_allowed_time(now: datetime, cutoff_hour: int) -> bool:
    """
    Check if it's an appropriate time to run.

    Allowed:
    - Friday at or after cutoff_hour
    - Saturday (weekday 5) or Sunday (weekday 6)

    Not allowed:
    - Monday through Thursday
    - Friday before cutoff_hour
    """
    weekday = now.weekday()
    if weekday in (5, 6):  # Saturday, Sunday
        return True
    if weekday == 4 and now.hour >= cutoff_hour:  # Friday after cutoff
        return True
    return False


def run(args, api=None):
    """
    Execute the reschedule-work-to-monday recipe.

    Args:
        args: argparse.Namespace with execute and force attributes.
        api: A TodoistAPI instance.
    """
    config = get_config()
    work_label = config["work_label"]
    no_robots_label = config["no_robots_label"]
    timezone = config["timezone"]
    cutoff_hour = config["friday_cutoff_hour"]

    now = _now_in_tz(timezone)

    # Day/time guardrail
    if not args.force and not _is_allowed_time(now, cutoff_hour):
        day_name = now.strftime("%A")
        print(
            f"It's {day_name} {now.strftime('%H:%M')} {timezone}. "
            f"This recipe is designed for Friday at {cutoff_hour}:00 or later. "
            f"Use --force to run anyway."
        )
        return

    # Calculate target Monday
    target_monday = _next_monday(now.date())
    target_str = target_monday.isoformat()

    print(f"Fetching overdue non-recurring tasks with '{work_label}' label...")

    all_overdue = get_overdue_non_recurring_tasks(api=api)

    # Filter to tasks with the work label
    work_tasks = [t for t in all_overdue if work_label in t.labels]

    # Respect no-robots
    skipped = [t for t in work_tasks if no_robots_label in t.labels]
    eligible = [t for t in work_tasks if no_robots_label not in t.labels]

    if skipped:
        print(f"Skipping {len(skipped)} task(s) with '{no_robots_label}' label.")

    if not eligible:
        print(f"No overdue '{work_label}' tasks to reschedule.")
        return

    if args.execute:
        _execute(api, eligible, target_str)
    else:
        _dry_run(eligible, target_str)


def _dry_run(tasks, target_date: str):
    """
    Print what would be rescheduled without making changes.
    """
    print(f"DRY RUN: {len(tasks)} task(s) would be rescheduled to {target_date}:\n")
    for task in tasks:
        print(f"  - {_task_link(task)}  (due: {task.due.date})")
    print(f"\nTo execute, re-run with --execute")


def _execute(api, tasks, target_date: str):
    """
    Reschedule qualifying tasks to the target Monday.
    """
    rescheduled = 0
    failed = 0
    for task in tasks:
        try:
            api.update_task(task.id, due_date=target_date)
            print(f"  Rescheduled to {target_date}: {_task_link(task)}")
            rescheduled += 1
        except Exception as ex:
            print(f"  FAILED: {_task_link(task)} -- {ex}")
            failed += 1

    total = len(tasks)
    print(f"\nRescheduled {rescheduled} of {total} task(s) to {target_date}. {failed} failure(s).")
