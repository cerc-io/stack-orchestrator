"""Sortable timestamp-based ID generation for cluster naming.

Uses base36 encoding with 100ms resolution and a 2024-01-01 epoch
to produce compact, sortable IDs like 'laconic-3k7m2ab'.

Format: {prefix}-{timestamp}{random}
- timestamp: 7 chars base36 (100ms resolution, ~2500 years from 2024)
- random: 2 chars (1,296 unique per 100ms slot)
"""
# Adapted from exophial/src/exophial/ids.py

import random
import time

# 2024-01-01 00:00:00 UTC in milliseconds
EPOCH_2024 = 1704067200000

# Sortable base36 alphabet (0-9, a-z) — lowercase only to satisfy
# kind cluster name validation (^[a-z0-9.-]+$)
ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"


def _base36(n: int) -> str:
    """Encode integer as base36 string."""
    if n == 0:
        return ALPHABET[0]
    s = ""
    while n:
        n, r = divmod(n, len(ALPHABET))
        s = ALPHABET[r] + s
    return s


def _random_suffix(length: int = 2) -> str:
    """Generate random base36 suffix."""
    return "".join(random.choice(ALPHABET) for _ in range(length))


def _timestamp_id() -> str:
    """Generate a sortable timestamp ID (100ms resolution, 2024 epoch) with random suffix."""
    now_ms = int(time.time() * 1000)
    offset = (now_ms - EPOCH_2024) // 100  # 100ms resolution
    return f"{_base36(offset)}{_random_suffix()}"


def generate_id(prefix: str) -> str:
    """Generate a sortable ID with an arbitrary prefix like 'laconic-3k7m2ab'."""
    return f"{prefix}-{_timestamp_id()}"
