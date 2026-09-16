#ifndef CONVOLUTION_H
#define CONVOLUTION_H

#include <cuda.h>
#include <cuda_runtime.h>
#include <device_launch_parameters.h>

// The filter is symmetrical, with 100 elements on the left and 100 elements on the right of a selected index.
constexpr int FILTER_WIDTH = 201;
constexpr int HALF_OF_FILTER_WIDTH = FILTER_WIDTH / 2;
constexpr int FILTER_CENTER_INDEX = 100;
constexpr float FILTER_STANDARD_DEVIATION = (FILTER_WIDTH - FILTER_CENTER_INDEX) / 3.0f;
constexpr float SQUARED_STD_MULT_2 = 2.0f * FILTER_STANDARD_DEVIATION * FILTER_STANDARD_DEVIATION;

__global__ void k_runConvolution(float* coefficients_d, float sumOfCoefficients, float* inputArray_d, float* outputArray_d, int arraySize);

#endif // CONVOLUTION_H