import time

class BossAgent:
    def __init__(self,understander,planner,decomposer,decision,approval,supervisor,report):
        self.understander=understander; self.planner=planner; self.decomposer=decomposer
        self.decision=decision; self.approval=approval; self.supervisor=supervisor; self.report=report

    def run(self,instruction,*,target=None,constraints=None,expected_result=None,step_results=None,approval=None,steps=None):
        completed=[]; approvals=[]; evidence=[]; recovery=[]; start=time.monotonic()
        intent=self.understander.understand(instruction,target=target,constraints=constraints,expected_result=expected_result)
        if intent.critical_missing:
            return self.report.build(outcome="CLARIFICATION_REQUIRED",steps=[],approvals=[],evidence=[],recovery=[],verification=False)

        plan=self.planner.build(intent,steps=steps)
        actions=self.decomposer.decompose(plan)

        for action in actions:
            action["worker"]=self.decision.worker_for(action)
            if self.decision.must_approve(action):
                if approval is None or str(approval).upper() not in {"APPROVED","REJECTED"}:
                    self.approval.request(action)
                    return self.report.build(outcome="WAITING_APPROVAL",steps=completed,approvals=approvals,
                                             evidence=evidence,recovery=recovery,verification=False)
                if str(approval).upper()=="REJECTED":
                    approvals.append("REJECTED")
                    completed.append({"step":action["step_id"],"status":"skipped"})
                    return self.report.build(outcome="FAILED",steps=completed,approvals=approvals,
                                             evidence=evidence,recovery=recovery,verification=False)
                approvals.append("APPROVED")

            result=(step_results or {}).get(action["step_id"],{"success":False,"evidence":None})
            attempts=0
            while True:
                attempts+=1
                ok,diag=self.supervisor.verify(result)
                if ok:
                    evidence.append(result["evidence"])
                    completed.append({"step":action["step_id"],"status":"completed","attempts":attempts})
                    break

                pattern=str(diag.get("evidence") or diag.get("reason") or "NO_EVIDENCE")
                if self.supervisor.recoverable(pattern):
                    recovery.append({"step":action["step_id"],"pattern":pattern,"attempt":attempts})
                    # A recovery requires a fresh result supplied by the caller; never
                    # treat the same failed evidence as a successful retry.
                    fresh=(step_results or {}).get((action["step_id"],attempts+1))
                    if fresh is None:
                        completed.append({"step":action["step_id"],"status":"failed"})
                        return self.report.build(outcome="FAILED",steps=completed,approvals=approvals,
                                                 evidence=evidence,recovery=recovery,verification=False)
                    result=fresh
                    continue

                completed.append({"step":action["step_id"],"status":"failed","attempts":attempts})
                return self.report.build(outcome="FAILED",steps=completed,approvals=approvals,
                                         evidence=evidence,recovery=recovery,verification=False)

            if time.monotonic()-start>plan.max_runtime_s:
                return self.report.build(outcome="TIMEOUT",steps=completed,approvals=approvals,
                                         evidence=evidence,recovery=recovery,verification=False)

        return self.report.build(outcome="SUCCESS",steps=completed,approvals=approvals,
                                 evidence=evidence,recovery=recovery,verification=True)
