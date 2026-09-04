from pathlib import Path
class DownloadHandler:
    def validate(self,item,request):
        p=Path(item["path"])
        safe=Path(request.get("safe_directory","/safe/downloads")).resolve()
        try: p.resolve().relative_to(safe)
        except ValueError: raise RuntimeError("DOWNLOAD_FAILED: unsafe destination")
        if not item.get("complete"): raise RuntimeError("DOWNLOAD_FAILED: incomplete")
        if request.get("expected_name") and item.get("name")!=request["expected_name"]: raise RuntimeError("DOWNLOAD_FAILED: name mismatch")
        return True
