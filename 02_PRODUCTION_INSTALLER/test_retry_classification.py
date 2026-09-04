from download_manager.downloader import RETRYABLE_HTTP
def test_retryable_codes(): assert 503 in RETRYABLE_HTTP and 404 not in RETRYABLE_HTTP
