class Allowlist:
    def __init__(self,domains=None):self.domains=set(domains or [])
    def allowed(self,domain):return domain in self.domains
