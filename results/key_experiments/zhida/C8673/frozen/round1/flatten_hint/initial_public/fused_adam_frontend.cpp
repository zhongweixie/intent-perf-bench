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

void multi_tensor_grad_copy_cuda(int chunk_size, at::Tensor overflow,
                                 std::vector<std::vector<at::Tensor>> tensor_lists);

void multi_tensor_adam_master_cuda(int chunk_size, at::Tensor noop_flag,
                                  std::vector<std::vector<at::Tensor>> tensor_lists,
                                  float lr, float beta1, float beta2, float epsilon,
                                  int step, int mode, int bias_correction,
                                  float weight_decay, float inv_scale);

PYBIND11_MODULE(TORCH_EXTENSION_NAME, m)
{
    m.def("multi_tensor_grad_copy", &multi_tensor_grad_copy_cuda,
          "Convert and pack gradients while detecting non-finite values");
    m.def("multi_tensor_adam_master", &multi_tensor_adam_master_cuda,
          "FP32 master Adam update with scaling and low-precision writeback");
    m.def("multi_tensor_adam",
          &multi_tensor_adam_cuda,
          "Compute and apply gradient update to parameters for Adam optimizer");
}
