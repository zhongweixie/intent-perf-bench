"""Log Formatting Pipeline

Main pipeline: Load → Format → Write
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from log_formatter.loader import LogLoader
from log_formatter.formatter import LogFormatter
from log_formatter.writer import LogWriter


def run_log_pipeline():
    """Run the complete log formatting pipeline."""
    print("=" * 70)
    print("Log Formatting Pipeline")
    print("=" * 70)

    # Stage 1: Load logs
    print("\n[1/3] Loading structured logs...")
    t = time.time()
    loader = LogLoader(simulate_io=True)
    logs = loader.load_logs(n_logs=30000)
    stage1_time = time.time() - t
    print(f"      Loaded {len(logs)} logs in {stage1_time:.4f}s")

    # Stage 2: Format logs
    print("\n[2/3] Formatting logs...")
    t = time.time()
    formatter = LogFormatter()
    formatted = formatter.format_logs(logs)
    stage2_time = time.time() - t
    print(f"      Formatted in {stage2_time:.4f}s")

    # Stage 3: Write logs
    print("\n[3/3] Writing output...")
    t = time.time()
    writer = LogWriter()
    writer.write_logs(formatted)
    stage3_time = time.time() - t
    print(f"      Written in {stage3_time:.4f}s")

    total = stage1_time + stage2_time + stage3_time
    print(f"\n{'='*70}")
    print(f"Total: {total:.4f}s")
    print(f"  Load:   {stage1_time:.4f}s ({stage1_time/total*100:.1f}%)")
    print(f"  Format: {stage2_time:.4f}s ({stage2_time/total*100:.1f}%)")
    print(f"  Write:  {stage3_time:.4f}s ({stage3_time/total*100:.1f}%)")
    return total


if __name__ == "__main__":
    run_log_pipeline()
