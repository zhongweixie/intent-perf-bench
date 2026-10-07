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

// Convert directly into master-gradient storage while checking every input
// for overflow. A single flag is shared by all groups.
template <typename T>
struct GradCopyFunctor {
    __device__ __forceinline__ void operator()(int chunk_size, volatile int* overflow,
                                               TensorListMetadata<2>& tl)
    {
        int t = tl.block_to_tensor[blockIdx.x];
        int64_t offset = (int64_t)tl.block_to_chunk[blockIdx.x] * chunk_size;
        int64_t n = min(tl.sizes[t] - offset, (int64_t)chunk_size);
        const T* src = (const T*)tl.addresses[0][t] + offset;
        float* dst = (float*)tl.addresses[1][t] + offset;
        bool non_finite = false;
        for (int64_t start = 0; start < n; start += blockDim.x * ILP) {
#pragma unroll
            for (int j = 0; j < ILP; ++j) {
                int64_t k = start + threadIdx.x + j * blockDim.x;
                if (k < n) {
                    float value = (float)src[k];
                    dst[k] = value;
                    non_finite |= !isfinite(value);
                }
            }
        }
        if (__syncthreads_or(non_finite) && threadIdx.x == 0)
            atomicExch((int*)overflow, 1);
    }
};

void multi_tensor_grad_copy_cuda(int chunk_size, at::Tensor overflow,
                                 std::vector<std::vector<at::Tensor>> tensor_lists)
{
    TORCH_CHECK(tensor_lists.size() == 2, "Expected source and destination lists");
    for (const auto& tensor : tensor_lists[1])
        TORCH_CHECK(tensor.scalar_type() == at::kFloat, "Expected FP32 gradient destination");
    for (const auto& tensor : tensor_lists[0])
        TORCH_CHECK(tensor.scalar_type() == tensor_lists[0][0].scalar_type(),
                    "Gradient sources must have the same dtype");
    DISPATCH_DOUBLE_FLOAT_AND_HALF(tensor_lists[0][0].scalar_type(), 0, "grad_copy",
                                  multi_tensor_apply<2>(BLOCK_SIZE, chunk_size, overflow,
                                                        tensor_lists, GradCopyFunctor<scalar_t_0>());)
    AT_CUDA_CHECK(cudaGetLastError());
}

// FP32 master update, with gradient scaling and low-precision writeback
// in the same pass. The arithmetic order is identical to AdamFunctor.
template <typename OutputT>
struct MasterAdamFunctor {
    __device__ __forceinline__ void operator()(int chunk_size,
                                               volatile int* noop_gmem,
                                               TensorListMetadata<5>& tl,
                                               float beta1, float beta2,
                                               float correction1, float correction2,
                                               float epsilon, float lr,
                                               adamMode_t mode, float decay,
                                               float inv_scale)
    {
        int t = tl.block_to_tensor[blockIdx.x];
        int64_t offset = (int64_t)tl.block_to_chunk[blockIdx.x] * chunk_size;
        int64_t n = min(tl.sizes[t] - offset, (int64_t)chunk_size);
        float* g = (float*)tl.addresses[0][t] + offset;
        float* p = (float*)tl.addresses[1][t] + offset;
        float* m = (float*)tl.addresses[2][t] + offset;
        float* v = (float*)tl.addresses[3][t] + offset;
        OutputT* out = (OutputT*)tl.addresses[4][t] + offset;
        for (int64_t start = 0; start < n; start += blockDim.x * ILP) {
            float rg[ILP], rp[ILP], rm[ILP], rv[ILP];
#pragma unroll
            for (int j = 0; j < ILP; ++j) {
                int64_t k = start + threadIdx.x + j * blockDim.x;
                if (k < n) {
                    rg[j] = g[k] * inv_scale;
                    rp[j] = p[k];
                    rm[j] = m[k];
                    rv[j] = v[k];
                } else {
                    rg[j] = rp[j] = rm[j] = rv[j] = 0.0f;
                }
            }
#pragma unroll
            for (int j = 0; j < ILP; ++j) {
                if (mode == ADAM_MODE_0) rg[j] = rg[j] + decay * rp[j];
                rm[j] = beta1 * rm[j] + (1 - beta1) * rg[j];
                rv[j] = beta2 * rv[j] + (1 - beta2) * rg[j] * rg[j];
                float next_m = rm[j] / correction1;
                float next_v = rv[j] / correction2;
                float denom = sqrtf(next_v) + epsilon;
                float update = next_m / denom;
                if (mode == ADAM_MODE_1) update = update + decay * rp[j];
                rp[j] = rp[j] - lr * update;
            }
#pragma unroll
            for (int j = 0; j < ILP; ++j) {
                int64_t k = start + threadIdx.x + j * blockDim.x;
                if (k < n) {
                    p[k] = rp[j];
                    m[k] = rm[j];
                    v[k] = rv[j];
                    out[k] = (OutputT)rp[j];
                }
            }
        }
    }
};

void multi_tensor_adam_master_cuda(int chunk_size,
                                  at::Tensor noop_flag,
                                  std::vector<std::vector<at::Tensor>> tensor_lists,
                                  float lr, float beta1, float beta2, float epsilon,
                                  int step, int mode, int bias_correction,
                                  float weight_decay, float inv_scale)
{
    TORCH_CHECK(tensor_lists.size() == 5, "Expected five tensor lists");
    for (int d = 0; d < 4; ++d)
        for (const auto& tensor : tensor_lists[d])
            TORCH_CHECK(tensor.scalar_type() == at::kFloat, "Expected FP32 master tensors");
    float c1 = 1.0f, c2 = 1.0f;
    if (bias_correction == 1) {
        c1 = 1 - std::pow(beta1, step);
        c2 = 1 - std::pow(beta2, step);
    }
    DISPATCH_DOUBLE_FLOAT_AND_HALF(tensor_lists[4][0].scalar_type(),
                                  0, "adam_master",
                                  multi_tensor_apply<5>(BLOCK_SIZE, chunk_size, noop_flag,
                                                        tensor_lists, MasterAdamFunctor<scalar_t_0>(),
                                                        beta1, beta2, c1, c2, epsilon, lr,
                                                        (adamMode_t)mode, weight_decay, inv_scale);)
    AT_CUDA_CHECK(cudaGetLastError());
}
