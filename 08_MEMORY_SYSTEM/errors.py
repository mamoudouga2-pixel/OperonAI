"""
Error codes for the memory subsystem (spec section 8.29).

Each error is a distinct exception class so callers (Boss Agent, Core,
Interface layer) can branch on error type instead of parsing strings.
Every exception also exposes a ``.code`` attribute equal to the class
name, which keeps the previous string-based ``RuntimeError("CODE")``
behaviour working for any older caller that still does
``assertRaisesRegex(RuntimeError, "CODE")``-style matching, because all
of these classes subclass ``RuntimeError``.
"""


class MemoryError(RuntimeError):
    """Base class for all memory-subsystem errors."""

    code = "MEMORY_ERROR"

    def __init__(self, message=None, **context):
        self.context = context
        text = f"{self.code}: {message}" if message else self.code
        super().__init__(text)


class MemoryNotFound(MemoryError):
    code = "MEMORY_NOT_FOUND"


class MemoryScopeDenied(MemoryError):
    code = "MEMORY_SCOPE_DENIED"


class MemoryExpired(MemoryError):
    code = "MEMORY_EXPIRED"


class MemoryWriteBlocked(MemoryError):
    code = "MEMORY_WRITE_BLOCKED"


class MemoryProvenanceInvalid(MemoryError):
    code = "MEMORY_PROVENANCE_INVALID"


class MemorySensitivityBlocked(MemoryError):
    code = "MEMORY_SENSITIVITY_BLOCKED"


class VectorStoreUnavailable(MemoryError):
    code = "VECTOR_STORE_UNAVAILABLE"


class StructuredStoreUnavailable(MemoryError):
    code = "STRUCTURED_STORE_UNAVAILABLE"


class EmbeddingFailed(MemoryError):
    code = "EMBEDDING_FAILED"


class DeletePartial(MemoryError):
    code = "DELETE_PARTIAL"


class DeleteVerificationFailed(MemoryError):
    code = "DELETE_VERIFICATION_FAILED"


class BackupRestoreFailed(MemoryError):
    code = "BACKUP_RESTORE_FAILED"


CODE_TO_EXCEPTION = {
    cls.code: cls
    for cls in (
        MemoryNotFound,
        MemoryScopeDenied,
        MemoryExpired,
        MemoryWriteBlocked,
        MemoryProvenanceInvalid,
        MemorySensitivityBlocked,
        VectorStoreUnavailable,
        StructuredStoreUnavailable,
        EmbeddingFailed,
        DeletePartial,
        DeleteVerificationFailed,
        BackupRestoreFailed,
    )
}


def raise_for_code(code, message=None, **context):
    """Raise the exception class registered for ``code`` (or a generic
    MemoryError if the code is unknown)."""
    exc_cls = CODE_TO_EXCEPTION.get(code, MemoryError)
    raise exc_cls(message or code, **context)
