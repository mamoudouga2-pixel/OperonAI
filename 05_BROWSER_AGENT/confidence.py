class ConfidenceGate:
    def __init__(self,min_confidence=0.75): self.min_confidence=float(min_confidence)
    def allow(self,confidence): return float(confidence)>=self.min_confidence
