class LocatorFallback:
    def __init__(self,semantic,confidence): self.semantic=semantic; self.confidence=confidence
    def resolve(self,target,find):
        attempts=[]
        for method,value in self.semantic.candidates(target):
            spec={}
            if method=="role_name": spec={"role":target.get("role"),"name":target.get("name")}
            elif method=="text": spec={"text":value}
            elif method=="label": spec={"label":value}
            elif method=="placeholder": spec={"placeholder":value}
            elif method=="test_id": spec={"test_id":value}
            else: spec={method:value}
            found=find(spec); attempts.append(method)
            if found is not None:
                conf=(1.0 if method in {"role_name","label","test_id"}
                      else .85 if method in {"text","placeholder"}
                      else .78 if method=="structural"
                      else .75)  # vision: lowest-confidence fallback, still must clear the default gate
                if self.confidence.allow(conf): return {"found":found,"method":method,"confidence":conf,"attempts":attempts}
        raise RuntimeError("TARGET_NOT_FOUND")
