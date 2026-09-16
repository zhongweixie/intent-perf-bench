/*
 * solve.cu -- NTT butterfly (Cooley-Tukey) on Goldilocks prime (CUDA).
 * Edit this file to fix the performance regression.
 */

#include "solve.h"

namespace {

constexpr uint64_t P = NTT_PRIME;

__device__ __forceinline__ uint64_t mod_add_dev(uint64_t a, uint64_t b) {
    uint64_t s = a + b;
    if (s < a || s >= P) s -= P;
    return s;
}

__device__ __forceinline__ uint64_t mod_sub_dev(uint64_t a, uint64_t b) {
    return (a >= b) ? (a - b) : (a + (P - b));
}

__device__ __forceinline__ uint64_t mod_mul_dev(uint64_t a, uint64_t b) {
    unsigned long long lo = a * b;
    unsigned long long hi = __umul64hi(a, b);
    unsigned long long hi_red = hi % P;
    unsigned long long two64_mod = ((unsigned long long)0xFFFFFFFFFFFFFFFFULL % P + 1ULL) % P;
    unsigned long long high_part = (unsigned long long)(((__uint128_t)hi_red * (__uint128_t)two64_mod) % (__uint128_t)P);
    unsigned long long lo_red = lo % P;
    unsigned long long s = high_part + lo_red;
    if (s < high_part || s >= P) s -= P;
    return s;
}

__device__ __forceinline__ uint64_t mod_pow_dev(uint64_t base, uint64_t exp) {
    uint64_t r = 1, b = base % P;
    while (exp > 0) {
        if (exp & 1ULL) r = mod_mul_dev(r, b);
        b = mod_mul_dev(b, b);
        exp >>= 1;
    }
    return r;
}

__device__ __forceinline__ uint64_t omega_for_stage(int log_n) {
    uint64_t omega32 = mod_pow_dev(7ULL, ((uint64_t)1 << 32) - 1ULL);
    int shift = 32 - log_n;
    for (int i = 0; i < shift; ++i) omega32 = mod_mul_dev(omega32, omega32);
    return omega32;
}

__device__ __forceinline__ uint32_t bit_reverse_dev(uint32_t x, int bits) {
    x = ((x >> 1) & 0x55555555u) | ((x & 0x55555555u) << 1);
    x = ((x >> 2) & 0x33333333u) | ((x & 0x33333333u) << 2);
    x = ((x >> 4) & 0x0f0f0f0fu) | ((x & 0x0f0f0f0fu) << 4);
    x = ((x >> 8) & 0x00ff00ffu) | ((x & 0x00ff00ffu) << 8);
    x = (x >> 16) | (x << 16);
    return x >> (32 - bits);
}

__global__ void bitrev_kernel(uint64_t* data, int batch, int n, int log_n) {
    int row = blockIdx.y, i = blockIdx.x * blockDim.x + threadIdx.x;
    if (row >= batch || i >= n) return;
    uint32_t j = bit_reverse_dev((uint32_t)i, log_n);
    if ((int)j > i) {
        uint64_t* rd = data + (size_t)row * (size_t)n;
        uint64_t a = rd[i], b = rd[j]; rd[i] = b; rd[j] = a;
    }
}

// There are only n-1 distinct stage twiddles.  Generate them once, rather
// than making every row recompute powers of a root of unity.  This deliberately
// uses one thread: table construction is tiny compared with a batched NTT and
// the recurrence makes it just O(n) multiplications.
__global__ void make_twiddle_table(uint64_t* twiddles, int log_n) {
    if (blockIdx.x != 0 || threadIdx.x != 0) return;
    for (int s = 1; s <= log_n; ++s) {
        int half = 1 << (s - 1);
        int offset = half - 1; // 1 + 2 + ... + 2^(s-2)
        uint64_t omega = omega_for_stage(s);
        uint64_t w = 1;
        for (int j = 0; j < half; ++j) {
            twiddles[offset + j] = w;
            w = mod_mul_dev(w, omega);
        }
    }
}

__global__ void butterfly_stage_kernel(uint64_t* data, const uint64_t* twiddles,
                                       int batch, int n, int s) {
    int row = blockIdx.y, pair = blockIdx.x * blockDim.x + threadIdx.x;
    int half_total = n >> 1;
    if (row >= batch || pair >= half_total) return;
    int half = 1 << (s - 1);
    // pair is arranged as [half butterflies] per m-element group.  Since
    // half is a power of two, masks/shifts avoid an integer divide here.
    int j = pair & (half - 1);
    int k = (pair - j) << 1;
    uint64_t w = twiddles[(half - 1) + j];
    uint64_t* rd = data + (size_t)row * (size_t)n;
    uint64_t u = rd[k + j], v = mod_mul_dev(rd[k + j + half], w);
    rd[k + j] = mod_add_dev(u, v);
    rd[k + j + half] = mod_sub_dev(u, v);
}

}  // namespace

void ntt_forward_cuda(uint64_t* data,
                      void* workspace,
                      size_t workspace_bytes,
                      int batch, int n, cudaStream_t stream) {
    if (!data || !workspace || batch <= 0 || n <= 0) return;

    int log_n = 0;
    while ((1 << log_n) < n) ++log_n;
    // A transform of n points has exactly n - 1 stage twiddles.
    if (workspace_bytes < (size_t)(n - 1) * sizeof(uint64_t)) return;
    uint64_t* twiddles = static_cast<uint64_t*>(workspace);

    constexpr int block = 256;
    int half_total = n >> 1;
    int grid_x = (n + block - 1) / block;
    int grid_x2 = (half_total + block - 1) / block;

    // Stream ordering supplies all required stage fences.  In particular, do
    // not synchronize per row: every row is independent and grid.y batches
    // them in each launch.
    make_twiddle_table<<<1, 1, 0, stream>>>(twiddles, log_n);
    bitrev_kernel<<<dim3(grid_x, batch), block, 0, stream>>>(data, batch, n, log_n);
    for (int s = 1; s <= log_n; ++s) {
        butterfly_stage_kernel<<<dim3(grid_x2, batch), block, 0, stream>>>(
            data, twiddles, batch, n, s);
    }
}
