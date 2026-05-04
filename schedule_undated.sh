#!/usr/bin/env bash
################################################################################
# schedule_undated.sh
#
# Bash wrapper for the todoist schedule-undated recipe.
# Applies a sensible default due date (tomorrow, or next Monday if tomorrow
# is a weekend) to open tasks that have no due date set.
#
# USAGE:
#   ./schedule_undated.sh                  # Dry-run (default)
#   ./schedule_undated.sh --execute        # Actually apply due dates
#   ./schedule_undated.sh --help           # Show help
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
"${PYTHON}" -m todoist schedule-undated "$@"
