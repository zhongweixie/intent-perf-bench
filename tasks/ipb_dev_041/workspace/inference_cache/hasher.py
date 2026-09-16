"""Token-block content hasher for prefix cache address computation.

Each KV-cache block covers a fixed window of token IDs.  The content hash
provides a stable, content-addressable key so that identical token sequences
map to the same cache slot regardless of when or where they were generated.

The hash chain incorporates the parent block's hash so that the full prefix
up to any depth is captured in a single integer.
"""

import hashlib
import struct
from typing import Tuple

BLOCK_SIZE = 32


def hash_block_tokens(
    token_ids: Tuple[int, ...],
    prefix_hash: int = 0,
) -> int:
    """Return a 64-bit content hash for *token_ids* chained onto *prefix_hash*.

    Uses SHA-256 to guarantee collision resistance: two distinct token
    sequences will not share a cache slot.

    Args:
        token_ids:   Exactly BLOCK_SIZE token IDs covering this block.
        prefix_hash: Hash of the immediately preceding block (0 for the first
                     block in a sequence).

    Returns:
        A non-negative 64-bit integer suitable for use as a dict key.
    """
    raw = struct.pack(f"{len(token_ids)}I", *token_ids)
    raw += prefix_hash.to_bytes(8, byteorder="little")
    digest = hashlib.sha256(raw).digest()
    return int.from_bytes(digest[:8], byteorder="little")
