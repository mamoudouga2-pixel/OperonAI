import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _pathfix  # noqa: F401

from backup_recovery.backup import Backup
from backup_recovery.restore import Restore
from errors import BackupRestoreFailed


class TestBackupRestore(unittest.TestCase):
    def test_plain_roundtrip(self):
        path = Path(tempfile.mktemp())
        Backup().dump({"a": 1}, path)
        self.assertEqual(Restore().load(path), {"a": 1})
        path.unlink()

    def test_encrypted_roundtrip_requires_key(self):
        path = Path(tempfile.mktemp())
        Backup(encryption_key="secret").dump({"a": 1}, path, encrypt=True)
        with self.assertRaises(BackupRestoreFailed):
            Restore().load(path)  # no key supplied
        restored = Restore().load(path, encryption_key="secret")
        self.assertEqual(restored, {"a": 1})
        path.unlink()

    def test_corrupted_backup_fails_checksum(self):
        path = Path(tempfile.mktemp())
        Backup(encryption_key="secret").dump({"a": 1}, path, encrypt=True)
        import json
        envelope = json.loads(path.read_text())
        envelope["ciphertext_hex"] = "00" + envelope["ciphertext_hex"][2:]
        path.write_text(json.dumps(envelope))
        with self.assertRaises(BackupRestoreFailed):
            Restore().load(path, encryption_key="secret")
        path.unlink()

    def test_missing_file_fails_cleanly(self):
        with self.assertRaises(BackupRestoreFailed):
            Restore().load("/no/such/file.json")


if __name__ == "__main__":
    unittest.main()
