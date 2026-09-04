def is_newer(current,target):
    def t(v): return tuple(int(x) for x in v.split('.')[:3])
    return t(target)>t(current)
