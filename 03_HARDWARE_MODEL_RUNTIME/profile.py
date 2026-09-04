from dataclasses import dataclass, asdict
import os, platform, shutil

@dataclass(frozen=True)
class GPUProfile:
    vendor: str="unknown"
    vram_gb: float=0.0

@dataclass(frozen=True)
class HardwareProfile:
    os: str
    architecture: str
    cpu_cores: int
    cpu_threads: int
    ram_gb: float
    gpu: GPUProfile
    storage_free_gb: float
    def __post_init__(self):
        if self.cpu_cores<1 or self.cpu_threads<self.cpu_cores: raise ValueError("invalid CPU topology")
        if min(self.ram_gb,self.gpu.vram_gb,self.storage_free_gb)<0: raise ValueError("negative resource")
    def to_dict(self):
        return {"os":self.os,"architecture":self.architecture,
                "cpu":{"cores":self.cpu_cores,"threads":self.cpu_threads},
                "ram_gb":self.ram_gb,"gpu":asdict(self.gpu),"storage_free_gb":self.storage_free_gb}
    @classmethod
    def from_dict(cls,x):
        try:
            return cls(str(x["os"]),str(x["architecture"]),int(x["cpu"]["cores"]),int(x["cpu"]["threads"]),
                       float(x["ram_gb"]),GPUProfile(str(x["gpu"]["vendor"]),float(x["gpu"]["vram_gb"])),
                       float(x["storage_free_gb"]))
        except (KeyError,TypeError,ValueError) as e: raise ValueError(f"invalid hardware contract: {e}") from e

class HardwareDetector:
    def discover(self):
        t=os.cpu_count() or 1
        return HardwareProfile(platform.system().lower() or "unknown",platform.machine().lower() or "unknown",
                               t,t,self._ram(),GPUProfile(),self._free())
    def _ram(self):
        try:return round(os.sysconf("SC_PHYS_PAGES")*os.sysconf("SC_PAGE_SIZE")/1024**3,2)
        except (AttributeError,OSError,ValueError):return 0.0
    def _free(self):
        try:return round(shutil.disk_usage(".").free/1024**3,2)
        except OSError:return 0.0
