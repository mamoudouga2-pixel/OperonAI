from pathlib import Path
from download_manager.downloader import Downloader
from artifact_manager.validator import validate_file
from artifact_manager.archive_security import safe_extract
class Redownloader:
    def __init__(self,downloader=None): self.downloader=downloader or Downloader()
    def fetch(self,url,destination,sha256=None,signature=None,public_key=None,size=None):
        p=self.downloader.download(url,destination+'.download',expected_size=size,expected_sha256=sha256)
        validate_file(p,sha256,signature,public_key); Path(p).replace(destination); return Path(destination)
