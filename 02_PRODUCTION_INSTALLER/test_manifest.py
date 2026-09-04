from dependency_manager.manifest import Manifest

def test_manifest_contract():
    m=Manifest.from_dict({"components":[{"component_id":"runtime.local","component_type":"runtime","version":"1.0.0","platform":"any"}]}); c=m.components[0]; assert c.component_id=="runtime.local" and c.component_type=="runtime"
