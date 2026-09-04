class PluginIsolation:
    def __init__(self,checker):self.checker=checker
    def allowed(self,a):return self.checker.allowed(a["target"]["manifest"],a["requested_capability"]) if "manifest" in a["target"] else True
