"""Clear orig_* fields in remeasure_m1.json that provably belong to the other model.

The orig_* columns were copied from results/<task>_<variant>_m1.json. That
filename has no model in it, so when two models both ran under run-id m1 the
second clobbered the first (#109) -- and every one of the 12 task+variant pairs
then read the same surviving file for both of its entries. In each pair, the
entry whose model matches the surviving file keeps its genuine orig_*; the other
entry's orig_* is the wrong model's run and is removed.

The remeasured columns (median, samples, cv, score, correctness_ok) are left
alone: those came from each model's own retained workspace, whose path embeds
the model, and 11 of 12 pairs have differing medians.

Nothing is invented. Unattributable numbers are dropped and replaced with a
marker saying why, because leaving orig_passed=True on the opus-5 cpu_002/exact
row -- a run whose source was contaminated and never built -- is the specific
misreading this cleanup exists to prevent.
"""
import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent
REPORT = ROOT / "results" / "remeasure_m1.json"
ORIG_KEYS = ("orig_elapsed", "orig_passed", "orig_improvement")
NOTE = ("orig_* removed: results/{task}_{variant}_m1.json holds the "
        "{winner} run (run-id collision, #109), so the original figures for "
        "this model were overwritten and cannot be recovered")


def main() -> int:
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    args = p.parse_args()

    entries = json.loads(REPORT.read_text())
    cleared = kept = 0
    for e in entries:
        per_run = ROOT / "results" / f"{e['task']}_{e['variant']}_m1.json"
        if not per_run.exists():
            continue
        winner = json.loads(per_run.read_text()).get("model")
        if winner == e["model"]:
            kept += 1
            continue
        if not any(k in e for k in ORIG_KEYS):
            continue
        print(f"  clear  {e['task'][:30]:30} {e['variant']:11} {e['model']:16} "
              f"(file holds {winner}) was elapsed={e.get('orig_elapsed')} "
              f"passed={e.get('orig_passed')}")
        cleared += 1
        if args.apply:
            for k in ORIG_KEYS:
                e.pop(k, None)
            e["orig_unavailable"] = NOTE.format(
                task=e["task"], variant=e["variant"], winner=winner)

    print(f"\n{'would clear' if args.dry_run else 'cleared'} {cleared} "
          f"entr(ies); {kept} kept (orig_* genuinely theirs)")
    if args.apply:
        REPORT.write_text(json.dumps(entries, indent=2, default=str) + "\n")
        print(f"wrote {REPORT.relative_to(ROOT)}")
    else:
        print("dry run; re-run with --apply to write")
    return 0


if __name__ == "__main__":
    sys.exit(main())
