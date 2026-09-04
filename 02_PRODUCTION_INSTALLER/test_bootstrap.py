from installer_engine.install_paths import InstallPaths,ensure_directories
from configuration.generator import generate_config
from bootstrap.first_launch import run_first_launch
from dependency_manager.manifest import Manifest

def test_first_launch(tmp_path):
    p=InstallPaths(tmp_path); ensure_directories(p); m=Manifest.from_dict({"components":[]}); generate_config(p,m); r=run_first_launch(p); assert r["storage"] and r["browser"] and r["config"] and r["self_test"]
