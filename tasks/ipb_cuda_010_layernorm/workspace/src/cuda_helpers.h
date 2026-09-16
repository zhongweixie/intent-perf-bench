#ifndef CUDA_HELPERS_H
#define CUDA_HELPERS_H

#include <stdio.h>
#include <stdlib.h>
#include <cuda_runtime.h>

#define CUDA_CHECK(call) {                                              \
    cudaError_t error = call;                                           \
    if (error != cudaSuccess) {                                         \
        fprintf(stderr, "CUDA error at %s:%d - %s\n",                   \
                __FILE__, __LINE__, cudaGetErrorString(error));         \
        exit(EXIT_FAILURE);                                             \
    }                                                                   \
}

#define WARP_SIZE 32
#define CEIL_DIV(M, N) (((M) + (N) - 1) / (N))

// Warp-level reduction for sum
__device__ inline float warpReduceSum(float val) {
    for (int offset = 16; offset > 0; offset /= 2) {
        val += __shfl_xor_sync(0xFFFFFFFF, val, offset);
    }
    return val;
}

#endif // CUDA_HELPERS_H
