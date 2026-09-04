"""
Redaction (spec 8.15). Masks secret-shaped substrings so they can be
logged/audited without leaking the credential itself.
"""

import re

_REDACT_PATTERN = re.compile(
    r"(?i)(password|passwd|api[_ -]?key|secret[_ -]?key|auth[_ -]?token|"
    r"access[_ -]?token|private[_ -]?key)\s*[:=]\s*[^\s,;]+"
)
_BEARER_PATTERN = re.compile(r"(?i)(bearer)\s+[a-z0-9._-]{10,}")


class Redactor:
    """Replaces secret values with ``field=[REDACTED]`` in free text."""

    def redact(self, text):
        s = str(text or "")
        s = _REDACT_PATTERN.sub(lambda m: f"{m.group(1)}=[REDACTED]", s)
        s = _BEARER_PATTERN.sub(lambda m: f"{m.group(1)} [REDACTED]", s)
        return s

    def redact_dict(self, data, fields=("summary", "content", "text")):
        """Return a shallow copy of ``data`` with string values in
        ``fields`` redacted."""
        out = dict(data)
        for field in fields:
            if isinstance(out.get(field), str):
                out[field] = self.redact(out[field])
        return out
