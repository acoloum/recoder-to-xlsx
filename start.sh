#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/.venv/bin/activate"
export QT_QPA_PLATFORM_PLUGIN_PATH="$SCRIPT_DIR/.venv/lib/python3.12/site-packages/PyQt5/Qt5/plugins/platforms"
recorder2xlsx
