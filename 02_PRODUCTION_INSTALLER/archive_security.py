from pathlib import Path
import os, zipfile, tarfile
from common.errors import VerificationError

def safe_member(root:Path, name:str)->Path:
    if not name or os.path.isabs(name): raise VerificationError('Absolute archive path rejected','SEC_ARCHIVE_PATH_TRAVERSAL')
    candidate=(root/name).resolve(); base=root.resolve()
    if candidate!=base and base not in candidate.parents: raise VerificationError(f'Unsafe archive path: {name}','SEC_ARCHIVE_PATH_TRAVERSAL')
    return candidate

def safe_extract(archive, destination):
    archive=Path(archive); destination=Path(destination); destination.mkdir(parents=True,exist_ok=True)
    if archive.suffix=='.zip':
        with zipfile.ZipFile(archive) as z:
            for info in z.infolist(): safe_member(destination,info.filename)
            z.extractall(destination)
    elif str(archive).endswith(('.tar','.tar.gz','.tgz')):
        with tarfile.open(archive) as t:
            for m in t.getmembers():
                target=safe_member(destination,m.name)
                if m.issym() or m.islnk(): raise VerificationError('Symlink in archive rejected','SEC_ARCHIVE_PATH_TRAVERSAL')
            t.extractall(destination,filter='data' if 'filter' in tarfile.TarFile.extractall.__code__.co_varnames else None)
    else: raise VerificationError('Unsupported archive format','SEC_MANIFEST_INVALID')
    return destination
