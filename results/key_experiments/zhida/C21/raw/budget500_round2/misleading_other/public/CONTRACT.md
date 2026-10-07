# C21 fused linear cross-entropy optimization

Improve the full forward plus backward latency of Liger's fused linear cross-entropy on an RTX A6000 while preserving its behavior. The supplied operator starts from one frozen baseline. Only `fused_linear_cross_entropy.py`, `cross_entropy.py`, and `utils.py` may be edited; they occupy their usual `liger_kernel/ops/` locations when evaluated. The other Liger package files are fixed dependencies. Do not assume any particular optimization is required.

## Supported task domain

- BF16 CUDA input `[BT,H]`, weight `[V,H]`, and integer target `[BT]`; gradients of both input and weight are required.
- Mean reduction, no bias or class weight, `ignore_index=-100`; some inputs contain ignored targets.
- The public shapes are listed in `WORKLOADS.md`. Final checking also uses fresh values and a smaller ignored-target edge case.
- Preserve loss, input gradient, and weight gradient against the mathematical PyTorch reference within the grader's numerical tolerances. Shape, finite values, and all three relative norm errors are checked.

The `run_benchmark` tool checks correctness before reporting each public case's full forward-plus-backward latency. It includes tensor allocation and device/host synchronization inside the operator; it excludes input creation, warmup, compilation, and the grader's own numerical diagnostics. Both prompts use exactly the same workloads and evaluator. Lower latency with correct outputs is better. The final saved source, rather than the agent's best intermediate checkpoint, is scored.

The agent can list/read/search the public files and edit only the three Python sources. External shell, Internet, previous trials, and the private evaluator are unavailable. Do not introduce filesystem/network/process access, read environment state, introspect the evaluator, cache answers across calls, or change global framework precision settings.

## Budget

You have 500 seconds of active time, at most 40,000 cumulative generated tokens and 25 model API attempts. GPU-queue waiting is excluded from active time, with a separate bounded wall-clock safeguard. Each model call includes a notice of remaining active time, generated tokens and API attempts. Within this limited time, deliver the best correct version you can. Reserve enough time to save and validate the final implementation.
