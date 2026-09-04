from .normalizer import ActionNormalizer
from .decision import SecurityDecision
class SecurityGuard:
    def __init__(self,risk,permissions,approvals,audit,network=None,filesystem=None,plugins=None,rate_limiter=None,service_available=True):
        self.norm=ActionNormalizer();self.risk=risk;self.permissions=permissions;self.approvals=approvals;self.audit=audit
        self.network=network;self.filesystem=filesystem;self.plugins=plugins;self.rate_limiter=rate_limiter;self.service_available=service_available
    def check(self,action):
        if not self.service_available: raise RuntimeError("SECURITY_SERVICE_UNAVAILABLE")
        a=self.norm.normalize(action); self.audit.log("SECURITY_CHECK_STARTED",a)
        if self.rate_limiter: self.rate_limiter.consume(a["task_id"],"actions",a)
        r=self.risk.classify(a)
        if not self.permissions.allowed(a): return self._deny(a,r,"PERMISSION_DENIED")
        if self.filesystem and not self.filesystem.validate_action(a): return self._deny(a,r,"TARGET_VALIDATION_FAILED")
        if self.network and not self.network.validate(a): return self._deny(a,r,"NETWORK_POLICY_DENIED")
        if self.plugins and not self.plugins.allowed(a): return self._deny(a,r,"PLUGIN_CAPABILITY_DENIED")
        need=r=="RED"
        if need and not self.approvals.matches(a): return SecurityDecision(a["action_id"],"WAIT_FOR_APPROVAL",r,True,"POLICY-DEFAULT",["APPROVAL_REQUIRED"],{"max_attempts":1})
        d=SecurityDecision(a["action_id"],"ALLOW",r,need,"POLICY-DEFAULT",[],{"max_attempts":1})
        self.audit.log("SECURITY_DECISION_ALLOW",a,{"decision":d.to_dict()});return d
    def _deny(self,a,r,reason):
        d=SecurityDecision(a["action_id"],"DENY",r,r=="RED","POLICY-DEFAULT",[reason],{"max_attempts":0})
        self.audit.log("SECURITY_DECISION_DENY",a,{"decision":d.to_dict()});return d
