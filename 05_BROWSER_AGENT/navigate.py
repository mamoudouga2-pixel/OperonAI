from urllib.parse import urlparse
class Navigator:
    def __init__(self,adapter): self.adapter=adapter
    def validate(self,url,policy):
        p=urlparse(url)
        if p.scheme not in {"http","https"}: raise RuntimeError("NAVIGATION_BLOCKED")
        host=(p.hostname or "").lower(); allowed=[x.lower() for x in policy.get("allowed_domains",[])]
        if not any(host==d or (policy.get("allow_subdomains") and host.endswith("."+d)) for d in allowed):
            raise RuntimeError("NAVIGATION_BLOCKED")
        return True
    def navigate(self,sid,request,policy):
        self.validate(request["url"],policy)
        return self.adapter.navigate(sid,request["url"],request.get("timeout_ms",30000))
