"""Frozen correctness oracle and timing for the local AutoEP token-movement export."""
import importlib.util
import itertools
import json
import math
import statistics
import sys
import time
import traceback
from pathlib import Path

import torch


def main():
    repo = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(repo))
    import auto_ep_layer as candidate
    import _oracle_layer as oracle
    from local_pipeline import local_step

    torch.set_num_threads(1)
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 291828
    mode = sys.argv[2]
    torch.manual_seed(seed)
    checks = []

    def combine(module, rows, scores, index, k, shape, pre=False, legacy=False):
        return module.combine_from_routed(rows, scores, index, k,
                                         'pre' if pre else 'post',
                                         'legacy_bmm' if legacy else 'weighted_sum', shape)

    # The 48 numerical input combinations and tolerances come from the fixed
    # upstream #8326 tests. The hardware-availability guard is not an API of
    # the pre-PR baseline and is checked separately by the launcher.
    for k, h, row_dtype, score_dtype in itertools.product(
            (2, 4, 6, 8), (128, 130),
            (torch.float32, torch.float16, torch.bfloat16),
            (torch.float32, torch.bfloat16)):
        g = torch.Generator(device='cuda').manual_seed(20260824 + seed)
        selected = torch.randint(0, 8, (24, k), device='cuda', generator=g)
        index = selected.flatten().argsort(stable=True)
        rows = torch.randn(24*k, h, device='cuda', dtype=row_dtype, generator=g)
        scores = torch.rand(24, k, device='cuda', dtype=score_dtype, generator=g)
        upstream = torch.randn(1, 24, h, device='cuda', dtype=row_dtype, generator=g)
        a, b = rows.clone().requires_grad_(True), rows.clone().requires_grad_(True)
        s, t = scores.clone().requires_grad_(True), scores.clone().requires_grad_(True)
        actual = combine(candidate, a, s, index, k, (1, 24, h))
        expected = combine(oracle, b, t, index, k, (1, 24, h))
        tol = {'rtol': 1e-5, 'atol': 1e-6} if row_dtype == torch.float32 else {}
        torch.testing.assert_close(actual, expected, **tol)
        ag = torch.autograd.grad(actual, (a, s), upstream)
        bg = torch.autograd.grad(expected, (b, t), upstream)
        torch.testing.assert_close(ag[0], bg[0], **tol)
        st = {'rtol': 1e-4, 'atol': 1e-5} if score_dtype == torch.float32 else {}
        torch.testing.assert_close(ag[1], bg[1], **st)
    checks.append('48-upstream-combine-forward-and-both-gradients')

    # Preserve row order, padding, counts, and gradients on the regrouping path.
    for dtype, h, sources, experts in itertools.product(
            (torch.bfloat16, torch.float32), (1, 100, 2048), (1, 4), (3,)):
        counts = torch.randint(0, 24, (sources, experts), device='cuda', dtype=torch.int32)
        counts[:, 1] = 0
        if sources == 1:
            counts = counts.flatten()
        n = int(counts.sum().item())
        x = torch.randn(n, h, device='cuda', dtype=dtype)
        a, b = x.clone().requires_grad_(True), x.clone().requires_grad_(True)
        ca = candidate.permute_by_local_expert(a, counts)
        ob = oracle.permute_by_local_expert(b, counts)
        assert ca[3] == ob[3]
        for u, v in zip(ca[:3], ob[:3]):
            assert torch.equal(u, v), 'row permutation/count/padding changed'
        up = torch.randn_like(ca[0])
        ga = torch.autograd.grad(ca[0], a, up)[0]
        gb = torch.autograd.grad(ob[0], b, up)[0]
        assert torch.equal(ga, gb), 'permutation gradient changed'
        expert = torch.randn_like(ca[0])
        ra, rb = expert.clone().requires_grad_(True), expert.clone().requires_grad_(True)
        ya = candidate.unpermute_by_local_expert(ra, ca[1], n)
        yb = oracle.unpermute_by_local_expert(rb, ob[1], n)
        assert torch.equal(ya, yb), 'restored row order changed'
        up = torch.randn_like(ya)
        assert torch.equal(torch.autograd.grad(ya, ra, up)[0],
                           torch.autograd.grad(yb, rb, up)[0]), 'unpermute gradient changed'
    checks.append('24-empty-expert-and-hidden-shape-reorder-cases')

    for device in ('cpu', 'cuda'):
        counts = torch.tensor([[3, 0], [2, 1]], device=device, dtype=torch.int32)
        x = torch.randn(6, 10, device=device)[:, ::2]
        a = candidate.permute_by_local_expert(x, counts)
        b = oracle.permute_by_local_expert(x, counts)
        assert all(torch.equal(u, v) for u, v in zip(a[:3], b[:3]))
        assert torch.equal(candidate.unpermute_by_local_expert(a[0], a[1], 6), x)
        for pre, legacy in ((True, False), (False, True)):
            index = torch.randperm(12, device=device)
            rows = torch.randn(12, 7, device=device)
            scores = torch.rand(6, 2, device=device)
            torch.testing.assert_close(combine(candidate, rows, scores, index, 2, (2, 3, 7), pre, legacy),
                                       combine(oracle, rows, scores, index, 2, (2, 3, 7), pre, legacy))
    checks.append('cpu-strided-input-and-pre-legacy-fallbacks')

    # Timed inputs are fixed throughout a measurement, but their token values,
    # routing permutation, and counts change across independent evaluations.
    cases = []
    for name, n, k, h in (('local-4096-top8', 4096, 8, 2048),
                           ('local-8192-top8', 8192, 8, 2048)):
        g = torch.Generator(device='cuda').manual_seed(seed+n)
        selected = torch.randint(0, 128, (n, k), device='cuda', generator=g)
        index = selected.flatten().argsort(stable=True)
        counts = selected.flatten().bincount(minlength=128).reshape(16, 8).to(torch.int32)
        rows = torch.randn(n*k, h, device='cuda', dtype=torch.bfloat16, generator=g).requires_grad_(True)
        scores = torch.rand(n, k, device='cuda', generator=g).requires_grad_(True)
        upstream = torch.randn(1, n, h, device='cuda', dtype=torch.bfloat16, generator=g)

        def call(module=candidate):
            return local_step(module, rows, counts, scores, index, k, upstream)

        actual, expected = call(), call(oracle)
        torch.testing.assert_close(actual[0], expected[0])
        torch.testing.assert_close(actual[1][0], expected[1][0])
        # The wide hidden reduction spans 2048 terms rather than the 128/130
        # terms in upstream unit tests. The explicit absolute allowance covers
        # FP32 summation-order rounding, not missing routing contributions.
        torch.testing.assert_close(actual[1][1], expected[1][1], rtol=1e-4, atol=1e-4)
        for _ in range(2):
            call()
        samples = []
        for _ in range(4 if mode == 'interim' else 6):
            torch.cuda.synchronize()
            start = time.perf_counter()
            for _ in range(4):
                call()
            torch.cuda.synchronize()
            samples.append((time.perf_counter()-start)*1000/4)
        cases.append({'name': name, 'latency_ms': statistics.median(samples), 'samples_ms': samples})
    latency = math.exp(sum(math.log(c['latency_ms']) for c in cases)/len(cases))
    print(json.dumps({'correct': True, 'latency_ms': latency, 'cases': cases,
                      'checks': checks, 'errors': [], 'gpu': torch.cuda.get_device_name(),
                      'timing': 'local token movement, synchronized wall milliseconds; no communication or GEMM'}))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(json.dumps({'correct': False, 'errors': [type(exc).__name__+': '+str(exc)[:5000]],
                          'traceback': traceback.format_exc()[-5000:]}))
        raise SystemExit(1)
