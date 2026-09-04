class ApprovalManager:
    def __init__(self): self._pending=None
    def request(self,action):
        if str(action.get("risk","LOW")).upper()!="RED": return True
        self._pending={"action":dict(action),"status":"WAITING_APPROVAL"}
        return False
    def resolve(self,decision):
        d=str(decision).upper()
        if d not in {"APPROVED","REJECTED"}: raise ValueError("decision must be APPROVED or REJECTED")
        if self._pending is None: raise RuntimeError("no pending approval")
        self._pending["status"]=d
        return d=="APPROVED"
    @property
    def pending(self): return None if self._pending is None else dict(self._pending)
