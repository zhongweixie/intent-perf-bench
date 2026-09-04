#!/usr/bin/env python3
"""Inventory of fuzzy/misleading coverage across every task.

For each task reports: whether the variant file exists, whether the task is
eligible to be scored at all (a regression inside measurement noise cannot
separate models), and how many runs exist under the current harness.
"""
import glob
import json
import os
import collections

try:
    import tomllib
except ImportError:
    import tomli as tomllib

NEW_ERAS = ("g5", "g5a", "g5b", "g5c", "g6", "m1")
VARIANTS = ("fuzzy", "misleading")


def era_of(run_id):
    return str(run_id).split("_")[0] if run_id else ""


def load_results():
    per = collections.defaultdict(list)
    for fp in glob.glob(os.path.join("results", "*.json")):
        try:
            r = json.load(open(fp))
        except Exception:
            continue
        if not isinstance(r, dict) or "task_id" not in r or r.get("invalidated"):
            continue
        per[(r.get("task_id"), r.get("variant"))].append({
            "era": era_of(r.get("run_id")),
            "passed": bool(r.get("passed")),
            "model": r.get("model"),
        })
    return per


def task_meta(path):
    try:
        d = tomllib.load(open(path, "rb"))
    except Exception:
        return {}
    flat = {}
    for section in d.values():
        if isinstance(section, dict):
            flat.update(section)
    flat.update({k: v for k, v in d.items() if not isinstance(v, dict)})
    return flat


def main():
    per = load_results()
    rows = []
    for tpath in sorted(glob.glob("tasks/*/task.toml")):
        tdir = os.path.dirname(tpath)
        task = os.path.basename(tdir)
        meta = task_meta(tpath)
        classification = str(meta.get("classification", "") or "")
        scorable = meta.get("scorable")
        blocked = classification in ("blocked", "trivial_control") or scorable is False

        cells = {}
        for v in VARIANTS:
            has_file = os.path.exists(os.path.join(tdir, "variants", f"{v}.md"))
            runs = per.get((task, v), [])
            fresh = [r for r in runs if r["era"] in NEW_ERAS]
            cells[v] = (has_file, len(fresh), sum(1 for r in fresh if r["passed"]),
                        len(runs))
        rows.append((task, classification, blocked, cells))

    need_file = []
    need_runs = []
    excluded = []

    print(f"{'task':<40}{'class':<16}{'fuzzy':<16}{'misleading':<16}status")
    print("-" * 104)
    for task, classification, blocked, cells in rows:
        def cell(v):
            has_file, fresh, passed, total = cells[v]
            if not has_file:
                return "NO FILE"
            if fresh == 0:
                return f"0 new ({total} old)"
            return f"{passed}/{fresh} new"

        missing = [v for v in VARIANTS if not cells[v][0]]
        no_fresh = [v for v in VARIANTS if cells[v][0] and cells[v][1] == 0]

        if blocked:
            status = f"EXCLUDED ({classification or 'scorable=false'})"
            excluded.append(task)
        elif missing:
            status = f"need file: {','.join(missing)}"
            need_file.append((task, missing))
        elif no_fresh:
            status = f"need runs: {','.join(no_fresh)}"
            need_runs.append((task, no_fresh))
        else:
            status = "covered"
        print(f"{task:<40}{classification[:15]:<16}{cell('fuzzy'):<16}"
              f"{cell('misleading'):<16}{status}")

    print()
    print(f"excluded from scoring      : {len(excluded)}")
    print(f"missing a variant file     : {len(need_file)}")
    print(f"have files, need fresh runs: {len(need_runs)}")
    print()
    if need_runs:
        print("runs needed (task / variant):")
        for task, vs in need_runs:
            for v in vs:
                print(f"  {task} / {v}")
    if need_file:
        print("\nvariant files to author:")
        for task, vs in need_file:
            print(f"  {task}: {', '.join(vs)}")


if __name__ == "__main__":
    main()
