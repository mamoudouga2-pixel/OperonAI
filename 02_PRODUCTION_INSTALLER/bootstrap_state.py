from dataclasses import dataclass,asdict
import json
@dataclass
class BootstrapState:
    first_launch:bool=True; last_result:str="never"; last_error:str|None=None
    def save(self,path): path.write_text(json.dumps(asdict(self),indent=2),encoding='utf-8')
