#!/usr/bin/env bash
################################################################################
# reschedule_overdue_nonrecurring.sh
#
# Bash wrapper for the todoist reschedule-overdue-nonrecurring recipe.
# Reschedules overdue non-recurring (one-off) tasks to today.
# Activates the project venv and runs the CLI entry point.
#
# USAGE:
#   ./reschedule_overdue_nonrecurring.sh              # Dry-run (default)
#   ./reschedule_overdue_nonrecurring.sh --execute    # Actually reschedule tasks
#   ./reschedule_overdue_nonrecurring.sh --help       # Show help
#
# DEPENDENCIES:
#   - Python virtual environment at todoist/venv
#   - todoist package installed in that venv
################################################################################
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

# Validate venv exists
if [ ! -d "${SCRIPT_DIR}/todoist/venv" ]; then
    echo "ERROR: Virtual environment not found at ${SCRIPT_DIR}/todoist/venv" >&2
    echo "Run: python -m venv ${SCRIPT_DIR}/todoist/venv && source ${SCRIPT_DIR}/todoist/venv/bin/activate && pip install -e ${SCRIPT_DIR}/todoist" >&2
    exit 1
fi

PYTHON="${SCRIPT_DIR}/todoist/venv/bin/python"

cd "${SCRIPT_DIR}"
"${PYTHON}" -m todoist reschedule-overdue-nonrecurring "$@"
