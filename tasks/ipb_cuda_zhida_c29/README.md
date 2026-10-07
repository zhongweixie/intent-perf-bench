# C29: DeepSpeed AutoEP local token movement and weighted combine

Source: https://github.com/deepspeedai/DeepSpeed/pull/8326. This is an exported/derived task, not the full upstream issue checkout.
Frozen evidence: Three substantive supporting pairs span v2/v3. First v2 M2 includes a long unanswered request. v3 round2 all-arm timeout is retained as infrastructure, not success/failure evidence. M1 is not stable. A/C hypotheses overlap; B fixed-workload plausibility is weaker.

## Layout and isolation
`workspace/repo/` is the solver-visible initial source. `variants/` contains exact historical task text/system instructions. Only files listed in `task.json` are editable. `evaluation/runtime/` contains the caller-only original grader/runner and frozen dependencies; `groundtruth/` contains the reference and metadata. Never expose the complete task checkout, results or groundtruth to a solving agent. The dynamic-tools runners expose only `runtime/public/`, created as a symlink to `workspace/repo/` by setup.

## Setup and grade (Linux, CUDA 12.6, RTX A6000 SM86)
Use a Python 3.10 environment with torch 2.8.0+cu126 and Triton 3.4.0; nvcc is required. Landlock ABI >=3 is used by the original C19/C29/C8673 workers. No model key is needed to grade.

```bash
export IPB_PYTHON=/path/to/venv/bin/python
export IPB_GPU=0
"$IPB_PYTHON" scripts/setup.py
"$IPB_PYTHON" scripts/validate.py --output /tmp/c29-validation.json
"$IPB_PYTHON" evaluation/evaluate.py --baseline --output /tmp/c29-baseline.json
"$IPB_PYTHON" evaluation/evaluate.py --reference --output /tmp/c29-reference.json
"$IPB_PYTHON" evaluation/evaluate.py --candidate /path/to/submitted_source --output /tmp/c29-submission.json
```

`--patch /path/to/solution.diff` is also accepted. Original oracle, workloads, tolerances and timing are preserved. The adapter changes paths, Python/GPU selection and queue location, not acceptance thresholds. C21 returns the geometric mean of three family times; compare per-family baseline ratios for its historical speedup, not a single-family latency. Incorrect code has no valid latency. Infrastructure errors are separate. Recalibrate baseline and reference in the same job/host when making a new performance claim. Historic score values are in the results archive, not rewritten by packaging validation.

## Agent experiment
Historical model: `moonshotai/Kimi-K3`, reasoning `max`, 900 effective seconds; 60,000 generated tokens; 48 API attempts; 8192 per response. GPU waiting is excluded by the frozen controller. Original launchers are in evaluation/runtime/scripts/. They require a user-provided DEEPINFRA_API_KEY and execute under the frozen budget. Set the key only in your terminal; never save it in Git. DeepInfra OpenAI-compatible API

## Integration
This task uses its own preserved Python/Triton/CUDA worker rather than the repository's older Makefile/Slurm-only calibration path. The repository-level `scripts/evaluate_zhida_case.py` dispatches to this entrypoint. Do not silently substitute the older generic evaluator: its test/time assumptions differ. References and result trajectories are research-only material. See `groundtruth/adaptation.json` for packaging changes and limitations.
