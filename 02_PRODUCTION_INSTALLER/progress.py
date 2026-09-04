from dataclasses import dataclass
@dataclass(frozen=True)
class ProgressEvent:
    downloaded:int; total:int|None; speed_bps:float; eta_seconds:float|None
