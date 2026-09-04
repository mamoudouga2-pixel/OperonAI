from dependency_manager.manifest import Manifest
from dependency_manager.manager import DependencyManager
from common.errors import DependencyConflict

def test_dependency_order():
    m=Manifest.from_dict({"components":[{"component_id":"b","component_type":"asset","version":"1.0","dependencies":["a"]},{"component_id":"a","component_type":"asset","version":"1.0"}]})
    assert [c.component_id for c in DependencyManager(m).resolve()]==["a","b"]

def test_cycle():
    m=Manifest.from_dict({"components":[{"component_id":"a","component_type":"asset","version":"1.0","dependencies":["b"]},{"component_id":"b","component_type":"asset","version":"1.0","dependencies":["a"]}]})
    try: DependencyManager(m).resolve(); assert False
    except DependencyConflict: pass
