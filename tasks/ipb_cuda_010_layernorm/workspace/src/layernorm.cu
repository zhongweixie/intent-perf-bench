#include "layernorm.h"
#include "cuda_helpers.h"

// Inefficient baseline: naive implementation with poor memory access and synchronization
// Uses small block size and inefficient reduction pattern
__global__ void layernorm_kernel(float* __restrict__ out,
                                 float* __restrict__ mean,
                                 float* __restrict__ rstd,
                                 const float* __restrict__ inp,
                                 const float* __restrict__ weight,
                                 const float* __restrict__ bias,
                                 int N, int C) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= N) return;

    const float* x = inp + idx * C;
    float* o = out + idx * C;
    const float eps = 1e-5f;

    // Pass 1: Compute mean with inefficient reduction
    float sum = 0.0f;
    for (int i = 0; i < C; i++) {
        sum += x[i];
    }
    float m = sum / C;
    if (mean) mean[idx] = m;

    // Pass 2: Compute variance with inefficient reduction
    sum = 0.0f;
    for (int i = 0; i < C; i++) {
        float diff = x[i] - m;
        sum += diff * diff;
    }
    float s = rsqrtf(sum / C + eps);
    if (rstd) rstd[idx] = s;

    // Pass 3: Normalize and scale
    for (int i = 0; i < C; i++) {
        float n = s * (x[i] - m);
        o[i] = n * weight[i] + bias[i];
    }
}

void layernorm_forward(float* out, float* mean, float* rstd,
                       const float* inp, const float* weight, const float* bias,
                       int N, int C, cudaStream_t stream) {
    // Use very small block size for poor occupancy
    const int block_size = 32;
    const int grid_size = CEIL_DIV(N, block_size);

    layernorm_kernel<<<grid_size, block_size, 0, stream>>>(
        out, mean, rstd, inp, weight, bias, N, C);

    CUDA_CHECK(cudaGetLastError());
}
