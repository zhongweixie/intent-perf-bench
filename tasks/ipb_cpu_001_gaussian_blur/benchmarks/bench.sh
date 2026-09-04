#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../workspace" && pwd)
cd "$ROOT"
make clean >/dev/null
make >/dev/null
python3 - <<'PY'
import os, subprocess, re
raw = subprocess.check_output(["./blur", "/dev/zero", "-", "256", "256"], text=True)
m = re.search(r"time=([0-9.]+)", raw)
if not m: raise SystemExit(f"cannot parse benchmark output: {raw}")
print('{"time_ms": %.6f, "runs": 1, "executable": "blur"}' % (float(m.group(1))*1000))
PY
