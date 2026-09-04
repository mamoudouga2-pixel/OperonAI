class NetworkRequestGuard:
    def __init__(self,policy):self.policy=policy
    def validate(self,a):
        t=a["target"]
        if not self.policy.check(t.get("domain",""),t.get("protocol","https"),t.get("private",False)):return False
        if t.get("redirects",0)>self.policy.max_redirects:return False
        if t.get("size",0)>self.policy.max_size:return False
        if t.get("duration",0)>self.policy.max_duration:return False
        return True
