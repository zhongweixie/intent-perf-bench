#!/usr/bin/env python3
"""Per-task pass rates by variant, plus Fuzzy Gap where computable."""
import collections
import glob
import json
import os

rows = collections.defaultdict(list)
for fp in glob.glob(os.path.join('results', '*.json')):
    try:
        r = json.load(open(fp))
    except Exception:
        continue
    if not isinstance(r, dict) or 'task_id' not in r:
        continue
    if r.get('invalidated'):
        continue
    task, variant = r.get('task_id'), r.get('variant')
    if not task or not variant:
        continue
    rows[(task, variant)].append({
        'passed': bool(r.get('passed')),
        'model': r.get('model'),
        'run_id': r.get('run_id'),
        'file': os.path.basename(fp),
    })

VARIANTS = ('exact', 'fuzzy', 'misleading')
tasks = sorted({t for t, _ in rows})

print(f"{'task':<40}{'exact':>10}{'fuzzy':>10}{'mislead':>10}   Fuzzy-Gap")
print('-' * 88)
for task in tasks:
    cells = {}
    for v in VARIANTS:
        runs = rows.get((task, v), [])
        cells[v] = (sum(1 for x in runs if x['passed']), len(runs)) if runs else None

    def fmt(c):
        return f"{c[0]}/{c[1]}" if c else '-'

    e, f = cells['exact'], cells['fuzzy']
    if e and f:
        gap = f"{e[0] / e[1] - f[0] / f[1]:+.2f}"
    elif not e:
        gap = 'N/A (no exact.md)'
    else:
        gap = 'N/A'
    print(f"{task:<40}{fmt(cells['exact']):>10}{fmt(cells['fuzzy']):>10}"
          f"{fmt(cells['misleading']):>10}   {gap}")

print()
print('run-id breakdown (which batch produced each cell):')
for task in tasks:
    for v in VARIANTS:
        for run in rows.get((task, v), []):
            print(f"  {task:<38} {v:<11} {str(run['model']):<18} "
                  f"passed={run['passed']!s:<5} {run['run_id']}")
