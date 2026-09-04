import json

def validate_config(path):
    data=json.loads(open(path,encoding='utf-8').read());
    for key in ("runtime","browser","paths"):
        if key not in data: raise ValueError(f"Missing configuration key: {key}")
    return True
