from threading import RLock
class RuntimeManager:
    def __init__(self):self._items={};self._lock=RLock()
    def register(self,a):
        aid=a.metadata().get("adapter_id")
        if not aid:raise ValueError("adapter_id missing")
        with self._lock:
            if aid in self._items:raise ValueError(f"duplicate adapter: {aid}")
            self._items[aid]=a
        return aid
    def get(self,aid):
        with self._lock:
            if aid not in self._items:raise KeyError(f"unknown adapter: {aid}")
            return self._items[aid]
    def list_adapters(self):
        with self._lock:return sorted(self._items)
    def load(self,aid):
        a=self.get(aid)
        if not a.install():raise RuntimeError("install failed")
        if not a.load():raise RuntimeError("load failed")
        if not a.health_check():a.unload();raise RuntimeError("post-load health check failed")
        return a
    def unload(self,aid):return self.get(aid).unload()
    def remove(self,aid):
        a=self.get(aid)
        if a.loaded and not a.unload():raise RuntimeError("unload failed")
        with self._lock:self._items.pop(aid)
