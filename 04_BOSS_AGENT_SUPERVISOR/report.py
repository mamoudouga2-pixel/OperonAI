class ReportManager:
    def build(self,*,outcome,steps,approvals,evidence,recovery,verification):
        return {"task_outcome":outcome,"completed_failed_skipped_steps":steps,
                "approvals_used":approvals,"evidence_references":evidence,
                "recovery_attempts":recovery,"final_verification_status":verification}
