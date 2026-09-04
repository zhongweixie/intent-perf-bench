#!/usr/bin/env bash
# 在 ui2app.sif 容器内运行 run_agent.py
# 用法: ./scripts/run_in_container.sh --task-id ipb_dev_002 --variant fuzzy [--model claude-haiku-4-5-20251001]

set -euo pipefail
APPTAINER=/cm/shared/apps/apptainer/bin/apptainer
SIF=/aifs4su/hansirui_3rd/zxiebk/scripts/UI2APP/ui2app.sif
IPB=/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench

exec $APPTAINER exec \
  --bind /aifs4su:/aifs4su \
  --bind /home/hansirui_3rd:/home/hansirui_3rd \
  $SIF \
  bash -c "
    export ANTHROPIC_AUTH_TOKEN='${ANTHROPIC_AUTH_TOKEN}'
    export ANTHROPIC_BASE_URL='${ANTHROPIC_BASE_URL}'
    cd '$IPB'
    python3 scripts/run_agent.py $*
  "
