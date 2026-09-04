"""
Expiration helper shared by working memory and retention (spec 8.5, 8.19).
"""

from datetime import datetime, timedelta, timezone


def _parse(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def is_expired(expires_at, now=None):
    """True if ``expires_at`` (ISO-8601 string) is in the past.

    A falsy ``expires_at`` (None/"") never expires - that's how
    USER_CONTROLLED memories with no TTL are represented.
    """
    if not expires_at:
        return False
    return _parse(expires_at) <= (now or datetime.now(timezone.utc))


def expires_in(minutes, now=None):
    """Return an ISO-8601 timestamp ``minutes`` from now."""
    base = now or datetime.now(timezone.utc)
    return (base + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")
