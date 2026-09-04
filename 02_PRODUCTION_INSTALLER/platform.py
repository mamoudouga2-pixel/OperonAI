from dataclasses import dataclass
import os, platform, shutil
from pathlib import Path
from abc import ABC, abstractmethod

@dataclass(frozen=True)
class PlatformInfo:
    os: str
    os_version: str
    architecture: str
    cpu_architecture: str
    user_scope: str
    admin_available: bool

class PlatformAdapter(ABC):
    name = "unknown"
    @abstractmethod
    def user_app_dir(self): ...
    @abstractmethod
    def user_data_dir(self): ...
    def permission_action(self, permission): return None
    def is_admin(self): return os.name == "nt" and os.environ.get("USERNAME", "") == os.environ.get("USERDOMAIN", "")

class WindowsAdapter(PlatformAdapter):
    name="windows"
    def user_app_dir(self): return Path(os.environ.get("LOCALAPPDATA", Path.home())) / "LocalMultiAgentComputerWorker"
    def user_data_dir(self): return Path(os.environ.get("APPDATA", Path.home())) / "LocalMultiAgentComputerWorker"
    def permission_action(self, permission): return {"screen_access":"ms-settings:privacy-graphicscapture","file_access":"ms-settings:privacy-broadfilesystemaccess"}.get(permission)

class MacOSAdapter(PlatformAdapter):
    name="macos"
    def user_app_dir(self): return Path.home()/"Library"/"Application Support"/"LocalMultiAgentComputerWorker"
    def user_data_dir(self): return Path.home()/"Library"/"Application Support"/"LocalMultiAgentComputerWorker"/"user_data"
    def permission_action(self, permission): return {"screen_access":"x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture","accessibility":"x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"}.get(permission)

class LinuxAdapter(PlatformAdapter):
    name="linux"
    def user_app_dir(self): return Path(os.environ.get("XDG_DATA_HOME", Path.home()/".local/share"))/"LocalMultiAgentComputerWorker"
    def user_data_dir(self): return Path(os.environ.get("XDG_DATA_HOME", Path.home()/".local/share"))/"LocalMultiAgentComputerWorker"/"user_data"


def adapter():
    if os.name == "nt": return WindowsAdapter()
    if sys_platform() == "darwin": return MacOSAdapter()
    return LinuxAdapter()

def sys_platform(): return platform.system().lower()

def detect_platform():
    a=adapter(); machine=platform.machine().lower()
    arch={"amd64":"x64","x86_64":"x64","aarch64":"arm64","arm64":"arm64","x86":"x86"}.get(machine,machine or "unknown")
    return PlatformInfo(a.name, platform.version(), arch, arch, "current_user", a.is_admin())
