from .cleanup import remove_tree
from .user_data_policy import policy
class Uninstaller:
    def __init__(self,paths):self.paths=paths
    def uninstall(self,complete_data=False):
        pol=policy(complete_data)
        if pol["application"]: remove_tree(self.paths.app)
        if pol["runtime"]: remove_tree(self.paths.runtime)
        if pol["models"]: remove_tree(self.paths.models)
        if pol["cache"]: remove_tree(self.paths.cache)
        if pol["logs"]: remove_tree(self.paths.logs)
        if pol["browser_profile"]: remove_tree(self.paths.browser/"automation_profile")
        if pol["user_data"]: remove_tree(self.paths.user_data)
        return pol
