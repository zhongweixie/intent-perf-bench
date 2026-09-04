#!/bin/bash
#SBATCH --job-name=ipb-eval-008
#SBATCH --partition=llm-debug
#SBATCH --qos=llm_debug
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=0-01:00:00
#SBATCH --output=/home/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/slurm_outputs/eval_008_%j.log
#SBATCH --error=/home/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/slurm_outputs/eval_008_%j.err

set -e

# ── Environment ──────────────────────────────────────────────────────────────
PYTHON=/aifs4su/hansirui_3rd/gaoyisen/miniconda3/bin/python3
WORK_DIR=/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench
cd $WORK_DIR

# Load CUDA module
module load cuda/12.5

echo "=========================================="
echo "IPB Evaluation: 008 only (fuzzy vs misleading)"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURMD_NODENAME"
echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"
echo "=========================================="
echo

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
MODEL="gpt-5.6-luna"
MAX_TURNS=15

TASK="ipb_cuda_008_conv1d_shared"
VARIANTS=("fuzzy" "misleading")

for variant in "${VARIANTS[@]}"; do
    run_id="${TASK}_${variant}_${TIMESTAMP}"

    echo "=== Running: $TASK / $variant ==="
    echo "Run ID: $run_id"

    $PYTHON scripts/run_agent.py \
        --task-id "$TASK" \
        --variant "$variant" \
        --model "$MODEL" \
        --provider openai \
        --max-turns $MAX_TURNS \
        --run-id "$run_id"

    echo
    echo "✓ Completed: $TASK / $variant"
    echo
    sleep 5
done

echo "=========================================="
echo "Evaluation complete!"
echo "=========================================="
echo

# Summary
$PYTHON << 'PYEOF'
import json
import glob
import sys

results = []
for f in glob.glob("results/ipb_cuda_008_*.json"):
    with open(f) as fp:
        d = json.load(fp)
        # Filter today's results
        if "20260823" in d.get("run_id", ""):
            results.append({
                "task": d["task_id"],
                "variant": d["variant"],
                "passed": d["passed"],
                "time_ms": d.get("elapsed_time"),
                "turns": d.get("turns", "?"),
                "run_id": d["run_id"]
            })

if not results:
    print("No results found for task 008")
    sys.exit(0)

# Sort by run_id to get latest
results.sort(key=lambda x: x["run_id"], reverse=True)

print("\n=== 008 (1D Convolution) Results ===")
print("Variant     | Passed | Time(ms) | Turns | Run ID")
print("-" * 80)
seen = set()
for r in results:
    key = r['variant']
    if key in seen:
        continue
    seen.add(key)

    time_str = f"{r['time_ms']:.2f}" if r['time_ms'] is not None else "N/A"
    print(f"{r['variant']:11} | {str(r['passed']):6} | {time_str:>8} | {r['turns']:>5} | {r['run_id'][-20:]}")

print("\nReference:")
print("  Baseline:  12.99ms")
print("  Reference: 8.92ms")

# Calculate Gap if we have both
by_variant = {r['variant']: r for r in results if r['variant'] in seen}
if 'fuzzy' in by_variant and 'misleading' in by_variant:
    fuzzy_time = by_variant['fuzzy']['time_ms']
    misleading_time = by_variant['misleading']['time_ms']
    if fuzzy_time is not None and misleading_time is not None:
        print(f"\nGap: fuzzy={fuzzy_time:.2f}ms, misleading={misleading_time:.2f}ms")
        print(f"Difference: {misleading_time - fuzzy_time:+.2f}ms")
PYEOF
