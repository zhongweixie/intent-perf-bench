#!/usr/bin/env python3
"""Split results by measurement era before reporting discrimination.

Runs from different eras are not comparable: the g2/g3/g4 CUDA runs used the
leaky variant text (fuzzy naming the file and the target speedup) and the
pre-budget-warning harness, while g5/g5a use rewritten variants and the harness
that warns before the turn cap. Pooling them hides which contrast a number
actually came from, so each era is reported separately.
"""
import collections
import glob
import json
import os

ERAS = {
    "g5": "new harness + rewritten variants",
    "g5a": "new harness + rewritten variants",
    "m1": "CPU batch (variants were never leaky)",
    "g2": "old harness + leaky CUDA variants",
    "g3": "old harness + leaky CUDA variants",
    "g4": "old harness + leaky CUDA variants",
}
VARIANTS = ("exact", "fuzzy", "misleading")


def era_of(run_id):
    if not run_id:
        return "unknown"
    head = str(run_id).split("_")[0]
    return head if head in ERAS else "other"


def load():
    cells = collections.defaultdict(list)
    for fp in glob.glob(os.path.join("results", "*.json")):
        try:
            r = json.load(open(fp))
        except Exception:
            continue
        if not isinstance(r, dict) or "task_id" not in r or r.get("invalidated"):
            continue
        task, variant = r.get("task_id"), r.get("variant")
        if not task or variant not in VARIANTS:
            continue
        cells[(era_of(r.get("run_id")), task, variant)].append(bool(r.get("passed")))
    return cells


def main():
    cells = load()
    eras = sorted({e for e, _, _ in cells},
                  key=lambda e: (e not in ("g5", "g5a"), e))

    for era in eras:
        tasks = sorted({t for e, t, _ in cells if e == era})
        if not tasks:
            continue
        label = ERAS.get(era, "uncategorised")
        print(f"\n=== era {era}: {label} ===")
        print(f"{'task':<40}{'exact':>9}{'fuzzy':>9}{'mislead':>9}   verdict")
        print("-" * 88)
        for task in tasks:
            got = {v: cells.get((era, task, v), []) for v in VARIANTS}

            def cell(v):
                runs = got[v]
                return f"{sum(runs)}/{len(runs)}" if runs else "-"

            e_runs, f_runs, m_runs = got["exact"], got["fuzzy"], got["misleading"]
            if not e_runs:
                verdict = "cannot score (no exact.md)"
            elif not f_runs:
                verdict = "incomplete"
            else:
                e_rate = sum(e_runs) / len(e_runs)
                f_rate = sum(f_runs) / len(f_runs)
                m_rate = sum(m_runs) / len(m_runs) if m_runs else None
                if e_rate == 0 and f_rate == 0 and (m_rate in (0, None)):
                    verdict = "floor: nobody passes, no signal"
                elif e_rate == 1 and f_rate == 1 and m_rate == 1:
                    verdict = "ceiling: everyone passes, no signal"
                else:
                    gap = e_rate - f_rate
                    tail = f" / mislead {m_rate:+.2f}".replace("+", "") if m_rate is not None else ""
                    verdict = f"gap {gap:+.2f}{tail}"
            print(f"{task:<40}{cell('exact'):>9}{cell('fuzzy'):>9}"
                  f"{cell('misleading'):>9}   {verdict}")

    n_new = sum(len(v) for (e, _, _), v in cells.items() if e in ("g5", "g5a"))
    print(f"\nruns under the new harness + rewritten variants: {n_new}")


if __name__ == "__main__":
    main()
