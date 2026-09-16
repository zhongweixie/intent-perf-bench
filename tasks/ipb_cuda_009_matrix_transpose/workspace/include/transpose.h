#ifndef TRANSPOSE_H
#define TRANSPOSE_H

// Matrix dimension (square matrix N×N)
constexpr int MATRIX_SIZE = 4096;

// CUDA kernel function signature
// Transposes input matrix (N×N) to output matrix
// out[i][j] = in[j][i]
__global__ void k_transpose(const float* __restrict__ input,
                           float* __restrict__ output,
                           int N);

#endif // TRANSPOSE_H
