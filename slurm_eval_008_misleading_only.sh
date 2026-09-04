#!/bin/bash
#SBATCH --job-name=ipb-008-misleading
#SBATCH --partition=llm-debug
#SBATCH --qos=llm_debug
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=0-00:30:00
#SBATCH --output=/home/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/slurm_outputs/eval_008_misleading_%j.log
#SBATCH --error=/home/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/slurm_outputs/eval_008_misleading_%j.err

set -e

# ── Environment ──────────────────────────────────────────────────────────────
PYTHON=/aifs4su/hansirui_3rd/gaoyisen/miniconda3/bin/python3
WORK_DIR=/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench
cd $WORK_DIR

# Load CUDA module
module load cuda/12.5

echo "=========================================="
echo "IPB Evaluation: 008 misleading (修改后)"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURMD_NODENAME"
echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"
echo "=========================================="
echo

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
MODEL="gpt-5.6-luna"
MAX_TURNS=15

TASK="ipb_cuda_008_conv1d_shared"
VARIANT="misleading"

run_id="${TASK}_${VARIANT}_${TIMESTAMP}"

echo "=== Running: $TASK / $VARIANT ==="
echo "Run ID: $run_id"

$PYTHON scripts/run_agent.py \
    --task-id "$TASK" \
    --variant "$VARIANT" \
    --model "$MODEL" \
    --provider openai \
    --max-turns $MAX_TURNS \
    --run-id "$run_id"

echo
echo "✓ Completed"
echo

# Show result
$PYTHON << 'PYEOF'
import json
import glob

# Find the latest result
results = sorted(glob.glob("results/ipb_cuda_008_conv1d_shared_misleading_*.json"),
                 key=lambda x: x, reverse=True)

if results:
    with open(results[0]) as f:
        d = json.load(f)

    print("\n" + "="*60)
    print("008 Misleading (修改后) 结果")
    print("="*60)
    print(f"Passed:     {d['passed']}")
    print(f"Time:       {d.get('elapsed_time', 'N/A')}ms")
    print(f"Turns:      {d['turns']}")
    print(f"\n对比之前的结果:")
    print(f"  Fuzzy:      8.61ms")
    print(f"  Misleading (旧): 8.35ms")

    if d.get('elapsed_time'):
        print(f"  Misleading (新): {d['elapsed_time']:.2f}ms")
        print(f"\nGap: fuzzy vs misleading(新) = {8.61 - d['elapsed_time']:.2f}ms")
PYEOF
