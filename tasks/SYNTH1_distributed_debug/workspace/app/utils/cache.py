"""Simple in-memory caching layer."""


class Cache:
    def __init__(self):
        self._store = {}

    def get(self, key):
        """Get value from cache. Returns None if not found."""
        return self._store.get(key)

    def set(self, key, value):
        """Set value in cache."""
        self._store[key] = value

    def delete(self, key):
        """Delete a key from cache."""
        self._store.pop(key, None)

    def clear(self):
        """Clear all cached values."""
        self._store.clear()


# Global cache instance
cache = Cache()
