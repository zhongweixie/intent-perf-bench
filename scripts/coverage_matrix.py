"""Coverage matrix: which task x variant cells have a usable score.

Two prompt layouts exist. The perf tasks (cuda/cpu) keep variants/<v>.md; the
dev tasks keep variants/system_prompt_<v>.md, and 15 older dev tasks still use
the first form. Both are counted -- keying only on the first form silently
dropped all 43 dev tasks and their 636 result files from this matrix.

A cell counts as usable only if some result file for it is not invalidated and
carries a real improvement_score. Invalidated runs keep their numbers under
invalidated_scores, so counting raw score keys would overstate coverage.
"""
import collections
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).parent.parent
VARIANTS = ("exact", "fuzzy", "misleading")


def prompt_for(d: pathlib.Path, v: str):
    for cand in (f"{v}.md", f"system_prompt_{v}.md", f"{v}.txt"):
        if (d / "variants" / cand).exists():
            return cand
    return None


tasks = {}
for d in sorted((ROOT / "tasks").iterdir()):
    if not d.is_dir() or not (d / "variants").is_dir():
        continue
    toml = (d / "task.toml").read_text() if (d / "task.toml").exists() else ""
    cat = re.search(r'category\s*=\s*"([^"]+)"', toml)
    status = re.search(r'status\s*=\s*"([^"]+)"', toml)
    tasks[d.name] = {
        "prompts": {v: prompt_for(d, v) for v in VARIANTS},
        "category": cat.group(1) if cat else ("dev" if "_dev_" in d.name else "?"),
        "diff_status": status.group(1) if status else None,
    }

valid = collections.defaultdict(set)
invalid = collections.defaultdict(set)
reasons = collections.defaultdict(collections.Counter)
for p in sorted((ROOT / "results").glob("*.json")):
    try:
        data = json.loads(p.read_text())
    except json.JSONDecodeError:
        continue
    if not isinstance(data, dict) or "task_id" not in data:
        continue
    key = (data["task_id"], data.get("variant"))
    model = data.get("model") or "?"
    if "invalidated_scores" in data:
        invalid[key].add(model)
        for r in data.get("invalidated_reasons") or ["?"]:
            reasons[key][r] += 1
    elif data.get("improvement_score") is not None:
        valid[key].add(model)


def cell(name, info, v):
    if not info["prompts"][v]:
        return "NO PROMPT"
    nv, ni = len(valid[(name, v)]), len(invalid[(name, v)])
    if not nv and not ni:
        return "-"
    return f"{nv} ok" + (f" /{ni} bad" if ni else "")


groups = collections.defaultdict(list)
for name, info in tasks.items():
    groups[info["category"]].append((name, info))

for cat in sorted(groups):
    print(f"\n=== {cat} ===")
    print(f"{'task':38} {'exact':>14} {'fuzzy':>14} {'misleading':>14}")
    for name, info in sorted(groups[cat]):
        cells = [cell(name, info, v) for v in VARIANTS]
        if cells == ["-", "-", "-"] and cat == "dev":
            continue  # never run and never scored: not informative here
        print(f"{name:38} {cells[0]:>14} {cells[1]:>14} {cells[2]:>14}")

print("\n" + "=" * 78)
gaps = []
for name, info in sorted(tasks.items()):
    for v in ("fuzzy", "misleading"):
        if not info["prompts"][v]:
            gaps.append((name, v, "no prompt file"))
        elif not valid[(name, v)]:
            why = reasons[(name, v)]
            gaps.append((name, v, ", ".join(sorted(why)) if why else "never run"))

n_cells = 2 * len(tasks)
print(f"tasks with a variants/ dir: {len(tasks)}")
print(f"fuzzy+misleading cells total: {n_cells}   with a valid score: "
      f"{n_cells - len(gaps)}   missing: {len(gaps)}")

by_reason = collections.Counter(g[2] for g in gaps)
print("\nmissing cells by cause:")
for why, n in by_reason.most_common():
    print(f"  {n:4}  {why}")

print("\nmissing cells (task, variant, cause):")
for name, v, why in gaps:
    print(f"  {name:38} {v:11} {why}")
