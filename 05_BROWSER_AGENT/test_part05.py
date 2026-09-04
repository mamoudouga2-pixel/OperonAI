import sys,unittest,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from browser_agent import BrowserAgent
from adapters.mock_adapter import MockBrowserAdapter
from locator_engine.locator import LocatorEngine
from locator_engine.confidence import ConfidenceGate
from recovery.recovery import LoopDetector
from observation.logger import BrowserLogger
from form_handler.form import FormHandler
from upload_handler.upload import UploadHandler
from download_handler.download import DownloadHandler

class T(unittest.TestCase):
    def setUp(self):
        self.adapter=MockBrowserAdapter(); self.b=BrowserAgent(self.adapter)
        self.s=self.b.create_session({"task_id":"TASK-001","session_id":"BROWSER-001"})
        self.adapter.sessions["BROWSER-001"]["target_map"][("button","Save")]="SAVE"
        self.adapter.sessions["BROWSER-001"]["target_map"][("text","Save")]="SAVE"
    def test_session_create_close(self):
        self.assertTrue(self.b.health_check("BROWSER-001"));self.b.close_session("BROWSER-001");self.assertFalse(self.b.health_check("BROWSER-001"))
    def test_navigation_domain_and_block(self):
        r=self.b.navigate("BROWSER-001",{"url":"https://example.com","constraints":{"allowed_domains":["example.com"],"allow_subdomains":False}})
        self.assertEqual(r["status"],"SUCCESS")
        with self.assertRaisesRegex(RuntimeError,"NAVIGATION_BLOCKED"):
            self.b.navigate("BROWSER-001",{"url":"https://evil.example","constraints":{"allowed_domains":["example.com"],"allow_subdomains":False}})
    def test_target_semantic_and_fallback(self):
        r=self.b.find_target("BROWSER-001",{"role":"button","name":"Save","text":"Save"})
        self.assertEqual(r["method"],"role_name")
        self.adapter.sessions["BROWSER-001"]["target_map"].pop(("button","Save"))
        r=self.b.find_target("BROWSER-001",{"role":"button","name":"Nope","text":"Save"})
        self.assertEqual(r["method"],"text")
    def test_click_evidence_contract(self):
        r=self.b.execute_action("BROWSER-001",{"action_id":"ACT-001","action_type":"CLICK","target":{"role":"button","name":"Save"}})
        self.assertEqual(r["status"],"SUCCESS");self.assertEqual(r["evidence_ids"],["EVID-001"]);self.assertEqual(r["error"],None)
    def test_sensitive_logging(self):
        x=BrowserLogger().event("TYPE",password="secret",token="abc",safe="ok")
        self.assertEqual(x["data"]["password"],"<REDACTED>");self.assertEqual(x["data"]["safe"],"ok")
    def test_non_idempotent_protection(self):
        with self.assertRaisesRegex(RuntimeError,"PERMISSION_BLOCKED"):
            self.b.execute_action("BROWSER-001",{"action_type":"DELETE","target":{"role":"button","name":"Save"}})
        r=self.b.execute_action("BROWSER-001",{"action_type":"DELETE","target":{"role":"button","name":"Save"},"approval":"APPROVED"})
        self.assertEqual(r["status"],"SUCCESS")
    def test_form_upload_download(self):
        self.assertTrue(FormHandler().validate({"name":"x"},["name"]))
        with tempfile.NamedTemporaryFile(suffix=".txt") as f:
            with self.assertRaisesRegex(RuntimeError,"approved file reference"): UploadHandler().validate({"file_ref":f.name,"allowed_extensions":[".txt"]})
            self.assertTrue(UploadHandler().validate({"file_ref":f.name,"approved_file_refs":[f.name],"allowed_extensions":[".txt"]}))
        self.assertTrue(DownloadHandler().validate({"path":"/safe/downloads/file.txt","name":"file.txt","complete":True},{"safe_directory":"/safe/downloads","expected_name":"file.txt"}))
    def test_tab_frame(self):
        self.assertEqual(self.b.switch_tab("BROWSER-001","TAB-001")["tab_id"],"TAB-001")
        self.assertEqual(self.b.switch_frame("BROWSER-001","FRAME-001")["frame_id"],"FRAME-001")
        with self.assertRaisesRegex(RuntimeError,"FRAME_NOT_FOUND"): self.b.switch_frame("BROWSER-001","NOPE")
    def test_loop_detection(self):
        d=LoopDetector(2);d.observe("A","S");d.observe("A","S")
        with self.assertRaisesRegex(RuntimeError,"LOOP_DETECTED"):d.observe("A","S")
    def test_evidence_hash_and_verification_requirement(self):
        ev=self.b.capture_evidence("BROWSER-001")
        self.assertTrue(ev["hash"]);self.assertEqual(ev["type"],"SCREENSHOT")
        # Browser Agent itself exposes an action result with evidence, but has no final-task
        # success gate; independent verification belongs to Part 07.
    def test_public_api_surface(self):
        for name in ["create_session","close_session","navigate","inspect_page","find_target",
                     "execute_action","upload","download","switch_tab","switch_frame",
                     "capture_evidence","health_check"]:
            self.assertTrue(callable(getattr(self.b,name)))
    def test_error_code_retry_policy(self):
        from recovery.recovery import RecoveryManager
        r=RecoveryManager(3)
        self.assertTrue(r.retryable("TARGET_NOT_FOUND"))
        self.assertTrue(r.retryable("BROWSER_CRASHED"))
        self.assertFalse(r.retryable("PERMISSION_BLOCKED"))
    def test_confidence_gate(self):
        self.assertTrue(ConfidenceGate(.75).allow(.75));self.assertFalse(ConfidenceGate(.75).allow(.74))
    def test_cleanup_after_failed_start(self):
        class Broken(MockBrowserAdapter):
            def create_context(self,sid): raise RuntimeError("BROWSER_START_FAILED")
        b=BrowserAgent(Broken())
        with self.assertRaisesRegex(RuntimeError,"BROWSER_START_FAILED"): b.create_session({"task_id":"T","session_id":"S"})
        self.assertEqual(b.controller.registry.sessions,{})
    def test_vision_fallback_reaches_confidence_gate(self):
        # Regression: structural/vision must be able to clear the default confidence
        # gate (0.75), or the vision-grounding fallback required by spec 5.8 is dead code.
        self.adapter.sessions["BROWSER-001"]["target_map"][("vision","icon-1")]="ICON"
        r=self.b.find_target("BROWSER-001",{"vision":"icon-1"})
        self.assertEqual(r["method"],"vision")
        self.assertGreaterEqual(r["confidence"],.75)
    def test_retryable_error_is_retried_then_succeeds(self):
        calls={"n":0}
        orig=self.adapter.find_target
        def flaky(sid,target):
            calls["n"]+=1
            return None if calls["n"]<2 else orig(sid,target)
        self.adapter.find_target=flaky
        r=self.b.execute_action("BROWSER-001",{"action_id":"ACT-R","action_type":"CLICK","target":{"role":"button","name":"Save"}})
        self.assertEqual(r["status"],"SUCCESS")
        self.assertEqual(calls["n"],2)
    def test_non_retryable_error_fails_fast(self):
        calls={"n":0}
        orig=self.adapter.find_target
        def counting(sid,target):
            calls["n"]+=1; return orig(sid,target)
        self.adapter.find_target=counting
        with self.assertRaisesRegex(RuntimeError,"PERMISSION_BLOCKED"):
            self.b.execute_action("BROWSER-001",{"action_type":"DELETE","target":{"role":"button","name":"Save"}})
        self.assertEqual(calls["n"],0)  # blocked before any locator attempt, no retry loop entered
    def test_keyboard_action_uses_keyboard_not_click(self):
        self.b.execute_action("BROWSER-001",{"action_id":"ACT-K","action_type":"KEYBOARD","key":"Enter"})
        self.assertIn(("KEYBOARD","Enter"),self.adapter.sessions["BROWSER-001"]["actions"])
    def test_redirect_to_disallowed_domain_is_blocked(self):
        class RedirectAdapter(MockBrowserAdapter):
            def navigate(self,sid,url,timeout_ms):
                super().navigate(sid,url,timeout_ms)
                return {"url":"https://evil.example/","redirected":True}
        b=BrowserAgent(RedirectAdapter())
        b.create_session({"task_id":"T","session_id":"S"})
        with self.assertRaisesRegex(RuntimeError,"NAVIGATION_BLOCKED"):
            b.navigate("S",{"url":"https://example.com","constraints":{"allowed_domains":["example.com"]}})
if __name__=="__main__":unittest.main()
