"""Performance Benchmark for Log Formatting Pipeline"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from log_formatter.loader import LogLoader
from log_formatter.formatter import LogFormatter
from log_formatter.writer import LogWriter

THRESHOLD = 0.30  # baseline ~0.04s (no I/O), regressed ~6.4s (no I/O)


def run_once():
    loader = LogLoader(simulate_io=False)
    logs = loader.load_logs(n_logs=30000)
    formatter = LogFormatter()
    formatted = formatter.format_logs(logs)
    writer = LogWriter()
    writer.write_logs(formatted)
    return formatted


def benchmark_pipeline(n_runs: int = 3):
    """Run pipeline benchmark."""
    print("=" * 70)
    print("Log Formatting Pipeline Performance Benchmark")
    print("=" * 70)
    print(f"\nConfiguration: 30,000 logs, {n_runs} runs\n")

    times = []
    for i in range(n_runs):
        print(f"--- Run {i+1}/{n_runs} ---")
        t_start = time.time()
        run_once()
        elapsed = time.time() - t_start
        times.append(elapsed)
        print(f"Run {i+1}: {elapsed:.4f}s\n")

    times_sorted = sorted(times)
    best_time = times_sorted[0]
    median = times_sorted[len(times_sorted) // 2]
    mean = sum(times) / len(times)

    print("=" * 70)
    print("Benchmark Results")
    print("=" * 70)
    print(f"Run times: {[f'{t:.4f}s' for t in times]}")
    print(f"Best time: {best_time:.4f}s")
    print(f"Median:    {median:.4f}s")
    print(f"Mean:      {mean:.4f}s")
    print(f"Threshold: {THRESHOLD:.4f}s")
    print()

    if best_time <= THRESHOLD:
        print(f"PASS: pipeline meets performance threshold ({best_time:.4f}s <= {THRESHOLD:.4f}s)")
        return 0
    else:
        print(f"FAIL: pipeline too slow ({best_time:.4f}s > {THRESHOLD:.4f}s)")
        return 1


if __name__ == "__main__":
    sys.exit(benchmark_pipeline())
