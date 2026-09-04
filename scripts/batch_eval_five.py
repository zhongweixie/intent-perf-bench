#!/usr/bin/env python3
"""
批量运行五个 IPB 任务的模型评测

用法：
  export OPENAI_API_KEY=sk-...
  export OPENAI_BASE_URL=https://...
  python scripts/batch_eval_five.py --models gpt-5.6-luna gpt-5.6-terra --variants normal fuzzy misleading
"""

import argparse
import subprocess
import sys
import json
from pathlib import Path

TASKS = [
    "ipb_cpu_001_gaussian_blur",
    "ipb_cpu_002_flash_attention",
    "ipb_cpu_003_bvh_raytracer",
    "ipb_cpu_004_hash_join",
    "ipb_cuda_005_l2norm_reduction",
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", required=True, help="模型列表")
    parser.add_argument("--variants", nargs="+", default=["exact", "fuzzy", "misleading"])
    parser.add_argument("--max-turns", type=int, default=15)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).parent.parent
    results_dir = root / "results"
    results_dir.mkdir(exist_ok=True)

    runs = []
    for task in TASKS:
        for variant in args.variants:
            for model in args.models:
                runs.append((task, variant, model))

    print(f"将执行 {len(runs)} 次评测：")
    print(f"  任务：{TASKS}")
    print(f"  变体：{args.variants}")
    print(f"  模型：{args.models}")
    print()

    if args.dry_run:
        for task, variant, model in runs:
            print(f"  {task} / {variant} / {model}")
        return

    failed = []
    python_exe = "/aifs4su/hansirui_3rd/gaoyisen/miniconda3/bin/python3"
    for i, (task, variant, model) in enumerate(runs, 1):
        print(f"\n[{i}/{len(runs)}] {task} / {variant} / {model}")
        cmd = [
            python_exe, str(root / "scripts/run_agent.py"),
            "--task-id", task,
            "--variant", variant,
            "--provider", "openai",
            "--model", model,
            "--max-turns", str(args.max_turns),
        ]
        try:
            subprocess.run(cmd, check=True, cwd=str(root))
        except subprocess.CalledProcessError as e:
            print(f"✗ 失败: {e}")
            failed.append((task, variant, model))
        except KeyboardInterrupt:
            print("\n用户中断")
            sys.exit(1)

    print("\n" + "="*60)
    print(f"完成 {len(runs) - len(failed)}/{len(runs)} 次评测")
    if failed:
        print(f"\n失败 ({len(failed)}):")
        for task, variant, model in failed:
            print(f"  - {task} / {variant} / {model}")
    else:
        print("全部成功")

if __name__ == "__main__":
    main()
