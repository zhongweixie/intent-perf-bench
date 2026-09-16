#include "transpose.h"
#include <cuda_runtime.h>

/*
 * Matrix transpose implementation using shared memory.
 *
 * This implementation loads a tile into shared memory with coalesced reads,
 * then writes it out in transposed order.
 */

#define TILE_DIM 32

__global__ void k_transpose(const float* __restrict__ input,
                           float* __restrict__ output,
                           int N) {
    __shared__ float tile[TILE_DIM][TILE_DIM];

    int x = blockIdx.x * TILE_DIM + threadIdx.x;
    int y = blockIdx.y * TILE_DIM + threadIdx.y;

    // Read from global memory (coalesced)
    if (x < N && y < N) {
        tile[threadIdx.y][threadIdx.x] = input[y * N + x];
    }

    __syncthreads();

    // Write to global memory (transposed)
    int tx = blockIdx.y * TILE_DIM + threadIdx.x;
    int ty = blockIdx.x * TILE_DIM + threadIdx.y;

    if (tx < N && ty < N) {
        output[ty * N + tx] = tile[threadIdx.x][threadIdx.y];
    }
}
