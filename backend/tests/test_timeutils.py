from datetime import datetime, timezone

from backend.timeutils import utc_iso, utcnow, utcnow_naive


def test_utc_iso_ends_with_z_and_parses():
    s = utc_iso()
    assert s.endswith("Z")
    # Parses as a valid UTC timestamp.
    parsed = datetime.fromisoformat(s.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None


def test_utcnow_naive_is_naive():
    assert utcnow_naive().tzinfo is None


def test_utcnow_is_aware_utc():
    assert utcnow().tzinfo == timezone.utc
