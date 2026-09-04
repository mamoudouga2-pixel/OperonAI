from dataclasses import dataclass,asdict
@dataclass
class BrowserSession:
    session_id:str
    task_id:str
    status:str="READY"
    current_url:str="about:blank"
    active_tab_id:str="TAB-001"
    active_frame_id:str|None=None
    def to_dict(self): return asdict(self)
