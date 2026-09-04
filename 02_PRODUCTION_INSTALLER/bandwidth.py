import time
class BandwidthLimiter:
    def __init__(self,bytes_per_second=None): self.rate=bytes_per_second; self.started=time.monotonic(); self.sent=0
    def consume(self,n):
        if not self.rate:return
        self.sent+=n; expected=self.sent/self.rate; actual=time.monotonic()-self.started
        if expected>actual: time.sleep(expected-actual)
