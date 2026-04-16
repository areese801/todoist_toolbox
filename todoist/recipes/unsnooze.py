"""
Recipe: unsnooze

Scans active Todoist tasks for snooze metadata comments. If a task's
wake_time has passed, restores its original due date/string and deletes
the snooze comment.

Designed to run on a 5-minute cron via GitHub Actions, or manually via CLI.
Dry-run is the default — pass --execute to apply changes.
"""

from datetime import datetime

from todoist.config import get_config
from todoist.todoist_tasks import get_active_tasks, _task_link
from todoist.tui.snooze import (
    build_restore_kwargs,
    is_past_wake_time,
    is_snooze_comment,
    parse_snooze_comment,
)


def _ts():
    """
    Return a formatted timestamp for logging.
    """
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def _find_snoozed_tasks(api, tasks):
    """
    Find tasks that have snooze comments with elapsed wake_times.

    Args:
        api: A TodoistAPI instance.
        tasks: List of active Task objects.

    Returns:
        List of (task, snooze_data, comment_id) tuples for tasks ready to unsnooze.
    """
    now = datetime.now()
    ready = []

    for task in tasks:
        try:
            comments = api.get_comments(task_id=task.id)
        except Exception:
            continue

        for comment in comments:
            content = getattr(comment, "content", "")
            if not is_snooze_comment(content):
                continue

            snooze_data = parse_snooze_comment(content)
            if snooze_data is None:
                continue

            if is_past_wake_time(snooze_data, now=now):
                ready.append((task, snooze_data, comment.id))
                break  # Only one snooze comment per task

    return ready


def _dry_run(ready):
    """
    Print what would be unsnoozed without making changes.

    Args:
        ready: List of (task, snooze_data, comment_id) tuples.
    """
    print(f"DRY RUN: {len(ready)} task(s) would be unsnoozed:\n")
    for task, snooze_data, _ in ready:
        wake = snooze_data["wake_time"].strftime("%Y-%m-%d %H:%M")
        restore = build_restore_kwargs(snooze_data)
        print(f"  - {_task_link(task)}")
        print(f"    wake_time: {wake}")
        print(f"    restore: {restore}")
    print(f"\nTo execute, re-run with --execute")


def _execute(api, ready):
    """
    Restore original due dates and delete snooze comments.

    Args:
        api: A TodoistAPI instance.
        ready: List of (task, snooze_data, comment_id) tuples.
    """
    restored = 0
    failed = 0

    for task, snooze_data, comment_id in ready:
        try:
            # Restore original due date
            kwargs = build_restore_kwargs(snooze_data)
            if kwargs:
                api.update_task(task.id, **kwargs)

            # Delete the snooze comment
            api.delete_comment(comment_id)

            print(f"  [{_ts()}] Unsnoozed: {_task_link(task)}")
            restored += 1
        except Exception as ex:
            print(f"  [{_ts()}] FAILED: {_task_link(task)} -- {ex}")
            failed += 1

    total = len(ready)
    print(f"\nUnsnoozed {restored} of {total} task(s). {failed} failure(s).")


def run(args, api=None):
    """
    Execute the unsnooze recipe.

    Args:
        args: An argparse.Namespace with at least an `execute` bool attribute.
        api: A TodoistAPI instance.
    """
    config = get_config()
    no_robots_label = config["no_robots_label"]

    print(f"[{_ts()}] Fetching active tasks...")
    all_tasks = get_active_tasks(api=api)

    # Filter out tasks with no_robots label
    tasks = [t for t in all_tasks if no_robots_label not in getattr(t, "labels", [])]
    skipped = len(all_tasks) - len(tasks)
    if skipped:
        print(f"[{_ts()}] Skipping {skipped} task(s) with '{no_robots_label}' label.")

    print(f"[{_ts()}] Checking {len(tasks)} task(s) for snooze comments...")
    ready = _find_snoozed_tasks(api, tasks)

    if not ready:
        print("No snoozed tasks ready to wake up.")
        return

    print(f"[{_ts()}] Found {len(ready)} task(s) ready to unsnooze.")

    if args.execute:
        _execute(api, ready)
    else:
        _dry_run(ready)
