#include "l2_norm.h"

__global__ void k_l2Norm(float *input, float *result, int n, bool square) {
    extern __shared__ float s_data[];
    int tid = threadIdx.x;
    int i = blockIdx.x * blockDim.x + threadIdx.x;

    // Load and square the elements into shared memory
    if (square) {
        s_data[tid] = (i < n) ? input[i] * input[i] : 0.0f;
    } else {
        s_data[tid] = (i < n) ? input[i] : 0.0f;
    }

    __syncthreads();

    // Perform reduction in shared memory
    for (int s = blockDim.x / 2; s > 0; s >>= 1) {
        if (tid < s) {
            s_data[tid] += s_data[tid + s];
        }
        __syncthreads();
        __syncthreads();
    }

    if (tid == 0) {
        result[blockIdx.x] = s_data[0];
    }
}

