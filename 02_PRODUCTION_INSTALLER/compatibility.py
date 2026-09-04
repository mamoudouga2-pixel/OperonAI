import re

def version_tuple(v):
    return tuple(int(x) for x in re.findall(r"\d+",v)[:3])+(0,0,0)
def compatible(component,app_version):
    v=version_tuple(app_version)
    if component.minimum_app_version and v<version_tuple(component.minimum_app_version): return False
    if component.maximum_app_version and v>version_tuple(component.maximum_app_version): return False
    return True
