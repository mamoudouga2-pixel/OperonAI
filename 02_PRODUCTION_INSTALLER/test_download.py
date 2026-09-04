from http.server import BaseHTTPRequestHandler,HTTPServer
import threading
from download_manager.downloader import Downloader
class H(BaseHTTPRequestHandler):
    payload=b"abcdef"*1000
    def do_GET(self):
        start=0; rng=self.headers.get("Range")
        if rng: start=int(rng.split("=")[1].split("-")[0])
        body=self.payload[start:]
        self.send_response(206 if start else 200); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self,*a): pass

def test_download(tmp_path):
    s=HTTPServer(("127.0.0.1",0),H); threading.Thread(target=s.serve_forever,daemon=True).start()
    try:
        out=tmp_path/"x.bin"; Downloader().download(f"http://127.0.0.1:{s.server_port}/x",out,expected_size=len(H.payload)); assert out.read_bytes()==H.payload
    finally:s.shutdown()
