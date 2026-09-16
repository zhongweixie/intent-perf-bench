#!/usr/bin/env bash
# Run a command using the workspace Python + repo pandas.
# Usage: ./run.sh scripts/daily_report.py
#        ./run.sh -c "import pandas; print(pandas.__version__)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHONPATH="$SCRIPT_DIR/repo" \
  /aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/ipb_py310_env/bin/python "$@"
