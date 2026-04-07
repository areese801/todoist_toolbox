#!/usr/bin/env bash
################################################################################
# reschedule_work_to_monday.sh
#
# Bash wrapper for the todoist reschedule-work-to-monday recipe.
# Reschedules overdue work-labeled tasks to the following Monday.
#
# USAGE:
#   ./reschedule_work_to_monday.sh                  # Dry-run (default)
#   ./reschedule_work_to_monday.sh --execute        # Actually reschedule
#   ./reschedule_work_to_monday.sh --force          # Bypass day/time check
#   ./reschedule_work_to_monday.sh --help           # Show help
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
    echo "Run: python -m venv ${SCRIPT_DIR}/todoist/venv && source ${SCRIPT_DIR}/todoist/venv/bin/activate && pip install -r ${SCRIPT_DIR}/todoist/requirements.txt" >&2
    exit 1
fi

PYTHON="${SCRIPT_DIR}/todoist/venv/bin/python"

cd "${SCRIPT_DIR}"
"${PYTHON}" -m todoist reschedule-work-to-monday "$@"
