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


// Flat fp32 master update with in-register unscaling and low-precision
// writeback. No optimizer state is kept in the low-precision output.
template <typename Output>
__global__ void mixed_precision_adam_kernel(const float* g,
                                            float* p,
                                            float* m,
                                            float* v,
                                            Output* output,
                                            int64_t n,
                                            float beta1,
                                            float beta2,
                                            float correction1,
                                            float correction2,
                                            float epsilon,
                                            float lr,
                                            int mode,
                                            float decay,
                                            float inv_scale)
{
    for (int64_t start = (int64_t)blockIdx.x * blockDim.x * 4;
         start < n;
         start += (int64_t)gridDim.x * blockDim.x * 4) {
        float rg[4], rp[4], rm[4], rv[4];
#pragma unroll
        for (int j = 0; j < 4; ++j) {
            int64_t i = start + threadIdx.x + j * blockDim.x;
            if (i < n) {
                // Match the rounding of the original standalone fp32 mul_.
                rg[j] = __fmul_rn(g[i], inv_scale);
                rp[j] = p[i];
                rm[j] = m[i];
                rv[j] = v[i];
            } else {
                rg[j] = rp[j] = rm[j] = rv[j] = 0.0f;
            }
        }
#pragma unroll
        for (int j = 0; j < 4; ++j) {
            if (mode == ADAM_MODE_0) {
                rg[j] = rg[j] + decay * rp[j];
                rm[j] = beta1 * rm[j] + (1 - beta1) * rg[j];
                rv[j] = beta2 * rv[j] + (1 - beta2) * rg[j] * rg[j];
                float next_m = rm[j] / correction1;
                float next_v = rv[j] / correction2;
                float denom = sqrtf(next_v) + epsilon;
                float update = next_m / denom;
                rp[j] = rp[j] - lr * update;
            } else {
                rm[j] = beta1 * rm[j] + (1 - beta1) * rg[j];
                rv[j] = beta2 * rv[j] + (1 - beta2) * rg[j] * rg[j];
                float next_m = rm[j] / correction1;
                float next_v = rv[j] / correction2;
                float denom = sqrtf(next_v) + epsilon;
                float update = next_m / denom + decay * rp[j];
                rp[j] = rp[j] - lr * update;
            }
        }
#pragma unroll
        for (int j = 0; j < 4; ++j) {
            int64_t i = start + threadIdx.x + j * blockDim.x;
            if (i < n) {
                p[i] = rp[j];
                m[i] = rm[j];
                v[i] = rv[j];
                output[i] = (Output)rp[j];
            }
        }
    }
}

void mixed_precision_adam_cuda(at::Tensor grad,
                               at::Tensor param,
                               at::Tensor exp_avg,
                               at::Tensor exp_avg_sq,
                               at::Tensor output,
                               const float lr,
                               const float beta1,
                               const float beta2,
                               const float epsilon,
                               const int step,
                               const int mode,
                               const int bias_correction,
                               const float weight_decay,
                               const float inv_scale)
{
    for (const auto& t : {grad, param, exp_avg, exp_avg_sq}) {
        TORCH_CHECK(t.is_cuda() && t.is_contiguous() &&
                    t.scalar_type() == at::kFloat &&
                    t.numel() == param.numel() && t.device() == param.device(),
                    "mixed precision Adam requires matching contiguous CUDA fp32 tensors");
    }
    TORCH_CHECK(output.is_cuda() && output.is_contiguous() &&
                output.numel() == param.numel() && output.device() == param.device(),
                "mixed precision Adam output must match the master tensor");
    TORCH_CHECK(output.scalar_type() == at::kHalf || output.scalar_type() == at::kBFloat16,
                "mixed precision Adam output must be fp16 or bf16");
    if (!param.numel()) return;
    const at::cuda::OptionalCUDAGuard device_guard(device_of(param));
    auto stream = at::cuda::getCurrentCUDAStream();
    float correction1 = 1.0f, correction2 = 1.0f;
    if (bias_correction == 1) {
        correction1 = 1 - std::pow(beta1, step);
        correction2 = 1 - std::pow(beta2, step);
    }
    int blocks = (int)std::min<int64_t>((param.numel() + 1023) / 1024, 4096);
    if (output.scalar_type() == at::kHalf) {
        mixed_precision_adam_kernel<at::Half><<<blocks, 256, 0, stream>>>(
            grad.data_ptr<float>(), param.data_ptr<float>(), exp_avg.data_ptr<float>(),
            exp_avg_sq.data_ptr<float>(), output.data_ptr<at::Half>(), param.numel(),
            beta1, beta2, correction1, correction2, epsilon, lr, mode, weight_decay, inv_scale);
    } else {
        mixed_precision_adam_kernel<at::BFloat16><<<blocks, 256, 0, stream>>>(
            grad.data_ptr<float>(), param.data_ptr<float>(), exp_avg.data_ptr<float>(),
            exp_avg_sq.data_ptr<float>(), output.data_ptr<at::BFloat16>(), param.numel(),
            beta1, beta2, correction1, correction2, epsilon, lr, mode, weight_decay, inv_scale);
    }
    AT_CUDA_CHECK(cudaGetLastError());
}

