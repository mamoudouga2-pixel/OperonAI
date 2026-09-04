import argparse, json, tempfile
from pathlib import Path
from installer_engine.installer import Installer
from dependency_manager.manifest import Manifest
from bootstrap.first_launch import run_first_launch

def demo_manifest():
    return Manifest.from_dict({"components":[
        {"component_id":"runtime.local","component_type":"runtime","version":"1.0.0","platform":"any","install_mode":"external_artifact","metadata":{"runtime_name":"ollama"}},
        {"component_id":"browser.controlled","component_type":"browser","version":"1.0.0","platform":"any","dependencies":["runtime.local"]},
    ]})

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--demo",action="store_true"); ap.add_argument("--root"); args=ap.parse_args()
    root=Path(args.root or tempfile.mkdtemp(prefix="lmacw-installer-"));
    if args.demo:
        # Demo uses a pre-created dummy runtime artifact only for exercising state/storage flows; it does not install Ollama.
        inst=Installer(root); print(json.dumps({"platform":__import__('installer_engine.architecture',fromlist=['platform_contract']).platform_contract(),"root":str(root)},indent=2)); return
    print("Installer module: provide a signed deployment manifest to Installer.install().")
if __name__=="__main__": main()
