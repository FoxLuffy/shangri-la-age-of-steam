"""UTC time helpers.

Replacements for the deprecated `datetime.utcnow()` (Python 3.12+) that preserve the
project's existing timestamp formats exactly.
"""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Timezone-aware current UTC time."""
    return datetime.now(timezone.utc)


def utcnow_naive() -> datetime:
    """Naive UTC datetime — a drop-in for the deprecated `datetime.utcnow()`."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def utc_iso() -> str:
    """ISO-8601 UTC timestamp ending in 'Z' (matches the previously stored format)."""
    return utcnow_naive().isoformat() + "Z"
