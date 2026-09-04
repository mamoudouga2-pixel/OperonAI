DEFAULT_POLICY={"application_files":True,"runtime":"managed_only","models":"ask","browser_profile":True,"cache":True,"logs":True,"user_data":False}
def complete_data_policy(): return {k:True for k in DEFAULT_POLICY}
