#!/usr/bin/env python3
"""Run batches g5 and g6 sequentially with the new harness."""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON = "/aifs4su/hansirui_3rd/gaoyisen/miniconda3/bin/python3"
RUN_AGENT = ROOT / "scripts/run_agent.py"

def run_batch(batch_name, batch_file, max_turns, parallel):
    """Run all lines in batch_file, serial execution (parallel=1 is safest for workspace isolation)."""
    lines = [ln.strip() for ln in open(batch_file) if ln.strip()]
    print(f"\nbatch {batch_name}: {len(lines)} runs, parallel={parallel}")
    print(f"  scratch: {ROOT / '.scratch' / f'batch_{batch_name}'}")
    print(f"  logs:    {ROOT / 'results/batch_logs' / batch_name}")
    logdir = ROOT / "results/batch_logs" / batch_name
    logdir.mkdir(parents=True, exist_ok=True)

    ok = 0
    for i, ln in enumerate(lines, 1):
        task, variant, model = [x.strip() for x in ln.split('/')]
        run_id = f"{batch_name}_{model.replace('claude-','')}"
        log = logdir / f"{task}__{variant}__{model.replace('claude-','')}.log"

        cmd = [PYTHON, str(RUN_AGENT), "--task-id", task, "--variant", variant,
               "--model", model, "--max-turns", str(max_turns),
               "--budget-warning-turns", "5", "--run-id", run_id]

        print(f"[{i}/{len(lines)}] {task} / {variant} / {model} ... ", end='', flush=True)
        t0 = time.time()
        try:
            with open(log, 'w') as f:
                subprocess.run(cmd, cwd=str(ROOT), stdout=f, stderr=subprocess.STDOUT,
                               check=True, timeout=1800)
            ok += 1
            print(f"ok  ({time.time()-t0:.1f}s)")
        except subprocess.TimeoutExpired:
            print(f"TIMEOUT")
        except subprocess.CalledProcessError as e:
            print(f"FAILED exit {e.returncode}")
        except Exception as e:
            print(f"ERROR {e}")

    print("="*70)
    print(f"batch {batch_name}: {ok}/{len(lines)} ok")
    if ok < len(lines):
        print(f"  FAILED {' '.join(str(logdir / f.name) for f in logdir.iterdir())}")
    print(f"{batch_name} finished at {time.strftime('%c')}")
    return ok == len(lines)

if __name__ == "__main__":
    source_secrets = "source /home/hansirui_3rd/zxiebk/scripts/claw/claw-adapters/train/rl/load_secrets.sh"
    subprocess.run(source_secrets, shell=True, executable='/bin/bash')

    # GPU tasks need IPB_GPU_JOBID
    import os
    os.environ['IPB_GPU_JOBID'] = '373841'

    g5_ok = run_batch('g5', ROOT / '.scratch/batch_g5.txt', max_turns=30, parallel=1)
    if not g5_ok:
        print("\nWARNING: g5 had failures, but continuing to g6")

    g6_ok = run_batch('g6', ROOT / '.scratch/batch_g6.txt', max_turns=30, parallel=1)

    sys.exit(0 if (g5_ok and g6_ok) else 1)
