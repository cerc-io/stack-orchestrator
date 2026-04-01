"""Sortable timestamp-based ID generation for cluster naming.

Uses base62 encoding with 100ms resolution and a 2024-01-01 epoch
to produce compact, sortable IDs like 'laconic-iqE6Za'.

Format: {prefix}-{timestamp}{random}
- timestamp: 5 chars (100ms resolution, ~180 years from 2024)
- random: 2 chars (3,844 unique per 100ms slot)
"""
# Adapted from exophial/src/exophial/ids.py

import random
import time

# 2024-01-01 00:00:00 UTC in milliseconds
EPOCH_2024 = 1704067200000

# Sortable base62 alphabet (0-9, A-Z, a-z)
ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def _base62(n: int) -> str:
    """Encode integer as base62 string."""
    if n == 0:
        return ALPHABET[0]
    s = ""
    while n:
        n, r = divmod(n, 62)
        s = ALPHABET[r] + s
    return s


def _random_suffix(length: int = 2) -> str:
    """Generate random base62 suffix."""
    return "".join(random.choice(ALPHABET) for _ in range(length))


def _timestamp_id() -> str:
    """Generate a sortable timestamp ID (100ms resolution, 2024 epoch) with random suffix."""
    now_ms = int(time.time() * 1000)
    offset = (now_ms - EPOCH_2024) // 100  # 100ms resolution
    return f"{_base62(offset)}{_random_suffix()}"


def generate_id(prefix: str) -> str:
    """Generate a sortable ID with an arbitrary prefix like 'laconic-iqE6Za'."""
    return f"{prefix}-{_timestamp_id()}"
