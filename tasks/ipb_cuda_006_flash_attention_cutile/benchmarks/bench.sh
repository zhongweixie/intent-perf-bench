#!/bin/bash
# Benchmark script for Flash Attention cuTile task

set -e

cd "$(dirname "$0")/.."

# Run performance benchmark
PYTHONPATH=. python test/test_fmha.py --perf

# Extract timing from output
# The test script should print: "bench_region: <time_ms> ms"
