import sys,unittest,tempfile,copy,datetime
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
from plugin_security.isolation import PluginIsolation
from rate_limits.limiter import RateLimiter
from audit.integrity import AuditIntegrity
from audit.logger import AuditLogger
from incident.detector import IncidentDetector
from incident.response import IncidentResponse

class T(unittest.TestCase):
 def action(self,typ="LIST_DIRECTORY",path=None,cap="filesystem.read"):
  return {"action_id":"A1","task_id":"T1","worker":"desktop","action_type":typ,"target":{"path":path or str(Path(self.tmp.name)/"a.txt")},"requested_capability":cap}
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.grants=GrantStore();self.grants.grant("desktop","filesystem.read",str(Path(self.tmp.name)/"*"))
  self.policy=PermissionPolicy({"desktop":{"filesystem.read"}});self.perm=PermissionEvaluator(self.policy,self.grants)
  self.audit=AuditLogger();self.ap=ApprovalManager();self.guard=SecurityGuard(RiskClassifier(),self.perm,self.ap,self.audit)
 def tearDown(self):self.tmp.cleanup()

 def test_allow_and_deny(self):self.assertEqual(self.guard.check(self.action()).decision,"ALLOW");self.assertEqual(self.guard.check(self.action(cap="filesystem.write")).decision,"DENY")
 def test_red_requires_approval(self):
  a=self.action("DELETE",cap="filesystem.read");self.assertEqual(self.guard.check(a).decision,"WAIT_FOR_APPROVAL")
 def test_fingerprint(self):
  a=self.action("DELETE");b=dict(a);b["target"]={"path":a["target"]["path"]+"/other"};self.assertNotEqual(ApprovalRequest.fingerprint(a),ApprovalRequest.fingerprint(b))
 def test_scope_escape(self):
  with self.assertRaises(RuntimeError):PathPolicy([self.tmp.name]).validate("/etc")
 def test_symlink_escape(self):
  outside=tempfile.TemporaryDirectory()
  link=Path(self.tmp.name)/"escape"
  link.symlink_to(outside.name)
  with self.assertRaises(RuntimeError):PathPolicy([self.tmp.name]).validate(str(link/"secret.txt"))
  outside.cleanup()
 def test_secret(self):self.assertIn("[REDACTED]",Redactor().redact("password=abc api_key=xyz token=1"))
 def test_credential_auth(self):
  v=Vault();v.store("k","secret")
  with self.assertRaisesRegex(RuntimeError,"CREDENTIAL_ACCESS_DENIED"):v.retrieve_for_authorized_use("k")
  self.assertEqual(v.retrieve_for_authorized_use("k",True),"secret")
 def test_credential_access_blocked_is_audited_and_redacted(self):
  redactor=lambda x:{**x,"data":{**x.get("data",{}),"key":Redactor().redact(f"password={x['data'].get('key','')}")}}
  audit=AuditLogger(redactor=redactor);v=Vault(audit=audit);v.store("k","secret")
  a=self.action()
  with self.assertRaises(RuntimeError):v.retrieve_for_authorized_use("k",False,a)
  self.assertEqual(audit.records[-1]["event"],"CREDENTIAL_ACCESS_BLOCKED")
  self.assertIn("[REDACTED]",audit.records[-1]["data"]["key"])
 def test_network(self):
  g=NetworkRequestGuard(NetworkPolicy(Allowlist({"example.com"})));a=self.action();a["target"]={"domain":"example.com","protocol":"https","redirects":0};self.assertTrue(g.validate(a));a["target"]["domain"]="evil.com";self.assertFalse(g.validate(a))
 def test_network_redirect_and_size_limits(self):
  g=NetworkRequestGuard(NetworkPolicy(Allowlist({"example.com"}),max_redirects=1,max_size=100,max_duration=10))
  a=self.action();a["target"]={"domain":"example.com","protocol":"https","redirects":5};self.assertFalse(g.validate(a))
  a["target"]={"domain":"example.com","protocol":"https","size":1000};self.assertFalse(g.validate(a))
  a["target"]={"domain":"example.com","protocol":"https","duration":999};self.assertFalse(g.validate(a))
  a["target"]={"domain":"example.com","protocol":"https","redirects":1,"size":10,"duration":1};self.assertTrue(g.validate(a))
 def test_plugin(self):
  m=PluginManifest("p",{"browser.read"});self.assertTrue(CapabilityChecker().allowed(m,"browser.read"));self.assertFalse(CapabilityChecker().allowed(m,"filesystem.write"))
 def test_plugin_undeclared_capability_denied_via_guard(self):
  iso=PluginIsolation(CapabilityChecker())
  guard=SecurityGuard(RiskClassifier(),self.perm,self.ap,self.audit,plugins=iso)
  a=self.action();a["target"]["manifest"]=PluginManifest("p",{"filesystem.read"})
  d=guard.check(a);self.assertEqual(d.decision,"ALLOW")
  b=self.action();b["target"]["manifest"]=PluginManifest("p2",{"browser.read"})
  d2=guard.check(b);self.assertEqual(d2.decision,"DENY");self.assertIn("PLUGIN_CAPABILITY_DENIED",d2.reasons)
  # Direct isolation check (undeclared capability must be denied)
  self.assertFalse(iso.allowed({"target":{"manifest":PluginManifest("p3",{"browser.read"})},"requested_capability":"filesystem.write"}))
 def test_rate(self):
  l=RateLimiter(max_actions=1);l.consume("T")
  with self.assertRaisesRegex(RuntimeError,"RATE_LIMIT_EXCEEDED"):l.consume("T")
 def test_rate_limit_is_audited(self):
  audit=AuditLogger();l=RateLimiter(max_actions=1,audit=audit)
  a=self.action();l.consume("T2","actions",a)
  with self.assertRaises(RuntimeError):l.consume("T2","actions",a)
  self.assertEqual(audit.records[-1]["event"],"RATE_LIMIT_EXCEEDED")
 def test_audit(self):self.audit.log("SECURITY_CHECK_STARTED",self.action());self.assertTrue(AuditIntegrity().verify(self.audit.records))
 def test_audit_tamper_detected(self):
  self.audit.log("SECURITY_CHECK_STARTED",self.action())
  self.audit.log("SECURITY_DECISION_ALLOW",self.action())
  self.assertTrue(AuditIntegrity().verify(self.audit.records))
  tampered=copy.deepcopy(self.audit.records)
  tampered[0]["event"]="SECURITY_DECISION_ALLOW"  # simulate a log rewrite
  self.assertFalse(AuditIntegrity().verify(tampered))
 def test_audit_missing_record_detected(self):
  self.audit.log("SECURITY_CHECK_STARTED",self.action())
  self.audit.log("SECURITY_DECISION_ALLOW",self.action())
  self.audit.log("SECURITY_CHECK_STARTED",self.action())
  truncated=[self.audit.records[0],self.audit.records[2]]
  self.assertFalse(AuditIntegrity().verify(truncated))
 def test_approval_expiry(self):
  ap=ApprovalManager(audit=self.audit)
  a=self.action("DELETE",cap="filesystem.read")
  past=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(minutes=1)).isoformat()
  ap.create("APR-X","T1",a,"delete","RED",past,past)
  ap.grant("APR-X",a)
  self.assertFalse(ap.matches(a))
  self.assertEqual(ap.items["APR-X"]["status"],"EXPIRED")
  self.assertIn("APPROVAL_EXPIRED",[r["event"] for r in self.audit.records])
 def test_incident_response_notifies_and_audits(self):
  audit=AuditLogger();resp=IncidentResponse().respond(self.action(),audit)
  self.assertEqual(resp["action"],"STOP");self.assertTrue(resp["notify_core"])
  self.assertEqual(audit.records[-1]["event"],"SECURITY_INCIDENT_DETECTED")
  self.assertTrue(IncidentDetector().detect({"severity":"SUSPICIOUS"}))
  self.assertFalse(IncidentDetector().detect({"severity":"INFO"}))
 def test_fail_closed(self):
  g=SecurityGuard(RiskClassifier(),self.perm,self.ap,self.audit,service_available=False)
  with self.assertRaisesRegex(RuntimeError,"SECURITY_SERVICE_UNAVAILABLE"):g.check(self.action())

if __name__=="__main__":unittest.main()
