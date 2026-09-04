"""
Step 1: 从 SWE-fficiency 数据集筛选 Intent-Perf-Bench 候选任务

用法：
    python scripts/01_select_candidates.py \
        --output seed/swefficiency_candidates.jsonl \
        --min-speedup 1.20 \
        --repos pandas-dev/pandas numpy/numpy scipy/scipy scikit-learn/scikit-learn
"""

import argparse
import json
import sys

PRIORITY_REPOS = [
    "pandas-dev/pandas",
    "numpy/numpy",
    "scipy/scipy",
    "scikit-learn/scikit-learn",
]

MIN_SPEEDUP_DEFAULT = 1.20


def parse_args():
    p = argparse.ArgumentParser(description="筛选 SWE-fficiency 候选任务")
    p.add_argument("--output", default="seed/swefficiency_candidates.jsonl")
    p.add_argument("--min-speedup", type=float, default=MIN_SPEEDUP_DEFAULT)
    p.add_argument("--repos", nargs="+", default=PRIORITY_REPOS)
    p.add_argument("--split", default="test", help="HuggingFace split（通常是 test）")
    p.add_argument("--top-n", type=int, default=30, help="输出前 N 个候选（人工从中选 6）")
    return p.parse_args()


def load_dataset_safe(split: str):
    """加载数据集，出错时打印有用的诊断信息。"""
    try:
        from datasets import load_dataset
    except ImportError:
        print("请先安装依赖：pip install datasets", file=sys.stderr)
        sys.exit(1)

    print(f"正在加载 swefficiency/swefficiency (split={split!r})...")
    ds = load_dataset("swefficiency/swefficiency", split=split, trust_remote_code=True)
    print(f"  字段列表: {list(ds.features.keys())}")
    print(f"  总任务数: {len(ds)}")
    return ds


def extract_speedup(row: dict) -> float:
    """兼容不同字段名（speedup / expert_speedup / ratio）。"""
    for key in ("speedup", "expert_speedup", "speedup_ratio", "ratio"):
        if key in row and row[key] is not None:
            return float(row[key])
    return 0.0


def row_to_candidate(row: dict) -> dict:
    """将原始数据行转换为规范化的候选任务格式。"""
    return {
        "instance_id":      row.get("instance_id", ""),
        "repo":             row.get("repo", ""),
        "base_commit":      row.get("base_commit", ""),
        "speedup":          extract_speedup(row),
        "workload":         row.get("workload", row.get("workload_script", "")),
        "workload_desc":    row.get("workload_description", row.get("workload_desc", "")),
        "tests":            row.get("tests", row.get("test_files", [])),
        "patch":            row.get("patch", ""),
        "pr_url":           row.get("pr_url", row.get("pull_url", "")),
        "pr_description":   row.get("pr_description", row.get("pr_body", "")),
        # IPB 分类标签（全部历史公开任务为 legacy）
        "provenance":       "legacy",
        "source_benchmark": "swefficiency",
    }


def main():
    args = parse_args()
    ds = load_dataset_safe(args.split)

    # --- 筛选 ---
    candidates = []
    repo_set = set(args.repos)

    for row in ds:
        row = dict(row)
        repo = row.get("repo", "")
        speedup = extract_speedup(row)

        if repo_set and repo not in repo_set:
            continue
        if speedup < args.min_speedup:
            continue

        candidates.append(row_to_candidate(row))

    # 按 speedup 降序，优先选信号强的任务
    candidates.sort(key=lambda x: x["speedup"], reverse=True)
    top = candidates[: args.top_n]

    # --- 输出统计 ---
    print(f"\n筛选结果：{len(candidates)} 个满足条件，输出前 {len(top)} 个")
    repo_counts: dict[str, int] = {}
    for c in top:
        repo_counts[c["repo"]] = repo_counts.get(c["repo"], 0) + 1
    for repo, cnt in sorted(repo_counts.items(), key=lambda x: -x[1]):
        print(f"  {repo}: {cnt} 个")

    # --- 写文件 ---
    import pathlib
    out = pathlib.Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        for c in top:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    print(f"\n已写入 {out}（{len(top)} 行）")
    print("下一步：人工审阅，从中选出 6 个作为 pre-pilot 底层任务，")
    print("        然后运行：python scripts/02_build_task.py --seed-id <instance_id>")


if __name__ == "__main__":
    main()
