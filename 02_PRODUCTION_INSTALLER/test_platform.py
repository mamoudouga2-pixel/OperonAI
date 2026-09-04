from installer_engine.architecture import platform_contract

def test_contract():
    c=platform_contract(); assert {"os","os_version","architecture","cpu_architecture","user_scope","admin_available"}.issubset(c)
