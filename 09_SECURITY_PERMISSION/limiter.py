class RateLimiter:
    def __init__(self,max_actions=100,max_retries=3,max_network=100,max_approvals=20,audit=None):
        self.max_actions=max_actions;self.max_retries=max_retries;self.max_network=max_network;self.max_approvals=max_approvals
        self.counts={};self.audit=audit
    def consume(self,task,kind="actions",context=None):
        key=(task,kind);self.counts[key]=self.counts.get(key,0)+1
        limit={"actions":self.max_actions,"retries":self.max_retries,"network":self.max_network,"approvals":self.max_approvals}[kind]
        if self.counts[key]>limit:
            if self.audit and context:self.audit.log("RATE_LIMIT_EXCEEDED",context,{"kind":kind,"count":self.counts[key],"limit":limit})
            raise RuntimeError("RATE_LIMIT_EXCEEDED")
