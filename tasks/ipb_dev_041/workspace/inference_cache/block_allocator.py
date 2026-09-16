"""Physical block allocator for the KV-cache prefix manager.

Manages a fixed pool of physical cache blocks.  Freed blocks are handed to
the evictor so they can be reclaimed later under memory pressure.
"""

import time
from typing import Dict, Optional, Tuple

from .evictor import LRUEvictor, EvictionPolicy, make_evictor
from .hasher import hash_block_tokens


class PhysicalBlock:
    """Represents one physical slot in the KV-cache."""

    def __init__(self, block_id: int) -> None:
        self.block_id = block_id
        self.content_hash: Optional[int] = None
        self.num_hashed_tokens: int = 0
        self.ref_count: int = 0
        self.last_accessed: float = 0.0


class BlockAllocator:
    """Allocates and reclaims physical KV-cache blocks.

    Blocks that are freed go into the evictor's pool.  When the allocator
    runs out of free blocks it calls evict() to reclaim the least-recently-
    used cached block.
    """

    def __init__(self, num_blocks: int, eviction_policy: EvictionPolicy = EvictionPolicy.LRU) -> None:
        self._num_blocks = num_blocks
        self._blocks: Dict[int, PhysicalBlock] = {
            i: PhysicalBlock(i) for i in range(num_blocks)
        }
        self._free_block_ids = list(range(num_blocks))
        self._evictor = make_evictor(eviction_policy)

        # Allocate statistics
        self.num_allocations: int = 0
        self.num_evictions: int = 0
        self.num_cache_hits: int = 0

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def allocate(
        self,
        token_ids: Tuple[int, ...],
        prefix_hash: int = 0,
        num_hashed_tokens: int = 0,
    ) -> PhysicalBlock:
        """Return a block for the given token window.

        If no free blocks remain, the LRU cached block is evicted first.
        """
        content_hash = hash_block_tokens(token_ids, prefix_hash)

        block_id = self._get_free_block_id()
        block = self._blocks[block_id]
        block.content_hash = content_hash
        block.num_hashed_tokens = num_hashed_tokens
        block.ref_count = 1
        block.last_accessed = time.monotonic()
        self.num_allocations += 1
        return block

    def free(self, block: PhysicalBlock) -> None:
        """Release a block back to the free pool / evictor."""
        block.ref_count -= 1
        if block.ref_count == 0:
            self._evictor.add(
                block.block_id,
                block.content_hash or 0,
                block.num_hashed_tokens,
                block.last_accessed,
            )
            self._free_block_ids  # keep the list consistent via evictor

    def touch(self, block: PhysicalBlock) -> None:
        """Record a cache hit — update the block's access timestamp."""
        block.last_accessed = time.monotonic()
        if block.block_id in self._evictor:
            self._evictor.update(block.block_id, block.last_accessed)
        self.num_cache_hits += 1

    @property
    def num_free_blocks(self) -> int:
        return len(self._free_block_ids) + self._evictor.num_blocks

    @property
    def evictor(self) -> LRUEvictor:
        return self._evictor  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_free_block_id(self) -> int:
        if self._free_block_ids:
            return self._free_block_ids.pop()
        # Evict the LRU cached block to make room.
        block_id, _ = self._evictor.evict()
        self.num_evictions += 1
        return block_id
