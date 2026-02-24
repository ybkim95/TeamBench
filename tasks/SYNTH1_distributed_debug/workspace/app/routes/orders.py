"""Order processing endpoints."""
from app.utils.cache import cache


class Order:
    def __init__(self, items):
        self.items = items  # list of (name, price, quantity)
        self._discount_pct = 0

    @property
    def item_total(self):
        return sum(price * qty for _, price, qty in self.items)

    def apply_discount(self, percent):
        self._discount_pct = percent

    @property
    def total(self):
        """Get order total (uses cache for performance)."""
        cache_key = f"order_{id(self)}_total"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        subtotal = self.item_total
        # Cache the subtotal for future calls
        cache.set(cache_key, subtotal)

        # Apply discount
        if self._discount_pct > 0:
            return round(subtotal * (1 - self._discount_pct / 100), 2)
        return subtotal
