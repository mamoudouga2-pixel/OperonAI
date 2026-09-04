import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from instruction_understanding.understander import InstructionUnderstander
from planner.planner import Planner
from task_decomposer.decomposer import TaskDecomposer
from decision_engine.engine import DecisionEngine
from approval_manager.approval import ApprovalManager
from supervisor.supervisor import Supervisor
from report_manager.report import ReportManager
from graph.runner import BossAgent

def make():
    return BossAgent(InstructionUnderstander(),Planner(),TaskDecomposer(),DecisionEngine(),ApprovalManager(),Supervisor(2),ReportManager())

class T(unittest.TestCase):
    def test_structured_plan(self):
        x=make(); r=x.run("open browser and check page",target="browser",expected_result="verified",step_results={1:{"success":True,"evidence":"ev1"}})
        self.assertEqual(r["task_outcome"],"SUCCESS");self.assertTrue(r["final_verification_status"])
    def test_clarification(self):
        r=make().run("do task",target=None,expected_result="done")
        self.assertEqual(r["task_outcome"],"CLARIFICATION_REQUIRED")
    def test_worker_selection(self):
        d=DecisionEngine()
        self.assertEqual(d.worker_for({"action":"browser work"}),"Browser Agent")
        self.assertEqual(d.worker_for({"action":"local file"}),"Desktop Agent")
        self.assertEqual(d.worker_for({"action":"memory retrieval"}),"Memory System")
        self.assertEqual(d.worker_for({"action":"permission decision"}),"Security System")
    def test_red_pauses(self):
        x=make()
        r=x.run("dangerous action",target="x",expected_result="done",steps=[{"action":"delete","risk":"RED"}])
        self.assertEqual(r["task_outcome"],"WAITING_APPROVAL")
        r=x.run("dangerous action",target="x",expected_result="done",steps=[{"action":"delete","risk":"RED"}],approval="APPROVED",step_results={1:{"success":True,"evidence":"approved-evidence"}})
        self.assertEqual(r["task_outcome"],"SUCCESS")
    def test_approval_manager(self):
        a=ApprovalManager();self.assertFalse(a.request({"risk":"RED","action":"delete"}))
        self.assertEqual(a.pending["status"],"WAITING_APPROVAL")
        self.assertTrue(a.resolve("APPROVED"))
    def test_evidence_required(self):
        x=make();r=x.run("verify task",target="check",expected_result="done",step_results={1:{"success":True,"evidence":None}})
        self.assertEqual(r["task_outcome"],"FAILED")
    def test_loop_prevention(self):
        s=Supervisor(2)
        self.assertTrue(s.recoverable("A"));self.assertFalse(s.recoverable("A"))
        self.assertTrue(s.recoverable("B"));self.assertFalse(s.recoverable("C"))
    def test_state_machine(self):
        from supervisor.state import SupervisorState
        s=SupervisorState()
        for n in ["UNDERSTANDING","PLANNING","SECURITY_CHECK","EXECUTING","VERIFYING","SUCCESS"]:s.transition(n)
        self.assertIn("SUCCESS",s.TERMINAL)
        with self.assertRaises(RuntimeError):s.transition("EXECUTING")
    def test_recovery_never_reuses_failed_evidence(self):
        x=make()
        results={1:{"success":False,"evidence":"E1"},(1,2):{"success":True,"evidence":"E2"}}
        r=x.run("recover task",target="x",expected_result="done",step_results=results)
        self.assertEqual(r["task_outcome"],"SUCCESS")
        self.assertEqual(r["evidence_references"],["E2"])
        self.assertEqual(len(r["recovery_attempts"]),1)

    def test_report_fields(self):
        r=ReportManager().build(outcome="SUCCESS",steps=[],approvals=[],evidence=["x"],recovery=[],verification=True)
        for k in ["task_outcome","completed_failed_skipped_steps","approvals_used","evidence_references","recovery_attempts","final_verification_status"]:
            self.assertIn(k,r)
if __name__=="__main__":unittest.main()
