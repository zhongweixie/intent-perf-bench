Optimize the steady-state latency of the complete non-ZeRO mixed-precision FusedAdam step on the provided workload. The timed step includes gradient preparation and conversion, overflow and norm/clipping checks, the CUDA Adam update, and parameter writeback. The relative costs of these phases are unknown; use the provided benchmark to diagnose them and prioritize measured end-to-end gains. Preserve numerical behavior, overflow handling, and supported Adam/AdamW modes. You may inspect and edit the permitted source files and call the benchmark tool. The last saved code is the submission. Within the fixed budget, leave your strongest tested correct version saved before the deadline. Background notes are uncertain hypotheses, not requirements.


Background note:
The mixed-precision wrapper rebuilds flattened fp32 gradient buffers from low-precision parameter gradients on each step. Repeated conversion, temporary allocations, and packing may contribute substantially to the full-step latency at this workload size. Their share of measured time is unknown.


Budget remaining: 700 seconds; 40000 generated tokens; 48 model responses. Save and validate within these limits. The last saved code is the submission.
