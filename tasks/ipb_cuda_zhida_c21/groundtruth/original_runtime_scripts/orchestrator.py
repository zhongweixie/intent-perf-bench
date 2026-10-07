"""Two C21 budget-sensitivity rounds with two concurrent isolated agent arms."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import statistics
import subprocess
import sys
import time

from remote_client import evaluate
from remote_controller import ROOT, catalog, dump, secret, sources

CONDITIONS = ["fuzzy", "misleading_other"]
ARMS = ["base"] + CONDITIONS
FAMILIES = ["small", "main", "wide_hidden"]
ORDERS = [
    ["base", "fuzzy", "misleading_other"],
    ["misleading_other", "base", "fuzzy"],
    ["fuzzy", "misleading_other", "base"],
]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def progress(root, phase, **details):
    dump(root / "run_status.json", {"phase": phase, "updated_at": datetime.datetime.now().isoformat(), **details})
    print("STATUS", phase, json.dumps(details, ensure_ascii=False), flush=True)


def validate_package(protocol):
    if protocol["wall_seconds"] != 500 or protocol["conditions"] != CONDITIONS or protocol["rounds"] != 2:
        raise RuntimeError("Frozen C21 protocol mismatch")
    for name, expected in protocol["public_hashes"].items():
        actual = hashlib.sha256((ROOT / "public" / name).read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError("Public package hash mismatch: " + name)
    for name, expected in protocol["prompt_hashes"].items():
        actual = hashlib.sha256((ROOT / "private" / (name + ".txt")).read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError("Prompt package hash mismatch: " + name)


def episode(round_dir, condition, protocol, namespace):
    output = round_dir / condition
    output.mkdir(parents=True, exist_ok=False)
    args = [sys.executable, "-u", str(ROOT / "scripts" / "agent_episode.py"), condition, str(output), namespace]
    started = time.monotonic()
    with (output / "agent.log").open("w", encoding="utf-8") as logfile:
        child = subprocess.Popen(args, cwd=ROOT, stdout=logfile, stderr=subprocess.STDOUT,
                                 env=os.environ.copy(), start_new_session=True)
        while child.poll() is None:
            now = time.monotonic()
            real = now - started
            clock_file = output / "clock.json"
            if clock_file.exists():
                clock = load(clock_file)
                waiting = ((now - clock["queue_since_monotonic"])
                           if clock["queue_since_monotonic"] is not None else 0.0)
                queued = clock["paused_seconds"] + waiting
                active = now - clock["start_monotonic"] - queued
            else:
                active, queued = real, 0.0
            if (active > protocol["wall_seconds"] + 4 or
                    queued > protocol["max_queue_wait_seconds"] + 4 or
                    real > protocol["wall_seconds"] + protocol["max_queue_wait_seconds"] + 4):
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait(timeout=2)
                dump(output / "watchdog.json", {"triggered": True, "active_seconds": active,
                                                "queue_seconds": queued, "real_seconds": real})
                raise RuntimeError("External deadline reached for " + condition)
            time.sleep(0.5)
        if child.returncode:
            raise RuntimeError(f"Agent worker failed for {condition}; see {output / 'agent.log'}")
    status = load(output / "status.json")
    if status["agent_seconds"] > protocol["wall_seconds"] + 3:
        raise RuntimeError("Agent duration exceeded limit for " + condition)
    return status


def result_medians(item):
    if not item.get("correct"):
        return None
    mapping = {case["name"]: case["median_us"] for case in item.get("cases", [])}
    return mapping if all(name in mapping for name in FAMILIES) else None


def score_round(round_dir):
    family = {}
    for family_name in FAMILIES:
        family[family_name] = {}
        for arm in ARMS:
            values = []
            for block in range(1, len(ORDERS) + 1):
                item = load(round_dir / "final_comparison" / f"block{block}-{arm}.json")
                medians = result_medians(item)
                if medians is not None:
                    values.append(medians[family_name])
            family[family_name][arm] = statistics.median(values) if len(values) == len(ORDERS) else None
    speedups = {}
    for arm in CONDITIONS:
        final = load(round_dir / arm / "final_evaluation.json")
        ratios = [family[name]["base"] / family[name][arm] for name in FAMILIES
                  if family[name]["base"] and family[name][arm]]
        speedups[arm] = (math.exp(statistics.mean(map(math.log, ratios)))
                         if final.get("correct") and len(ratios) == len(FAMILIES) else None)
    usage = {arm: load(round_dir / arm / "status.json") for arm in CONDITIONS}
    summary = {"family_median_us": family, "final_geomean_speedup": speedups,
               "per_condition_status": usage,
               "score_method": "Three equal-weight BF16 full-call families; three balanced rotated block medians; correctness-gated."}
    dump(round_dir / "summary.json", summary)
    return summary


def run_round(root, number, protocol, baseline):
    round_dir = root / f"round{number}"
    round_dir.mkdir(parents=True, exist_ok=False)
    namespaces = {arm: f"{root.name}-r{number}-{arm}" for arm in ARMS}
    progress(root, "prewarm", round=number)
    for arm in ARMS:
        result = evaluate(baseline, namespaces[arm], timeout=180)
        dump(round_dir / f"prewarm-{arm}.json", result)
        if not result.get("correct"):
            raise RuntimeError(f"Baseline prewarm failed for round {number}, {arm}: {result.get('error')}")
    progress(root, "agents_running", round=number, conditions=CONDITIONS)
    with ThreadPoolExecutor(max_workers=len(CONDITIONS)) as pool:
        futures = {pool.submit(episode, round_dir, arm, protocol, namespaces[arm]): arm for arm in CONDITIONS}
        for future in as_completed(futures):
            arm = futures[future]
            status = future.result()
            print("AGENT_END", number, arm, status["stop_reason"], round(status["agent_seconds"], 1), flush=True)
            if status["stop_reason"] == "infrastructure_error":
                raise RuntimeError(f"Infrastructure error in round {number}, {arm}")
    frozen = {"base": baseline}
    progress(root, "hidden_grading", round=number)
    for arm in CONDITIONS:
        files = {p.name: p.read_text(encoding="utf-8") for p in (round_dir / arm / "public").glob("*.py")}
        frozen[arm] = files
        result = evaluate(files, namespaces[arm], timeout=180, final=True, seed=32000 + number * 100)
        dump(round_dir / arm / "final_evaluation.json", result)
        if result.get("infrastructure_error"):
            raise RuntimeError(f"Final grader failure in round {number}, {arm}")
    progress(root, "final_scoring", round=number)
    for block, order in enumerate(ORDERS, 1):
        for arm in order:
            result = evaluate(frozen[arm], namespaces[arm], timeout=180,
                              final=True, seed=42000 + number * 1000 + block * 10)
            dump(round_dir / "final_comparison" / f"block{block}-{arm}.json", result)
            if result.get("infrastructure_error"):
                raise RuntimeError(f"Scoring infrastructure failure in round {number}, block {block}, {arm}")
    summary = score_round(round_dir)
    dump(round_dir / "completed.json", {"round": number, "scores": summary["final_geomean_speedup"]})
    progress(root, "round_complete", round=number, scores=summary["final_geomean_speedup"])
    return summary


def main():
    run_dir = Path(sys.argv[1]).resolve()
    if run_dir.parent != ROOT / "runs":
        raise RuntimeError("Invalid run directory")
    protocol = load(ROOT / "private" / "protocol.json")
    validate_package(protocol)
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise RuntimeError("OPENROUTER_API_KEY is absent from launcher environment")
    dump(run_dir / "protocol.json", protocol)
    dump(run_dir / "public_snapshot.json", {p.name: p.read_text(encoding="utf-8")
                                            for p in (ROOT / "public").iterdir() if p.is_file()})
    dump(run_dir / "model_catalog.json", catalog(secret(), protocol["model"]))
    baseline = sources()
    summaries = []
    for number in range(1, protocol["rounds"] + 1):
        summaries.append(run_round(run_dir, number, protocol, baseline))
    dump(run_dir / "summary.json", {"rounds": summaries, "claim": "Two post-confirmation budget-sensitivity runs at 500 active seconds; do not pool them as preregistered confirmation replicates."})
    dump(run_dir / "completed.json", {"completed_at": datetime.datetime.now().isoformat(), "rounds": protocol["rounds"]})
    progress(run_dir, "complete")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT
        if path.parent == ROOT / "runs":
            dump(path / "failed.json", {"error_type": type(exc).__name__, "error": str(exc)})
            progress(path, "failed", error=str(exc))
        raise
