class BrowserLogger:
    SENSITIVE={"password","token","secret","authorization","api_key","value"}
    def sanitize(self,data):
        if isinstance(data,dict):
            return {k:("<REDACTED>" if k.lower() in self.SENSITIVE else self.sanitize(v)) for k,v in data.items()}
        if isinstance(data,list): return [self.sanitize(x) for x in data]
        return data
    def event(self,event,**data): return {"event":event,"data":self.sanitize(data)}
