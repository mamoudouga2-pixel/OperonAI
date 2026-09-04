from dataclasses import dataclass
from enum import Enum
import platform, subprocess, os, sys
@dataclass(frozen=True)
class PermissionRequest:
    permission:str; reason:str; required_when:str='on-demand'
MATRIX={
'screen_access':('Screen observation','on-demand'),
'keyboard_mouse_control':('Keyboard/mouse automation','on-demand'),
'file_access':('User-selected files','scoped'),
'network_access':('Download/update/browser','when-used'),
'microphone':('Voice input','optional'),
'camera':('Visual input','optional'),
}
class PermissionManager:
    def is_supported(self,permission): return permission in MATRIX
    def explain_requirement(self,permission): return MATRIX.get(permission,('Unknown permission','unsupported'))[0]
    def required(self,capabilities): return [PermissionRequest(x,*MATRIX[x]) for x in capabilities if x in MATRIX]
    def get_status(self,permission):
        if not self.is_supported(permission): return 'unsupported'
        if permission=='network_access': return 'available'
        if permission=='file_access': return 'scoped'
        if platform.system()=='Darwin' and permission in {'screen_access','keyboard_mouse_control','microphone','camera'}: return 'unknown'
        if platform.system()=='Windows' and permission in {'screen_access','keyboard_mouse_control'}: return 'unknown'
        if platform.system()=='Linux' and permission in {'screen_access','keyboard_mouse_control'}: return 'unknown'
        return 'unknown'
    def request(self,permission):
        if not self.is_supported(permission): return False
        return self.open_system_settings(permission) if self.get_status(permission)=='unknown' else self.get_status(permission) in {'available','scoped','granted'}
    def open_system_settings(self,permission):
        system=platform.system()
        try:
            if system=='Windows': subprocess.Popen(['cmd','/c','start','ms-settings:privacy'])
            elif system=='Darwin': subprocess.Popen(['open','x-apple.systempreferences:com.apple.preference.security'])
            elif system=='Linux':
                # No single portable permission UI; never bypass OS security.
                return False
            return True
        except OSError: return False
