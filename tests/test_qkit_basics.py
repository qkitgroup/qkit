import pytest

@pytest.fixture(scope="session", autouse=True)
def do_something(request):
    import os
    import pathlib
    from qkit.install.install import create_base_structure
    cwd = pathlib.Path(os.getcwd())
    print("CWD", cwd)
    create_base_structure(cwd)

def test_qkit_load():
    import qkit
    qkit.cfg['run_id'] = "Test"
    qkit.cfg['user'] = "Automated Test"
    qkit.start()