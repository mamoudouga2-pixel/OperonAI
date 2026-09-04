class StartupRecovery:
    def recover(self,state):
        return {"resume": bool(state.pending_components), "stage": state.current_stage}
