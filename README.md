# todoist_toolbox

CLI recipes for bulk Todoist task management. Automates the tedious stuff — closing piled-up recurring tasks, rescheduling forgotten one-offs — so you can move on with your day.

## Recipes

### complete-overdue-recurring

Finds overdue recurring tasks that recur every 7 days or fewer and closes them. Closing a recurring task in Todoist advances it to the next occurrence (nothing is lost).

```bash
./complete_overdue_recurring.sh              # dry-run (default)
./complete_overdue_recurring.sh --execute    # actually close them
```

### reschedule-overdue-nonrecurring

Finds overdue non-recurring (one-off) tasks and reschedules them to today.

```bash
./reschedule_overdue_nonrecurring.sh              # dry-run (default)
./reschedule_overdue_nonrecurring.sh --execute    # actually reschedule them
```

### label-by-color

Applies a label to all tasks under projects of a given color. Useful for tagging everything in a work project (e.g., all tasks under a `sky_blue` project get the `Work` label).

```bash
./label_by_color.sh --color sky_blue --label Work              # dry-run (default)
./label_by_color.sh --color sky_blue --label Work --execute    # actually apply labels
```

For cron use, set env vars instead of passing args each time:

```bash
# in todoist/.env
TODOIST_LABEL_COLOR=sky_blue
TODOIST_LABEL_NAME=Work
```

Then just: `./label_by_color.sh --execute`

## Opting tasks out of automation

Add the `_no_robots` label to any Todoist task to exclude it from automation. Both `complete-overdue-recurring` and `reschedule-overdue-nonrecurring` will skip tasks with this label and log how many were skipped. `label-by-color` does not check for this label.

## Setup

Requires Python 3.10+.

```bash
python -m venv todoist/venv
source todoist/venv/bin/activate
pip install -r todoist/requirements.txt
```

### Environment variables

Create a `todoist/.env` file (see `todoist/.env_EXAMPLE` for the template):

```bash
# todoist/.env
TODOIST_API_TOKEN=your-token-here
```

The value can be the token itself or a path to a file containing it.

The `label-by-color` recipe also accepts optional env var fallbacks (`TODOIST_LABEL_COLOR`, `TODOIST_LABEL_NAME`) if you prefer not to pass `--color` and `--label` each time.

## GitHub Actions

Two workflows run automatically via GitHub Actions:

- **Daily Todoist Recipes** (`daily-todoist-recipes.yml`) — runs at 5 AM MT (11:00 UTC) each day. Executes `complete-overdue-recurring` and `reschedule-overdue-nonrecurring`.
- **Hourly Label by Color** (`hourly-label-by-color.yml`) — runs every hour. Labels tasks in `sky_blue` projects with `Work`.

Both can also be triggered manually from the Actions tab (`workflow_dispatch`).

The `TODOIST_API_TOKEN` secret must be set in the repository's Settings > Secrets > Actions.

## Running directly

```bash
source todoist/venv/bin/activate
python -m todoist complete-overdue-recurring
python -m todoist reschedule-overdue-nonrecurring
python -m todoist label-by-color --color sky_blue --label Work
```

## Tests

```bash
source todoist/venv/bin/activate
python -m pytest todoist/tests/ -v
```
