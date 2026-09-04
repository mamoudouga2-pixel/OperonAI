import fnmatch
class PermissionEvaluator:
    def __init__(self,policy,grants):self.policy=policy;self.grants=grants
    def allowed(self,a):
        w,c=a["worker"],a["requested_capability"]
        if not self.policy.has_capability(w,c):return False
        scope=self.grants.get(w,c)
        if scope is None:return False
        target=str(a["target"].get("path",a["target"].get("value","")))
        if isinstance(scope,str):return fnmatch.fnmatch(target,scope)
        if isinstance(scope,(list,tuple)):return any(fnmatch.fnmatch(target,x) for x in scope)
        return False
