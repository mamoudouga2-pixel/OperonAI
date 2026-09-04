from urllib.parse import urlparse
from common.errors import DownloadError

def validate_url(url, allowed_hosts=None, require_https=True):
    p=urlparse(url)
    if p.scheme not in ('https','http') or not p.netloc: raise DownloadError('Invalid download URL','DL_SOURCE_UNAVAILABLE')
    if require_https and p.scheme!='https' and p.hostname not in {'127.0.0.1','localhost'}: raise DownloadError('HTTPS required','SEC_UNTRUSTED_SOURCE')
    if allowed_hosts and p.hostname not in set(allowed_hosts): raise DownloadError('Untrusted source','SEC_UNTRUSTED_SOURCE')
    return p

def validate_redirect(original, final_url, allowed_hosts=None):
    return validate_url(final_url,allowed_hosts=allowed_hosts,require_https=True)
