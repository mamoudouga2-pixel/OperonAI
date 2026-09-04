"""
Memory write policy (spec 8.13 MEMORY WRITE POLICY).

    Candidate Memory
      -> classify sensitivity
      -> validate provenance
      -> check retention policy
      -> determine whether consent/approval is required
      -> redact if necessary
      -> persist
      -> emit MEMORY_STORED
"""

from errors import (
    MemoryProvenanceInvalid,
    MemorySensitivityBlocked,
    MemoryWriteBlocked,
)
from privacy.classification import Classifier
from privacy.redaction import Redactor

VALID_PROVENANCE_SOURCES = {
    "USER_EXPLICIT",
    "TASK_RESULT",
    "USER_APPROVED_INFERENCE",
    "SYSTEM_CONFIGURATION",
}

# Provenance sources that are not, by themselves, sufficient grounds to
# write a permanent memory. Spec 8.12: unverified model hallucination
# must not become permanent memory.
REQUIRES_APPROVAL = {"USER_APPROVED_INFERENCE"}


class MemoryPolicy:
    """Validates a candidate memory object before it is persisted."""

    ALLOWED_RETENTION = {
        "EPHEMERAL",
        "TASK_RETENTION",
        "USER_CONTROLLED",
        "EXPIRING",
        "SECURITY/AUDIT",
    }
    # Backwards-compatible alias used by older callers/tests.
    ALLOWED = ALLOWED_RETENTION

    def __init__(
        self,
        require_provenance=True,
        default_local_only=True,
        max_retrieval_items=10,
        classifier=None,
        redactor=None,
    ):
        self.require_provenance = require_provenance
        self.default_local_only = default_local_only
        self.max_retrieval_items = max_retrieval_items
        self.classifier = classifier or Classifier()
        self.redactor = redactor or Redactor()

    def validate(self, memory):
        """Raise on policy violation, otherwise return True."""
        if self.require_provenance:
            provenance = memory.get("provenance")
            if not isinstance(provenance, dict) or not provenance.get("source"):
                raise MemoryProvenanceInvalid(memory_id=memory.get("memory_id"))
            if provenance["source"] not in VALID_PROVENANCE_SOURCES:
                raise MemoryProvenanceInvalid(memory_id=memory.get("memory_id"))
            if provenance["source"] in REQUIRES_APPROVAL and not provenance.get("approved"):
                raise MemoryProvenanceInvalid(
                    "USER_APPROVED_INFERENCE requires explicit approval",
                    memory_id=memory.get("memory_id"),
                )

        if memory.get("retention_policy") not in self.ALLOWED_RETENTION:
            raise MemoryWriteBlocked(memory_id=memory.get("memory_id"))

        sensitivity = memory.get("sensitivity", "NORMAL")
        text = memory.get("summary") or memory.get("content") or ""
        if sensitivity != "SECRET" and self.classifier.classify(text) == "SECRET":
            sensitivity = "SECRET"

        if sensitivity == "SECRET":
            raise MemorySensitivityBlocked(memory_id=memory.get("memory_id"))

        return True

    def redact(self, memory):
        """Return a copy of ``memory`` with any embedded secrets masked."""
        redacted = dict(memory)
        for field in ("summary", "content"):
            if isinstance(redacted.get(field), str):
                redacted[field] = self.redactor.redact(redacted[field])
        return redacted
