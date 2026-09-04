import json
class ActionNormalizer:
    REQUIRED={"action_id","task_id","worker","action_type","target","requested_capability"}
    def normalize(self,a):
        if not isinstance(a,dict) or not self.REQUIRED.issubset(a): raise RuntimeError("TARGET_VALIDATION_FAILED")
        x=dict(a); x["target"]=dict(x["target"]) if isinstance(x["target"],dict) else {"value":x["target"]}
        return x
