#!/usr/bin/env bash
################################################################################
# complete_overdue_recurring.sh
#
# Bash wrapper for the todoist complete-overdue-recurring recipe.
# Closes overdue recurring tasks that recur every 7 days or fewer.
# Activates the project venv and runs the CLI entry point.
#
# USAGE:
#   ./complete_overdue_recurring.sh                  # Dry-run (default)
#   ./complete_overdue_recurring.sh --execute        # Actually close qualifying tasks
#   ./complete_overdue_recurring.sh --clear-cache    # Clear cached intervals first
#   ./complete_overdue_recurring.sh --help           # Show help
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
"${PYTHON}" -m todoist complete-overdue-recurring "$@"
