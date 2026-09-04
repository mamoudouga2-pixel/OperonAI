import hashlib,json
class AuditIntegrity:
    """Recomputes the hash chain over a record list and checks it against the
    chain each record actually stored. Returns False the moment a record is
    missing, out of order, or has been altered after being written."""
    def verify(self,records):
        prev=""
        for r in records:
            if "hash" not in r or "prev_hash" not in r: return False
            if r["prev_hash"]!=prev: return False
            body={k:v for k,v in r.items() if k not in ("hash","prev_hash")}
            h=hashlib.sha256((prev+json.dumps(body,sort_keys=True,default=str)).encode()).hexdigest()
            if h!=r["hash"]: return False
            prev=h
        return True
