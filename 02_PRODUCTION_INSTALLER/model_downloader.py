class ModelDownloader:
    def __init__(self,runtime): self.runtime=runtime
    def pull(self,model_name): return self.runtime.pull_model(model_name)
