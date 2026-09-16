import enum
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Optional, Tuple


class EvictionPolicy(enum.Enum):
    """Eviction policy used by make_evictor."""
    LRU = enum.auto()


class BlockMetaData:
    """Metadata stored per cached block in the evictor."""

    def __init__(
        self,
        content_hash: int,
        num_hashed_tokens: int,
        last_accessed: float,
    ) -> None:
        self.content_hash = content_hash
        self.num_hashed_tokens = num_hashed_tokens
        self.last_accessed = last_accessed


class Evictor(ABC):
    """Abstract base for block evictors used by the BlockAllocator."""

    @abstractmethod
    def __init__(self) -> None: pass

    @abstractmethod
    def __contains__(self, block_id: int) -> bool: pass

    @abstractmethod
    def evict(self) -> Tuple[int, int]: pass

    @abstractmethod
    def add(self, block_id: int, content_hash: int, num_hashed_tokens: int,
            last_accessed: float) -> None: pass

    @abstractmethod
    def update(self, block_id: int, last_accessed: float) -> None: pass

    @abstractmethod
    def remove(self, block_id: int) -> None: pass

    @property
    @abstractmethod
    def num_blocks(self) -> int: pass


class LRUEvictor(Evictor):
    """Evicts blocks in least-recently-used order.

    Among all blocks with the same (oldest) last_accessed timestamp the one
    with the most hashed tokens is preferred.

    Implementation note
    -------------------
    The free_table is an OrderedDict keyed by block_id in insertion order.
    Blocks freed most recently appear near the end of the dict; older,
    eviction-eligible blocks cluster near the front due to temporal locality
    of the workload.  The eviction scan therefore exits early once it
    encounters a block whose last_accessed exceeds the current best candidate
    -- typically after inspecting only a small prefix of the table.
    """

    def __init__(self) -> None:
        self.free_table: OrderedDict[int, BlockMetaData] = OrderedDict()

    def __contains__(self, block_id: int) -> bool:
        return block_id in self.free_table

    def evict(self) -> Tuple[int, int]:
        if not self.free_table:
            raise ValueError("No usable cache memory left")

        evicted_block: Optional[BlockMetaData] = None
        evicted_block_id: Optional[int] = None

        for _id, block in self.free_table.items():
            if evicted_block is None:
                evicted_block, evicted_block_id = block, _id
                continue
            if evicted_block.last_accessed < block.last_accessed:
                # Remaining entries are newer -- no better candidate exists.
                break
            if evicted_block.num_hashed_tokens < block.num_hashed_tokens:
                evicted_block, evicted_block_id = block, _id

        assert evicted_block is not None
        assert evicted_block_id is not None
        self.free_table.pop(evicted_block_id)
        return evicted_block_id, evicted_block.content_hash

    def add(self, block_id: int, content_hash: int, num_hashed_tokens: int,
            last_accessed: float) -> None:
        self.free_table[block_id] = BlockMetaData(
            content_hash, num_hashed_tokens, last_accessed
        )

    def update(self, block_id: int, last_accessed: float) -> None:
        self.free_table[block_id].last_accessed = last_accessed

    def remove(self, block_id: int) -> None:
        if block_id not in self.free_table:
            raise ValueError(
                f"Attempting to remove block {block_id} that is not in evictor"
            )
        self.free_table.pop(block_id)

    @property
    def num_blocks(self) -> int:
        return len(self.free_table)


def make_evictor(eviction_policy: EvictionPolicy) -> Evictor:
    if eviction_policy == EvictionPolicy.LRU:
        return LRUEvictor()
    raise ValueError(f"Unknown eviction policy: {eviction_policy}")
