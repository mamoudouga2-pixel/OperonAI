class Waiter:
    def wait_for(self,condition,timeout_ms=10000):
        if timeout_ms<=0:
            raise RuntimeError("PAGE_LOAD_TIMEOUT")
        if condition():
            return True
        raise RuntimeError("PAGE_LOAD_TIMEOUT")
