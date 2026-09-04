"""User-controlled preferences, versioned and consent-gated."""

from .consent import Consent
from .preferences import Preferences

__all__ = ["Preferences", "Consent"]
