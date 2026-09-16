#include "convolution.h"

/*
 * Naive 1D Convolution implementation (baseline - slow version).
 *
 * Performance bottlenecks:
 * 1. No shared memory - all reads from global memory
 * 2. Redundant reads of input data (each element read FILTER_WIDTH times)
 * 3. Redundant reads of coefficients (read from global memory in inner loop)
 * 4. No tiling optimization
 */

__global__ void k_runConvolution(float* coefficients_d, float sumOfCoefficients,
                                float* inputArray_d, float* outputArray_d, int arraySize) {
    // Simple one-thread-per-output-element mapping
    int gid = blockIdx.x * blockDim.x + threadIdx.x;

    if (gid < arraySize) {
        float sum = 0.0f;

        // Naive convolution: read from global memory for each access
        for (int j = 0; j < FILTER_WIDTH; j++) {
            int inputIndex = gid - HALF_OF_FILTER_WIDTH + j;

            float inputValue = 0.0f;
            if (inputIndex >= 0 && inputIndex < arraySize) {
                // Uncoalesced global memory read
                inputValue = inputArray_d[inputIndex];
            }

            // Redundant global memory read of coefficient
            float coefficient = coefficients_d[j];

            // Simple multiply-add (no fmaf optimization)
            sum += coefficient * inputValue;
        }

        // Normalize and write output
        outputArray_d[gid] = sum / sumOfCoefficients;
    }
}
