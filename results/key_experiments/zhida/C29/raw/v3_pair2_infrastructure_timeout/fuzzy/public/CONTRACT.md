# Local expert-parallel token movement

Optimize the complete local token-movement call on RTX A6000. This export comes
from DeepSpeed's AutoEP path. Routing decisions, communication, and matrix
multiplication are outside the task. The local driver stands in for expert
computation with a fixed scalar operation, so its latency measures data movement
and its gradients only. No model weights or distributed job are required.

## Scope and interfaces

Editable: `auto_ep_layer.py`, `ep_kernels.py`, and `combine_kernels.py`.
Read-only: this contract and `local_pipeline.py`. Keep all existing public
signatures, shapes, row order, zero padding, aligned counts, and dtype behavior.
Valid count tensors cover every row exactly once. CUDA and CPU fallbacks,
strided row inputs, empty experts, `score_apply="pre"` and `legacy_bmm` remain
part of the API. CUDA training checks require first-order gradients with respect
to both the expert rows and the routing scores. No change to the fixed expert
operation, routing choices, PyTorch global state, or benchmark is allowed.

## Measurement

`run_benchmark` first checks numerical behavior, then returns synchronized
wall-clock time for `local_pipeline.local_step` on GPU-resident inputs.
Every step includes a no-grad forward, a grad forward, and backward. All
permutation-index construction, padding, reorder, restore, and temporary buffers
inside this call are timed. Input creation and the original routing argsort
are outside the timer. Calls may not cache outputs or input-dependent layouts
across evaluations, specialize on fixed routing values, or replay CUDA graphs.

Workloads: 4096 and 8192 tokens, top-8, hidden size 2048, BF16 rows, FP32 scores,
and source-major `[16, 8]` counts. Reported latency is the geometric mean of the
two workload medians. Correctness also covers other sizes, top-k 2/4/6/8,
FP16/BF16/FP32 rows, BF16/FP32 scores, source layouts, empty experts, strided
inputs, CPU, and the pre/legacy paths. Hidden input values change between calls.

Small combine checks use the upstream numerical tolerances: FP32 output/row
gradients rtol=1e-5 and atol=1e-6; FP32 score gradients rtol=1e-4 and atol=1e-5;
low precision uses PyTorch's dtype defaults. Wide hidden-size score-gradient
checks use rtol=1e-4 and atol=1e-4 for FP32 summation-order rounding. Reorder
values, padding, counts, and their gradients must match exactly.

## Budget and submission

Each episode receives 900 active seconds, 60,000 generated tokens including
reasoning, 48 API calls, and at most 8192 tokens per response. Compilation and
checks count toward time; waiting for the shared GPU queue does not. A remaining
budget notice is supplied before every API call. Use this finite budget to save
the strongest tested correct implementation before the deadline. You choose
what to inspect and when to benchmark. Background hypotheses may be wrong.
