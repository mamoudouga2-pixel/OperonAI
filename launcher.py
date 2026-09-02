from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / '01_CORE'))
from orchestrator import CoreOrchestrator

if __name__ == '__main__':
    core = CoreOrchestrator('./runtime')
    core.start()
    print(core.app_controller.state)
    core.shutdown()
