"""Cache operations using global LRUCache instance."""

from .lru_cache import LRUCache

# Global cache instance
_cache = LRUCache(capacity=1000)


def get_cached(key):
    """Retrieve value from global cache.

    Args:
        key: Cache key

    Returns:
        Cached value or None if not found
    """
    return _cache.get(key)


def set_cached(key, value):
    """Store value in global cache.

    Args:
        key: Cache key
        value: Value to cache
    """
    _cache.set(key, value)


def clear_cache():
    """Clear all cached items and reset stats."""
    _cache.clear()


def cache_stats():
    """Get cache statistics.

    Returns:
        Dict with hits, misses, size, hit_rate
    """
    return _cache.stats()
