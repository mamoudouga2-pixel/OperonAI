class SupervisorState:
    TERMINAL={"SUCCESS","FAILED","CANCELLED","TIMEOUT"}
    ALLOWED={
      "NEW":{"UNDERSTANDING","CANCELLED","TIMEOUT"},
      "UNDERSTANDING":{"PLANNING","FAILED","CANCELLED","TIMEOUT"},
      "PLANNING":{"SECURITY_CHECK","FAILED","CANCELLED","TIMEOUT"},
      "SECURITY_CHECK":{"WAITING_APPROVAL","EXECUTING","FAILED","CANCELLED","TIMEOUT"},
      "WAITING_APPROVAL":{"EXECUTING","FAILED","CANCELLED","TIMEOUT"},
      "EXECUTING":{"VERIFYING","RECOVERING","FAILED","CANCELLED","TIMEOUT"},
      "VERIFYING":{"SUCCESS","RECOVERING","FAILED","CANCELLED","TIMEOUT"},
      "RECOVERING":{"EXECUTING","VERIFYING","PLANNING","FAILED","CANCELLED","TIMEOUT"},
    }
    def __init__(self): self.current="NEW"; self.history=["NEW"]
    def transition(self,new):
        if new not in self.ALLOWED.get(self.current,set()): raise RuntimeError(f"invalid transition {self.current}->{new}")
        self.current=new; self.history.append(new); return new
