import subprocess

def version_of(binary):
    try:
        p=subprocess.run([binary,"--version"],capture_output=True,text=True,timeout=5); return p.stdout.strip() or p.stderr.strip()
    except Exception:return None
