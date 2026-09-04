import sys,unittest,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from security_guard.guard import SecurityGuard
from permissions.policy import PermissionPolicy
from permissions.grants import GrantStore
from permissions.evaluator import PermissionEvaluator
from risk_engine.classifier import RiskClassifier
from approval.manager import ApprovalManager
from approval.request import ApprovalRequest
from credentials.vault import Vault
from credentials.redaction import Redactor
from network_policy.allowlist import Allowlist
from network_policy.policy import NetworkPolicy
from network_policy.request_guard import NetworkRequestGuard
from filesystem_policy.paths import PathPolicy
from filesystem_policy.operations import FilesystemPolicy
from plugin_security.manifest import PluginManifest
from plugin_security.capabilities import CapabilityChecker
from rate_limits.limiter import RateLimiter
from audit.integrity import AuditIntegrity
from audit.logger import AuditLogger
class E(unittest.TestCase):
 def test_red_action_flow(self):
  grants=GrantStore();grants.grant("desktop","filesystem.read","/tmp/*")
  perm=PermissionEvaluator(PermissionPolicy({"desktop":{"filesystem.read"}}),grants);audit=AuditLogger();ap=ApprovalManager()
  guard=SecurityGuard(RiskClassifier(),perm,ap,audit)
  a={"action_id":"D","task_id":"T","worker":"desktop","action_type":"DELETE","target":{"path":"/tmp/x"},"requested_capability":"filesystem.read"}
  self.assertEqual(guard.check(a).decision,"WAIT_FOR_APPROVAL")
if __name__=="__main__":unittest.main()
