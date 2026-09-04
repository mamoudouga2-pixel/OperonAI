from dataclasses import dataclass
@dataclass
class Candidate:
 role:str;text:str;bounding_box:dict;confidence:float;window_id:str|None=None
