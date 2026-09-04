ORDER=("role_name","label","text","placeholder","test_id","structural","vision")
class SemanticLocator:
    ORDER=ORDER
    def candidates(self,target):
        if target.get("role") is not None and target.get("name") is not None:
            yield "role_name",(target.get("role"),target.get("name"))
        for k in self.ORDER[1:]:
            if k in target and target[k] is not None:
                yield k,target[k]
