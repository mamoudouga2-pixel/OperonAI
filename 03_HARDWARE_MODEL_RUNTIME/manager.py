class FallbackManager:
    ORDER=("primary","secondary","lightweight","deterministic")
    def __init__(self,runtime,selector,checker,*,max_attempts=4):self.runtime=runtime;self.selector=selector;self.checker=checker;self.max_attempts=max_attempts
    def execute(self,req,profile,adapters,prompt,*,task_state="RUNNING",required_capabilities=None,human_approval=None,deterministic=None,policy=None,**kwargs):
        if task_state not in {"RUNNING","RECOVERING","VERIFYING"}:raise RuntimeError("invalid task state for runtime execution")
        required=set(required_capabilities or req.get("required_capabilities",[]))
        ranked=self.selector.rank(req,profile,adapters,policy)
        errors=[];attempts=0
        for choice in ranked[:self.max_attempts]:
            attempts+=1;a=self.runtime.get(choice.adapter_id)
            try:
                if not a.loaded:self.runtime.load(choice.adapter_id)
                if not a.health_check():raise RuntimeError("health check failed")
                if not required.issubset(a.capabilities):raise RuntimeError("post-load capability validation failed")
                out=a.generate(prompt,**kwargs)
                return out,{"route":"runtime","adapter_id":a.adapter_id,"attempts":attempts,"errors":errors,"validated":True}
            except Exception as e:
                errors.append({"adapter_id":a.adapter_id,"error":str(e)})
                try:a.unload()
                except Exception:pass
        # Deterministic fallback is allowed only when explicitly supplied.
        if deterministic is not None and callable(deterministic):
            try:
                out=deterministic(prompt)
                return out,{"route":"deterministic","attempts":attempts,"errors":errors,"validated":True}
            except Exception as e:errors.append({"route":"deterministic","error":str(e)})
        if human_approval is not None:
            approved=bool(human_approval({"reason":"runtime fallbacks exhausted","errors":errors}))
            if approved:return {"status":"approved_for_manual_handling"},{"route":"human_approval","attempts":attempts,"errors":errors,"validated":True}
        raise RuntimeError(f"SAFE_FAILURE: all bounded runtime fallbacks failed: {errors}")
