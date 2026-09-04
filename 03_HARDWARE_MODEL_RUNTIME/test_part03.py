import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from detector.profile import *
from runtime_manager.adapter import *
from runtime_manager.manager import RuntimeManager
from compatibility.checker import CompatibilityChecker
from model_selector.selector import ModelSelector
from performance_manager.policy import PerformancePolicy
from performance_manager.monitor import ResourceMonitor
from fallback_manager.manager import FallbackManager
from benchmark.runner import BenchmarkRunner

class T(unittest.TestCase):
    def setUp(self):
        self.p=HardwareProfile("test","x86",4,8,16,GPUProfile("gpu",8),100)
        self.r=RuntimeManager();self.c=CompatibilityChecker();self.s=ModelSelector(self.c)
        self.policy=PerformancePolicy(16,8,1,4096,2,False)
    def test_contract_roundtrip(self):self.assertEqual(HardwareProfile.from_dict(self.p.to_dict()),self.p)
    def test_all_adapter_classes(self):
        xs=[ReasoningLanguageAdapter("r",["reasoning","language"]),VisionAdapter("v",["vision"]),
            EmbeddingAdapter("e",["embedding"]),LightweightFallbackAdapter("l",["lightweight","language"])]
        for a in xs:self.r.register(a)
        self.assertEqual(len(self.r.list_adapters()),4)
    def test_remote_policy(self):
        a=RemoteAdapter("remote",["language","remote"])
        self.assertFalse(self.c.check({"required_capabilities":["language"]},self.p,a,self.policy).compatible)
        p=PerformancePolicy(16,8,1,4096,2,True)
        self.assertTrue(self.c.check({"required_capabilities":["language"]},self.p,a,p).compatible)
    def test_selection_and_diagnostic(self):
        a=ReasoningLanguageAdapter("r",["language"],ram_gb=1);self.r.register(a)
        self.assertEqual(self.s.select({"required_capabilities":["language"]},self.p,[a],self.policy).adapter_id,"r")
        with self.assertRaisesRegex(RuntimeError,"UNSUPPORTED_CONFIGURATION"):
            self.s.select({"required_capabilities":["vision"]},self.p,[a],self.policy)
    def test_lifecycle_health(self):
        a=ReasoningLanguageAdapter("r",["language"]);self.r.register(a);self.r.load("r");self.assertTrue(a.health_check());self.r.unload("r");self.assertFalse(a.health_check())
    def test_concurrency_and_low_resource(self):
        m=ResourceMonitor(HardwareProfile("t","x",1,1,1,GPUProfile(),10),PerformancePolicy(1,1,1,100))
        m.acquire()
        with self.assertRaisesRegex(RuntimeError,"CONCURRENCY_LIMIT"):m.acquire()
        self.assertTrue(m.snapshot()["low_resource_mode"]);m.release()
    def test_fallback_revalidates_capability(self):
        class Bad(ReasoningLanguageAdapter):
            def generate(self,prompt,**kw):raise RuntimeError("boom")
        bad=Bad("bad",["language"]);good=ReasoningLanguageAdapter("good",["language"]);self.r.register(bad);self.r.register(good)
        f=FallbackManager(self.r,self.s,self.c,max_attempts=2)
        out,meta=f.execute({"required_capabilities":["language"]},self.p,[bad,good],"x",required_capabilities=["language"],policy=self.policy)
        self.assertEqual(out["adapter_id"],"good");self.assertTrue(meta["validated"])
    def test_deterministic_fallback(self):
        a=ReasoningLanguageAdapter("bad",["language"]);self.r.register(a)
        class X(ReasoningLanguageAdapter):
            def generate(self,prompt,**kw):raise RuntimeError("x")
        self.r.remove("bad");self.r.register(X("x",["language"]))
        f=FallbackManager(self.r,self.s,self.c,max_attempts=1)
        out,meta=f.execute({"required_capabilities":["language"]},self.p,[self.r.get("x")],"q",deterministic=lambda q:"det",policy=self.policy)
        self.assertEqual(meta["route"],"deterministic")
    def test_safe_failure(self):
        a=ReasoningLanguageAdapter("a",["language"]);self.r.register(a)
        class X(ReasoningLanguageAdapter):
            def generate(self,prompt,**kw):raise RuntimeError("x")
        self.r.remove("a");x=X("x",["language"]);self.r.register(x)
        f=FallbackManager(self.r,self.s,self.c,max_attempts=1)
        with self.assertRaisesRegex(RuntimeError,"SAFE_FAILURE"):
            f.execute({"required_capabilities":["language"]},self.p,[x],"q",policy=self.policy)
    def test_model_swap_without_selector_change(self):
        a=ReasoningLanguageAdapter("one",["language"]);b=ReasoningLanguageAdapter("two",["language"])
        self.r.register(a);self.r.register(b)
        self.assertIsNotNone(self.s.select({"required_capabilities":["language"]},self.p,[a,b],self.policy))
    def test_benchmark_runner(self):
        a=ReasoningLanguageAdapter("bench",["language"]);self.r.register(a)
        b=BenchmarkRunner(self.r)
        result=b.run("bench","hello",trials=3)
        self.assertEqual(result.trials,3);self.assertEqual(result.metrics.calls,3)
        self.assertEqual(result.metrics.failures,0);self.assertEqual(result.to_dict()["adapter_id"],"bench")
    def test_generate_kwargs_key(self):
        a=ReasoningLanguageAdapter("kw",["language"]);a.load()
        out=a.generate("hi",temperature=0.2)
        self.assertIn("kwargs",out);self.assertEqual(out["kwargs"]["temperature"],0.2)
    def test_pressure(self):
        x=ResourceMonitor(self.p,self.policy).pressure(8,4);self.assertAlmostEqual(x["ram_pressure"],.5);self.assertAlmostEqual(x["vram_pressure"],.5)

if __name__=="__main__":unittest.main()
