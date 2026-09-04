from .browser_version import version_of

def health(binary): return bool(version_of(binary))
