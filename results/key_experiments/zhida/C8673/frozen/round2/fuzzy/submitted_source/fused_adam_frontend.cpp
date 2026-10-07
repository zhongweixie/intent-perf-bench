// Copyright (c) Microsoft Corporation.
// SPDX-License-Identifier: Apache-2.0

// DeepSpeed Team

#include <torch/extension.h>

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
                            const float weight_decay);

at::Tensor prepare_mixed_cuda(at::Tensor g, at::Tensor dst);

void adam_mixed_cuda(at::Tensor g, at::Tensor p, at::Tensor m, at::Tensor v,
                     at::Tensor out, float scale, float lr, float beta1, float beta2,
                     float epsilon, int step, int mode, int bias_correction, float decay);

PYBIND11_MODULE(TORCH_EXTENSION_NAME, m)
{
    m.def("prepare_mixed", &prepare_mixed_cuda, "Convert gradients and collect norm and nonfinite statistics");
    m.def("adam_mixed", &adam_mixed_cuda, "Adam with fused scaling and low precision writeback");
    m.def("multi_tensor_adam",
          &multi_tensor_adam_cuda,
          "Compute and apply gradient update to parameters for Adam optimizer");
}
