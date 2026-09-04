import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from memory_manager.policy import MemoryPolicy
from memory_manager.router import MemoryRouter
from working_memory.state_store import StateStore
from working_memory.expiration import is_expired
from task_memory.checkpoint import CheckpointStore
from structured_storage.sqlite_adapter import SQLiteAdapter
from vector_storage.qdrant_adapter import QdrantAdapter
from long_term_memory.embedding import EmbeddingAdapter
from long_term_memory.semantic_store import SemanticStore
from user_preferences.preferences import Preferences
from retention.policy import RetentionPolicy
from forgetting.deletion import DeletionCoordinator
from privacy.classification import Classifier
from privacy.redaction import Redactor
class T(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.agent_scope="U1"
  self.db=SQLiteAdapter();self.v=QdrantAdapter();self.e=EmbeddingAdapter();self.s=SemanticStore(self.v,self.e)
  self.mem={"memory_id":"M1","user_scope":"U1","namespace":"preferences","type":"LONG_TERM_SEMANTIC","summary":"tea","provenance":{"source":"USER_EXPLICIT","task_id":"T1"},"retention_policy":"USER_CONTROLLED","sensitivity":"NORMAL"}
 def tearDown(self):self.tmp.cleanup()
 def test_policy(self):
  p=MemoryPolicy()
  with self.assertRaisesRegex(RuntimeError,"MEMORY_PROVENANCE_INVALID"):p.validate({"retention_policy":"USER_CONTROLLED","sensitivity":"NORMAL"})
  with self.assertRaisesRegex(RuntimeError,"MEMORY_SENSITIVITY_BLOCKED"):p.validate({**self.mem,"sensitivity":"SECRET"})
 def test_working_ttl(self):
  s=StateStore();s.upsert({"memory_id":"M","expires_at":"2000-01-01T00:00:00+00:00"});s.cleanup(is_expired);self.assertIsNone(s.get("M"))
 def test_checkpoint_safe_resume(self):
  c=CheckpointStore();c.save("T",["a"],["E"],1,"b","fp");self.assertEqual(c.resume("T","fp")["safe_resume_point"],"b")
  with self.assertRaisesRegex(RuntimeError,"MEMORY_WRITE_BLOCKED"):c.resume("T","changed")
 def test_sqlite(self):
  self.db.upsert(self.mem);self.assertEqual(self.db.get("M1")["memory_id"],"M1");self.db.delete("M1");self.assertIsNone(self.db.get("M1"))
 def test_vector_upsert_search_delete(self):
  self.s.upsert(self.mem);self.assertEqual(len(self.s.search("tea",{"user_scope":"U1"})),1);self.s.delete("M1");self.assertEqual(self.v.search("",{"user_scope":"U1"}),[])
 def test_namespace_scope(self):
  self.s.upsert(self.mem);m=dict(self.mem);m.update(memory_id="M2",user_scope="U2");self.s.upsert(m);self.assertEqual([x["id"] for x in self.s.search("tea",{"user_scope":"U1"})],["M1"])
 def test_preference_version(self):
  from structured_storage.repository import Repository
  p=Preferences(Repository(self.db));a=p.set(dict(self.mem,type="PREFERENCE"));b=p.set(a);self.assertEqual(b["version"],2)
 def test_secret_redaction(self):
  self.assertEqual(Classifier().classify("api_key=abc"),"SECRET");self.assertIn("[REDACTED]",Redactor().redact("api_key=abc"))
 def test_partial_delete(self):
  with self.assertRaisesRegex(RuntimeError,"DELETE_PARTIAL"):DeletionCoordinator().delete(["M"],{"a":lambda i:None,"b":lambda i:(_ for _ in ()).throw(Exception())})
 def test_retention_backup(self):
  self.assertTrue(RetentionPolicy().expired({"expires_at":"2000-01-01T00:00:00+00:00"}))
  from backup_recovery.backup import Backup
  from backup_recovery.restore import Restore
  f=Path(tempfile.mktemp());Backup().dump({"a":1},f);self.assertEqual(Restore().load(f),{"a":1});f.unlink()
 def test_router(self):self.assertEqual(MemoryRouter().route("PREFERENCE"),"structured")
if __name__=="__main__":unittest.main()
