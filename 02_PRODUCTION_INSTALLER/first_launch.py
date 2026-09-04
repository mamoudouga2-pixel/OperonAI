from pathlib import Path
from .environment_check import check
from .bootstrap_state import BootstrapState
from configuration.validator import validate_config
from runtime_setup.ollama_adapter import OllamaAdapter

def run_first_launch(paths,model=None):
    result={"environment":check(paths),"storage":paths.user_data.exists(),"runtime":False,"model":False,"browser":paths.browser.exists(),"config":False,"self_test":False}
    if paths.config.exists():
        validate_config(paths.config); result["config"]=True
    rt=OllamaAdapter(paths.runtime/"ollama"); runtime_health=rt.health_check(); result["runtime"]=bool(runtime_health.get("healthy"))
    if result["runtime"] and model:
        try: rt.chat(model,"installer self-test"); result["model"]=True
        except Exception: result["model"]=False
    test=paths.temp/"self_test.txt"; test.write_text("LOCAL_MULTI_AGENT_COMPUTER_WORKER_SELF_TEST",encoding='utf-8'); result["self_test"]=test.read_text(encoding='utf-8').startswith("LOCAL_"); test.unlink(missing_ok=True)
    BootstrapState(first_launch=False,last_result="ready" if all(v is True for k,v in result.items() if k not in {"environment"}) else "degraded").save(paths.base/"bootstrap_state.json")
    return result
