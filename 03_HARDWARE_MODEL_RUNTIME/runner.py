from time import monotonic
from performance_manager.metrics import RuntimeMetrics

class BenchmarkResult:
    def __init__(self,adapter_id,trials,metrics):
        self.adapter_id=adapter_id;self.trials=trials;self.metrics=metrics
    def to_dict(self):
        return {"adapter_id":self.adapter_id,"trials":self.trials,
                "calls":self.metrics.calls,"failures":self.metrics.failures,
                "average_latency_s":self.metrics.average_latency_s}

class BenchmarkRunner:
    """Measures adapter.generate() latency/reliability so the model_selector
    can be informed by observed performance, not just declared requirements."""
    def __init__(self,runtime):self.runtime=runtime
    def run(self,adapter_id,prompt,*,trials=3,**kwargs):
        if trials<1:raise ValueError("trials must be >= 1")
        a=self.runtime.get(adapter_id)
        if not a.loaded:self.runtime.load(adapter_id)
        metrics=RuntimeMetrics()
        for _ in range(trials):
            started=monotonic();failed=False
            try:a.generate(prompt,**kwargs)
            except Exception:failed=True
            finally:metrics.observe(started,failed=failed)
        return BenchmarkResult(adapter_id,trials,metrics)
    def compare(self,adapter_ids,prompt,*,trials=3,**kwargs):
        results=[self.run(aid,prompt,trials=trials,**kwargs) for aid in adapter_ids]
        return sorted(results,key=lambda r:(r.metrics.failures,r.metrics.average_latency_s))
