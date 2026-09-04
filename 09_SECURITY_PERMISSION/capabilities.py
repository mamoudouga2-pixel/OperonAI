class CapabilityChecker:
    def allowed(self,manifest,requested):return requested in manifest.capabilities
