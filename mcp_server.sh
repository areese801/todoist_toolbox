#!/usr/bin/env bash
################################################################################
# mcp_server.sh
#
# Bash wrapper to launch the Todoist MCP server.
# Activates the project venv and runs the MCP server entry point.
#
# This script is what you point your MCP client config at.  For example,
# in Claude Desktop's config:
#
#   {
#     "mcpServers": {
#       "todoist": {
#         "command": "/path/to/todoist_toolbox/mcp_server.sh"
#       }
#     }
#   }
#
# The MCP client spawns this script as a subprocess and communicates
# over stdin/stdout using JSON-RPC.  You won't see any visible output
# when it's running — that's normal.
#
# USAGE:
#   ./mcp_server.sh          # Start the MCP server (stdin/stdout mode)
#
# DEPENDENCIES:
#   - Python virtual environment at todoist/venv
#   - todoist package + mcp SDK installed in that venv
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
exec "${PYTHON}" -m todoist.mcp_server
