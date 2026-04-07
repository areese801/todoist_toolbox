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

Applies a label to all tasks under projects of a given color. Defaults to the color and label in `config.json`, or can be overridden with CLI args or env vars.

```bash
./label_by_color.sh                                                  # dry-run with config defaults
./label_by_color.sh --color sky_blue --label Work --execute          # override and execute
```

### reschedule-work-to-monday

Reschedules overdue non-recurring tasks with the configured work label to the following Monday. Designed to run Friday evening so leftover work tasks get a clean start next week.

Has built-in day/time guardrails: only runs on Friday after 6 PM, Saturday, or Sunday. Use `--force` to bypass.

```bash
./reschedule_work_to_monday.sh                  # dry-run (default)
./reschedule_work_to_monday.sh --execute        # actually reschedule to Monday
./reschedule_work_to_monday.sh --force          # bypass day/time check
```

## Opting tasks out of automation

Add the `_no_robots` label to any Todoist task to exclude it from automation. The `complete-overdue-recurring`, `reschedule-overdue-nonrecurring`, and `reschedule-work-to-monday` recipes will skip tasks with this label and log how many were skipped. `label-by-color` does not check for this label. The label name is configurable in `config.json`.

## Setup

Requires Python 3.10+.

```bash
python -m venv todoist/venv
source todoist/venv/bin/activate
pip install -r todoist/requirements.txt
```

### Configuration

Non-sensitive settings live in `todoist/config.json` (committed to version control):

```json
{
  "work_label": "Work",
  "project_color": "sky_blue",
  "no_robots_label": "_no_robots",
  "timezone": "America/Denver",
  "friday_cutoff_hour": 18
}
```

Recipes read from this file for label names, project colors, timezone, and the Friday cutoff hour.

### Environment variables

Create a `todoist/.env` file (see `todoist/.env_EXAMPLE` for the template):

```bash
# todoist/.env
TODOIST_API_TOKEN=your-token-here
```

The value can be the token itself or a path to a file containing it.

The `label-by-color` recipe also accepts optional env var overrides (`TODOIST_LABEL_COLOR`, `TODOIST_LABEL_NAME`) which take precedence over `config.json`.

## GitHub Actions

Three workflows run automatically via GitHub Actions:

- **Daily Todoist Recipes** (`daily-todoist-recipes.yml`) — runs at 5 AM MT (11:00 UTC) each day. Executes `complete-overdue-recurring` and `reschedule-overdue-nonrecurring`.
- **Hourly Label by Color** (`hourly-label-by-color.yml`) — runs every hour. Labels tasks using the color and label from `config.json`.
- **Friday Work to Monday** (`friday-reschedule-work.yml`) — runs Friday at 6 PM MT (midnight Saturday UTC). Reschedules overdue work-labeled tasks to the following Monday.

All can be triggered manually from the Actions tab (`workflow_dispatch`).

The `TODOIST_API_TOKEN` secret must be set in the repository's Settings > Secrets > Actions.

## Running directly

```bash
source todoist/venv/bin/activate
python -m todoist complete-overdue-recurring
python -m todoist reschedule-overdue-nonrecurring
python -m todoist label-by-color
python -m todoist reschedule-work-to-monday --force    # bypass day/time check
```

## Tests

```bash
source todoist/venv/bin/activate
python -m pytest todoist/tests/ -v
```
