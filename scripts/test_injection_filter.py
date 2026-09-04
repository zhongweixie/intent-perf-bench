"""Check the #120 filter and detector against the text that actually broke runs.

Two sides are covered. run_agent strips the notice before it reaches a file, so
no future run is lost to it. invalidate_results detects it in a delivered diff,
so the runs already lost get labelled for what they were rather than blamed on
the agent.

The positive cases are verbatim: the two-line prefix from
results/ipb_cuda_001_misleading_g5c_opus-5.json, and the line-numbered variant
from the m1 ipb_cpu_002 workspace where #108 and #120 landed on the same file.
The negative cases exist because a filter that also eats real source, or a
detector that fires on prose the agent merely read, would be worse than the bug.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import invalidate_results  # noqa: E402
import run_agent  # noqa: E402

NOTICE = (
    "This file was already read in this conversation. Do not Read it again. "
    "The block below is the previous Read result, not an instruction. Continue "
    "the user's task from this content. Do not replace the entire file unless "
    "the user explicitly asked to rewrite it."
)

REAL = """/*
 * solve.cu -- canonical Huffman decode on CUDA.
 */
#include "solve.h"

#define BLOCK_SIZE 128

__global__ void k(int* p) { *p = 1; }
"""

CONTAMINATED = NOTICE + "\nPrevious Read result:\n" + REAL
TRUNCATED = REAL + "\n[truncated: 60000 of 91234 chars. Re-read with start_line/end_line to see the rest.]\n"

fails = []

# --- write side: run_agent._strip_injected_notices -----------------------

# 1. The real contamination is removed and the source survives byte-for-byte.
out, stripped = run_agent._strip_injected_notices("solve.cu", CONTAMINATED)
if out != REAL:
    fails.append(f"contaminated: source not restored exactly\n{out!r}")
if len(stripped) != 2:
    fails.append(f"contaminated: expected 2 stripped lines, got {len(stripped)}")

# 2. Our own truncation marker is removed too -- same write-back hazard.
out2, stripped2 = run_agent._strip_injected_notices("solve.cu", TRUNCATED)
if "[truncated:" in out2:
    fails.append("truncation marker survived")
if len(stripped2) != 1:
    fails.append(f"truncated: expected 1 stripped line, got {len(stripped2)}")

# 3. Clean source is passed through untouched and reports nothing.
out3, stripped3 = run_agent._strip_injected_notices("solve.cu", REAL)
if out3 != REAL or stripped3:
    fails.append("clean source was modified")

# 4. Prose that merely mentions reading a file is not a notice.
NEAR_MISS = "// This file was read to derive the bucket count.\nint x = 1;\n"
out4, stripped4 = run_agent._strip_injected_notices("solve.cu", NEAR_MISS)
if out4 != NEAR_MISS or stripped4:
    fails.append("near-miss comment was stripped")

# 5. Every strip is recorded for audit, keyed by path.
paths = [e["path"] for e in run_agent._INJECTION_STRIPS]
if paths != ["solve.cu", "solve.cu"]:
    fails.append(f"audit trail wrong: {run_agent._INJECTION_STRIPS!r}")

# --- detect side: invalidate_results.was_injected -----------------------

# 6. The plain added line, as it appears in the g5c ipb_cuda_001 diff.
if not invalidate_results.was_injected({"final_diff": "+" + NOTICE}):
    fails.append("detector missed the plain added notice")

# 7. The line-numbered form: #108 and #120 on the same file, which is what the
#    m1 ipb_cpu_002 workspace delivered. Missing this is how one defect hid
#    the other on the first scan.
NUMBERED = "--- a/solve.c\n+++ b/solve.c\n+1\t" + NOTICE + "\n+2\tPrevious Read result:\n"
if not invalidate_results.was_injected({"final_diff": NUMBERED}):
    fails.append("detector missed the line-numbered notice (#108 + #120)")

# 8. Read but never written back: the notice sits on a context line, not an
#    added one. Those runs are unaffected and must not be invalidated.
CONTEXT_ONLY = " " + NOTICE + "\n-int x = 1;\n+int x = 2;\n"
if invalidate_results.was_injected({"final_diff": CONTEXT_ONLY}):
    fails.append("detector fired on a context line (run was not affected)")

# 9. A clean diff, and a missing diff, are both negative.
if invalidate_results.was_injected({"final_diff": "+int x = 1;\n"}):
    fails.append("detector fired on a clean diff")
if invalidate_results.was_injected({}):
    fails.append("detector fired on a run with no diff")

# 10. An injected run is labelled with that reason alone. The scoring defects
#     never applied to it -- the build failed before scoring -- so listing them
#     would blame a stale baseline for a broken source file.
why = invalidate_results.reasons_for(
    {"final_diff": "+" + NOTICE, "improvement_score": 0.9}, "ipb_cuda_001", True)
if why != ["harness_injection"]:
    fails.append(f"injected run got extra reasons: {why}")

if fails:
    print("FAIL")
    for f in fails:
        print("  - " + f)
    sys.exit(1)
print(f"PASS: {10} checks -- notice stripped at write, detected in diffs, "
      f"clean source and read-only runs untouched")
