"""
Recipe: label-by-color

Applies a label to all tasks under projects of a given color.
Dry-run is the default.
"""

import os
import sys

from todoist.todoist_tasks import get_active_tasks, get_projects, _task_link


def _resolve_config(args):
    """
    Resolve color and label from CLI args or env var fallback.

    Args:
        args: argparse.Namespace with optional color and label attributes.
    Returns:
        Tuple of (color, label) strings.
    Raises:
        SystemExit if either value cannot be resolved.
    """
    color = args.color or os.environ.get("TODOIST_LABEL_COLOR")
    label = args.label or os.environ.get("TODOIST_LABEL_NAME")

    if not color:
        print(
            "Error: --color is required (or set TODOIST_LABEL_COLOR env var).",
            file=sys.stderr,
        )
        sys.exit(1)

    if not label:
        print(
            "Error: --label is required (or set TODOIST_LABEL_NAME env var).",
            file=sys.stderr,
        )
        sys.exit(1)

    return color, label


def run(args, api=None):
    """
    Execute the label-by-color recipe.

    Args:
        args: An argparse.Namespace with color, label, and execute attributes.
        api: A TodoistAPI instance.
    """
    color, label_name = _resolve_config(args)

    # Find matching projects
    projects = get_projects(api=api)
    matching_project_ids = {p.id for p in projects if p.color == color}

    if not matching_project_ids:
        print(f"No projects found with color '{color}'.")
        return

    # Build a name lookup for output
    project_names = {p.id: p.name for p in projects if p.id in matching_project_ids}

    # Find tasks that need the label
    all_tasks = get_active_tasks(api=api)
    tasks_in_projects = [t for t in all_tasks if t.project_id in matching_project_ids]
    tasks_to_label = [t for t in tasks_in_projects if label_name not in t.labels]

    if not tasks_to_label:
        print(
            f"No tasks need labeling. All tasks in matching projects already have '{label_name}'."
        )
        return

    if args.execute:
        _execute(api, tasks_to_label, label_name, project_names)
    else:
        _dry_run(tasks_to_label, label_name, project_names)


def _dry_run(tasks, label_name, project_names):
    """
    Print what would be labeled without making changes.
    """
    print(f'DRY RUN: {len(tasks)} task(s) would be labeled with "{label_name}":\n')
    for task in tasks:
        proj_name = project_names.get(task.project_id, "unknown")
        print(f"  - {_task_link(task)}  (project: {proj_name})")
    print(f"\nTo execute, re-run with --execute")


def _execute(api, tasks, label_name, project_names):
    """
    Actually apply the label to qualifying tasks.
    """
    labeled = 0
    failed = 0
    for task in tasks:
        try:
            updated_labels = list(task.labels) + [label_name]
            api.update_task(task_id=task.id, labels=updated_labels)
            print(f"  Labeled: {_task_link(task)}")
            labeled += 1
        except Exception as ex:
            print(f"  FAILED: {_task_link(task)} -- {ex}")
            failed += 1

    total = len(tasks)
    print(f"\nLabeled {labeled} of {total} task(s). {failed} failure(s).")
