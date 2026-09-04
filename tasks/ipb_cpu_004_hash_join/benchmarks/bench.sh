#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../workspace" && pwd)
cd "$ROOT"
make clean >/dev/null
make >/dev/null
./join --verify >/dev/null
python3 - <<'PY'
import re, subprocess
raw = subprocess.check_output(["./join"], text=True)
m = re.search(r"time=([0-9.]+)", raw)
if not m: raise SystemExit(f"cannot parse benchmark output: {raw}")
print('{"time_ms": %.6f, "runs": 1, "executable": "join"}' % (float(m.group(1))*1000))
PY
