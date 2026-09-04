class AccessibilityReader:
    def read(self,page):
        return page.get("accessibility",[])
