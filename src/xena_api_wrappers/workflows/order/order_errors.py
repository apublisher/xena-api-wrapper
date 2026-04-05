from __future__ import annotations


class OrderWriteError(ValueError):
    """Base error for order write workflow operations."""


class OrderWriteHydrationError(OrderWriteError):
    """Raised when order DTO hydration input is invalid."""


class OrderDistributionError(OrderWriteError):
    """Raised when order distribution input or prerequisites are invalid."""
