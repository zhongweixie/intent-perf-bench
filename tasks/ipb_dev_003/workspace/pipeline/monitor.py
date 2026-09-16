"""Performance Monitoring Module"""

import time
from contextlib import contextmanager
from typing import Dict, List


class PerformanceMonitor:
    """Monitors and reports performance metrics."""

    def __init__(self):
        self.timings: Dict[str, List[float]] = {}

    @contextmanager
    def measure(self, stage: str):
        """Context manager to measure execution time."""
        start = time.time()
        yield
        elapsed = time.time() - start
        
        if stage not in self.timings:
            self.timings[stage] = []
        self.timings[stage].append(elapsed)

    def print_report(self):
        """Print performance report."""
        print("\n" + "=" * 60)
        print("Performance Report")
        print("=" * 60)
        
        total = sum(sum(times) for times in self.timings.values())
        
        # Sort by total time descending
        sorted_stages = sorted(
            self.timings.items(),
            key=lambda x: sum(x[1]),
            reverse=True
        )
        
        for stage, times in sorted_stages:
            stage_total = sum(times)
            stage_mean = stage_total / len(times)
            percentage = (stage_total / total * 100) if total > 0 else 0
            
            print(f"\n{stage}:")
            print(f"  Total: {stage_total:.4f}s ({percentage:.1f}%)")
            print(f"  Mean:  {stage_mean:.4f}s")
            print(f"  Calls: {len(times)}")
        
        print(f"\nTotal Pipeline Time: {total:.4f}s")
        print("=" * 60)
