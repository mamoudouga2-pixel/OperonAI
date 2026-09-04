from browser_controller.controller import BrowserController
from page_reader.reader import PageReader
from locator_engine.locator import LocatorEngine
from web_actions.actions import ActionExecutor
from web_actions.navigate import Navigator
from observation.observation import ObservationManager
from observation.logger import BrowserLogger
from frame_tab_manager.manager import FrameTabManager
from recovery.recovery import LoopDetector, RecoveryManager
import json
class BrowserAgent:
    def __init__(self,adapter,config=None):
        self.config=config or {"browser":{"default_timeout_ms":10000,"navigation_timeout_ms":30000,"max_action_retries":3,"allow_new_tabs":True,"allow_downloads":True},
                               "security":{"require_domain_policy":True,"block_unknown_redirects":True}}
        self.controller=BrowserController(adapter,self.config.get("max_concurrent_sessions",4))
        self.reader=PageReader(adapter); self.locator=LocatorEngine(); self.actions=ActionExecutor(adapter,self.locator)
        self.navigator=Navigator(adapter); self.obs=ObservationManager(adapter); self.logger=BrowserLogger()
        self.tabs=FrameTabManager(adapter); self.loops=LoopDetector()
        max_retries=self.config.get("browser",{}).get("max_action_retries",3)
        self.recovery=RecoveryManager(max_retries)
        self.adapter=adapter
    def create_session(self,task_context):
        session=self.controller.create_session(task_context)
        self.logger.event("BROWSER_SESSION_CREATED",session_id=session.session_id,task_id=session.task_id)
        self.logger.event("BROWSER_SESSION_READY",session_id=session.session_id)
        return session.to_dict()
    def close_session(self,sid):
        result=self.controller.close_session(sid)
        self.logger.event("BROWSER_SESSION_CLOSED",session_id=sid)
        return result
    def navigate(self,sid,request):
        policy=request.get("constraints",{"allowed_domains":[],"allow_subdomains":False})
        if self.config["security"]["require_domain_policy"] and not policy.get("allowed_domains"): raise RuntimeError("NAVIGATION_BLOCKED")
        self.logger.event("BROWSER_NAVIGATION_STARTED",session_id=sid,url=request.get("url"))
        before=self.reader.inspect(sid)
        nav_result=self.navigator.navigate(sid,request,policy)
        # Redirect destination must also satisfy the domain policy (5.13/5.14): a page
        # that starts on an allowed domain but redirects elsewhere must not be trusted silently.
        if isinstance(nav_result,dict) and nav_result.get("redirected") and self.config["security"].get("block_unknown_redirects",True):
            final_url=nav_result.get("url",request.get("url"))
            self.navigator.validate(final_url,policy)
        after=self.reader.inspect(sid)
        self.logger.event("BROWSER_NAVIGATION_COMPLETED",session_id=sid,url=after.get("url"))
        return {"status":"SUCCESS","current_url":after["url"],"state_changed":before!=after,"error":None}
    def inspect_page(self,sid): return self.reader.inspect(sid)
    def find_target(self,sid,target):
        result=self.locator.find(target,lambda spec:self.adapter.find_target(sid,spec))
        self.logger.event("BROWSER_TARGET_FOUND",session_id=sid,method=result.get("method"),confidence=result.get("confidence"))
        return result
    def execute_action(self,sid,action):
        action_id=action.get("action_id","ACT-001")
        typ=str(action.get("action_type","")).upper()
        max_retries=self.recovery.max_retries
        self.logger.event("BROWSER_ACTION_STARTED",session_id=sid,action_id=action_id,action_type=typ)
        last_error=None
        for attempt in range(1,max_retries+1):
            before=self.reader.inspect(sid)
            # Loop signature is based on approved action + observable page state.
            self.loops.observe(json.dumps(action,sort_keys=True,default=str),json.dumps(before,sort_keys=True,default=str))
            try:
                result=self.actions.execute(sid,action)
            except RuntimeError as exc:
                last_error=exc
                error_code=str(exc).split(":")[0]
                self.logger.event("BROWSER_ACTION_FAILED",session_id=sid,action_id=action_id,error=error_code,attempt=attempt)
                if self.recovery.retryable(error_code) and attempt<max_retries:
                    continue
                raise
            after=self.reader.inspect(sid)
            ev=self.obs.evidence(sid,self.controller.registry.get(sid).task_id,action_id)
            self.logger.event("BROWSER_EVIDENCE_CREATED",session_id=sid,evidence_id=ev.evidence_id)
            self.logger.event("BROWSER_ACTION_COMPLETED",session_id=sid,action_id=action_id,attempt=attempt)
            return {"action_id":action_id,"status":"SUCCESS","message":"Action completed","current_url":after["url"],
                    "state_changed":before!=after,"evidence_ids":[ev.evidence_id],"error":None,"evidence":ev.to_dict()}
        raise last_error
    def upload(self,sid,request):
        from upload_handler.upload import UploadHandler
        p=UploadHandler().validate(request); result=self.adapter.upload_file(sid,request["target"],str(p))
        self.logger.event("BROWSER_UPLOAD_COMPLETED",session_id=sid)
        return {"status":"SUCCESS","result":result}
    def download(self,sid,request):
        from download_handler.download import DownloadHandler
        item=self.adapter.download_file(sid,request["target"]); DownloadHandler().validate(item,request)
        self.logger.event("BROWSER_DOWNLOAD_COMPLETED",session_id=sid,name=item.get("name"))
        return {"status":"SUCCESS","download":item}
    def switch_tab(self,sid,tab_id): return self.tabs.switch_tab(sid,tab_id)
    def switch_frame(self,sid,frame_id): return self.tabs.switch_frame(sid,frame_id)
    def capture_evidence(self,sid):
        ev=self.obs.evidence(sid,self.controller.registry.get(sid).task_id,"EVIDENCE_ONLY"); return ev.to_dict()
    def health_check(self,sid): return self.controller.health_check(sid)
