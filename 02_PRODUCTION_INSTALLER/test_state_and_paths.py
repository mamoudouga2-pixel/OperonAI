from installer_engine.install_paths import InstallPaths,ensure_directories
from installer_engine.install_state import InstallationState

def test_state_roundtrip(tmp_path):
    p=InstallPaths(tmp_path); ensure_directories(p); s=InstallationState.load(p.state); s.current_stage="DOWNLOAD"; s.snapshot.pending_components=["x"]; s.save(); t=InstallationState.load(p.state); assert t.current_stage=="DOWNLOAD" and t.pending_components==["x"]
