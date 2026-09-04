from installer_engine.install_paths import InstallPaths,ensure_directories
from update_system.staged_update import StagedUpdate
from update_system.rollback import Rollback

def test_stage_activate_rollback(tmp_path):
    p=InstallPaths(tmp_path); ensure_directories(p); (p.current/"v").write_text("old"); s=StagedUpdate(p); s.stage(); (p.staging/"v").write_text("new"); s.activate(); assert (p.current/"v").read_text()=="new"; assert Rollback(p).execute(); assert (p.current/"v").read_text()=="old"
