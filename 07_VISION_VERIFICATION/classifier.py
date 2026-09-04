class FailureClassifier:
    """Maps a detected signal to one of the 10 failure classes in spec 7.17.

    Previously only 5 of the 10 classes were ever reachable (CONFLICT,
    TARGET_NOT_FOUND, MODEL_UNCERTAINTY, VERIFICATION_FAILURE,
    SECURITY_BLOCK could never be produced, always falling through to
    UNKNOWN). Extended to cover the new ErrorDetector signals, and made
    idempotent for classes that originate elsewhere in the system
    (grounding confidence -> MODEL_UNCERTAINTY, Verifier -> VERIFICATION_
    FAILURE, ConfidencePolicy -> SECURITY_BLOCK) so a caller can pass an
    already-normalized class straight through.
    """

    ALL_CLASSES = (
        "TRANSIENT", "CONFLICT", "PERMISSION", "TARGET_NOT_FOUND", "WRONG_STATE",
        "NETWORK", "MODEL_UNCERTAINTY", "VERIFICATION_FAILURE", "SECURITY_BLOCK", "UNKNOWN",
    )

    MAP = {
        # from ErrorDetector signals
        "VISIBLE_ERROR": "WRONG_STATE",
        "UNEXPECTED_DIALOG": "CONFLICT",
        "PERMISSION": "PERMISSION",
        "SESSION_EXPIRED": "WRONG_STATE",
        "LOADING_TIMEOUT": "TRANSIENT",
        "NETWORK": "NETWORK",
        "WRONG_WINDOW": "TARGET_NOT_FOUND",
        "FILE_CONFLICT": "CONFLICT",
        "TARGET_DISAPPEARED": "TARGET_NOT_FOUND",
        # identity pass-through for classes produced elsewhere in the system
        "TRANSIENT": "TRANSIENT",
        "CONFLICT": "CONFLICT",
        "TARGET_NOT_FOUND": "TARGET_NOT_FOUND",
        "WRONG_STATE": "WRONG_STATE",
        "MODEL_UNCERTAINTY": "MODEL_UNCERTAINTY",
        "VERIFICATION_FAILURE": "VERIFICATION_FAILURE",
        "SECURITY_BLOCK": "SECURITY_BLOCK",
    }

    def classify(self, error):
        return self.MAP.get(error, "UNKNOWN")
