#!/usr/bin/env bash
################################################################################
# label_by_color.sh
#
# Bash wrapper for the todoist label-by-color recipe.
# Applies a label to all tasks under projects of a given color.
# Activates the project venv and runs the CLI entry point.
#
# USAGE:
#   ./label_by_color.sh --color sky_blue --label work             # Dry-run
#   ./label_by_color.sh --color sky_blue --label work --execute   # Apply labels
#   ./label_by_color.sh --help                                    # Show help
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

source "${SCRIPT_DIR}/todoist/venv/bin/activate"

cd "${SCRIPT_DIR}"
python -m todoist label-by-color "$@"
