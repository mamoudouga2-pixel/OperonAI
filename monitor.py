from communication.protocols import Event

class HealthMonitor:
    def __init__(self, module_manager, event_bus):
        self.module_manager, self.event_bus = module_manager, event_bus

    def check(self, module_id):
        result = self.module_manager.health_check(module_id)
        self.event_bus.publish(Event("module.health.checked", result))
        return result

    def check_all(self):
        return {m: self.check(m) for m in self.module_manager.list_modules()}
