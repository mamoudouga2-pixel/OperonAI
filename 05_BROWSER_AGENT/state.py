import json,hashlib
class PageState:
    @staticmethod
    def signature(state):
        raw=json.dumps(state,sort_keys=True,default=str,separators=(",",":")).encode()
        return hashlib.sha256(raw).hexdigest()
