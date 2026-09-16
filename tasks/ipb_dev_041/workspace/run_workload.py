"""LLM Prefix KV-Cache Workload Simulator.

Simulates a realistic LLM serving workload:
  Stage 1 - Initialise block pool and evictor
  Stage 2 - Generate synthetic request batch
  Stage 3 - Compute prefix hashes for all token windows
  Stage 4 - Run cache lookup and block allocation
  Stage 5 - Process eviction cycles under memory pressure
  Stage 6 - Collect and write cache statistics

Run:
    python run_workload.py
"""

import hashlib
import random
import struct
import sys
import time
from typing import List, Tuple

from inference_cache.evictor import make_evictor, EvictionPolicy
from inference_cache.hasher import BLOCK_SIZE

# ---------------------------------------------------------------------------
# Workload parameters
# ---------------------------------------------------------------------------

POOL_SIZE = 10_000          # physical KV-cache blocks
NUM_REQUESTS = 5_000        # number of simulated inference requests
WINDOWS_PER_REQUEST = 80    # prefix hash windows computed per request
EVICTIONS_PER_REQUEST = 2   # eviction cycles triggered per request
RANDOM_SEED = 2024


def run_workload() -> dict:
    rng = random.Random(RANDOM_SEED)

    # ------------------------------------------------------------------
    # Stage 1: Initialise block pool
    # ------------------------------------------------------------------
    print("[Stage 1] Initialising KV-cache block pool ...")
    evictor = make_evictor(EvictionPolicy.LRU)
    # Pre-populate with all blocks: simulates a warm server that reloaded
    # its cached state from disk (timestamps are from the previous session).
    for block_id in range(POOL_SIZE):
        evictor.add(
            block_id,
            content_hash=rng.randint(0, (1 << 64) - 1),
            num_hashed_tokens=rng.randint(1, 16) * BLOCK_SIZE,
            last_accessed=rng.random() * 1_000,
        )

    # ------------------------------------------------------------------
    # Stage 2: Generate synthetic request batch
    # ------------------------------------------------------------------
    print("[Stage 2] Generating synthetic request batch ...")
    vocab_size = 32_000
    all_windows: List[Tuple[int, ...]] = [
        tuple(rng.randint(0, vocab_size - 1) for _ in range(BLOCK_SIZE))
        for _ in range(NUM_REQUESTS * WINDOWS_PER_REQUEST)
    ]

    # ------------------------------------------------------------------
    # Stage 3: Compute prefix hashes  (hot path — called for every window)
    # ------------------------------------------------------------------
    print("[Stage 3] Computing prefix hashes for request batch ...")
    # (hashing runs inline in the main loop below)

    # ------------------------------------------------------------------
    # Stage 4: Run cache lookup
    # ------------------------------------------------------------------
    print("[Stage 4] Running cache lookup and block allocation ...")

    # ------------------------------------------------------------------
    # Stage 5: Eviction cycles under memory pressure  (hot path)
    # ------------------------------------------------------------------
    print("[Stage 5] Processing eviction cycles under memory pressure ...")

    total_evictions = 0
    prefix_hash = 0
    idx = 0

    for req in range(NUM_REQUESTS):
        # Stage 3 hot path: compute prefix hashes for this request's windows.
        for _ in range(WINDOWS_PER_REQUEST):
            window = all_windows[idx]; idx += 1
            raw = struct.pack(f"{BLOCK_SIZE}I", *window) + prefix_hash.to_bytes(8, "little")
            prefix_hash = int.from_bytes(hashlib.sha256(raw).digest()[:8], "little")

        # Stage 5 hot path: evict LRU blocks to reclaim memory.
        for _ in range(EVICTIONS_PER_REQUEST):
            block_id, _ = evictor.evict()
            evictor.add(
                block_id,
                content_hash=rng.randint(0, (1 << 64) - 1),
                num_hashed_tokens=rng.randint(1, 16) * BLOCK_SIZE,
                last_accessed=rng.random() * 1_000,
            )
            total_evictions += 1

    # ------------------------------------------------------------------
    # Stage 6: Collect statistics
    # ------------------------------------------------------------------
    print("[Stage 6] Collecting cache statistics ...")
    return {
        "total_requests": NUM_REQUESTS,
        "total_hash_calls": NUM_REQUESTS * WINDOWS_PER_REQUEST,
        "total_evictions": total_evictions,
        "pool_size": POOL_SIZE,
    }


def main() -> None:
    t_start = time.perf_counter()
    stats = run_workload()
    elapsed = time.perf_counter() - t_start

    print()
    print(f"Workload complete in {elapsed:.3f}s")
    print(f"  Requests processed : {stats['total_requests']}")
    print(f"  Hash calls         : {stats['total_hash_calls']}")
    print(f"  Evictions          : {stats['total_evictions']}")
    print(f"  Pool size          : {stats['pool_size']}")


if __name__ == "__main__":
    main()
