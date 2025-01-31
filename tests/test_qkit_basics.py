import pytest

import qkit.core

@pytest.fixture(scope="session", autouse=True)
def setup(request):
    import os
    import pathlib
    from qkit.install.install import create_base_structure
    cwd = pathlib.Path(os.getcwd())
    print("CWD", cwd)
    create_base_structure(cwd)

def test_qkit_load():
    import qkit
    qkit.cfg['fid_scan_datadir'] = False
    qkit.cfg['run_id'] = "Basic Test"
    qkit.cfg['user'] = "Automated Test"
    qkit.start()

def test_load_datadir():
    import qkit
    qkit.cfg['fid_scan_datadir'] = True
    qkit.cfg['run_id'] = "Basic Test"
    qkit.cfg['user'] = "Automated Test"
    qkit.start()