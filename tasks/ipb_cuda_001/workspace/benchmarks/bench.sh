#!/usr/bin/env bash
# Compile and benchmark the Huffman decode CUDA pipeline.
# Exit 0 = PASS, Exit 1 = FAIL or compile error.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$(dirname "$SCRIPT_DIR")"

echo "=== Huffman Decode Benchmark ==="
echo "Building..."
cd "$WORKSPACE"
make clean -s
make -s

echo "Warming up..."
./huffman_decode --verify > /dev/null

echo "Running benchmark (7 trials)..."
OUTPUT=$(./huffman_decode --benchmark 2>&1)
echo "$OUTPUT"

# Parse median time_ms from output line: "result=ok time_ms=X.XXXXXX ..."
TIME_MS=$(echo "$OUTPUT" | grep -oP 'time_ms=\K[0-9]+\.[0-9]+' | head -1)

if [[ -z "$TIME_MS" ]]; then
    echo "ERROR: could not parse time_ms from benchmark output"
    exit 1
fi

THRESHOLD="11.2"

# Use awk for float comparison
PASS=$(awk -v t="$TIME_MS" -v th="$THRESHOLD" 'BEGIN { print (t+0 <= th+0) ? "1" : "0" }')

echo ""
echo "=== Result ==="
if [[ "$PASS" == "1" ]]; then
    echo "✓ PASS — ${TIME_MS}ms ≤ ${THRESHOLD}ms threshold (≥5× speedup over baseline)"
    exit 0
else
    echo "✗ FAIL — ${TIME_MS}ms > ${THRESHOLD}ms threshold"
    exit 1
fi
