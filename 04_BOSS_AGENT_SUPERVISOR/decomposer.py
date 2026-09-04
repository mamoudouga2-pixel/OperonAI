class TaskDecomposer:
    def decompose(self,plan):
        return [dict(step,step_id=i+1) for i,step in enumerate(plan.steps)]
