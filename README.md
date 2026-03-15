# todoist_toolbox

CLI recipes for bulk Todoist task management. Automates the tedious stuff — closing piled-up recurring tasks, rescheduling forgotten one-offs — so you can move on with your day.

## Recipes

### complete-overdue-recurring

Finds overdue recurring tasks that recur every 7 days or fewer and closes them. Closing a recurring task in Todoist advances it to the next occurrence (nothing is lost).

```bash
./complete_overdue_recurring.sh              # dry-run (default)
./complete_overdue_recurring.sh --execute    # actually close them
./complete_overdue_recurring.sh --clear-cache  # re-probe recurrence intervals
```

### reschedule-overdue-nonrecurring

Finds overdue non-recurring (one-off) tasks and reschedules them to today.

```bash
./reschedule_overdue_nonrecurring.sh              # dry-run (default)
./reschedule_overdue_nonrecurring.sh --execute    # actually reschedule them
```

## Setup

```bash
python -m venv todoist/venv
source todoist/venv/bin/activate
pip install -e todoist/
```

Set `TODOIST_API_TOKEN` in a `.env` file or as an environment variable. The value can be the token itself or a path to a file containing the token.

## Running directly

```bash
source todoist/venv/bin/activate
python -m todoist complete-overdue-recurring
python -m todoist reschedule-overdue-nonrecurring
```

## Tests

```bash
source todoist/venv/bin/activate
python -m pytest todoist/tests/ -v
```
