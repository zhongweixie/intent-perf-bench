// Copyright (c) Microsoft Corporation.
// SPDX-License-Identifier: Apache-2.0

// DeepSpeed Team

/*
Copyright NVIDIA/apex
This file is adapted from fused adam in NVIDIA/apex, commit a109f85
*/

#include <ATen/ATen.h>
#include <ATen/AccumulateType.h>
#include <ATen/cuda/CUDAContext.h>
#include <ATen/cuda/Exceptions.h>
// Another possibility:
// #include <torch/all.h>

#include <assert.h>

#include "multi_tensor_apply.cuh"
#include "type_shim.h"

#define BLOCK_SIZE 512
#define ILP 4

typedef enum : int {
    ADAM_MODE_0 = 0,  // L2 regularization mode
    ADAM_MODE_1 = 1   // Decoupled weight decay mode(AdamW)
} adamMode_t;

using MATH_T = float;

template <typename T, typename index_t>
struct AdamFunctor {
    __device__ __forceinline__ void operator()(int chunk_size,
                                               volatile int* noop_gmem,
                                               TensorListMetadata<4>& tl,
                                               const float beta1,
                                               const float beta2,
                                               const float beta1_correction,
                                               const float beta2_correction,
                                               const float epsilon,
                                               const float lr,
                                               adamMode_t mode,
                                               const float decay)
    {
        // I'd like this kernel to propagate infs/nans.
        // if(*noop_gmem == 1)
        //   return;

        index_t tensor_loc = tl.block_to_tensor[blockIdx.x];

        // potentially use to pass in list of scalar
        // int tensor_num = tl.start_tensor_this_launch + tensor_loc;

        index_t chunk_idx = tl.block_to_chunk[blockIdx.x];
        index_t n = tl.sizes[tensor_loc];

        T* g = (T*)tl.addresses[0][tensor_loc];
        g += chunk_idx * chunk_size;

        T* p = (T*)tl.addresses[1][tensor_loc];
        p += chunk_idx * chunk_size;

        T* m = (T*)tl.addresses[2][tensor_loc];
        m += chunk_idx * chunk_size;

        T* v = (T*)tl.addresses[3][tensor_loc];
        v += chunk_idx * chunk_size;

        n -= chunk_idx * chunk_size;

        // see note in multi_tensor_scale_kernel.cu
        for (index_t i_start = 0; i_start < n && i_start < chunk_size;
             i_start += blockDim.x * ILP) {
            MATH_T r_g[ILP];
            MATH_T r_p[ILP];
            MATH_T r_m[ILP];
            MATH_T r_v[ILP];
#pragma unroll
            for (int ii = 0; ii < ILP; ii++) {
                int i = i_start + threadIdx.x + ii * blockDim.x;
                if (i < n && i < chunk_size) {
                    r_g[ii] = g[i];
                    r_p[ii] = p[i];
                    r_m[ii] = m[i];
                    r_v[ii] = v[i];
                } else {
                    r_g[ii] = MATH_T(0);
                    r_p[ii] = MATH_T(0);
                    r_m[ii] = MATH_T(0);
                    r_v[ii] = MATH_T(0);
                }
            }
#pragma unroll
            for (int ii = 0; ii < ILP; ii++) {
                if (mode == ADAM_MODE_0) {  // L2
                    r_g[ii] = r_g[ii] + (decay * r_p[ii]);
                    r_m[ii] = beta1 * r_m[ii] + (1 - beta1) * r_g[ii];
                    r_v[ii] = beta2 * r_v[ii] + (1 - beta2) * r_g[ii] * r_g[ii];
                    MATH_T next_m_unbiased = r_m[ii] / beta1_correction;
                    MATH_T next_v_unbiased = r_v[ii] / beta2_correction;
                    MATH_T denom = sqrtf(next_v_unbiased) + epsilon;
                    MATH_T update = next_m_unbiased / denom;
                    r_p[ii] = r_p[ii] - (lr * update);
                } else {  // weight decay
                    r_m[ii] = beta1 * r_m[ii] + (1 - beta1) * r_g[ii];
                    r_v[ii] = beta2 * r_v[ii] + (1 - beta2) * r_g[ii] * r_g[ii];
                    MATH_T next_m_unbiased = r_m[ii] / beta1_correction;
                    MATH_T next_v_unbiased = r_v[ii] / beta2_correction;
                    MATH_T denom = sqrtf(next_v_unbiased) + epsilon;
                    MATH_T update = (next_m_unbiased / denom) + (decay * r_p[ii]);
                    r_p[ii] = r_p[ii] - (lr * update);
                }
            }
#pragma unroll
            for (int ii = 0; ii < ILP; ii++) {
                int i = i_start + threadIdx.x + ii * blockDim.x;
                if (i < n && i < chunk_size) {
                    p[i] = r_p[ii];
                    m[i] = r_m[ii];
                    v[i] = r_v[ii];
                }
            }
        }
    }
};

void multi_tensor_adam_cuda(int chunk_size,
                            at::Tensor noop_flag,
                            std::vector<std::vector<at::Tensor>> tensor_lists,
                            const float lr,
                            const float beta1,
                            const float beta2,
                            const float epsilon,
                            const int step,
                            const int mode,
                            const int bias_correction,
                            const float weight_decay)
{
    using namespace at;

    // Handle bias correction mode
    float bias_correction1 = 1.0f, bias_correction2 = 1.0f;
    if (bias_correction == 1) {
        bias_correction1 = 1 - std::pow(beta1, step);
        bias_correction2 = 1 - std::pow(beta2, step);
    }

    size_t max_size = 0;
    bool requires_64bit_indexing = false;
    for (auto it = tensor_lists.begin(); it != tensor_lists.end(); it++) {
        for (auto it2 = it->begin(); it2 != it->end(); it2++) {
            if (it2->numel() > max_size) {
                max_size = it2->numel();
                if (max_size >= INT_MAX) {
                    requires_64bit_indexing = true;
                    break;
                }
            }
        }
        if (requires_64bit_indexing) { break; }
    }

    // Assume single type across p,g,m1,m2 now
    if (requires_64bit_indexing) {
        DISPATCH_DOUBLE_FLOAT_AND_HALF(tensor_lists[0][0].scalar_type(),
                                       0,
                                       "adam",
                                       multi_tensor_apply<4>((int64_t)BLOCK_SIZE,
                                                             (int64_t)chunk_size,
                                                             noop_flag,
                                                             tensor_lists,
                                                             AdamFunctor<scalar_t_0, int64_t>(),
                                                             beta1,
                                                             beta2,
                                                             bias_correction1,
                                                             bias_correction2,
                                                             epsilon,
                                                             lr,
                                                             (adamMode_t)mode,
                                                             weight_decay);)
    } else {
        DISPATCH_DOUBLE_FLOAT_AND_HALF(tensor_lists[0][0].scalar_type(),
                                       0,
                                       "adam",
                                       multi_tensor_apply<4>(BLOCK_SIZE,
                                                             chunk_size,
                                                             noop_flag,
                                                             tensor_lists,
                                                             AdamFunctor<scalar_t_0, int32_t>(),
                                                             beta1,
                                                             beta2,
                                                             bias_correction1,
                                                             bias_correction2,
                                                             epsilon,
                                                             lr,
                                                             (adamMode_t)mode,
                                                             weight_decay);)
    }

    AT_CUDA_CHECK(cudaGetLastError());
}


// The wrapper's low-precision gradients need not be materialized as fp32.
// Reduce them once for both the norm and the non-finite check, then convert
// in registers during the update and write both copies of the parameters.
template <typename T>
__global__ void mixed_grad_partials(const T* __restrict__ g, int64_t n,
                                    float* __restrict__ sums,
                                    float* __restrict__ bad)
{
    float s = 0.f;
    float b = 0.f;
    int64_t start = (int64_t)blockIdx.x * 8192;
    int64_t end = min(start + 8192, n);
    for (int64_t i = start + threadIdx.x; i < end; i += blockDim.x) {
        float x = (float)g[i];
        s += x * x;
        b = fmaxf(b, isfinite(x) ? 0.f : 1.f);
    }
    __shared__ float sm[256], bm[256];
    sm[threadIdx.x] = s;
    bm[threadIdx.x] = b;
    __syncthreads();
    for (int d = 128; d > 0; d >>= 1) {
        if (threadIdx.x < d) {
            sm[threadIdx.x] += sm[threadIdx.x + d];
            bm[threadIdx.x] = fmaxf(bm[threadIdx.x], bm[threadIdx.x + d]);
        }
        __syncthreads();
    }
    if (threadIdx.x == 0) {
        sums[blockIdx.x] = sm[0];
        bad[blockIdx.x] = bm[0];
    }
}

__global__ void mixed_grad_finish(const float* sums, const float* bad,
                                  int n, float* out)
{
    float s = 0.f, b = 0.f;
    for (int i = threadIdx.x; i < n; i += blockDim.x) {
        s += sums[i];
        b = fmaxf(b, bad[i]);
    }
    __shared__ float sm[256], bm[256];
    sm[threadIdx.x] = s;
    bm[threadIdx.x] = b;
    __syncthreads();
    for (int d = 128; d > 0; d >>= 1) {
        if (threadIdx.x < d) {
            sm[threadIdx.x] += sm[threadIdx.x + d];
            bm[threadIdx.x] = fmaxf(bm[threadIdx.x], bm[threadIdx.x + d]);
        }
        __syncthreads();
    }
    if (threadIdx.x == 0) {
        out[0] = sqrtf(sm[0]);
        out[1] = bm[0];
    }
}

at::Tensor mixed_grad_stats_cuda(at::Tensor g)
{
    TORCH_CHECK(g.is_cuda() && g.is_contiguous(), "Expected contiguous CUDA gradient");
    const at::cuda::OptionalCUDAGuard guard(device_of(g));
    auto stream = at::cuda::getCurrentCUDAStream();
    int blocks = (g.numel() + 8191) / 8192;
    auto out = at::zeros({2}, g.options().dtype(at::kFloat));
    if (blocks == 0) return out;
    auto partial = at::empty({2, blocks}, g.options().dtype(at::kFloat));
    auto sums = partial.data_ptr<float>();
    auto bad = sums + blocks;
    if (g.scalar_type() == at::kHalf) {
        mixed_grad_partials<<<blocks, 256, 0, stream>>>(g.data_ptr<at::Half>(), g.numel(), sums, bad);
    } else if (g.scalar_type() == at::kBFloat16) {
        mixed_grad_partials<<<blocks, 256, 0, stream>>>(g.data_ptr<at::BFloat16>(), g.numel(), sums, bad);
    } else {
        TORCH_CHECK(false, "Expected fp16 or bf16 gradient");
    }
    mixed_grad_finish<<<1, 256, 0, stream>>>(sums, bad, blocks, out.data_ptr<float>());
    AT_CUDA_CHECK(cudaGetLastError());
    return out;
}

template <typename T>
__global__ void mixed_adam_kernel(const T* __restrict__ g,
                                  float* __restrict__ p,
                                  float* __restrict__ m,
                                  float* __restrict__ v,
                                  T* __restrict__ out,
                                  int64_t n, float inv_scale,
                                  float beta1, float beta2,
                                  float correction1, float correction2,
                                  float eps, float lr, int mode, float decay)
{
    for (int64_t start = (int64_t)blockIdx.x * blockDim.x * 4;
         start < n; start += (int64_t)gridDim.x * blockDim.x * 4) {
        float rg[4], rp[4], rm[4], rv[4];
#pragma unroll
        for (int j = 0; j < 4; ++j) {
            int64_t i = start + threadIdx.x + j * blockDim.x;
            if (i < n) {
                rg[j] = __fmul_rn((float)g[i], inv_scale);
                rp[j] = p[i];
                rm[j] = m[i];
                rv[j] = v[i];
            } else {
                rg[j] = rp[j] = rm[j] = rv[j] = 0.f;
            }
        }
#pragma unroll
        for (int j = 0; j < 4; ++j) {
            if (mode == 0) rg[j] = rg[j] + decay * rp[j];
            rm[j] = beta1 * rm[j] + (1 - beta1) * rg[j];
            rv[j] = beta2 * rv[j] + (1 - beta2) * rg[j] * rg[j];
            float mu = rm[j] / correction1;
            float vu = rv[j] / correction2;
            float denom = sqrtf(vu) + eps;
            float update = mu / denom;
            if (mode != 0) update = update + decay * rp[j];
            rp[j] = rp[j] - lr * update;
        }
#pragma unroll
        for (int j = 0; j < 4; ++j) {
            int64_t i = start + threadIdx.x + j * blockDim.x;
            if (i < n) {
                p[i] = rp[j];
                m[i] = rm[j];
                v[i] = rv[j];
                out[i] = (T)rp[j];
            }
        }
    }
}

void mixed_adam_cuda(at::Tensor g, at::Tensor p, at::Tensor m, at::Tensor v,
                     at::Tensor out, float inv_scale, float lr,
                     float beta1, float beta2, float eps, int step,
                     int mode, int bias_correction, float decay)
{
    TORCH_CHECK(g.is_cuda() && p.is_cuda() && m.is_cuda() && v.is_cuda() && out.is_cuda(),
                "Expected CUDA tensors");
    TORCH_CHECK(g.is_contiguous() && p.is_contiguous() && m.is_contiguous() &&
                v.is_contiguous() && out.is_contiguous(), "Expected contiguous tensors");
    TORCH_CHECK(p.scalar_type() == at::kFloat && m.scalar_type() == at::kFloat &&
                v.scalar_type() == at::kFloat && out.scalar_type() == g.scalar_type(),
                "Invalid mixed Adam dtypes");
    TORCH_CHECK(p.numel() == g.numel() && m.numel() == g.numel() &&
                v.numel() == g.numel() && out.numel() == g.numel(), "Size mismatch");
    TORCH_CHECK(g.device() == p.device() && g.device() == m.device() &&
                g.device() == v.device() && g.device() == out.device(), "Device mismatch");
    const at::cuda::OptionalCUDAGuard guard(device_of(g));
    auto stream = at::cuda::getCurrentCUDAStream();
    if (g.numel() == 0) return;
    float c1 = 1.f, c2 = 1.f;
    if (bias_correction) {
        c1 = 1 - std::pow(beta1, step);
        c2 = 1 - std::pow(beta2, step);
    }
    int blocks = std::min<int64_t>((g.numel() + 1023) / 1024, 4096);
    if (g.scalar_type() == at::kHalf) {
        mixed_adam_kernel<<<blocks, 256, 0, stream>>>(g.data_ptr<at::Half>(),
            p.data_ptr<float>(), m.data_ptr<float>(), v.data_ptr<float>(),
            out.data_ptr<at::Half>(), g.numel(), inv_scale, beta1, beta2,
            c1, c2, eps, lr, mode, decay);
    } else if (g.scalar_type() == at::kBFloat16) {
        mixed_adam_kernel<<<blocks, 256, 0, stream>>>(g.data_ptr<at::BFloat16>(),
            p.data_ptr<float>(), m.data_ptr<float>(), v.data_ptr<float>(),
            out.data_ptr<at::BFloat16>(), g.numel(), inv_scale, beta1, beta2,
            c1, c2, eps, lr, mode, decay);
    } else {
        TORCH_CHECK(false, "Expected fp16 or bf16 gradient");
    }
    AT_CUDA_CHECK(cudaGetLastError());
}

