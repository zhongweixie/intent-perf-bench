import json

d = json.load(open('results/remeasure_m1.json'))
print("entries:", len(d), "(expect 24)")

n_orig = sum(1 for e in d if 'orig_elapsed' in e)
n_note = sum(1 for e in d if 'orig_unavailable' in e)
both = sum(1 for e in d if 'orig_elapsed' in e and 'orig_unavailable' in e)
print(f"with orig_*: {n_orig}   with note: {n_note}   both (must be 0): {both}")

n_med = sum(1 for e in d if e.get('median') is not None)
n_score = sum(1 for e in d if e.get('score') is not None)
print(f"retaining remeasured median: {n_med}   score: {n_score}")

for e in d:
    if e['task'].startswith('ipb_cpu_002') and e['variant'] == 'exact':
        print("\n" + e['model'])
        for k in ('median', 'correctness_ok', 'orig_elapsed', 'orig_passed',
                  'orig_unavailable', 'error'):
            if k in e:
                print(f"   {k:18} {str(e[k])[:170]}")
