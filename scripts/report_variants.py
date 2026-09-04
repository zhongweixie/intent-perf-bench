#!/usr/bin/env python3
"""Report fuzzy/misleading measurements per task under the current harness."""
import glob
import json
import os
from collections import defaultdict

NEW_ERAS = ("g5", "g5a", "g5b", "g5c", "g6", "m1")
ORDER = {"exact": 0, "fuzzy": 1, "misleading": 2}


def era(run_id):
    return str(run_id).split("_")[0] if run_id else ""


rows = defaultdict(list)
for fp in glob.glob(os.path.join("results", "*.json")):
    try:
        r = json.load(open(fp))
    except Exception:
        continue
    if not isinstance(r, dict) or "task_id" not in r or r.get("invalidated"):
        continue
    if era(r.get("run_id")) not in NEW_ERAS:
        continue
    sd = r.get("score_detail") or {}
    rows[r["task_id"]].append({
        "variant": r.get("variant"),
        "model": (r.get("model") or "").replace("claude-", ""),
        "passed": bool(r.get("passed")),
        "final": sd.get("final_median_ms"),
        "base": sd.get("baseline_median_ms"),
        "thresh": sd.get("threshold_ms"),
        "speedup": sd.get("speedup"),
    })

print(f"{'task':<32}{'variant':<12}{'model':<10}{'pass':<6}"
      f"{'final ms':>10}{'thresh':>9}{'speedup':>9}")
print("-" * 88)
for task in sorted(rows):
    runs = sorted(rows[task], key=lambda d: (ORDER.get(d["variant"], 9), d["model"]))
    for d in runs:
        f = f"{d['final']:.4f}" if isinstance(d["final"], (int, float)) else "-"
        t = f"{d['thresh']:.4f}" if isinstance(d["thresh"], (int, float)) else "-"
        s = f"{d['speedup']:.2f}x" if isinstance(d["speedup"], (int, float)) else "-"
        print(f"{task:<32}{str(d['variant']):<12}{d['model']:<10}"
              f"{str(d['passed']):<6}{f:>10}{t:>9}{s:>9}")
    print()
