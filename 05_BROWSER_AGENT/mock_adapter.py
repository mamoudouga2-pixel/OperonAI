from .base import BrowserAdapter

class MockBrowserAdapter(BrowserAdapter):
    def __init__(self):
        self.sessions={}
        self.counter=0
    def create_context(self, session_id):
        if session_id in self.sessions: raise RuntimeError("BROWSER_START_FAILED")
        self.sessions[session_id]={"url":"about:blank","title":"","ready_state":"complete","loading":False,
            "tabs":["TAB-001"],"frames":["FRAME-001"],"forms":[],"dialogs":[],"errors":[],"screenshot_counter":0,
            "actions":[],"target_map":{},"downloads":[],"uploads":[],"crashed":False}
        return True
    def _s(self,sid):
        if sid not in self.sessions: raise RuntimeError("BROWSER_START_FAILED")
        s=self.sessions[sid]
        if s["crashed"]: raise RuntimeError("BROWSER_CRASHED")
        return s
    def close_context(self,sid):
        self.sessions.pop(sid,None); return True
    def navigate(self,sid,url,timeout_ms):
        s=self._s(sid)
        if not url or not isinstance(url,str): raise ValueError("NAVIGATION_BLOCKED")
        s["loading"]=False;s["ready_state"]="complete";s["url"]=url;s["title"]=url.split("//")[-1].split("/")[0]
        s["actions"].append(("NAVIGATE",url)); return {"url":url,"redirected":False}
    def get_page_state(self,sid):
        s=self._s(sid); return {k:v for k,v in s.items() if k not in {"target_map","screenshot_counter","actions","crashed"}}
    def find_target(self,sid,target):
        s=self._s(sid)
        key=(target.get("role"),target.get("name"))
        found=s["target_map"].get(key)
        if found is None and target.get("text"): found=s["target_map"].get(("text",target["text"]))
        if found is None:
            for method in ("label","placeholder","test_id","structural","vision"):
                if method in target and target[method] is not None:
                    found=s["target_map"].get((method,target[method]))
                    if found is not None: break
        return found
    def click(self,sid,target):
        s=self._s(sid); s["actions"].append(("CLICK",target)); return {"state_changed":True}
    def type(self,sid,target,value):
        s=self._s(sid); s["actions"].append(("TYPE",target,"<REDACTED>")); return {"state_changed":True}
    def select(self,sid,target,value):
        s=self._s(sid); s["actions"].append(("SELECT",target,"<REDACTED>")); return {"state_changed":True}
    def scroll(self,sid,amount):
        s=self._s(sid); s["actions"].append(("SCROLL",amount)); return {"state_changed":False}
    def keyboard(self,sid,key):
        s=self._s(sid); s["actions"].append(("KEYBOARD",key)); return {"state_changed":False}
    def upload_file(self,sid,target,file_ref):
        s=self._s(sid); s["uploads"].append(file_ref); return {"state_changed":True}
    def download_file(self,sid,target):
        s=self._s(sid); item={"path":"/safe/downloads/file.txt","name":"file.txt","type":"text/plain","complete":True}
        s["downloads"].append(item); return item
    def switch_tab(self,sid,tab_id):
        s=self._s(sid)
        if tab_id not in s["tabs"]: raise RuntimeError("TARGET_NOT_FOUND")
        return {"tab_id":tab_id}
    def switch_frame(self,sid,frame_id):
        s=self._s(sid)
        if frame_id not in s["frames"]: raise RuntimeError("FRAME_NOT_FOUND")
        return {"frame_id":frame_id}
    def screenshot(self,sid):
        s=self._s(sid);s["screenshot_counter"]+=1
        return {"path":f"evidence/{sid}-{s['screenshot_counter']}.png","bytes":b"mock"}
    def health_check(self,sid): return sid in self.sessions and not self.sessions[sid]["crashed"]
