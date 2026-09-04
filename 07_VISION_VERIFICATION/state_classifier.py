class StateClassifier:
 def classify(self,analysis):
  if analysis.get("loading"): return "LOADING"
  if analysis.get("errors"): return "ERROR"
  if analysis.get("uncertainty_reason"): return "UNCERTAIN"
  return "READY"
