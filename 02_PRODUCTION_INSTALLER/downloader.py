from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import time, hashlib, json
from .download_state import DownloadState
from .resume import range_header
from .retry import RetryPolicy
from .progress import ProgressEvent
from .bandwidth import BandwidthLimiter
from .http_policy import validate_url
from common.errors import DownloadError

RETRYABLE_HTTP={408,425,429,500,502,503,504}
class Downloader:
    def __init__(self,retry=None,timeout=30,bandwidth=None,allowed_hosts=None,max_redirects=3):
        self.retry=retry or RetryPolicy(); self.timeout=timeout; self.bandwidth=BandwidthLimiter(bandwidth); self.allowed_hosts=allowed_hosts; self.max_redirects=max_redirects
    def _request(self,url,offset):
        validate_url(url,self.allowed_hosts,True)
        return Request(url,headers=range_header(offset),method='GET')
    def download(self,url,destination,state_path=None,expected_size=None,expected_sha256=None,on_progress=None,metadata_path=None,source_identity=None):
        dest=Path(destination); dest.parent.mkdir(parents=True,exist_ok=True); part=dest.with_suffix(dest.suffix+'.part'); meta=Path(metadata_path) if metadata_path else part.with_suffix(part.suffix+'.json')
        old={};
        if meta.exists():
            try: old=json.loads(meta.read_text())
            except Exception: old={}
        offset=part.stat().st_size if part.exists() else 0
        if offset and old.get('url')!=url: offset=0; part.unlink(missing_ok=True)
        state=DownloadState(url,str(dest),offset,expected_size or 0,old.get('etag',''),'partial' if offset else 'starting')
        if state_path: state.save(state_path)
        started=time.monotonic()
        def op():
            nonlocal offset
            req=self._request(url,offset)
            try:
                with urlopen(req,timeout=self.timeout) as r:
                    status=getattr(r,'status',200); etag=r.headers.get('ETag')
                    if offset and status!=206:
                        offset=0; part.unlink(missing_ok=True);
                        req=self._request(url,0)
                        with urlopen(req,timeout=self.timeout) as r2: return self._stream(r2,part,0,expected_size,on_progress,started,meta,url)
                    total=int(r.headers.get('Content-Length','0') or 0)+(offset if status==206 else 0)
                    if expected_size is not None and total and total!=expected_size: raise DownloadError(f'Content length mismatch: {total}!={expected_size}','DL_SIZE_MISMATCH')
                    result=self._stream(r,part,offset,expected_size,on_progress,started,meta,url)
                    meta.write_text(json.dumps({'url':url,'etag':etag,'last_modified':r.headers.get('Last-Modified'),'bytes':result[0]}))
                    return result
            except HTTPError as e:
                if e.code not in RETRYABLE_HTTP: raise
                raise
        try: downloaded,total=self.retry.run(op)
        except Exception as e:
            if state_path: state.status='failed'; state.bytes_downloaded=part.stat().st_size if part.exists() else 0; state.save(state_path)
            raise DownloadError(str(e),'DL_NETWORK_FAILED') from e
        if expected_size is not None and downloaded!=expected_size: raise DownloadError(f'Incomplete download: {downloaded}/{expected_size}','DL_SIZE_MISMATCH')
        if expected_sha256:
            h=hashlib.sha256();
            with part.open('rb') as f:
                for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
            if h.hexdigest().lower()!=expected_sha256.lower(): raise DownloadError('Checksum mismatch','SEC_CHECKSUM_MISMATCH')
        import os; os.replace(part,dest); meta.unlink(missing_ok=True)
        if state_path: state.bytes_downloaded=downloaded; state.total_bytes=expected_size or total; state.status='completed'; state.save(state_path)
        return dest
    def _stream(self,r,part,offset,expected_size,on_progress,started,meta,url):
        mode='ab' if offset else 'wb'; downloaded=offset; part.parent.mkdir(parents=True,exist_ok=True)
        with part.open(mode) as f:
            while True:
                chunk=r.read(1024*1024)
                if not chunk: break
                f.write(chunk); downloaded+=len(chunk); self.bandwidth.consume(len(chunk))
                meta.write_text(json.dumps({'url':url,'bytes':downloaded,'etag':r.headers.get('ETag')}))
                elapsed=max(time.monotonic()-started,0.001); speed=downloaded/elapsed; eta=((expected_size-downloaded)/speed) if expected_size and speed>0 else None
                if on_progress: on_progress(ProgressEvent(downloaded,expected_size or int(r.headers.get('Content-Length','0') or 0),speed,eta))
        return downloaded,expected_size or downloaded
