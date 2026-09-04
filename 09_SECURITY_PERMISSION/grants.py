class GrantStore:
    def __init__(self):self.grants={}
    def grant(self,worker,capability,scope=None):self.grants[(worker,capability)]=scope
    def revoke(self,worker,capability):self.grants.pop((worker,capability),None)
    def get(self,worker,capability):return self.grants.get((worker,capability),None)
