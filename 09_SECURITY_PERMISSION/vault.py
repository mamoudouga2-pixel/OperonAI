from .provider import CredentialProvider
class Vault(CredentialProvider):
    def __init__(self,audit=None):self._data={};self.audit=audit
    def store(self,key,value):self._data[key]=value
    def retrieve_for_authorized_use(self,key,authorized=False,action=None):
        if not authorized:
            if self.audit and action:self.audit.log("CREDENTIAL_ACCESS_BLOCKED",action,{"key":key})
            raise RuntimeError("CREDENTIAL_ACCESS_DENIED")
        return self._data[key]
    def rotate(self,key,value):self._data[key]=value
    def delete(self,key):self._data.pop(key,None)
    def redact(self,text):
        return str(text).replace("password=","password=[REDACTED]").replace("api_key=","api_key=[REDACTED]").replace("token=","token=[REDACTED]")
