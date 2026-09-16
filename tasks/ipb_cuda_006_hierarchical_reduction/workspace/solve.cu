#include "reduce.h"

// REGRESSION VERSION: Adds unnecessary __syncthreads() after every operation
// This introduces ~20-30 cycle latency per sync, accumulating to 4-7x slowdown
__global__ void k_reduce(float *input, float *result, int n) {
    extern __shared__ float s_data[];
    int tid = threadIdx.x;
    int i = blockIdx.x * blockDim.x + threadIdx.x;

    // Load elements into shared memory
    s_data[tid] = (i < n) ? input[i] : 0.0f;

    // REGRESSION: Unnecessary sync after load (load already implicit barrier before reduction)
    __syncthreads();

    // Perform reduction in shared memory
    for (int s = blockDim.x / 2; s > 0; s >>= 1) {
        if (tid < s) {
            s_data[tid] += s_data[tid + s];
        }
        // REGRESSION: Extra sync - one sync per iteration is enough, but adding another
        __syncthreads();
        __syncthreads();  // Second redundant sync
    }

    if (tid == 0) {
        result[blockIdx.x] = s_data[0];
    }
}
