from dataclasses import dataclass
from pathlib import Path
import shutil

@dataclass(frozen=True)
class SpaceBreakdown:
    download_bytes:int
    temporary_bytes:int
    extraction_bytes:int
    installation_bytes:int
    safety_buffer:int
    required_bytes:int
    available_bytes:int
    sufficient:bool

def estimate(download:int, temporary:int=0, extraction:int=0, installation:int=0, safety_buffer:int=256*1024*1024, path='.') -> SpaceBreakdown:
    required=max(0,download)+max(0,temporary)+max(0,extraction)+max(0,installation)+max(0,safety_buffer)
    available=shutil.disk_usage(Path(path)).free
    return SpaceBreakdown(download,temporary,extraction,installation,safety_buffer,required,available,available>=required)

def require_space(b:SpaceBreakdown):
    if not b.sufficient:
        raise RuntimeError(f"Insufficient storage: required={b.required_bytes}, available={b.available_bytes}")
