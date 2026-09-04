from installer_engine.install_paths import InstallPaths,ensure_directories
from uninstall_system.uninstall import Uninstaller

def test_uninstall_preserves_user_data(tmp_path):
    p=InstallPaths(tmp_path); ensure_directories(p); (p.app/"x").write_text("x"); (p.user_data/"keep").write_text("k"); Uninstaller(p).uninstall(False); assert not p.app.exists(); assert (p.user_data/"keep").exists()
