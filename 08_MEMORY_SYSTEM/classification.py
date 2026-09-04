"""
Sensitivity classification (spec 8.15 SECRET AND CREDENTIAL POLICY).

Anything matching a secret pattern is classified "SECRET" and must
never be written as plaintext long-term semantic memory (Part 09
Security owns real credential storage).
"""

import re

SECRET_PATTERNS = [
    re.compile(r"(?i)\bpassword\b\s*[:=]"),
    re.compile(r"(?i)\bpasswd\b\s*[:=]"),
    re.compile(r"(?i)\bapi[_ -]?key\b\s*[:=]"),
    re.compile(r"(?i)\bsecret[_ -]?key\b\s*[:=]"),
    re.compile(r"(?i)\bauth[_ -]?token\b\s*[:=]"),
    re.compile(r"(?i)\baccess[_ -]?token\b\s*[:=]"),
    re.compile(r"(?i)\bprivate[_ -]?key\b\s*[:=]"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\bbearer\s+[a-z0-9._-]{10,}"),
]


class Classifier:
    """Classifies free text as ``SECRET`` or ``NORMAL``.

    This is a conservative, regex-based first line of defense, not a
    substitute for the dedicated Part 09 Security credential vault.
    """

    def __init__(self, patterns=None):
        self.patterns = patterns or SECRET_PATTERNS

    def classify(self, text):
        text = str(text or "")
        return "SECRET" if any(p.search(text) for p in self.patterns) else "NORMAL"

    def contains_secret(self, text):
        return self.classify(text) == "SECRET"
