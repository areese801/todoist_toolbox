"""
This module deals with tasks in the todoist API
"""

from todoist_api_python.api import TodoistAPI
from todoist_api_python.models import Task
from todoist_api_python.models import Due
from dotenv import load_dotenv
import logging
import os
from pathlib import Path
import sys
import time
from datetime import date, datetime

# Resolve the .env path relative to this file (todoist/.env)
# so load_dotenv works regardless of the working directory.
_DOTENV_PATH = Path(__file__).resolve().parent / ".env"


def _get_api_token():
    """
    Returns the API token from the TODOIST_API_TOKEN environment variable.

    If the value is a path to an existing file, the token is read from that file
    with trailing newline characters stripped. Otherwise, the value is treated as
    the literal token string.
    """

    load_dotenv(_DOTENV_PATH)
    raw_value = os.getenv("TODOIST_API_TOKEN")

    if not raw_value:
        raise ValueError("Failed to resolve Todoist API token")

    raw_value = raw_value.strip()

    if os.path.isfile(raw_value):
        with open(raw_value, "r") as f:
            token = f.read().rstrip("\n")
    else:
        token = raw_value

    return token


TODOIST_TASK_URL = "https://app.todoist.com/app/task/{task_id}"


def _task_link(task: Task) -> str:
    """
    Return the task content wrapped in an OSC 8 hyperlink escape sequence.

    Terminals that support OSC 8 (Ghostty, iTerm2, etc.) will render
    the task name as a clickable link to the Todoist web app.
    """
    url = TODOIST_TASK_URL.format(task_id=task.id)
    return f"\033]8;;{url}\033\\{task.content}\033]8;;\033\\"


def _make_due_datetime(task_object: Task, truncate: bool = True) -> datetime:
    """
    Task objects contain either a due date or a due datetime (or none), represented as strings
    This function inspects those strings and returns an actual datetime object that we can work with.
    The Todoist API returns either a date or a datetime depending on if there is any time precision
    However, this function will always return a datetime object with %H:%M:%S precision
    :param task_object: a todoist Task object
    :param truncate: If set to True, the resulting datetime object will have HH:MM:SS set to 00:00:00
        If set to false, the resulting datetime object will have HH:MM:SS set to the same values
        parsed from the current time.  This is useful for calculating overdueness of Task objects
        that have HH:MM:SS precision
    :return: a datetime object
    """

    due_part = getattr(task_object, "due")  # Contains a Due object or None

    # Short circuit if there is no due date
    if due_part is None:
        return None

    # The Due.date field can be either datetime.date or datetime.datetime
    # depending on whether the task has time precision
    due_value = due_part.date

    if isinstance(due_value, datetime):
        # Already a datetime object (has time precision)
        # Strip timezone info for comparison
        if due_value.tzinfo is not None:
            ret_val = due_value.replace(tzinfo=None)
        else:
            ret_val = due_value
    else:
        # It's a date object, convert to datetime
        if truncate is True:
            ret_val = datetime.combine(due_value, datetime.min.time())
        else:
            _now = datetime.now()
            ret_val = datetime.combine(due_value, _now.time().replace(microsecond=0))

    return ret_val


def _is_overdue(task_object: Task, truncate: bool = True) -> bool:
    """
    Returns a boolean object indicating of a Task object is Overdue or not
    :param task_object: a todoist Task object
    :param truncate: If set to True, the resulting datetime object will have HH:MM:SS set to 00:00:00
        If set to false, the resulting datetime object will have HH:MM:SS set to the same values
        parsed from the current time.  This is useful for calculating overdueness of Task objects
        that have HH:MM:SS precision
    :return:
    """

    due_date = _make_due_datetime(task_object=task_object, truncate=truncate)

    if due_date is None:
        ret_val = False
    else:
        _now = datetime.now().replace(microsecond=0)  # Drop Microsecond precision
        if _now > due_date:
            ret_val = True
        else:
            ret_val = False

    return ret_val


def get_active_tasks(api=None):
    """
    Gets a list of all open tasks in todoist.

    Args:
        api: An optional TodoistAPI instance. If not provided, one will be created
             using the token from the environment.
    Returns: A list of Todoist Tasks
    """

    if api is None:
        todoist_api_token = _get_api_token()
        api = TodoistAPI(todoist_api_token)

    try:
        # The API returns a ResultsPaginator that yields pages of tasks
        # We need to flatten the pages into a single list
        active_tasks: list[Task] = []
        for page in api.get_tasks():
            active_tasks.extend(page)
        ret_val = active_tasks
    except Exception as ex:
        print(
            f"Got Exception while trying to collect tasks from the Todoist API:\n{ex}.",
            file=sys.stderr,
        )
        raise ex

    return ret_val


def get_projects(api=None):
    """
    Fetch all projects from Todoist.

    Args:
        api: An optional TodoistAPI instance. If not provided, one will be created
             using the token from the environment.
    Returns: A list of Todoist Project objects.
    """
    if api is None:
        todoist_api_token = _get_api_token()
        api = TodoistAPI(todoist_api_token)

    try:
        result = api.get_projects()
        # If the SDK returns a paginator (like get_tasks), flatten it.
        # If it returns a plain list, just return it.
        if isinstance(result, list):
            return result
        projects = []
        for page in result:
            projects.extend(page)
        return projects
    except Exception as ex:
        print(
            f"Got Exception while trying to collect projects from the Todoist API:\n{ex}.",
            file=sys.stderr,
        )
        raise ex


def get_overdue_recurring_tasks(api=None) -> list:
    """
    Returns a pared down list (Overdue, Recurring) of tasks returned by get_active_tasks.

    Args:
        api: An optional TodoistAPI instance. If not provided, one will be created
             using the token from the environment.
    :return: A list of Todoist Tasks
    """

    active_tasks = get_active_tasks(api=api)

    overdue_tasks: list[Task] = []  # We'll append overdue tasks in here as we go

    for task in active_tasks:
        if _is_overdue(task_object=task, truncate=False) is True:
            # Only include recurring tasks
            if task.due is not None and task.due.is_recurring:
                overdue_tasks.append(task)

    return overdue_tasks


def get_overdue_non_recurring_tasks(api=None) -> list:
    """
    Returns a pared down list (Overdue, Non-Recurring) of tasks returned by get_active_tasks.

    Args:
        api: An optional TodoistAPI instance. If not provided, one will be created
             using the token from the environment.
    :return: A list of Todoist Tasks
    """

    active_tasks = get_active_tasks(api=api)

    overdue_tasks: list[Task] = []

    for task in active_tasks:
        if _is_overdue(task_object=task, truncate=False) is True:
            if task.due is not None and not task.due.is_recurring:
                overdue_tasks.append(task)

    return overdue_tasks


def _probe_next_due_date(api, due_string: str) -> int | None:
    """
    Probe the Todoist API to determine the recurrence interval for a due string.

    Creates a temporary task, records its initial due date, completes it
    (advancing to the next occurrence), then computes the interval as the
    difference between the two dates.

    Args:
        api: A TodoistAPI instance.
        due_string: A Todoist recurrence string (e.g., "every day", "every weekday").

    Returns:
        The recurrence interval in days, or None if resolution fails.
    """
    try:
        temp_task = api.add_task(content="__probe__", due_string=due_string)
    except Exception as ex:
        print(f'  [probe] add_task failed for "{due_string}": {type(ex).__name__}: {ex}')
        return None

    try:
        # Capture the initial due date before completing
        if temp_task.due is None:
            print(f'  [probe] temp_task.due is None for "{due_string}"')
            return None
        initial_due = temp_task.due.date
        if isinstance(initial_due, datetime):
            initial_due = initial_due.date()

        api.complete_task(temp_task.id)

        # Todoist may not advance the due date immediately after completion.
        # Retry a few times with a short delay to let the server catch up.
        advanced_task = None
        for attempt in range(5):
            time.sleep(1)
            advanced_task = api.get_task(temp_task.id)
            if advanced_task.due is not None:
                break
            print(f'  [probe] attempt {attempt + 1}: due still None for "{due_string}"')

        if advanced_task is None or advanced_task.due is None:
            print(f'  [probe] due remained None after 5 retries for "{due_string}"')
            return None

        next_due = advanced_task.due.date
        if isinstance(next_due, datetime):
            next_due = next_due.date()

        return (next_due - initial_due).days
    except Exception as ex:
        print(f'  [probe] exception for "{due_string}": {type(ex).__name__}: {ex}')
        return None
    finally:
        try:
            api.delete_task(temp_task.id)
        except Exception:
            pass


logger = logging.getLogger(__name__)


def _probe_next_due_date_with_retry(
    api, due_string: str, max_retries: int = 3
) -> int | None:
    """
    Wrap _probe_next_due_date with retry logic for 429 (rate limit) responses.

    Args:
        api: A TodoistAPI instance.
        due_string: A Todoist recurrence string.
        max_retries: Maximum number of attempts before giving up.

    Returns:
        The recurrence interval in days, or None if all attempts fail.
    """
    # The Todoist SDK may use requests (v3) or httpx (v4+). Import whichever
    # HTTP error class is available so we can catch 429 rate limits.
    try:
        from requests.exceptions import HTTPError
    except ImportError:
        try:
            from httpx import HTTPStatusError as HTTPError
        except ImportError:
            HTTPError = None

    for attempt in range(max_retries):
        try:
            return _probe_next_due_date(api, due_string)
        except Exception as exc:
            # Check if this is a 429 rate limit we should retry
            is_rate_limit = (
                HTTPError is not None
                and isinstance(exc, HTTPError)
                and hasattr(exc, "response")
                and exc.response is not None
                and exc.response.status_code == 429
            )
            if is_rate_limit:
                retry_after = int(exc.response.headers.get("Retry-After", 2))
                logger.debug(
                    "429 on attempt %d/%d for '%s', sleeping %ds",
                    attempt + 1,
                    max_retries,
                    due_string,
                    retry_after,
                )
                time.sleep(retry_after)
            else:
                raise
    return None


def get_labels(api=None):
    """
    Fetch all labels from Todoist.

    Args:
        api: An optional TodoistAPI instance. If not provided, one will be created
             using the token from the environment.
    Returns: A list of Todoist Label objects.
    """
    if api is None:
        api = TodoistAPI(_get_api_token())

    try:
        result = api.get_labels()
        if isinstance(result, list):
            return result
        labels = []
        for page in result:
            labels.extend(page)
        return labels
    except Exception as ex:
        print(
            f"Got Exception while trying to collect labels from the Todoist API:\n{ex}.",
            file=sys.stderr,
        )
        raise ex


def get_sections(api=None, project_id=None):
    """
    Fetch sections from Todoist, optionally filtered by project_id.

    Args:
        api: An optional TodoistAPI instance. If not provided, one will be created
             using the token from the environment.
        project_id: If provided, only return sections for this project.
    Returns: A list of Todoist Section objects.
    """
    if api is None:
        api = TodoistAPI(_get_api_token())

    try:
        if project_id:
            result = api.get_sections(project_id=project_id)
        else:
            result = api.get_sections()
        if isinstance(result, list):
            return result
        sections = []
        for page in result:
            sections.extend(page)
        return sections
    except Exception as ex:
        print(
            f"Got Exception while trying to collect sections from the Todoist API:\n{ex}.",
            file=sys.stderr,
        )
        raise ex


def _resolve_project_id(api, project_name):
    """
    Resolve a project name to its ID via case-insensitive match.

    Args:
        api: A TodoistAPI instance.
        project_name: The project name to search for (case-insensitive).
    Returns: The project ID string.
    Raises: ValueError if no matching project is found.
    """
    projects = get_projects(api=api)
    name_lower = project_name.lower()
    for p in projects:
        if p.name.lower() == name_lower:
            return p.id
    available = [p.name for p in projects]
    raise ValueError(
        f"Project '{project_name}' not found. Available projects: {available}"
    )


def _resolve_section_id(api, section_name, project_id=None):
    """
    Resolve a section name to its ID via case-insensitive match.

    Args:
        api: A TodoistAPI instance.
        section_name: The section name to search for (case-insensitive).
        project_id: If provided, only search sections within this project.
    Returns: The section ID string.
    Raises: ValueError if no matching section is found.
    """
    sections = get_sections(api=api, project_id=project_id)
    name_lower = section_name.lower()
    for s in sections:
        if s.name.lower() == name_lower:
            return s.id
    available = [s.name for s in sections]
    raise ValueError(
        f"Section '{section_name}' not found. Available sections: {available}"
    )


if __name__ == "__main__":
    overdue_tasks = get_overdue_recurring_tasks()
    if overdue_tasks:
        for t in overdue_tasks:
            print(f"OVERDUE:  due_date = {t.due.date}\ttask = {t.content}")
    else:
        print(f"Found no overdue tasks")
