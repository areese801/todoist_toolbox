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

### label-by-color

Applies a label to all tasks under projects of a given color. Useful for tagging everything in a work project (e.g., all tasks under a `sky_blue` project get the `work` label).

```bash
./label_by_color.sh --color sky_blue --label work              # dry-run (default)
./label_by_color.sh --color sky_blue --label work --execute    # actually apply labels
```

For cron use, set env vars instead of passing args each time:

```bash
# in .env
TODOIST_LABEL_COLOR=sky_blue
TODOIST_LABEL_NAME=work
```

Then just: `./label_by_color.sh --execute`

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
python -m todoist label-by-color --color sky_blue --label work
```

## Tests

```bash
source todoist/venv/bin/activate
python -m pytest todoist/tests/ -v
```
