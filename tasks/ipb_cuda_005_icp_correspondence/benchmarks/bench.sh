#!/bin/bash
set -e
cd "$(dirname "$0")/../workspace"

module load cuda/12.2 2>/dev/null || true
make clean >/dev/null 2>&1
make >/dev/null 2>&1

OUTPUT=$(srun -p llm-debug --qos=llm_debug --gres=gpu:1 -t 60 ./icp_corr --benchmark 2>&1)
TIME_MS=$(printf '%s\n' "$OUTPUT" | grep -oE 'time_ms=[0-9]+\.?[0-9]*' | head -1 | cut -d= -f2)
[ -n "$TIME_MS" ] || { printf '%s\n' "$OUTPUT" >&2; exit 1; }
printf '{"time_ms": %s, "runs": 7, "executable": "icp_corr"}\n' "$TIME_MS"
