class PageReader:
    def __init__(self,adapter): self.adapter=adapter
    def inspect(self,sid): return self.adapter.get_page_state(sid)
