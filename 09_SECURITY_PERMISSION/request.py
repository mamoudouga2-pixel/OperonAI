import hashlib,json
class ApprovalRequest:
    def __init__(self,approval_id,task_id,action_fingerprint,summary,risk_level,created_at,expires_at,status="WAITING"):
        self.data=locals();self.data.pop("self")
    @staticmethod
    def fingerprint(action):
        payload={"action_type":action["action_type"],"target":action["target"],"requested_capability":action["requested_capability"],"worker":action["worker"]}
        return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
