# C19: vLLM derived MoE routing and complete block

Source: https://github.com/vllm-project/vllm/commit/94923629729381d7f7c9efde72071a2441f7fd82. This is an exported/derived task, not the full upstream issue checkout.
Frozen evidence: Two exploratory pairs favor Fuzzy over layout; assignment is diagnostic and not stable. Initial weak Fuzzy pilot retained. No preregistered significance claim.

## Layout and isolation
`workspace/repo/` is the solver-visible initial source. `variants/` contains exact historical task text/system instructions. Only files listed in `task.json` are editable. `evaluation/runtime/` contains the caller-only original grader/runner and frozen dependencies; `groundtruth/` contains the reference and metadata. Never expose the complete task checkout, results or groundtruth to a solving agent. The dynamic-tools runners expose only `runtime/public/`, created as a symlink to `workspace/repo/` by setup.

## Setup and grade (Linux, CUDA 12.6, RTX A6000 SM86)
Use a Python 3.10 environment with torch 2.8.0+cu126 and Triton 3.4.0; nvcc is required. Landlock ABI >=3 is used by the original C19/C29/C8673 workers. No model key is needed to grade.

```bash
export IPB_PYTHON=/path/to/venv/bin/python
export IPB_GPU=0
"$IPB_PYTHON" scripts/setup.py
"$IPB_PYTHON" scripts/validate.py --output /tmp/c19-validation.json
"$IPB_PYTHON" evaluation/evaluate.py --baseline --output /tmp/c19-baseline.json
"$IPB_PYTHON" evaluation/evaluate.py --reference --output /tmp/c19-reference.json
"$IPB_PYTHON" evaluation/evaluate.py --candidate /path/to/submitted_source --output /tmp/c19-submission.json
```

`--patch /path/to/solution.diff` is also accepted. Original oracle, workloads, tolerances and timing are preserved. The adapter changes paths, Python/GPU selection and queue location, not acceptance thresholds. C21 returns the geometric mean of three family times; compare per-family baseline ratios for its historical speedup, not a single-family latency. Incorrect code has no valid latency. Infrastructure errors are separate. Recalibrate baseline and reference in the same job/host when making a new performance claim. Historic score values are in the results archive, not rewritten by packaging validation.

## Agent experiment
Historical model: `deepseek/deepseek-v4.1-flash`, reasoning `not separately set`, 450 effective seconds; 24,000 generated tokens; 28 API attempts; 8192 per response. GPU waiting is excluded by the frozen controller. Original launchers are in evaluation/runtime/scripts/. They require a user-provided OPENROUTER_API_KEY and execute under the frozen budget. Set the key only in your terminal; never save it in Git. Preserved scripts call OpenRouter; provider label in historical protocol is not a transport URL.

## Integration
This task uses its own preserved Python/Triton/CUDA worker rather than the repository's older Makefile/Slurm-only calibration path. The repository-level `scripts/evaluate_zhida_case.py` dispatches to this entrypoint. Do not silently substitute the older generic evaluator: its test/time assumptions differ. References and result trajectories are research-only material. See `groundtruth/adaptation.json` for packaging changes and limitations.
