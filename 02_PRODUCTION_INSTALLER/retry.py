import time, random
class RetryPolicy:
    def __init__(self,max_attempts=3,base_delay=0.8,max_delay=15): self.max_attempts=max_attempts; self.base_delay=base_delay; self.max_delay=max_delay
    def delay(self,attempt): return min(self.max_delay,self.base_delay*(2**max(0,attempt-1))+random.random()*0.25)
    def run(self,fn):
        last=None
        for attempt in range(1,self.max_attempts+1):
            try:return fn()
            except Exception as e:
                last=e
                if attempt==self.max_attempts: break
                time.sleep(self.delay(attempt))
        raise last
