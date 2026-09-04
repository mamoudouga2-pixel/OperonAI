from .platform import detect_platform

def platform_contract():
    p=detect_platform()
    return {"os":p.os,"os_version":p.os_version,"architecture":p.architecture,"cpu_architecture":p.cpu_architecture,"user_scope":p.user_scope,"admin_available":p.admin_available}
