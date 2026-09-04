#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../workspace" && pwd)
cd "$ROOT"
make clean >/dev/null
make >/dev/null
./solve --verify >/dev/null
python3 - <<'PY'
import re, subprocess
raw = subprocess.check_output(["./solve"], stderr=subprocess.STDOUT, text=True)
lines = raw.strip().splitlines()
value = lines[-1]
try: seconds = float(value)
except ValueError: raise SystemExit(f"cannot parse benchmark output: {raw}")
print('{"time_ms": %.6f, "runs": 5, "executable": "solve"}' % (seconds*1000))
PY
