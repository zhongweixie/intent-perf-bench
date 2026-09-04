#!/usr/bin/env bash
# scripts/measure_with_apptainer.sh
#
# 使用 Apptainer 对 ipb_dev_001 进行准确的 baseline 和 patched 性能测量。
# 依赖：/cm/shared/apps/apptainer/bin/apptainer（集群已安装）
#
# 用法：
#   bash scripts/measure_with_apptainer.sh [--task-id ipb_dev_001] [--sif-dir /raid/hansirui_3rd/ipb_sif]
#
# 流程：
#   1. 把 Docker 镜像 pull 成 SIF（已有则跳过）
#   2. 在未修改的容器里运行 benchmark → baseline
#   3. 从 SIF 建 writable sandbox，apply expert patch，rebuild pandas
#   4. 在 sandbox 里运行 benchmark → patched
#   5. 计算 speedup，写入 groundtruth/measurement.json

set -euo pipefail

# ─── 参数 ───────────────────────────────────────────────────────────────────
TASK_ID="ipb_dev_001"
SIF_DIR="/aifs4su/hansirui_3rd/claw_images"
APPTAINER="/cm/shared/apps/apptainer/bin/apptainer"
DOCKER_IMAGE="ghcr.io/swefficiency/swefficiency-images:pandas-dev__pandas-38248"
N_RUNS=9
WARMUP=3
THRESHOLD=1.5

while [[ $# -gt 0 ]]; do
  case $1 in
    --task-id)   TASK_ID="$2";   shift 2 ;;
    --sif-dir)   SIF_DIR="$2";   shift 2 ;;
    --n-runs)    N_RUNS="$2";    shift 2 ;;
    --warmup)    WARMUP="$2";    shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TASK_DIR="$PROJECT_DIR/tasks/$TASK_ID"
WORKSPACE="$TASK_DIR/workspace"
GROUNDTRUTH="$TASK_DIR/groundtruth"

# ─── 检查前置条件 ────────────────────────────────────────────────────────────
[ -x "$APPTAINER" ] || { echo "ERROR: apptainer not found: $APPTAINER"; exit 1; }
[ -d "$TASK_DIR" ]  || { echo "ERROR: task dir not found: $TASK_DIR";  exit 1; }
[ -f "$GROUNDTRUTH/expert_patch.diff" ] || { echo "ERROR: expert_patch.diff missing"; exit 1; }

mkdir -p "$SIF_DIR"
SIF_NAME="swefficiency-${TASK_ID}.sif"
SIF_PATH="$SIF_DIR/$SIF_NAME"
SANDBOX_PATH="$SIF_DIR/${TASK_ID}_sandbox"

echo "=== IPB Apptainer 性能测量 ==="
echo "  task:   $TASK_ID"
echo "  SIF:    $SIF_PATH"
echo "  image:  $DOCKER_IMAGE"
echo ""

# ─── Step 1：Pull Docker → SIF ──────────────────────────────────────────────
if [ -f "$SIF_PATH" ]; then
  echo "[1/4] SIF 已存在，跳过 pull"
else
  echo "[1/4] 拉取 Docker 镜像为 SIF（可能需要 5-10 分钟）..."
  APPTAINER_CACHEDIR="$SIF_DIR/.cache" \
    "$APPTAINER" pull "$SIF_PATH" "docker://$DOCKER_IMAGE"
  echo "  → $SIF_PATH ($(du -sh "$SIF_PATH" | cut -f1))"
fi

# ─── Step 2：Baseline 测量（原始镜像，未打 patch 的 pandas）───────────────────
echo ""
echo "[2/4] 测量 baseline（容器内 pandas 1.1.x，pre-GH#37462）..."

BENCHMARK_SCRIPT="$WORKSPACE/benchmarks/datetime_compare.py"

BASELINE_OUT=$("$APPTAINER" exec \
  --bind "$WORKSPACE:/workspace" \
  --no-home \
  --env "PYTHONPATH=/testbed" \
  "$SIF_PATH" \
  python3 /workspace/benchmarks/datetime_compare.py 2>/dev/null)

echo "$BASELINE_OUT"
BASELINE_MEDIAN=$(echo "$BASELINE_OUT" | grep "^Median:" | awk '{print $2}' | sed 's/s//')
echo "  → baseline median: ${BASELINE_MEDIAN}s"

# ─── Step 3：建立 writable sandbox 并打 patch ────────────────────────────────
echo ""
echo "[3/4] 建立 sandbox，apply expert patch，rebuild pandas..."

if [ -d "$SANDBOX_PATH" ]; then
  echo "  sandbox 已存在，清理重建..."
  rm -rf "$SANDBOX_PATH"
fi

"$APPTAINER" build --sandbox "$SANDBOX_PATH" "$SIF_PATH"

# 在 sandbox 内 apply patch + rebuild
"$APPTAINER" exec --writable \
  --bind "$GROUNDTRUTH:/groundtruth" \
  "$SANDBOX_PATH" \
  bash -c "
    set -e
    cd /testbed
    echo '  applying expert patch...'
    git apply /groundtruth/expert_patch.diff
    echo '  rebuilding pandas (pip install -e .)...'
    pip install -e . --no-build-isolation -q 2>&1 | tail -3
    echo '  rebuild done'
  "
echo "  → patch applied and pandas rebuilt"

# ─── Step 4：Patched 测量 ────────────────────────────────────────────────────
echo ""
echo "[4/4] 测量 patched 性能..."

PATCHED_OUT=$("$APPTAINER" exec \
  --bind "$WORKSPACE:/workspace" \
  --no-home \
  --env "PYTHONPATH=/testbed" \
  "$SANDBOX_PATH" \
  python3 /workspace/benchmarks/datetime_compare.py 2>/dev/null)

echo "$PATCHED_OUT"
PATCHED_MEDIAN=$(echo "$PATCHED_OUT" | grep "^Median:" | awk '{print $2}' | sed 's/s//')
echo "  → patched median: ${PATCHED_MEDIAN}s"

# ─── 计算结果 ────────────────────────────────────────────────────────────────
SPEEDUP=$(python3 -c "print(round(${BASELINE_MEDIAN} / ${PATCHED_MEDIAN}, 4))")
PASS=$(python3 -c "print('PASS' if ${SPEEDUP} >= ${THRESHOLD} else 'FAIL')")

echo ""
echo "=== 结果 ==="
echo "  baseline:  ${BASELINE_MEDIAN}s"
echo "  patched:   ${PATCHED_MEDIAN}s"
echo "  speedup:   ${SPEEDUP}x  (threshold=${THRESHOLD}x)  → $PASS"

# ─── 写入 measurement.json ───────────────────────────────────────────────────
python3 - <<PYEOF
import json, pathlib, datetime

out = pathlib.Path("$GROUNDTRUTH/measurement.json")
data = json.loads(out.read_text()) if out.exists() else {}

data.update({
    "baseline_median_s":  float("$BASELINE_MEDIAN"),
    "patched_median_s":   float("$PATCHED_MEDIAN"),
    "expert_speedup":     float("$SPEEDUP"),
    "n_runs":             $N_RUNS,
    "warmup_runs":        $WARMUP,
    "measured_on":        "$(hostname)",
    "method":             "apptainer: $DOCKER_IMAGE",
    "apptainer_sif":      "$SIF_PATH",
    "measured_at":        "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "WARNING":            None,
})

out.write_text(json.dumps(data, indent=2) + "\n")
print(f"已写入 {out}")
PYEOF

# ─── 清理 sandbox（保留 SIF）────────────────────────────────────────────────
rm -rf "$SANDBOX_PATH"
echo "sandbox 已清理，SIF 保留在 $SIF_PATH"
echo ""
echo "完成。重新测量请直接重跑此脚本（SIF 不会重新下载）。"
