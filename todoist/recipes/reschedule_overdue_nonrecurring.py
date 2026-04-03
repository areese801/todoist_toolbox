"""
Recipe: reschedule-overdue-nonrecurring

Identifies overdue non-recurring Todoist tasks and reschedules them to today.
Dry-run is the default.
"""

from todoist.todoist_tasks import get_overdue_non_recurring_tasks, _task_link, NO_ROBOTS_LABEL


def run(args, api=None):
    """
    Execute the reschedule-overdue-nonrecurring recipe.

    Args:
        args: An argparse.Namespace with at least an `execute` bool attribute.
        api: A TodoistAPI instance.
    """
    all_overdue = get_overdue_non_recurring_tasks(api=api)

    skipped = [t for t in all_overdue if NO_ROBOTS_LABEL in t.labels]
    overdue_tasks = [t for t in all_overdue if NO_ROBOTS_LABEL not in t.labels]

    if skipped:
        print(f"Skipping {len(skipped)} task(s) with '{NO_ROBOTS_LABEL}' label.")

    if not overdue_tasks:
        print("No overdue non-recurring tasks found.")
        return

    if args.execute:
        _execute(api, overdue_tasks)
    else:
        _dry_run(overdue_tasks)


def _dry_run(tasks):
    """
    Print what would be rescheduled without making changes.
    """
    print(f"DRY RUN: {len(tasks)} task(s) would be rescheduled to today:\n")
    for task in tasks:
        print(f"  - {_task_link(task)}  (due: {task.due.date})")
    print(f"\nTo execute, re-run with --execute")


def _execute(api, tasks):
    """
    Actually reschedule the qualifying tasks to today.
    """
    rescheduled = 0
    failed = 0
    for task in tasks:
        try:
            api.update_task(task.id, due_string="today")
            print(f"  Rescheduled: {_task_link(task)}")
            rescheduled += 1
        except Exception as ex:
            print(f"  FAILED: {_task_link(task)} -- {ex}")
            failed += 1

    total = len(tasks)
    print(f"\nRescheduled {rescheduled} of {total} task(s). {failed} failure(s).")
