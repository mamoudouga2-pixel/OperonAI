class FilesystemPolicy:
    def __init__(self,paths):self.paths=paths
    def validate_action(self,a):
        p=a["target"].get("path")
        if not p:return True
        self.paths.validate(p)
        if a["action_type"]=="DELETE" and a["target"].get("protected",False):raise RuntimeError("PROTECTED_PATH_DENIED")
        if a["action_type"] in {"COPY_FILE","MOVE_FILE"} and a["target"].get("overwrite",False):raise RuntimeError("TARGET_VALIDATION_FAILED")
        return True
