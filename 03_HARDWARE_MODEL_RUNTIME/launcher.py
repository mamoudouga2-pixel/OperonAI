import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent/"03_HARDWARE_RUNTIME"))
from detector.profile import HardwareDetector
from runtime_manager.adapter import ReasoningLanguageAdapter
from runtime_manager.manager import RuntimeManager
from compatibility.checker import CompatibilityChecker
from model_selector.selector import ModelSelector
from performance_manager.policy import PerformancePolicy
from performance_manager.monitor import ResourceMonitor
from fallback_manager.manager import FallbackManager

profile=HardwareDetector().discover()
runtime=RuntimeManager()
a=ReasoningLanguageAdapter("reference",["reasoning","language"],ram_gb=0.1)
runtime.register(a)
checker=CompatibilityChecker()
selector=ModelSelector(checker)
policy=PerformancePolicy(max_ram_gb=max(profile.ram_gb,0.1), max_vram_gb=max(profile.gpu.vram_gb,0.1),
                         max_concurrent_tasks=1, max_context_tokens=4096)
monitor=ResourceMonitor(profile,policy)
choice=selector.select({"required_capabilities":["language"],"context_budget":1024},profile,[a],policy)
runtime.load(choice.adapter_id)
print("selected:",choice.adapter_id)
print("health:",runtime.get(choice.adapter_id).health_check())
print("resources:",monitor.snapshot())
