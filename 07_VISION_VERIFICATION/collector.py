import re

from evidence.metadata import Evidence, now
from evidence.hashing import sha256_bytes
from events import default_bus, EVIDENCE_CREATED, EVIDENCE_REDACTED

# Keyword hits (previous behavior, kept) plus shape-based patterns so we
# also catch secrets that don't happen to contain the word "token"/"secret"
# -- e.g. a bare JWT or a long high-entropy hex/base64 string typed into a
# description by mistake (spec 7.11: no plaintext password/token/secret in
# evidence description).
SENSITIVE_KEYWORDS = ("password", "token", "secret", "api_key", "apikey", "credential")
SENSITIVE_PATTERNS = (
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),  # JWT-shaped
    re.compile(r"\b[A-Za-z0-9_-]{32,}\b"),  # long opaque token-shaped string
)


def _needs_redaction(description: str) -> bool:
    lowered = description.lower()
    if any(k in lowered for k in SENSITIVE_KEYWORDS):
        return True
    return any(p.search(description) for p in SENSITIVE_PATTERNS)


class EvidenceCollector:
    VALID_TYPES = ("SCREENSHOT", "DOM_SNAPSHOT", "FILE_STATE", "LOG", "OCR_TEXT")

    def __init__(self, store, event_bus=None):
        self.store = store
        self.event_bus = event_bus or default_bus
        self.n = 0

    def collect(self, task_id, action_id, source, data, description, evidence_type="SCREENSHOT"):
        if evidence_type not in self.VALID_TYPES:
            raise ValueError(f"unknown evidence type: {evidence_type!r}")
        self.n += 1
        evidence_id = f"EVID-{self.n:03d}"

        redacted = _needs_redaction(description)
        final_description = "<REDACTED>" if redacted else description
        redaction_status = "APPLIED" if redacted else "NOT_NEEDED"

        path = self.store.save(f"{evidence_id}.bin", data)
        evidence = Evidence(
            evidence_id, task_id, action_id, evidence_type, source,
            now().isoformat(), path, sha256_bytes(data), final_description, redaction_status,
        )

        self.event_bus.emit(EVIDENCE_CREATED, evidence_id=evidence_id, task_id=task_id, source=source)
        if redacted:
            self.event_bus.emit(EVIDENCE_REDACTED, evidence_id=evidence_id, task_id=task_id)
        return evidence
