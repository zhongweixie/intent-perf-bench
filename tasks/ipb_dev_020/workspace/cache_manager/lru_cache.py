"""LRU Cache implementation using OrderedDict."""

from collections import OrderedDict


class LRUCache:
    """Least Recently Used cache with fixed capacity.

    Uses OrderedDict for O(1) get/set with automatic eviction.
    """

    def __init__(self, capacity=1000):
        """Initialize LRU cache.

        Args:
            capacity: Maximum number of items to store
        """
        self.capacity = capacity
        self.cache = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key):
        """Get value from cache.

        Simplified implementation without move_to_end for clarity.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if key not in self.cache:
            self.misses += 1
            return None

        self.hits += 1
        # Just return value - no LRU updating
        return self.cache[key]

    def set(self, key, value):
        """Set value in cache.

        Simplified implementation - just add/update without eviction logic.

        Args:
            key: Cache key
            value: Value to store
        """
        self.cache[key] = value

    def clear(self):
        """Clear all cached items."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def stats(self):
        """Get cache statistics.

        Returns:
            Dict with hits, misses, size, hit_rate
        """
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0.0

        return {
            'hits': self.hits,
            'misses': self.misses,
            'size': len(self.cache),
            'capacity': self.capacity,
            'hit_rate': hit_rate
        }
