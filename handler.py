class ErrorHandler:
    def __init__(self, state_store):
        self.state_store = state_store

    def record(self, category, message, context=None):
        self.state_store.audit("error", {
            "category": category,
            "message": str(message),
            "context": context or {},
        })

    def fail_closed(self, reason, context=None):
        self.record("FAIL_CLOSED", reason, context)
