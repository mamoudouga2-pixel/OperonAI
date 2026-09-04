class NetworkPolicy:
    def __init__(self,allowlist,protocols=("https",),max_size=10_000_000,max_redirects=3,max_duration=300):
        self.allowlist=allowlist;self.protocols=set(protocols);self.max_size=max_size
        self.max_redirects=max_redirects;self.max_duration=max_duration
    def check(self,domain,protocol,private=False):
        return domain in self.allowlist.domains and protocol in self.protocols and not private
