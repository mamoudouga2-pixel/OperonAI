class TaskDispatcher:
    def dispatch(self,worker,action):
        if not worker: raise ValueError("worker required")
        return worker.execute(action)
