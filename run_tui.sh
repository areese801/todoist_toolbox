#!/usr/bin/env bash
################################################################################
# run_tui.sh
#
# Bash wrapper for the todoist TUI application.
# Launches a keyboard-driven Textual interface for managing Todoist tasks.
# Activates the project venv and runs the CLI entry point.
#
# USAGE:
#   ./run_tui.sh            # Launch the TUI
#   ./run_tui.sh --help     # Show help
#
# DEPENDENCIES:
#   - Python virtual environment at todoist/venv
#   - todoist package installed in that venv
#   - textual and thefuzz packages
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
"${PYTHON}" -m todoist tui "$@"
