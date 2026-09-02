import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orchestrator import CoreOrchestrator
from communication.protocols import Event, FailureReport
from module_manager.manifest import ModuleManifest
from configuration.config import CoreConfig

class CoreAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.core = CoreOrchestrator(self.tmp.name)

    def tearDown(self):
        self.core.shutdown(); self.tmp.cleanup()

    def test_application_lifecycle(self):
        self.core.start(); self.assertEqual(self.core.app_controller.state, "RUNNING")
        self.core.pause(); self.assertEqual(self.core.app_controller.state, "PAUSED")
        self.core.resume(); self.assertEqual(self.core.app_controller.state, "RUNNING")

    def test_task_lifecycle_and_terminal_lock(self):
        t = self.core.task_manager.create_task("test")
        self.core.task_manager.transition(t.task_id, "PLANNING")
        self.core.task_manager.transition(t.task_id, "RUNNING")
        self.core.task_manager.transition(t.task_id, "VERIFYING")
        self.core.task_manager.complete_task(t.task_id)
        self.assertEqual(t.state, "SUCCESS")
        with self.assertRaises(ValueError): self.core.task_manager.transition(t.task_id, "RUNNING")

    def test_invalid_transition_is_audited(self):
        t = self.core.task_manager.create_task("test")
        with self.assertRaises(ValueError): self.core.task_manager.transition(t.task_id, "SUCCESS")
        self.assertIn("INVALID_STATE_TRANSITION",
                      (Path(self.tmp.name)/"audit.jsonl").read_text(encoding="utf-8"))

    def test_event_bus_and_limits(self):
        seen=[]
        self.core.event_bus.subscribe("demo", lambda e: seen.append(e.payload["x"]))
        self.core.event_bus.publish(Event("demo", {"x": 9}))
        self.assertEqual(seen,[9])
        limited = CoreOrchestrator(self.tmp.name + "/limited", CoreConfig(event_payload_limit=20))
        with self.assertRaises(ValueError):
            limited.event_bus.publish(Event("big", {"x":"a"*100}))
        limited.shutdown()

    def test_manifest_validation(self):
        m = ModuleManifest.from_dict({
            "module_id":"worker_x","version":"1.0","api_version":"1",
            "capabilities":["demo"],"permissions":[]
        })
        self.assertEqual(m.module_id,"worker_x")
        with self.assertRaises(ValueError):
            ModuleManifest.from_dict({"module_id":"bad"})

    def test_worker_failure_recovery(self):
        calls={"n":0}
        def start():
            calls["n"] += 1
            if calls["n"] == 1: raise RuntimeError("crash")
        self.core.module_manager.register({
            "module_id":"worker_x","version":"1.0","api_version":"1",
            "capabilities":["demo"],"permissions":[]
        }, start_fn=start, stop_fn=lambda:None, health_fn=lambda:True)
        self.core.start()
        self.assertFalse(self.core.module_manager.start("worker_x"))
        self.assertTrue(self.core.module_manager.health_check("worker_x")["healthy"])

    def test_fail_closed(self):
        self.core.module_manager.register({
            "module_id":"safe","version":"1","api_version":"1",
            "capabilities":["demo"],"permissions":[]
        })
        r=self.core.module_manager.handle_failure(
            FailureReport("safe","permission uncertain",permission_uncertain=True))
        self.assertEqual(r["action"],"fail_closed")
        self.assertEqual(self.core.module_manager.status("safe"),"FAIL_CLOSED")

    def test_retry_budget(self):
        c=CoreConfig(max_task_retries=1)
        self.core.shutdown()
        self.core=CoreOrchestrator(self.tmp.name+"/r2", c)
        t=self.core.task_manager.create_task("retry")
        self.assertEqual(self.core.task_manager.increment_retry(t.task_id),1)
        with self.assertRaises(RuntimeError): self.core.task_manager.increment_retry(t.task_id)

    def test_restart_health_and_stop(self):
        calls = {"start": 0, "stop": 0}
        def start(): calls["start"] += 1
        def stop(): calls["stop"] += 1
        self.core.module_manager.register({"module_id":"restartable","version":"1","api_version":"1","capabilities":["demo"],"permissions":[]}, start_fn=start, stop_fn=stop, health_fn=lambda: True)
        self.assertTrue(self.core.module_manager.start("restartable"))
        self.assertTrue(self.core.module_manager.restart("restartable"))
        self.assertGreaterEqual(calls["start"], 2)
        self.assertGreaterEqual(calls["stop"], 1)
        self.assertTrue(self.core.module_manager.health_check("restartable")["healthy"])

    def test_cancellation_and_timeout(self):
        cancelled = self.core.task_manager.create_task("cancel")
        self.core.task_manager.cancel_task(cancelled.task_id)
        self.assertEqual(cancelled.state, "CANCELLED")
        timed = self.core.task_manager.create_task("timeout")
        self.core.task_manager.transition(timed.task_id, "PLANNING")
        self.core.task_manager.transition(timed.task_id, "RUNNING")
        self.core.task_manager.timeout_task(timed.task_id)
        self.assertEqual(timed.state, "TIMEOUT")

    def test_event_unsubscribe_and_health_all(self):
        seen=[]
        handler=lambda e: seen.append(e.payload)
        self.core.event_bus.subscribe("x", handler)
        self.core.event_bus.publish(Event("x", {"v":1}))
        self.core.event_bus.unsubscribe("x", handler)
        self.core.event_bus.publish(Event("x", {"v":2}))
        self.assertEqual(seen, [{"v":1}])
        self.core.module_manager.register({"module_id":"healthy","version":"1","api_version":"1","capabilities":["demo"],"permissions":[]}, health_fn=lambda: True)
        self.assertTrue(self.core.health_monitor.check_all()["healthy"]["healthy"])

    def test_persistence(self):
        t=self.core.task_manager.create_task("persist")
        self.assertEqual(self.core.state_store.get_task(t.task_id)["state"],"NEW")

if __name__=="__main__": unittest.main()
