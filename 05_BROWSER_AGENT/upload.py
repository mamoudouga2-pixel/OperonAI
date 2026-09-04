from pathlib import Path
class UploadHandler:
    def validate(self,request):
        ref=request.get("file_ref")
        approved=set(request.get("approved_file_refs",[]))
        if not ref or not isinstance(ref,str) or ref not in approved:
            raise RuntimeError("UPLOAD_FAILED: approved file reference required")
        p=Path(ref)
        if not p.exists() or not p.is_file():
            raise RuntimeError("UPLOAD_FAILED: file does not exist")
        allowed=request.get("allowed_extensions")
        if allowed and p.suffix.lower() not in {str(x).lower() for x in allowed}:
            raise RuntimeError("UPLOAD_FAILED: type blocked")
        return p
