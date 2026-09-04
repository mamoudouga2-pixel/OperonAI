class FrameTabManager:
    def __init__(self,adapter): self.adapter=adapter
    def switch_tab(self,sid,tab_id): return self.adapter.switch_tab(sid,tab_id)
    def switch_frame(self,sid,frame_id): return self.adapter.switch_frame(sid,frame_id)
