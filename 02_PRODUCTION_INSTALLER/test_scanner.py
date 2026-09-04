from repair_system.scanner import RepairScanner
from artifact_manager.checksum import sha256_file

def test_scanner(tmp_path):
    (tmp_path/"a").write_text("ok"); h=sha256_file(tmp_path/"a"); assert RepairScanner().scan(tmp_path,{"a":h})==[]; (tmp_path/"a").write_text("bad"); assert RepairScanner().scan(tmp_path,{"a":h})[0]["issue"]=="corrupted"
