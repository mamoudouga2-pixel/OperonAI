class FormHandler:
    def validate(self,fields,required):
        missing=[x for x in required if x not in fields or fields[x] in (None,"")]
        if missing: raise RuntimeError("TARGET_NOT_READY: missing required fields "+",".join(missing))
        return True
