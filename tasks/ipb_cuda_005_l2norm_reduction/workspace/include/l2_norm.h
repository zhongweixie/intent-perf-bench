#ifndef L2_NORM_H
#define L2_NORM_H

#include <cuda_runtime.h>

// Kernel to perform per-block reduction for L2 norm computation
__global__ void k_l2Norm(float *input, float *result, int n, bool square);

#endif // L2_NORM_H
