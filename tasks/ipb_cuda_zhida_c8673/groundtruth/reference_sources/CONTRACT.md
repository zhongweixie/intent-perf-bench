Task: optimize the full non-ZeRO FP16/BF16 FusedAdam wrapper step while preserving Adam/AdamW, loss scaling, clipping, overflow behavior and optimizer state. Edit only the listed source files. The public benchmark uses 64,000,000 FP16 elements, AdamW, clip_grad=0.5, static loss scale 128, 20 warmups and 30 timed iterations on one RTX A6000. The benchmark tool reports absolute step latency and checks reference state. Source aliases map to:
fused_optimizer.py: deepspeed/runtime/fp16/fused_optimizer.py
fused_adam.py: deepspeed/ops/adam/fused_adam.py
utils.py: deepspeed/runtime/utils.py
multi_tensor_adam.cu: csrc/adam/multi_tensor_adam.cu
fused_adam_frontend.cpp: csrc/adam/fused_adam_frontend.cpp
multi_tensor_apply.cuh: csrc/adam/multi_tensor_apply.cuh
