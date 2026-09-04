class Revocation:
    def __init__(self,grants):self.grants=grants
    def revoke(self,worker,capability):self.grants.revoke(worker,capability)
