class DOMReader:
    def read(self,page):
        return page.get("forms",[])
