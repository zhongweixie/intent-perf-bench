#include "reduce.h"

// BASELINE VERSION: Efficient hierarchical reduction
// Uses proper synchronization - one sync per reduction iteration
__global__ void k_reduce(float *input, float *result, int n) {
    extern __shared__ float s_data[];
    int tid = threadIdx.x;
    int i = blockIdx.x * blockDim.x + threadIdx.x;

    // Load elements into shared memory
    s_data[tid] = (i < n) ? input[i] : 0.0f;

    // ONE sync needed before reduction starts
    __syncthreads();

    // Perform reduction in shared memory
    for (int s = blockDim.x / 2; s > 0; s >>= 1) {
        if (tid < s) {
            s_data[tid] += s_data[tid + s];
        }
        // ONE sync per iteration is sufficient
        __syncthreads();
    }

    if (tid == 0) {
        result[blockIdx.x] = s_data[0];
    }
}
