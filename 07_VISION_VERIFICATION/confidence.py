class ConfidencePolicy:
    """Confidence/uncertainty gate (spec 7.8).

    - UNCERTAIN is never SUCCESS.
    - Low confidence blocks destructive/irreversible action.
    - Threshold rises with task risk; HIGH risk additionally requires
      corroboration and explicit approval, never assumed.

    Risk is validated against a known set instead of silently falling
    through to the LOW-risk threshold for typos/unknown values, which was
    a silent-failure gap in the previous version -- an unrecognized risk
    level is treated as HIGH (fail closed), not LOW (fail open).
    """

    KNOWN_RISK_LEVELS = ("LOW", "MEDIUM", "HIGH")

    def __init__(self, low=0.75, high=0.9, medium=None):
        # Positional order kept as (low, high) for backward compatibility
        # with existing call sites; `medium` is keyword-only-by-convention
        # and defaults to the midpoint between low and high.
        self.low = low
        self.high = high
        self.medium = medium if medium is not None else (low + high) / 2

    def threshold_for(self, risk):
        if risk == "LOW":
            return self.low
        if risk == "MEDIUM":
            return self.medium
        # HIGH, or anything unrecognized: fail closed with the strictest bar.
        return self.high

    def allow(self, confidence, risk="LOW", corroborated=False, approved=False):
        risk = risk if risk in self.KNOWN_RISK_LEVELS else "HIGH"
        threshold = self.threshold_for(risk)
        if confidence < threshold:
            return False
        if risk == "HIGH":
            return bool(corroborated) and bool(approved)
        if risk == "MEDIUM":
            return bool(corroborated)
        return True
