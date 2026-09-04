NON_IDEMPOTENT={"SUBMIT","PUBLISH","PURCHASE","SEND","DELETE","FINAL_CONFIRMATION"}
class ActionExecutor:
    def __init__(self,adapter,locator): self.adapter=adapter; self.locator=locator
    def execute(self,sid,action):
        typ=str(action.get("action_type","")).upper()
        if typ in NON_IDEMPOTENT and not action.get("approval")=="APPROVED": raise RuntimeError("PERMISSION_BLOCKED")
        target=action.get("target",{})
        found=self.locator.find(target,lambda spec:self.adapter.find_target(sid,spec)) if target else None
        if typ=="CLICK": result=self.adapter.click(sid,found["found"])
        elif typ=="TYPE":
            if "value_ref" not in action: raise ValueError("TYPE requires value_ref")
            result=self.adapter.type(sid,found["found"],"<TASK_DATA_REFERENCE>")
        elif typ=="SELECT": result=self.adapter.select(sid,found["found"],action.get("option"))
        elif typ=="SCROLL": result=self.adapter.scroll(sid,action.get("amount",0))
        elif typ=="KEYBOARD": result=self.adapter.keyboard(sid,action.get("key"))
        elif typ in NON_IDEMPOTENT: result=self.adapter.click(sid,found["found"])
        else: raise ValueError("unsupported action_type")
        return result
