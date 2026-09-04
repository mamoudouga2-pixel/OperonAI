from .base import BrowserAdapter

class PlaywrightAdapter(BrowserAdapter):
    """Adapter seam. Install/use Playwright in the host application and implement
    these methods with its Browser/BrowserContext/Page APIs. The Browser Agent
    contract does not depend on Playwright-specific objects."""
    def _not_installed(self): raise RuntimeError("BROWSER_START_FAILED: Playwright adapter requires Playwright host integration")
    def create_context(self,session_id): self._not_installed()
    def close_context(self,session_id): self._not_installed()
    def navigate(self,session_id,url,timeout_ms): self._not_installed()
    def get_page_state(self,session_id): self._not_installed()
    def find_target(self,session_id,target): self._not_installed()
    def click(self,session_id,target): self._not_installed()
    def type(self,session_id,target,value): self._not_installed()
    def select(self,session_id,target,value): self._not_installed()
    def scroll(self,session_id,amount): self._not_installed()
    def keyboard(self,session_id,key): self._not_installed()
    def upload_file(self,session_id,target,file_ref): self._not_installed()
    def download_file(self,session_id,target): self._not_installed()
    def switch_tab(self,session_id,tab_id): self._not_installed()
    def switch_frame(self,session_id,frame_id): self._not_installed()
    def screenshot(self,session_id): self._not_installed()
    def health_check(self,session_id): self._not_installed()
