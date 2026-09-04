class IncidentResponse:
    def respond(self,action=None,audit=None):
        if audit and action:audit.log("SECURITY_INCIDENT_DETECTED",action,{"response":"STOP"})
        return {"action":"STOP","notify_core":True,"require_review":True}
