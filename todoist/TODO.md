# Todoist Mass Complete Overdue Recurring — Pickup Notes

## Current State

**Branch:** `dev` (based off `claude/cranky-goodall` worktree)
**Status:** Implementation complete, all 23 tests passing. Ready for live testing.

## What Was Built

A recipe-based CLI for bulk Todoist task management. First recipe: `complete-overdue`.

### complete-overdue recipe

Finds overdue recurring tasks that recur every 7 days or fewer and closes them.
Closing a recurring task in Todoist advances it to the next occurrence — it does not delete it.

- **Dry-run by default** — shows what would be closed
- **`--execute` flag** — actually closes the tasks
- **Frequency resolution via API probing** — creates a temp task with the same `due_string`, completes it, reads back the next due date, computes interval in days, then deletes the temp task. Avoids parsing natural language recurrence strings.
- **Interval caching** — probes once per unique `due.string` to minimize API calls
- **MAX_INTERVAL_DAYS = 7** — only tasks recurring every 7 days or fewer qualify

### Smart API token handling

`_get_api_token()` reads `TODOIST_API_TOKEN` from `.env`. If the value is a file path (`os.path.isfile()`), reads the token from that file (stripping trailing newlines). Otherwise treats the string as the literal token.

## How to Run

```bash
cd /Users/areese/projects/personal/toolbox
source todoist/venv/bin/activate

# Dry-run (safe, shows what would be closed)
python -m todoist complete-overdue

# Actually close qualifying tasks
python -m todoist complete-overdue --execute
```

## How to Test

```bash
cd /Users/areese/projects/personal/toolbox
source todoist/venv/bin/activate
python -m pytest todoist/tests/ -v
```

All 23 tests should pass.

## File Layout

```
todoist/
├── __init__.py
├── __main__.py              # Entry point for `python -m todoist`, delegates to todoist_tasks.main()
├── todoist_tasks.py          # Core library + CLI (build_parser, main, _get_api_token, etc.)
├── .env                      # TODOIST_API_TOKEN (git-ignored)
├── .env_EXAMPLE              # Example env file
├── requirements.txt          # python-dotenv, todoist_api_python, pytest
├── recipes/
│   ├── __init__.py
│   └── complete_overdue.py   # The complete-overdue recipe (run, _dry_run, _execute)
├── tests/
│   ├── __init__.py
│   ├── helpers.py            # make_task() and make_due() mock factories
│   ├── test_todoist_tasks.py # 13 tests: _get_api_token, get_active_tasks, get_overdue_recurring_tasks, _resolve_recurrence_interval
│   ├── test_complete_overdue.py # 6 tests: dry-run, execute, interval caching
│   ├── test_main.py          # 3 tests: CLI subcommand dispatch
│   └── test_smoke.py         # 1 test: module importability
└── venv/                     # Virtual environment (git-ignored)
```

## Commits on `dev` (ahead of `main`)

```
d3b8b2f Enhance _get_api_token() to read token from file path
759ef88 Add CLI entry point with argparse subcommand dispatch
6b82e5d Add complete-overdue recipe with dry-run and execute modes
de17c21 Add _resolve_recurrence_interval to probe recurrence frequency via API
04f5be0 Refactor get_active_tasks and get_overdue_recurring_tasks to accept optional api parameter
e159fba Add test helper factories for mock Task and Due objects
2e4ef70 Add package scaffolding and test infrastructure
d001855 latest
```

## What's Next

1. **Live test** — run `python -m todoist complete-overdue` against real API to verify dry-run output looks correct
2. **Live execute** — run with `--execute` once satisfied
3. **Merge to main** — squash or merge `dev` into `main` when ready
4. **Clean up worktree** — delete `claude/cranky-goodall` branch and `.claude/worktrees/` directory
5. **Cron setup** — schedule `python -m todoist complete-overdue --execute` on a cron

## Design Doc

Full design rationale is in `docs/plans/2026-02-24-complete-overdue-recurring-design.md`.
