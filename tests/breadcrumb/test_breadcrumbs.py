from qkit.core.lib.file_service.breadcrumbs import *
from pytest import fixture
from unittest.mock import patch
import qkit
from pathlib import Path

def test_breadcrumb_name_constant():
    assert derive_breadcrumb_filename() == derive_breadcrumb_filename()

def test_read_single_file():
    datadir_path = Path(__file__).parent
    result = read_breadcrumb(datadir_path / ".1337deadbeef.breadcrumb")
    assert len(result) == 1
    assert result['MNOPQR'] == datadir_path / "file3.h5"

def test_multiple_writers():
    try:
        writer1 = BreadCrumbCreator()
        writer2 = BreadCrumbCreator()
    finally:
        # Cleanup breadcrumb
        if derive_breadcrumb_filename().exists():
            import os
            os.remove(derive_breadcrumb_filename())

def test_read_all_breadcrumbs():
    datadir_path =  Path(__file__).parent
    result = read_breadcrumbs(datadir_path)
    assert len(result) == 3
    assert result['ABCDEF'] == datadir_path / "file1.h5"
    assert result['GHIJKL'] == datadir_path / "file2.h5"
    assert result['MNOPQR'] == datadir_path / "file3.h5"

def test_clear_breadcrumb():
    try:
        writer = BreadCrumbCreator()
        writer.clear_file()
        assert not writer._breadcrumb_path.exists()
    finally:
        # Cleanup breadcrumb
        if derive_breadcrumb_filename().exists():
            import os
            os.remove(derive_breadcrumb_filename())

@patch("os.getcwd", return_value=(str(Path(__file__).parent)))
@patch("builtins.input", return_value="y")
def test_manual_index(*args, **kwargs):
    # Index the h5 file next to this one.
    qkit.cfg['datadir'] = Path(__file__).parent
    manual_index()
    # Wait on the background task to finish.
    import threading
    [thread.join() for thread in threading.enumerate() if thread.name == "creating_db"]

    # Check indexing worked
    result = read_breadcrumbs(Path(__file__).parent)
    assert result['STUVWX'] == Path(__file__).parent / "STUVWX_dummy.h5"

    # Cleanup breadcrumb
    if derive_breadcrumb_filename().exists():
        import os
        os.remove(derive_breadcrumb_filename())

