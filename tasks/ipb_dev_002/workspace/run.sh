#!/usr/bin/env bash
# Run the daily report.
# Usage: ./run.sh [--parquet path/to/transactions.parquet]
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/scripts/daily_report.py" "$@"
