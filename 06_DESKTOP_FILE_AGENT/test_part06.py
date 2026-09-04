import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from path_policy import PathPolicy
from files import FileAgent
from desktop import DesktopController
from security import SecurityGate
from workflow import WorkflowRecorder, WorkflowSerializer, ReplayValidator
from recovery import RetryPolicy, LoopDetector, Recovery
from adapter import MockAdapter, ScreenObserver
from application import ApplicationLauncher
from input_controller import InputController, CancellationToken
from errors import E


class T(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.r = Path(self.t.name)
        self.r.joinpath("a.txt").write_text("hello")
        self.f = FileAgent(PathPolicy([self.r]))

    def tearDown(self):
        self.t.cleanup()

    # ---------------------------------------------------------- file ops --
    def test_list_and_bound(self):
        self.assertTrue(any(x["name"] == "a.txt" for x in self.f.scan(self.r)))

    def test_mkdir(self):
        self.assertTrue(self.f.mkdir(self.r, "cat").is_dir())

    def test_mkdir_invalid_name(self):
        with self.assertRaisesRegex(RuntimeError, E.PATH_NOT_ALLOWED):
            self.f.mkdir(self.r, "../escape")

    def test_copy_source_preserved(self):
        x = self.f.copy(self.r / "a.txt", self.r / "b.txt")
        self.assertEqual(x["status"], "SUCCESS")
        self.assertTrue((self.r / "a.txt").exists())

    def test_copy_conflict(self):
        (self.r / "b.txt").write_text("x")
        with self.assertRaisesRegex(RuntimeError, E.DESTINATION_EXISTS):
            self.f.copy(self.r / "a.txt", self.r / "b.txt")

    def test_move(self):
        self.f.move(self.r / "a.txt", self.r / "c.txt")
        self.assertFalse((self.r / "a.txt").exists())
        self.assertTrue((self.r / "c.txt").exists())

    def test_rename_conflict(self):
        (self.r / "b.txt").write_text("x")
        with self.assertRaisesRegex(RuntimeError, E.DESTINATION_EXISTS):
            self.f.rename(self.r / "a.txt", "b.txt")

    def test_rename_invalid_name(self):
        with self.assertRaisesRegex(RuntimeError, E.RENAME_FAILED):
            self.f.rename(self.r / "a.txt", "../evil.txt")

    # --------------------------------------------------------- path policy --
    def test_traversal_block(self):
        with self.assertRaisesRegex(RuntimeError, E.PATH_NOT_ALLOWED):
            self.f.scan(self.r / "../")

    def test_restricted_root(self):
        q = self.r / "system"
        q.mkdir()
        g = FileAgent(PathPolicy([self.r], [q]))
        with self.assertRaisesRegex(RuntimeError, E.PATH_NOT_ALLOWED):
            g.scan(q)

    def test_restricted_subtree_pruned_during_scan(self):
        # restricted dir lives *underneath* an allowed root: scanning the
        # allowed root must skip it instead of only checking the top call.
        secret = self.r / "private"
        secret.mkdir()
        (secret / "s.txt").write_text("secret")
        g = FileAgent(PathPolicy([self.r], [secret]))
        names = {x["name"] for x in g.scan(self.r)}
        self.assertIn("private", names)  # the dir entry itself is listed
        self.assertNotIn("s.txt", names)  # but its contents are not

    def test_invalid_path_rejected(self):
        with self.assertRaisesRegex(RuntimeError, E.PATH_NOT_ALLOWED):
            self.f.mkdir(self.r, "sub/../../escape")

    def test_large_directory_bound(self):
        for i in range(10):
            (self.r / f"f{i}.txt").write_text("x")
        bounded = FileAgent(PathPolicy([self.r]), max_items=3)
        self.assertLessEqual(len(bounded.scan(self.r)), 3)

    # -------------------------------------------------------- permissions --
    @unittest.skipIf(os.geteuid() == 0, "root bypasses permission checks")
    def test_permission_denied(self):
        blocked = self.r / "blocked"
        blocked.mkdir()
        (blocked / "x.txt").write_text("x")
        blocked.chmod(0o000)
        try:
            with self.assertRaisesRegex(RuntimeError, E.PERMISSION_DENIED):
                self.f.scan(blocked)
        finally:
            blocked.chmod(stat.S_IRWXU)

    def test_locked_file(self):
        locked_agent = FileAgent(PathPolicy([self.r]), is_locked=lambda p: p.name == "a.txt")
        with self.assertRaisesRegex(RuntimeError, E.FILE_LOCKED):
            locked_agent.move(self.r / "a.txt", self.r / "c.txt")
        self.assertTrue(RetryPolicy().can_retry(E.FILE_LOCKED, 0))

    # ------------------------------------------------------------ delete --
    def test_delete_blocked(self):
        with self.assertRaisesRegex(RuntimeError, E.DELETE_BLOCKED):
            SecurityGate({}).delete("APPROVED")

    # -------------------------------------------------- session / window --
    def test_session_and_window(self):
        d = DesktopController()
        s = d.create("T", "S")
        self.assertEqual(s.task_id, "T")
        with self.assertRaisesRegex(RuntimeError, E.WINDOW_NOT_FOUND):
            d.require_window("S", "editor")

    def test_application_launch(self):
        d = DesktopController()
        d.create("T", "S")
        adapter = MockAdapter(launchable={"/apps/editor"})
        sec = SecurityGate({"editor": "/apps/editor"})
        launcher = ApplicationLauncher(sec, adapter, d)
        window = launcher.launch("S", "editor")
        self.assertEqual(window["app"], "/apps/editor")
        self.assertEqual(d.sessions["S"].focused_application, "editor")

    def test_application_not_found(self):
        d = DesktopController()
        d.create("T", "S")
        launcher = ApplicationLauncher(SecurityGate({}), MockAdapter(), d)
        with self.assertRaisesRegex(RuntimeError, E.APPLICATION_NOT_FOUND):
            launcher.launch("S", "unknown")

    def test_wrong_window_prevention(self):
        d = DesktopController()
        d.create("T", "S")
        d.set_window("S", {"app": "notepad"}, "notepad")
        adapter = MockAdapter()
        ctl = InputController(adapter, d, "S", expected_app="editor")
        with self.assertRaisesRegex(RuntimeError, E.WINDOW_NOT_FOUND):
            ctl.click((10, 10))
        self.assertEqual(adapter.clicks, [])  # nothing was actually sent

    def test_mouse_cancellation(self):
        d = DesktopController()
        d.create("T", "S")
        d.set_window("S", {"app": "editor"}, "editor")
        adapter = MockAdapter()
        ctl = InputController(adapter, d, "S", expected_app="editor")
        token = CancellationToken()
        token.cancel()
        with self.assertRaisesRegex(RuntimeError, E.ACTION_TIMEOUT):
            ctl.click((1, 1), token=token)
        self.assertEqual(adapter.clicks, [])

    def test_focus_recovery(self):
        d = DesktopController()
        d.create("T", "S")
        adapter = MockAdapter(launchable={"editor"})
        s = d.recover_focus("S", adapter, "editor")
        self.assertEqual(s.focused_application, "editor")

    # -------------------------------------------------------------- screen --
    def test_screen_observation_failure(self):
        obs = ScreenObserver(MockAdapter(fail_screenshot=True))
        with self.assertRaisesRegex(RuntimeError, E.SCREEN_OBSERVATION_FAILED):
            obs.capture()

    def test_screen_observation_evidence(self):
        obs = ScreenObserver(MockAdapter())
        rec = obs.capture()
        self.assertIsNotNone(rec["hash"])
        self.assertTrue(rec["evidence_id"].startswith("EVID-"))

    # ----------------------------------------------------- retry / loop --
    def test_retry_loop(self):
        self.assertTrue(RetryPolicy().can_retry(E.FILE_LOCKED, 0))
        self.assertFalse(RetryPolicy().can_retry(E.PERMISSION_DENIED, 0))
        loop = LoopDetector(2)
        loop.observe("A", "S")
        loop.observe("A", "S")
        with self.assertRaisesRegex(RuntimeError, E.LOOP_DETECTED):
            loop.observe("A", "S")

    def test_recovery_bounded_then_raises(self):
        calls = {"n": 0}

        def always_locked():
            calls["n"] += 1
            raise RuntimeError(E.FILE_LOCKED)

        rec = Recovery(RetryPolicy(max_retries=2), LoopDetector(10))
        with self.assertRaisesRegex(RuntimeError, E.FILE_LOCKED):
            rec.run("LOCK_TEST", always_locked)
        self.assertEqual(calls["n"], 3)  # 1 initial + 2 retries, then stop

    def test_recovery_verification_failure(self):
        rec = Recovery(RetryPolicy(), LoopDetector(10))
        with self.assertRaisesRegex(RuntimeError, E.VERIFICATION_REQUIRED):
            rec.run("VERIFY_TEST", lambda: "done", verify=lambda r: False)

    def test_crash_recovery_no_duplicate_move(self):
        # Simulate: worker moved the file, then crashed before reporting.
        # A naive re-run of move() would raise FILE_NOT_FOUND on source.
        # move_idempotent() must recognise the destination already matches.
        self.f.move(self.r / "a.txt", self.r / "moved.txt")
        result = self.f.move_idempotent(self.r / "a.txt", self.r / "moved.txt")
        self.assertEqual(result["status"], "SUCCESS")
        self.assertFalse(result["changed"])

    # -------------------------------------------------------------- workflow --
    def test_replay(self):
        w = {"environment_preconditions": {"application": "editor", "target_state": "ready"}}
        with self.assertRaisesRegex(RuntimeError, E.WORKFLOW_REPLAY_UNSAFE):
            ReplayValidator().validate(w, {"application": "editor", "target_state": "changed"})

    def test_replay_non_idempotent_step_blocked(self):
        step = {"idempotent": False, "expected_precondition": "empty"}
        with self.assertRaisesRegex(RuntimeError, E.WORKFLOW_REPLAY_UNSAFE):
            ReplayValidator().validate_step(step, current_target_state="not-empty")

    def test_workflow_record_and_serialize_roundtrip(self):
        rec = WorkflowRecorder()
        rec.record({"action_type": "MOVE", "source": "a", "destination": "b"})
        w = rec.build({"application": "editor"}, {"file": "b"}, ["postcondition_exists"])
        text = WorkflowSerializer.dumps(w)
        back = WorkflowSerializer.loads(text)
        self.assertEqual(back["steps"][0]["action_type"], "MOVE")

    # -------------------------------------------------------------- contract --
    def test_result_contract(self):
        r = self.f.copy(self.r / "a.txt", self.r / "z.txt")
        for k in ["action_id", "status", "changed", "evidence_ids", "data", "error"]:
            self.assertIn(k, r)
        self.assertTrue(r["evidence_ids"][0].startswith("EVID-"))


if __name__ == "__main__":
    unittest.main()
