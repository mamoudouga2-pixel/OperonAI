class Supervisor:
    def __init__(self,max_retries=2):
        self.max_retries=max_retries; self.retries=0; self.patterns=set()
    def verify(self,result):
        if not isinstance(result,dict): return False,{"reason":"missing evidence object"}
        evidence=result.get("evidence")
        verified=(evidence is not None and evidence != "" and result.get("success") is True)
        return verified,{"evidence":evidence,"worker_claim":result.get("success",False)}
    def recoverable(self,failure_pattern):
        if failure_pattern in self.patterns: return False
        self.patterns.add(failure_pattern)
        if self.retries>=self.max_retries:return False
        self.retries+=1; return True
