from installer_engine.disk_space import estimate
def test_disk_formula(tmp_path):
    x=estimate(10,20,30,40,50,path=tmp_path); assert x.required_bytes==150
