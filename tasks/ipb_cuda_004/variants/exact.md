# Exact Variant

Optimize the BLS12-381 G1 MSM implementation in `solve.cu`. Preserve curve arithmetic and exact verification behavior. Analyze the whole Pippenger pipeline: scalar windows, bucket accumulation, point representation, memory traffic, atomics, synchronization, and launch configuration. Do not modify the harness or interface.
