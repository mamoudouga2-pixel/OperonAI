from .rules import RISK
class RiskClassifier:
    def classify(self,a):
        try:return RISK[a["action_type"]]
        except KeyError: raise RuntimeError("RISK_CLASSIFICATION_FAILED")
