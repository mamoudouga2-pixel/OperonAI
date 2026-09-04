class DecisionEngine:
    def worker_for(self,action):
        text=str(action.get("action","")).lower()+" "+str(action.get("target","")).lower()
        if "browser" in text or "web" in text: return "Browser Agent"
        if any(x in text for x in ("file","desktop","local")): return "Desktop Agent"
        if any(x in text for x in ("vision","verify","check")): return "Vision & Verification"
        if "memory" in text: return "Memory System"
        if any(x in text for x in ("permission","security","authorize")): return "Security System"
        return action.get("worker","Desktop Agent")
    def risk(self,action):
        return str(action.get("risk","LOW")).upper()
    def must_approve(self,action):
        return self.risk(action)=="RED"
