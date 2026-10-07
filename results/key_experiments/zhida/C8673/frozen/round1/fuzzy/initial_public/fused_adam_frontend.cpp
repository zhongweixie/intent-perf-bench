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

at::Tensor mixed_grad_stats_cuda(at::Tensor g);
void mixed_adam_cuda(at::Tensor g, at::Tensor p, at::Tensor m, at::Tensor v,
                     at::Tensor out, float inv_scale, float lr,
                     float beta1, float beta2, float eps, int step,
                     int mode, int bias_correction, float decay);

PYBIND11_MODULE(TORCH_EXTENSION_NAME, m)
{
    m.def("mixed_grad_stats", &mixed_grad_stats_cuda);
    m.def("mixed_adam", &mixed_adam_cuda);
    m.def("multi_tensor_adam",
          &multi_tensor_adam_cuda,
          "Compute and apply gradient update to parameters for Adam optimizer");
}
