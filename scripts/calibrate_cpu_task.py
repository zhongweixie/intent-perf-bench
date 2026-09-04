#!/usr/bin/env python3
"""Measure a CPU task's regressed and optimal states in an isolated copy.

Written because task.toml numbers have proven untrustworthy: l2norm advertised
a 4-7x regression and actually measures 1.11x, which is inside noise. Before a
task is tagged and run against models, both states must be built, verified and
timed here, several times each, so the claimed gap is checked rather than taken
on faith.
"""
import argparse
import json
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd, cwd, timeout=900):
    return subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str),
                          capture_output=True, text=True, timeout=timeout)


def build(ws, label):
    run("make clean", ws)
    r = run("make", ws)
    if r.returncode != 0:
        return False, f"{label}: build failed: {r.stderr.strip()[:400]}"
    return True, None


def verify(ws, exe, label):
    r = run(f"./{exe} --verify", ws)
    if r.returncode != 0:
        return False, f"{label}: verify failed: {(r.stdout + r.stderr).strip()[:400]}"
    return True, None


def parse_seconds(out):
    """Tasks print timings differently; accept the same forms bench.sh does."""
    m = re.search(r"time=([0-9.]+)", out)
    if m:
        return float(m.group(1))
    lines = [ln.strip() for ln in out.strip().splitlines() if ln.strip()]
    if lines:
        try:
            return float(lines[-1])
        except ValueError:
            pass
    return None


def time_ms(ws, exe, reps):
    times = []
    for _ in range(reps):
        r = run(f"./{exe}", ws)
        out = r.stdout + r.stderr
        seconds = parse_seconds(out)
        if seconds is None:
            return None, f"cannot parse: {out.strip()[:300]}"
        times.append(seconds * 1000.0)
    return times, None


def calibrate(task, exe, reps):
    src = ROOT / "tasks" / task / "workspace"
    opt = next((p for p in src.glob("solve_optimized.*")), None)
    if opt is None:
        return {"task": task, "error": "no solve_optimized.* in workspace"}

    solve = src / ("solve.cpp" if opt.suffix == ".cpp" else "solve.c")
    if not solve.exists():
        return {"task": task, "error": f"missing {solve.name}"}

    out = {"task": task, "executable": exe, "reps": reps}
    with tempfile.TemporaryDirectory(prefix=f"cal_{task}_") as tmp:
        ws = Path(tmp) / "workspace"
        shutil.copytree(src, ws, ignore=shutil.ignore_patterns(".git"))

        for label in ("regressed", "optimal"):
            if label == "optimal":
                shutil.copyfile(ws / opt.name, ws / solve.name)
            ok, err = build(ws, label)
            if not ok:
                out[label] = {"error": err}
                continue
            ok, err = verify(ws, exe, label)
            if not ok:
                out[label] = {"error": err}
                continue
            times, err = time_ms(ws, exe, reps)
            if err:
                out[label] = {"error": f"{label}: {err}"}
                continue
            out[label] = {
                "median_ms": round(statistics.median(times), 4),
                "min_ms": round(min(times), 4),
                "max_ms": round(max(times), 4),
                "times_ms": [round(t, 4) for t in times],
            }

    reg, opti = out.get("regressed", {}), out.get("optimal", {})
    if "median_ms" in reg and "median_ms" in opti and opti["median_ms"] > 0:
        speedup = reg["median_ms"] / opti["median_ms"]
        spread = max(reg["max_ms"] - reg["min_ms"], opti["max_ms"] - opti["min_ms"])
        gap = reg["median_ms"] - opti["median_ms"]
        out["measured_speedup"] = round(speedup, 3)
        out["gap_ms"] = round(gap, 4)
        out["worst_spread_ms"] = round(spread, 4)
        out["gap_exceeds_noise"] = bool(gap > 3 * spread)
        if speedup < 1.0:
            out["verdict"] = "BACKWARDS: the 'optimal' state is slower"
        elif speedup >= 1.5 and out["gap_exceeds_noise"]:
            out["verdict"] = "usable"
        else:
            out["verdict"] = "too small / inside noise"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", nargs="+", required=True)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--out", default=".scratch/cpu_calibration.json")
    args = ap.parse_args()

    exes = {
        "ipb_cpu_002_flash_attention": "attn",
        "ipb_cpu_003_bvh_raytracer": "solve",
        "ipb_cpu_004_hash_join": "join",
        "ipb_cpu_001_gaussian_blur": "blur",
    }

    results = []
    for task in args.tasks:
        exe = exes.get(task)
        if not exe:
            results.append({"task": task, "error": "unknown executable name"})
            print(f"{task}: unknown executable", flush=True)
            continue
        print(f"calibrating {task} ...", flush=True)
        try:
            res = calibrate(task, exe, args.reps)
        except subprocess.TimeoutExpired as exc:
            res = {"task": task, "error": f"timeout: {exc}"}
        results.append(res)
        if "error" in res:
            print(f"  ERROR {res['error']}", flush=True)
        else:
            for label in ("regressed", "optimal"):
                d = res.get(label, {})
                print(f"  {label:<10}"
                      + (d["error"] if "error" in d
                         else f"median {d['median_ms']} ms  (min {d['min_ms']}, max {d['max_ms']})"),
                      flush=True)
            if "measured_speedup" in res:
                print(f"  speedup   {res['measured_speedup']}x  "
                      f"gap {res['gap_ms']} ms vs spread {res['worst_spread_ms']} ms"
                      f"  -> {res['verdict']}", flush=True)

    outp = ROOT / args.out
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(results, indent=2))
    print(f"\nwrote {outp}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
