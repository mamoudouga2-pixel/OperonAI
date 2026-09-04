class RecoveryManager:
    RETRYABLE={"TARGET_NOT_FOUND","TARGET_NOT_READY","PAGE_LOAD_TIMEOUT","BROWSER_CRASHED","UNEXPECTED_PAGE_STATE"}
    def __init__(self,max_retries=3): self.max_retries=max_retries
    def retryable(self,error): return str(error).split(":")[0] in self.RETRYABLE
    def attempts(self,error): return min(self.max_retries,3)
class LoopDetector:
    def __init__(self,limit=3): self.limit=limit; self.counts={}
    def observe(self,action_sig,state_sig):
        key=(action_sig,state_sig); self.counts[key]=self.counts.get(key,0)+1
        if self.counts[key]>self.limit: raise RuntimeError("LOOP_DETECTED")
        return self.counts[key]
