#!/bin/bash
#
# Generic benchmark script for IPB CUDA tasks
# Runs the benchmark and extracts timing information
#
# Usage: ./bench.sh [--commit HASH]
#
# Options:
#   --commit HASH   Checkout specific commit before benchmarking
#
# Output format (JSON):
# {
#   "time_ms": <average_time_in_milliseconds>,
#   "time_ns": <average_time_in_nanoseconds>,
#   "runs": <number_of_benchmark_runs>
# }

set -e

COMMIT=""
RUNS=100

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --commit)
            COMMIT="$2"
            shift 2
            ;;
        --runs)
            RUNS="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Get to workspace directory
cd "$(dirname "$0")/../workspace"

# Checkout specific commit if requested
if [ -n "$COMMIT" ]; then
    git checkout "$COMMIT" 2>/dev/null
fi

# Build
make clean > /dev/null 2>&1
make > /dev/null 2>&1

# Find the benchmark executable
# Common names: *_benchmark, test, benchmark, main
EXECUTABLE=""
for name in *_benchmark benchmark test main; do
    if [ -x "$name" ]; then
        EXECUTABLE="$name"
        break
    fi
done

if [ -z "$EXECUTABLE" ]; then
    echo "Error: No executable found" >&2
    exit 1
fi

# Run verification first
if ./$EXECUTABLE --verify > /dev/null 2>&1; then
    : # Verification passed
else
    echo "Error: Verification failed" >&2
    exit 1
fi

# Run benchmark on GPU
OUTPUT=$(srun -p llm-debug --qos=llm_debug --gres=gpu:1 ./$EXECUTABLE --benchmark 2>&1)

# Extract timing from output
# Look for patterns like:
#   "Average time: 5.7 ms"
#   "Time: 124.3ms"
#   "Elapsed: 340.0 ms"
#   "Kernel time: 50.0 ms"

TIME_MS=$(echo "$OUTPUT" | grep -iE "(average|elapsed|time|kernel).*[0-9]+\.?[0-9]* ?ms" | \
          grep -oE "[0-9]+\.?[0-9]+" | head -1)

if [ -z "$TIME_MS" ]; then
    # Try nanoseconds
    TIME_NS=$(echo "$OUTPUT" | grep -iE "(average|elapsed|time|kernel).*[0-9]+ ?ns" | \
              grep -oE "[0-9]+" | head -1)

    if [ -n "$TIME_NS" ]; then
        TIME_MS=$(echo "scale=3; $TIME_NS / 1000000" | bc)
    else
        echo "Error: Could not extract timing from output" >&2
        echo "Output was:" >&2
        echo "$OUTPUT" >&2
        exit 1
    fi
fi

# Output as JSON
cat << EOF
{
  "time_ms": $TIME_MS,
  "runs": $RUNS,
  "executable": "$EXECUTABLE"
}
EOF

# Go back to original commit if we changed it
if [ -n "$COMMIT" ]; then
    git checkout - > /dev/null 2>&1
fi
