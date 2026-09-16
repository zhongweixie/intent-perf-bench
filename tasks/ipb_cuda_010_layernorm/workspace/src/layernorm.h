#ifndef LAYERNORM_H
#define LAYERNORM_H

#include <cuda_runtime.h>

void layernorm_forward(float* out, float* mean, float* rstd,
                       const float* inp, const float* weight, const float* bias,
                       int N, int C, cudaStream_t stream = 0);

#endif // LAYERNORM_H
