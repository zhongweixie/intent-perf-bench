"""
Step 2: 将 SWE-fficiency 种子任务转换为 IPB 任务目录结构

用法：
    python scripts/02_build_task.py \
        --seed-id pandas__pandas-50741 \
        --task-id ipb_dev_001 \
        --candidates seed/swefficiency_candidates.jsonl
"""

import argparse
import json
import pathlib
import textwrap

TASKS_DIR = pathlib.Path("tasks")

TASK_DIRS = [
    "variants",
    "workspace/repo",
    "workspace/scripts",
    "workspace/data",
    "workspace/docs",
    "workspace/benchmarks",
    "workspace/.github/workflows",
    "evaluation/correctness",
    "evaluation/performance",
    "groundtruth",
]

# 占位 intent.json，人工填写后才能生成变体
INTENT_TEMPLATE = {
    "task_id":             "",
    "level":               "L?",
    "source": {
        "benchmark":       "swefficiency",
        "instance_id":     "",
        "provenance":      "legacy",
    },
    "primary_workload":    "TODO: 用自然语言描述用户实际跑的工作流",
    "primary_metric":      "end-to-end-runtime",
    "threshold":           None,
    "threshold_source":    "TODO: workspace/.github/workflows/performance.yml",
    "primary_targets":     [{"file": "TODO", "symbols": ["TODO"]}],
    "acceptable_targets":  [],
    "misdiagnosed_targets": [],
    "visible_evidence":    [],
    "required_investigation_steps": [
        "run_reproducer", "profile_workload", "read_benchmark",
        "read_threshold_source", "read_correctness_contract"
    ],
    "misdiagnosis_counterfactual": {
        "component_share":          None,
        "maximum_possible_speedup": None,
        "can_meet_threshold":       None
    }
}

MEASUREMENT_TEMPLATE = {
    "baseline_median_s":  None,
    "patched_median_s":   None,
    "expert_speedup":     None,
    "baseline_cv":        None,
    "patched_cv":         None,
    "n_runs":             9,
    "warmup_runs":        3,
    "measured_on":        "TODO: docker image or machine spec",
    "notes":              ""
}


def parse_args():
    p = argparse.ArgumentParser(description="将种子任务转换为 IPB 目录结构")
    p.add_argument("--seed-id",    required=True, help="SWE-fficiency instance_id")
    p.add_argument("--task-id",    required=True, help="IPB task_id，如 ipb_dev_001")
    p.add_argument("--candidates", default="seed/swefficiency_candidates.jsonl")
    return p.parse_args()


def load_seed(seed_id: str, candidates_path: str) -> dict:
    path = pathlib.Path(candidates_path)
    assert path.exists(), f"候选文件不存在: {path}\n请先运行 01_select_candidates.py"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("instance_id") == seed_id:
            return row
    raise ValueError(f"未找到 instance_id={seed_id!r}，请检查 {candidates_path}")


def create_scaffold(task_id: str, seed: dict):
    task_dir = TASKS_DIR / task_id
    for subdir in TASK_DIRS:
        (task_dir / subdir).mkdir(parents=True, exist_ok=True)

    # groundtruth/intent.json（需人工填写）
    intent = dict(INTENT_TEMPLATE)
    intent["task_id"] = task_id
    intent["source"]["instance_id"] = seed["instance_id"]
    intent["source"]["benchmark"]   = seed.get("source_benchmark", "swefficiency")
    intent["source"]["provenance"]  = seed.get("provenance", "legacy")
    _write_json(task_dir / "groundtruth" / "intent.json", intent)

    # groundtruth/measurement.json（由 04_measure_baseline.py 填写）
    _write_json(task_dir / "groundtruth" / "measurement.json", MEASUREMENT_TEMPLATE)

    # groundtruth/expert_patch.diff（从 seed 写入）
    (task_dir / "groundtruth" / "expert_patch.diff").write_text(seed.get("patch", ""))

    # variants/ 占位文件
    for v in ("exact", "target_known", "fuzzy", "misleading"):
        (task_dir / "variants" / f"{v}.md").write_text(f"# {v.upper()} variant\n\nTODO: 由 03_generate_variants.py 生成\n")

    # workspace/scripts/reproduce.py（从 seed workload 生成）
    workload = seed.get("workload", "# TODO: 粘贴 workload 脚本")
    (task_dir / "workspace" / "scripts" / "reproduce.py").write_text(workload)

    print(f"已创建任务目录: {task_dir}")
    print("下一步：")
    print(f"  1. 手动填写 {task_dir}/groundtruth/intent.json 中的 TODO 字段")
    print(f"  2. 运行 python scripts/04_measure_baseline.py --task-id {task_id}")
    print(f"  3. 运行 python scripts/03_generate_variants.py --task-id {task_id}")


def _write_json(path: pathlib.Path, data: dict):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def main():
    args = parse_args()
    seed = load_seed(args.seed_id, args.candidates)
    speedup_str = f"{seed['speedup']:.2f}x" if seed['speedup'] is not None else "未测量"
    print(f"种子任务: {seed['instance_id']}  speedup={speedup_str}  repo={seed['repo']}")
    create_scaffold(args.task_id, seed)


if __name__ == "__main__":
    main()
