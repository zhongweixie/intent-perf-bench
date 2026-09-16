#ifndef REDUCE_H
#define REDUCE_H

#include <cuda_runtime.h>

// Kernel to perform hierarchical reduction (sum) on a vector
// Uses block-level shared memory reduction
__global__ void k_reduce(float *input, float *result, int n);

#endif // REDUCE_H
