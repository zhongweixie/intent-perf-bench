#!/usr/bin/env python3
"""按 run-id 汇总 IPB 评测分数。

区分三种结果，避免把基础设施故障计入模型失败：
  - scored:     benchmark 跑通，improvement_score 有数值
  - structural: 编译/verify/解析失败，score 为 None（任务或环境问题）
同时分别报告 passed（含 threshold）和 score（连续性能），二者是互补维度。
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

STRUCTURAL_MARKERS = (
    "[COMPILE FAILED]", "[UNKNOWN CUDA TASK]", "[could not parse",
    "No such file or directory", "[VERIFY FAILED]",
)


def classify(rec):
    out = rec.get("benchmark_output") or ""
    if rec.get("improvement_score") is None:
        for marker in STRUCTURAL_MARKERS:
            if marker in out:
                return "structural", marker
        return "structural", "no score"
    return "scored", None


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def fmt(x, spec=".3f"):
    return format(x, spec) if isinstance(x, (int, float)) else "  n/a"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True, help="结果文件名中的 run-id 片段")
    ap.add_argument("--results-dir", default=None)
    args = ap.parse_args()

    root = Path(__file__).resolve().parent.parent
    rdir = Path(args.results_dir) if args.results_dir else root / "results"
    files = sorted(p for p in rdir.glob("ipb_*.json") if args.run_id in p.name)
    if not files:
        raise SystemExit(f"没有匹配 run-id={args.run_id} 的结果文件，目录：{rdir}")

    recs = []
    for p in files:
        rec = json.loads(p.read_text())
        rec["_kind"], rec["_why"] = classify(rec)
        recs.append(rec)

    print(f"run-id={args.run_id}  结果文件 {len(recs)} 个")
    scored = [r for r in recs if r["_kind"] == "scored"]
    struct = [r for r in recs if r["_kind"] == "structural"]
    print(f"  有效计分 {len(scored)}  结构性失败 {len(struct)}\n")

    grid = defaultdict(dict)
    for r in recs:
        grid[r["task_id"]][(r["variant"], r["model"])] = r

    variants = ["exact", "fuzzy", "misleading"]
    models = sorted({r["model"] for r in recs})

    for task in sorted(grid):
        cells = grid[task]
        ok = [r for r in cells.values() if r["_kind"] == "scored"]
        print("=" * 78)
        print(f"{task}   有效 {len(ok)}/{len(cells)}")
        if not ok:
            whys = sorted({r["_why"] for r in cells.values()})
            print(f"  全部结构性失败：{', '.join(whys)}")
            print()
            continue
        head = "  " + "变体".ljust(12) + "".join(m.ljust(26) for m in models)
        print(head)
        for v in variants:
            row = "  " + v.ljust(12)
            for m in models:
                r = cells.get((v, m))
                if r is None:
                    row += "—".ljust(26)
                elif r["_kind"] == "structural":
                    row += f"[{r['_why'][:20]}]".ljust(26)
                else:
                    mark = "PASS" if r.get("passed") else "fail"
                    ms = r.get("elapsed_time")
                    row += f"{r['improvement_score']:.3f} {mark} {fmt(ms, '.1f')}ms".ljust(26)
            print(row)
        vs = {v: mean([cells[(v, m)]["improvement_score"]
                       for m in models
                       if (v, m) in cells and cells[(v, m)]["_kind"] == "scored"])
              for v in variants}
        print(f"  变体均分  exact={fmt(vs['exact'])}  fuzzy={fmt(vs['fuzzy'])}"
              f"  misleading={fmt(vs['misleading'])}")
        if vs["exact"] is not None:
            for g in ("fuzzy", "misleading"):
                if vs[g] is not None:
                    print(f"    {g:<11}Gap = {vs['exact'] - vs[g]:+.3f}")
        print()

    print("=" * 78)
    print("模型汇总（只统计有效计分）")
    for m in models:
        rs = [r for r in scored if r["model"] == m]
        if not rs:
            print(f"  {m:<18} 无有效结果")
            continue
        p = sum(1 for r in rs if r.get("passed"))
        print(f"  {m:<18} n={len(rs):<3} 均分={fmt(mean([r['improvement_score'] for r in rs]))}"
              f"  passed={p}/{len(rs)}")

    if struct:
        print("\n结构性失败明细（不计入模型能力）")
        agg = defaultdict(list)
        for r in struct:
            agg[r["task_id"]].append(f"{r['variant']}/{r['model']}: {r['_why']}")
        for t in sorted(agg):
            print(f"  {t}")
            for line in agg[t]:
                print(f"    - {line}")


if __name__ == "__main__":
    main()
