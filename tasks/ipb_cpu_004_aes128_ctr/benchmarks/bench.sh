#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../workspace" && pwd)
cd "$ROOT"
make clean >/dev/null
make >/dev/null
python3 - <<'PY'
import re, subprocess
raw = subprocess.check_output(["./solve"], text=True)
m = re.search(r"time=([0-9.]+)", raw)
if not m or "result=ok" not in raw: raise SystemExit(f"benchmark failed: {raw}")
print('{"time_ms": %.6f, "runs": 5, "executable": "solve"}' % (float(m.group(1))*1000))
PY
