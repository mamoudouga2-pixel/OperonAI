from dataclasses import dataclass
from time import monotonic
@dataclass
class RuntimeMetrics:
    calls:int=0;failures:int=0;total_latency_s:float=0
    def observe(self,started,failed=False):
        self.calls+=1;self.failures+=int(failed);self.total_latency_s+=max(0,monotonic()-started)
    @property
    def average_latency_s(self):return self.total_latency_s/self.calls if self.calls else 0
