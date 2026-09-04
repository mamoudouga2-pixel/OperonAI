import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from verification.postcondition import PostconditionEngine
from verification.independent_check import IndependentCheck
from verification.verifier import Verifier
from evidence.collector import EvidenceCollector
from evidence.metadata import Evidence
from capture.artifact_store import ArtifactStore
from grounding.confidence import ConfidencePolicy
from loop_detection.detector import LoopDetector
from recovery.retry_policy import RetryPolicy
from adapters.registry import AdapterRegistry
class VisionAdapter:
 def analyze(self,x): return {"elements":[{"role":"button","text":"Submit"}]}
class BadAdapter:
 def analyze(self,x): raise RuntimeError
class T(unittest.TestCase):
 def setUp(self): self.pc=PostconditionEngine();self.v=Verifier(IndependentCheck(self.pc))
 def req(self): return {"verification_id":"VER-001","task_id":"TASK-001","action_id":"ACT-001","claim":"Form submitted","expected_state":{"operator":"AND","conditions":[{"type":"EXPECTED_TEXT","expected":"Success"},{"type":"NO_ERROR"},{"type":"LOADING_FALSE"}]}}
 def test_correct_success_is_verified(self):
  r=self.v.verify(self.req(),{"text":["Success"],"errors":[],"loading":False,"evidence_age_ms":1},[{"evidence_id":"EVID-1"}]);self.assertEqual(r["status"],"VERIFIED")
 def test_worker_claim_does_not_override_failure(self):
  r=self.v.verify(self.req(),{"text":[],"errors":["bad"],"loading":False,"evidence_age_ms":1},[{"evidence_id":"EVID-1"}]);self.assertEqual(r["status"],"NOT_VERIFIED")
 def test_stale_evidence(self):
  r=self.v.verify(self.req(),{"text":["Success"],"errors":[],"loading":False,"evidence_age_ms":30001},[{"evidence_id":"EVID-1"}]);self.assertEqual(r["status"],"UNCERTAIN")
 def test_low_confidence_risky_block(self): self.assertFalse(ConfidencePolicy(.75,.9).allow(.99,"HIGH",True,False))
 def test_wrong_window(self):
  r=self.pc.check({"operator":"AND","conditions":[{"type":"WINDOW","expected":"W2"}]},{"window_id":"W1"});self.assertFalse(r)
 def test_visible_error(self): self.assertFalse(self.pc.check({"operator":"AND","conditions":[{"type":"NO_ERROR"}]},{"errors":["error"]}))
 def test_partial_recovery_bounded(self): self.assertTrue(RetryPolicy(3).allowed(2));self.assertFalse(RetryPolicy(3).allowed(3))
 def test_loop(self):
  d=LoopDetector(2);d.observe("a","t","s","x");d.observe("a","t","s","x")
  with self.assertRaisesRegex(RuntimeError,"LOOP_DETECTED"): d.observe("a","t","s","x")
 def test_evidence_hash_redaction(self):
  with tempfile.TemporaryDirectory() as d:
   e=EvidenceCollector(ArtifactStore(d)).collect("T","A","desktop",b"abc","password token")
   self.assertEqual(e.redaction_status,"APPLIED");self.assertEqual(e.description,"<REDACTED>");self.assertEqual(len(e.hash),64)
 def test_ocr_fallback(self):
  class O:
   def read(self,x): return {"ocr":"ok"}
  r=AdapterRegistry();r.register_vision(BadAdapter());r.register_ocr(O());self.assertEqual(r.analyze(b"x")["ocr"],"ok")
 def test_model_adapter_failure(self):
  r=AdapterRegistry();r.register_vision(BadAdapter())
  with self.assertRaisesRegex(RuntimeError,"MODEL_ADAPTER_FAILURE"): r.analyze(b"x")
 def test_postcondition_file_and_source(self):
  c={"operator":"AND","conditions":[{"type":"FILE_EXISTS","path":"x"},{"type":"SOURCE_STATE","expected":"MOVED"}]}
  self.assertTrue(self.pc.check(c,{"files":{"x":True},"source_state":"MOVED"}))
if __name__=="__main__":unittest.main()
