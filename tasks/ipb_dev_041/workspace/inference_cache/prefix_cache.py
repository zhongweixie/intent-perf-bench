"""Prefix-aware KV-cache manager.

Maintains a mapping from (prefix_hash, token_ids_tuple) to physical blocks
so that common prompt prefixes are shared across concurrent requests.
"""

import time
from typing import Dict, List, Optional, Tuple

from .block_allocator import BlockAllocator, PhysicalBlock
from .hasher import hash_block_tokens, BLOCK_SIZE


class PrefixCacheManager:
    """Manages prefix sharing across requests.

    For each incoming request the manager walks the token sequence in
    BLOCK_SIZE windows.  For each window it computes the content hash and
    checks whether a cached block already exists (cache hit) or whether a
    new block must be allocated (cache miss).
    """

    def __init__(self, allocator: BlockAllocator) -> None:
        self._allocator = allocator
        # content_hash -> PhysicalBlock
        self._cache: Dict[int, PhysicalBlock] = {}
        self.total_requests: int = 0

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def process_request(self, token_ids: List[int]) -> List[PhysicalBlock]:
        """Allocate (or reuse) blocks for *token_ids*.

        Returns the list of physical blocks covering the full token sequence.
        Partial trailing tokens that don't fill a complete block are ignored.
        """
        self.total_requests += 1
        blocks: List[PhysicalBlock] = []
        prefix_hash = 0
        num_hashed = 0

        for start in range(0, len(token_ids) - BLOCK_SIZE + 1, BLOCK_SIZE):
            window = tuple(token_ids[start : start + BLOCK_SIZE])
            content_hash = hash_block_tokens(window, prefix_hash)

            if content_hash in self._cache:
                block = self._cache[content_hash]
                self._allocator.touch(block)
            else:
                block = self._allocator.allocate(window, prefix_hash, num_hashed)
                self._cache[content_hash] = block

            blocks.append(block)
            prefix_hash = content_hash
            num_hashed += BLOCK_SIZE

        return blocks

    def evict_blocks(self, n: int) -> int:
        """Proactively evict *n* cached blocks to reclaim memory.

        Returns the number of blocks actually evicted.
        """
        evicted = 0
        for _ in range(n):
            if self._allocator.evictor.num_blocks == 0:
                break
            block_id, content_hash = self._allocator.evictor.evict()
            # Remove from the lookup cache as well.
            stale = [h for h, b in self._cache.items() if b.block_id == block_id]
            for h in stale:
                del self._cache[h]
            evicted += 1
        return evicted

    @property
    def cache_size(self) -> int:
        return len(self._cache)

    @property
    def stats(self) -> Dict[str, int]:
        a = self._allocator
        return {
            "total_requests": self.total_requests,
            "num_allocations": a.num_allocations,
            "num_evictions": a.num_evictions,
            "num_cache_hits": a.num_cache_hits,
            "cache_size": self.cache_size,
        }
