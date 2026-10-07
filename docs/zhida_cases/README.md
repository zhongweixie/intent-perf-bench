# Zhida retained task packages and experiment data

Four retained case IDs: C19, C21, C29, C8673. Each has a complete task workspace, exact observed prompts, original runner/worker dependencies, reference, standalone grader, and archived experimental evidence. IDs use `ipb_cuda_zhida_*` so they cannot overwrite existing numbered tasks. Use `results/key_experiments/zhida/CASE_INDEX.json` as the authoritative mapping. C34/C38 are not counted as retained cases.

## Reading order
1. `tasks/<id>/README.md`: source, setup, allowed files, model/budget, evaluation commands.
2. `variants/`: actual fuzzy and primary misleading; secondary prompts are labeled diagnostic.
3. `evaluation/` and `groundtruth/`: researcher-only grader, original source snapshot, reference patch and protocol.
4. `results/key_experiments/zhida/<case>/`: raw outcomes, final source, trajectories and scope limits.

## Evidence limits
C19 has two exploratory pairs and a weak Fuzzy pilot. C21 keeps all four 500s rounds, including the first reverse outcome; its 3-round favorable subset is post-hoc. C29 support spans v2/v3; a long M2 request confounds the first v2 pair and the all-arm v3 timeout is excluded only from substantive comparison. C8673 freezes two Codex medium/700s pairs; older API experiments and broader-budget successes are not evidence of universal robustness. Reference is a validated comparison solution, not a global optimum or guaranteed performance ceiling.

Only visible workspace sources and the selected prompt may be passed to a solver. Never pass this complete repository, groundtruth or historical results to an experiment agent. Runners use isolated dynamic tools. API credentials/login sessions are not distributed. New trials must use fresh output directories. The imported CUDA/Triton workers have a dedicated dispatcher; they are not silently declared compatible with the older repository-wide Makefile/Slurm harness.
