class RetryPolicy:
    def __init__(self,max_retries=3): self.max_retries=max_retries
    def allowed(self,attempt): return attempt<self.max_retries
