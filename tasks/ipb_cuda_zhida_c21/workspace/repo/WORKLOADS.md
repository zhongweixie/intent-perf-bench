# Public workloads

All three cases are BF16 CUDA full forward plus backward with mean cross-entropy. Each family has equal weight in the final geometric-mean speedup relative to the frozen baseline. Numerical checks use fresh random values; the third family includes ignored targets.

| Family | BT | H | V | Notes |
|---|---:|---:|---:|---|
| small | 512 | 1024 | 16384 | no ignored targets |
| main | 2048 | 1024 | 32768 | no ignored targets |
| wide_hidden | 1024 | 2048 | 32768 | some ignored targets |

The runner warms up each implementation and reports median microseconds from repeated full calls. On this shared server, small differences may be noisy. Final grading rotates baseline and all conditions through repeated blocks on the same GPU.
