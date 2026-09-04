def range_header(offset): return {"Range":f"bytes={offset}-"} if offset else {}
