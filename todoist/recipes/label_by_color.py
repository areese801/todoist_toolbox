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
        print("Error: --color is required (or set TODOIST_LABEL_COLOR env var).", file=sys.stderr)
        sys.exit(1)

    if not label:
        print("Error: --label is required (or set TODOIST_LABEL_NAME env var).", file=sys.stderr)
        sys.exit(1)

    return color, label
