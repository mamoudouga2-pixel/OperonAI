class BrowserManager:
    def __init__(self,profile_dir): self.profile_dir=profile_dir
    def profile(self): self.profile_dir.mkdir(parents=True,exist_ok=True); return self.profile_dir
