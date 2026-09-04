import time,json,hashlib
class AuditLogger:
    """Append-only audit logger. Every record is chained to the previous one
    (prev_hash -> hash) so AuditIntegrity can later detect tampering."""
    def __init__(self,redactor=None):
        self.records=[];self.redactor=redactor;self._prev=""
    def log(self,event,action,extra=None):
        x={"timestamp":time.time(),"event":event,"task_id":action.get("task_id"),
           "action_id":action.get("action_id"),"actor":action.get("worker"),
           "target_reference":action.get("target"),"data":extra or {}}
        if self.redactor:x=self.redactor(x)
        h=hashlib.sha256((self._prev+json.dumps(x,sort_keys=True,default=str)).encode()).hexdigest()
        x["prev_hash"]=self._prev;x["hash"]=h;self._prev=h
        self.records.append(x);return x
