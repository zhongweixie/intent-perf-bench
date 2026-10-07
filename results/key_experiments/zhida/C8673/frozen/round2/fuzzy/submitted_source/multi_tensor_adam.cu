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

template <typename Out>
__global__ void adam_mixed_kernel(const float* __restrict__ g, float* __restrict__ p,
                                  float* __restrict__ m, float* __restrict__ v,
                                  Out* __restrict__ out, int64_t n, float scale,
                                  float lr, float b1, float b2, float c1, float c2,
                                  float eps, int mode, float decay)
{
    for (int64_t i = (int64_t(blockIdx.x) * blockDim.x + threadIdx.x) * 4;
         i < n; i += int64_t(gridDim.x) * blockDim.x * 4) {
        float4 gg, pp, mm, vv;
        if (i + 3 < n) {
            gg = reinterpret_cast<const float4*>(g)[i / 4];
            pp = reinterpret_cast<const float4*>(p)[i / 4];
            mm = reinterpret_cast<const float4*>(m)[i / 4];
            vv = reinterpret_cast<const float4*>(v)[i / 4];
        } else {
            gg = pp = mm = vv = make_float4(0, 0, 0, 0);
            for (int j = 0; j < 4 && i+j < n; ++j) {
                (&gg.x)[j] = g[i+j]; (&pp.x)[j] = p[i+j];
                (&mm.x)[j] = m[i+j]; (&vv.x)[j] = v[i+j];
            }
        }
#pragma unroll
        for (int j = 0; j < 4; ++j) {
            float rg = (&gg.x)[j] * scale;
            float rp = (&pp.x)[j];
            if (mode == 0) rg = rg + decay * rp;
            float rm = b1 * (&mm.x)[j] + (1 - b1) * rg;
            float rv = b2 * (&vv.x)[j] + (1 - b2) * rg * rg;
            float update = (rm / c1) / (sqrtf(rv / c2) + eps);
            if (mode != 0) update = update + decay * rp;
            rp = rp - lr * update;
            (&pp.x)[j] = rp; (&mm.x)[j] = rm; (&vv.x)[j] = rv;
        }
        if (i + 3 < n) {
            reinterpret_cast<float4*>(p)[i / 4] = pp;
            reinterpret_cast<float4*>(m)[i / 4] = mm;
            reinterpret_cast<float4*>(v)[i / 4] = vv;
        } else {
            for (int j = 0; j < 4 && i+j < n; ++j) {
                p[i+j] = (&pp.x)[j]; m[i+j] = (&mm.x)[j]; v[i+j] = (&vv.x)[j];
            }
        }
#pragma unroll
        for (int j = 0; j < 4; ++j) {
            if (i+j < n) out[i+j] = static_cast<Out>((&pp.x)[j]);
        }
    }
}


template <typename In>
__global__ void prepare_mixed_kernel(const In* __restrict__ g, float* __restrict__ dst,
                                     float* __restrict__ stats, int64_t n)
{
    double sum = 0.;
    int bad = 0;
    for (int64_t i = int64_t(blockIdx.x) * blockDim.x + threadIdx.x;
         i < n; i += int64_t(gridDim.x) * blockDim.x) {
        float x = static_cast<float>(g[i]);
        dst[i] = x;
        bad |= !isfinite(x);
        sum += double(x) * double(x);
    }
    for (int offset = 16; offset > 0; offset >>= 1) {
        sum += __shfl_down_sync(0xffffffff, sum, offset);
        bad |= __shfl_down_sync(0xffffffff, bad, offset);
    }
    __shared__ double sums[8];
    __shared__ int flags[8];
    if ((threadIdx.x & 31) == 0) {
        sums[threadIdx.x >> 5] = sum;
        flags[threadIdx.x >> 5] = bad;
    }
    __syncthreads();
    if (threadIdx.x < 32) {
        sum = threadIdx.x < 8 ? sums[threadIdx.x] : 0.;
        bad = threadIdx.x < 8 ? flags[threadIdx.x] : 0;
        for (int offset = 16; offset > 0; offset >>= 1) {
            sum += __shfl_down_sync(0xffffffff, sum, offset);
            bad |= __shfl_down_sync(0xffffffff, bad, offset);
        }
        if (threadIdx.x == 0) {
            stats[2 * blockIdx.x] = static_cast<float>(sum);
            stats[2 * blockIdx.x + 1] = static_cast<float>(bad);
        }
    }
}

at::Tensor prepare_mixed_cuda(at::Tensor g, at::Tensor dst)
{
    TORCH_CHECK(g.is_cuda() && dst.is_cuda() && g.device() == dst.device(),
                "expected tensors on the same CUDA device");
    TORCH_CHECK(g.is_contiguous() && dst.is_contiguous() &&
                dst.scalar_type() == at::kFloat && g.numel() == dst.numel(), "invalid gradient buffers");
    const at::cuda::OptionalCUDAGuard guard(device_of(g));
    if (g.numel() == 0) return at::zeros({2}, dst.options());
    int blocks = std::min<int64_t>((g.numel() + 255) / 256, 4096);
    auto stats = at::empty({blocks, 2}, dst.options());
    auto stream = at::cuda::getCurrentCUDAStream();
    if (g.scalar_type() == at::kHalf) {
        prepare_mixed_kernel<at::Half><<<blocks, 256, 0, stream>>>(
            g.data_ptr<at::Half>(), dst.data_ptr<float>(), stats.data_ptr<float>(), g.numel());
    } else if (g.scalar_type() == at::kBFloat16) {
        prepare_mixed_kernel<at::BFloat16><<<blocks, 256, 0, stream>>>(
            g.data_ptr<at::BFloat16>(), dst.data_ptr<float>(), stats.data_ptr<float>(), g.numel());
    } else { TORCH_CHECK(false, "expected FP16 or BF16 gradients"); }
    AT_CUDA_CHECK(cudaGetLastError());
    return stats.sum(0);
}

void adam_mixed_cuda(at::Tensor g, at::Tensor p, at::Tensor m, at::Tensor v,
                     at::Tensor out, float scale, float lr, float beta1, float beta2,
                     float epsilon, int step, int mode, int bias_correction, float decay)
{
    TORCH_CHECK(g.scalar_type() == at::kFloat && p.scalar_type() == at::kFloat &&
                m.scalar_type() == at::kFloat && v.scalar_type() == at::kFloat, "expected FP32 tensors");
    TORCH_CHECK(g.is_contiguous() && p.is_contiguous() && m.is_contiguous() &&
                v.is_contiguous() && out.is_contiguous(), "expected contiguous tensors");
    TORCH_CHECK(g.numel() == p.numel() && m.numel() == p.numel() &&
                v.numel() == p.numel() && out.numel() == p.numel(), "size mismatch");
    const at::cuda::OptionalCUDAGuard guard(device_of(p));
    float c1 = 1.0f, c2 = 1.0f;
    if (bias_correction) { c1 = 1 - std::pow(beta1, step); c2 = 1 - std::pow(beta2, step); }
    if (p.numel() == 0) return;
    int blocks = std::min<int64_t>((p.numel() + 1023) / 1024, 4096);
    auto stream = at::cuda::getCurrentCUDAStream();
    if (out.scalar_type() == at::kHalf) {
        adam_mixed_kernel<at::Half><<<blocks, 256, 0, stream>>>(
            g.data_ptr<float>(), p.data_ptr<float>(), m.data_ptr<float>(), v.data_ptr<float>(),
            out.data_ptr<at::Half>(), p.numel(), scale, lr, beta1, beta2, c1, c2, epsilon, mode, decay);
    } else if (out.scalar_type() == at::kBFloat16) {
        adam_mixed_kernel<at::BFloat16><<<blocks, 256, 0, stream>>>(
            g.data_ptr<float>(), p.data_ptr<float>(), m.data_ptr<float>(), v.data_ptr<float>(),
            out.data_ptr<at::BFloat16>(), p.numel(), scale, lr, beta1, beta2, c1, c2, epsilon, mode, decay);
    } else { TORCH_CHECK(false, "expected FP16 or BF16 output"); }
    AT_CUDA_CHECK(cudaGetLastError());
}

