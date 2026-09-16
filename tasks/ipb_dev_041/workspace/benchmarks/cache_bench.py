"""Performance and correctness benchmark for the KV-cache prefix manager.

Checks two things:
  1. Timing  — the workload must complete within THRESHOLD seconds.
  2. Correctness — the LRU evictor must evict blocks in proper LRU order,
     including after update() calls that change last_accessed timestamps.

Exit code 0 = PASS (both checks satisfied).
Exit code 1 = FAIL (timing or correctness violation).
"""

import random
import sys
import time

# Make sure the workspace root is on the path regardless of cwd.
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from inference_cache.evictor import LRUEvictor, make_evictor, EvictionPolicy
from inference_cache.block_allocator import BlockAllocator
from inference_cache.hasher import hash_block_tokens, BLOCK_SIZE

THRESHOLD = 0.70  # seconds — regressed ~1.47 s, both-fixed ~0.10 s

# ---------------------------------------------------------------------------
# Workload parameters (must match run_workload.py exactly)
# ---------------------------------------------------------------------------
POOL_SIZE = 10_000
NUM_REQUESTS = 5_000
WINDOWS_PER_REQUEST = 80    # token windows hashed per request
EVICTIONS_PER_REQUEST = 2   # eviction cycles triggered per request
RANDOM_SEED = 2024


# ---------------------------------------------------------------------------
# Correctness checks
# ---------------------------------------------------------------------------

def _verify_lru_correctness() -> None:
    """Verify LRU evictor correctness with deterministic scenarios.

    Raises AssertionError if any check fails.
    """

    # --- Check 1: basic LRU order ---
    ev = make_evictor(EvictionPolicy.LRU)
    ev.add(0, 100, 16, 1.0)
    ev.add(1, 200, 16, 2.0)
    ev.add(2, 300, 16, 3.0)

    bid, _ = ev.evict()
    assert bid == 0, (
        f"[Correctness] Basic LRU: expected block 0 (oldest, t=1.0) "
        f"to be evicted first, got block {bid}"
    )
    bid, _ = ev.evict()
    assert bid == 1, (
        f"[Correctness] Basic LRU: expected block 1 (t=2.0) second, got block {bid}"
    )

    # --- Check 2: LRU order after update() ---
    ev2 = make_evictor(EvictionPolicy.LRU)
    ev2.add(10, 1000, 32, 1.0)
    ev2.add(11, 1001, 32, 2.0)
    ev2.add(12, 1002, 32, 3.0)

    # Block 10 is the oldest.  Refresh it — now block 11 is LRU.
    ev2.update(10, 99.0)

    bid, _ = ev2.evict()
    assert bid == 11, (
        f"[Correctness] After update(10, 99.0): block 11 (t=2.0) "
        f"should be evicted first, got block {bid}"
    )

    # --- Check 3: all blocks remain evictable after update() ---
    ev3 = make_evictor(EvictionPolicy.LRU)
    N = 50
    for i in range(N):
        ev3.add(i, i * 7, 32, float(i))

    rng = random.Random(0)
    for i in range(N):
        ev3.update(i, rng.random() * 1000)

    evicted_ids = []
    for _ in range(N):
        bid, _ = ev3.evict()
        evicted_ids.append(bid)

    assert len(evicted_ids) == N, (
        f"[Correctness] Expected {N} evictions, got {len(evicted_ids)}.  "
        f"Some blocks became stuck after update() calls."
    )
    assert len(set(evicted_ids)) == N, (
        f"[Correctness] Duplicate block IDs in eviction sequence — "
        f"evictor returned the same block twice."
    )

    # --- Check 4: LRU strictly respected after many updates ---
    ev4 = make_evictor(EvictionPolicy.LRU)
    timestamps = {}
    rng2 = random.Random(42)
    for i in range(20):
        t = rng2.random()
        ev4.add(i, i, 32, t)
        timestamps[i] = t

    for _ in range(30):
        i = rng2.randint(0, 19)
        new_t = rng2.random() * 2
        ev4.update(i, new_t)
        timestamps[i] = new_t

    prev_t = -1.0
    for _ in range(20):
        bid, _ = ev4.evict()
        t = timestamps[bid]
        assert t >= prev_t, (
            f"[Correctness] Eviction order violated: evicted block {bid} "
            f"with t={t:.4f} after a block with t={prev_t:.4f}"
        )
        prev_t = t


# ---------------------------------------------------------------------------
# Timing benchmark
# ---------------------------------------------------------------------------

def _run_timed_workload() -> float:
    import hashlib, struct

    rng = random.Random(RANDOM_SEED)

    # Pre-populate evictor with all blocks (simulates warm server reload from disk).
    evictor = make_evictor(EvictionPolicy.LRU)
    for block_id in range(POOL_SIZE):
        evictor.add(
            block_id,
            content_hash=rng.randint(0, (1 << 64) - 1),
            num_hashed_tokens=rng.randint(1, 16) * BLOCK_SIZE,
            last_accessed=rng.random() * 1_000,
        )

    # Generate token windows for all requests.
    vocab_size = 32_000
    all_windows = [
        tuple(rng.randint(0, vocab_size - 1) for _ in range(BLOCK_SIZE))
        for _ in range(NUM_REQUESTS * WINDOWS_PER_REQUEST)
    ]

    t0 = time.perf_counter()

    prefix_hash = 0
    idx = 0
    for req in range(NUM_REQUESTS):
        # Stage 3: compute prefix hashes for this request's token windows.
        for _ in range(WINDOWS_PER_REQUEST):
            window = all_windows[idx]; idx += 1
            raw = struct.pack(f"{BLOCK_SIZE}I", *window) + prefix_hash.to_bytes(8, "little")
            prefix_hash = int.from_bytes(hashlib.sha256(raw).digest()[:8], "little")

        # Stage 5: eviction cycles under memory pressure.
        for _ in range(EVICTIONS_PER_REQUEST):
            block_id, content_hash = evictor.evict()
            # Re-add with a fresh timestamp to keep pool size constant.
            evictor.add(
                block_id,
                content_hash=rng.randint(0, (1 << 64) - 1),
                num_hashed_tokens=rng.randint(1, 16) * BLOCK_SIZE,
                last_accessed=rng.random() * 1_000,
            )

    return time.perf_counter() - t0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("KV-Cache Prefix Manager Benchmark")
    print("=" * 60)

    # Step 1: correctness
    print("\n[1/2] Correctness check ...")
    try:
        _verify_lru_correctness()
        print("      PASS — LRU order correct in all scenarios")
    except AssertionError as e:
        print(f"      FAIL — {e}")
        sys.exit(1)

    # Step 2: timing
    print(f"\n[2/2] Timing check (threshold = {THRESHOLD:.2f}s) ...")
    elapsed = _run_timed_workload()
    print(f"      Elapsed: {elapsed:.3f}s")

    if elapsed < THRESHOLD:
        print(f"      PASS — {elapsed:.3f}s < {THRESHOLD:.2f}s")
    else:
        print(f"      FAIL — {elapsed:.3f}s >= {THRESHOLD:.2f}s")
        sys.exit(1)

    print("\nResult: PASS")


if __name__ == "__main__":
    main()
