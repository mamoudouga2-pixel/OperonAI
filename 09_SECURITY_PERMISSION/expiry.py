from datetime import datetime,timezone
def expired(ts,now=None):
    return datetime.fromisoformat(ts.replace("Z","+00:00")) <= (now or datetime.now(timezone.utc))
