from .request import ApprovalRequest
from .expiry import expired
class ApprovalManager:
    def __init__(self,audit=None):self.items={};self.audit=audit
    def create(self,approval_id,task_id,action,summary,risk,created,expires):
        self.items[approval_id]=ApprovalRequest(approval_id,task_id,ApprovalRequest.fingerprint(action),summary,risk,created,expires).data
        if self.audit:self.audit.log("APPROVAL_REQUESTED",action,{"approval_id":approval_id})
        return self.items[approval_id]
    def grant(self,approval_id,action=None):
        self.items[approval_id]["status"]="APPROVED"
        if self.audit and action:self.audit.log("APPROVAL_GRANTED",action,{"approval_id":approval_id})
    def reject(self,approval_id,action=None):
        self.items[approval_id]["status"]="REJECTED"
        if self.audit and action:self.audit.log("APPROVAL_REJECTED",action,{"approval_id":approval_id})
    def matches(self,action):
        fp=ApprovalRequest.fingerprint(action)
        for x in self.items.values():
            if x["task_id"]!=action["task_id"] or x["action_fingerprint"]!=fp or x["status"]!="APPROVED":continue
            if expired(x["expires_at"]):
                x["status"]="EXPIRED"
                if self.audit:self.audit.log("APPROVAL_EXPIRED",action,{"approval_id":x["approval_id"]})
                continue
            return True
        return False
