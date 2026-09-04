class TextReader:
 def read(self,analysis): return [e.get("text","") for e in analysis.get("elements",[]) if e.get("text")]
