class IncidentDetector:
    def detect(self,event):return event.get("severity")=="SUSPICIOUS"
