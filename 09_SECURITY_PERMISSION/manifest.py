class PluginManifest:
    def __init__(self,plugin_id,capabilities,permissions=None,memory_scope="plugin-specific"):
        self.plugin_id=plugin_id;self.capabilities=set(capabilities);self.permissions=permissions or [];self.memory_scope=memory_scope
