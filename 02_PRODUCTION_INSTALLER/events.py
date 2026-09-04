from dataclasses import dataclass, asdict
from typing import Callable, Any
import time
@dataclass(frozen=True)
class InstallerEvent:
    event:str; installation_id:str=''; component_id:str=''; progress:float|None=None; payload:dict[str,Any]|None=None; timestamp:float=0
    def to_dict(self):
        d=asdict(self); d['timestamp']=self.timestamp or time.time(); return d
class EventBus:
    def __init__(self): self._handlers=[]
    def subscribe(self,handler:Callable): self._handlers.append(handler); return lambda:self.unsubscribe(handler)
    def unsubscribe(self,handler):
        if handler in self._handlers:self._handlers.remove(handler)
    def emit(self,event):
        for h in list(self._handlers): h(event)
