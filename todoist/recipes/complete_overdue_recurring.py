"""
Recipe: complete-overdue-recurring

Identifies overdue recurring Todoist tasks that recur frequently (every 7 days
or fewer) and closes them in bulk. Dry-run is the default.

Closing a recurring task in Todoist advances it to the next occurrence —
it does not delete it.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from todoist.cache import load_cache, save_cache, get_cached_interval, MISS
from todoist.todoist_tasks import (
    get_overdue_recurring_tasks,
    _probe_next_due_date_with_retry,
    _task_link,
)

MAX_INTERVAL_DAYS = 7


def _ts():
    """
    Return a formatted timestamp for logging.
    """
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def _probe_intervals_parallel(api, due_strings: list[str]) -> dict[str, int | None]:
    """
    Probe recurrence intervals for a list of due strings in parallel.

    Args:
        api: A TodoistAPI instance.
        due_strings: Due strings to probe.

    Returns:
        Mapping of due_string -> interval in days (or None on failure).
    """
    results: dict[str, int | None] = {}
    total = len(due_strings)

    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_ds = {
            executor.submit(_probe_next_due_date_with_retry, api, ds): ds
            for ds in due_strings
        }
        for i, future in enumerate(as_completed(future_to_ds), start=1):
            ds = future_to_ds[future]
            try:
                interval = future.result()
            except Exception:
                interval = None
            results[ds] = interval
            print(f'[{_ts()}] [{i}/{total}] "{ds}" -> {interval}d')

    return results


def run(args, api=None):
    """
    Execute the complete-overdue-recurring recipe.

    Args:
        args: An argparse.Namespace with at least an `execute` bool attribute.
              Optional: `clear_cache` bool to reset the persistent cache.
        api: A TodoistAPI instance.
    """
    # Handle --clear-cache
    if getattr(args, "clear_cache", False):
        save_cache({})
        print(f"[{_ts()}] Cache cleared.")

    print(f"[{_ts()}] Fetching overdue recurring tasks...")
    overdue_tasks = get_overdue_recurring_tasks(api=api)
    print(f"[{_ts()}] Found {len(overdue_tasks)} overdue recurring task(s).")

    if not overdue_tasks:
        print("No overdue recurring tasks found.")
        return

    # Collect unique due strings
    unique_due_strings = list({task.due.string for task in overdue_tasks})

    # Load persistent cache and partition into hits vs misses
    persistent_cache = load_cache()
    hits: dict[str, int | None] = {}
    misses: list[str] = []

    for ds in unique_due_strings:
        cached = get_cached_interval(persistent_cache, ds)
        if cached is not MISS:
            hits[ds] = cached
        else:
            misses.append(ds)

    if hits:
        print(f"[{_ts()}] {len(hits)} interval(s) found in cache.")
    if misses:
        print(f"[{_ts()}] Probing {len(misses)} uncached interval(s)...")

    # Probe cache misses in parallel
    if misses:
        probed = _probe_intervals_parallel(api, misses)
        # Only cache successful probes — failed probes (None) should be
        # retried on the next run, not permanently stored as failures.
        successful_probes = {k: v for k, v in probed.items() if v is not None}
        persistent_cache.update(successful_probes)
        save_cache(persistent_cache)
        hits.update(probed)

    # Filter tasks by cached interval
    qualifying = []
    for task in overdue_tasks:
        interval = hits.get(task.due.string)
        if interval is not None and interval <= MAX_INTERVAL_DAYS:
            qualifying.append((task, interval))

    if not qualifying:
        print("No qualifying tasks found (none recur every 7 days or fewer).")
        return

    if args.execute:
        _execute(api, qualifying)
    else:
        _dry_run(qualifying)


def _dry_run(qualifying):
    """
    Print what would be closed without making changes.
    """
    print(f"DRY RUN: {len(qualifying)} task(s) would be closed:\n")
    for task, interval in qualifying:
        print(
            f"  - {_task_link(task)}"
            f"  (due: {task.due.date}, recurs every {interval}d,"
            f' string: "{task.due.string}")'
        )
    print(f"\nTo execute, re-run with --execute")


def _execute(api, qualifying):
    """
    Actually close the qualifying tasks.
    """
    closed = 0
    failed = 0
    for task, interval in qualifying:
        try:
            api.complete_task(task.id)
            print(f"  Closed: {_task_link(task)}")
            closed += 1
        except Exception as ex:
            print(f"  FAILED: {_task_link(task)} -- {ex}")
            failed += 1

    total = len(qualifying)
    print(f"\nClosed {closed} of {total} task(s). {failed} failure(s).")
