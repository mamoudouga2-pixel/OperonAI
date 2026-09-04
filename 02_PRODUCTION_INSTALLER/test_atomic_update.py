from installer_engine.install_paths import InstallPaths,ensure_directories
from update_system.staged_update import StagedUpdate
def test_atomic_health_gate(tmp_path):
 p=InstallPaths(tmp_path); ensure_directories(p); (p.current/'v').write_text('old'); s=StagedUpdate(p); s.stage(); (p.staging/'v').write_text('new'); assert s.activate(False) is False; assert (p.current/'v').read_text()=='old'
