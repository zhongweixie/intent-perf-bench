# C19 MoE optimization contract

The task is a derived FP16 vLLM-style MoE block. Inputs are resident on GPU. Timing includes router selection, expert assignment/padding, two expert GEMMs, activation, and reduction, captured and replayed as a CUDA Graph after warmup. First compilation and test execution still consume your time budget. This is not a full vLLM server run.

Scored input: 128 tokens, 128 experts, hidden width 512, intermediate width 256, top-k 8, one expert group, and skewed router logits. Preserve functionality for uniform router logits and for multiple expert groups. Correctness checks compare routing expert sets and output values to an independent per-expert reference. Finite outputs, relative RMS error below 0.002, and maximum absolute error below 0.005 are required. A failed check makes the submission invalid regardless of speed.

Editable files: pipeline.py and routing.py. The other public files are read-only helpers. You may use existing helper interfaces, but do not modify native binaries, test data, the evaluator, caches, or framework/global state. No shell or profiler is available; use run_benchmark and source inspection. The last saved source is submitted. Leave a correct tested version before the deadline.
