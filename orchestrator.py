from pathlib import Path
from configuration.config import CoreConfig
from state_manager.store import StateStore
from event_bus.bus import EventBus
from error_handler.handler import ErrorHandler
from module_manager.manager import ModuleManager
from task_manager.manager import TaskManager
from health_monitor.monitor import HealthMonitor
from app_controller.controller import ApplicationController

class CoreOrchestrator:
    def __init__(self, runtime_dir="./runtime", config=None):
        self.config = config or CoreConfig()
        self.state_store = StateStore(Path(runtime_dir), self.config)
        self.event_bus = EventBus(self.config)
        self.error_handler = ErrorHandler(self.state_store)
        self.module_manager = ModuleManager(self.event_bus, self.state_store, self.error_handler, self.config)
        self.task_manager = TaskManager(self.event_bus, self.state_store, self.error_handler, self.config)
        self.health_monitor = HealthMonitor(self.module_manager, self.event_bus)
        self.app_controller = ApplicationController(
            self.module_manager, self.task_manager, self.event_bus,
            self.health_monitor, self.state_store
        )

    def start(self): self.app_controller.start()
    def pause(self): self.app_controller.pause()
    def resume(self): self.app_controller.resume()
    def shutdown(self): self.app_controller.shutdown()
