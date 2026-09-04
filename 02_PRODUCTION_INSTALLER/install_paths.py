from pathlib import Path
from .platform import adapter
class InstallPaths:
    def __init__(self, base):
        self.base=Path(base); self.app=self.base/"app"; self.runtime=self.base/"runtime"; self.models=self.base/"models"; self.browser=self.base/"browser"; self.cache=self.base/"cache"; self.logs=self.base/"logs"; self.temp=self.base/"temporary"; self.user_data=self.base/"user_data"; self.tasks=self.user_data/"tasks"; self.memory=self.user_data/"memory"; self.settings=self.user_data/"settings"; self.workflows=self.user_data/"workflows"; self.exports=self.user_data/"exports"; self.state=self.base/"install_state.json"; self.config=self.base/"config.json"; self.registry=self.base/"component_registry.json"; self.current=self.base/"current"; self.staging=self.base/"staging"; self.backup=self.base/"backup"
    def all_dirs(self): return [self.app,self.runtime,self.models,self.browser,self.cache,self.logs,self.temp,self.user_data,self.tasks,self.memory,self.settings,self.workflows,self.exports,self.current,self.staging,self.backup]

def build_paths(root=None): return InstallPaths(root or (adapter().user_app_dir()))
def ensure_directories(paths):
    for p in paths.all_dirs(): p.mkdir(parents=True,exist_ok=True)
