from pytest import fixture
from pathlib import Path
from collections.abc import Iterable
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from qkit.core.lib.file_service import file_info_database

@fixture(scope="function")
def fid() -> 'Iterable[file_info_database.fid]':
    """
    Load and start qkit, initalize file info database and clean up after test execution
    """
    import qkit
    import qkit.core.s_init.S16_available_modules # Fix class loading
    from qkit.core.lib.file_service import file_info_database
    # Do not initialize with environment variable, patch config
    import os
    if "QKIT_LOCAL_CONFIG" in os.environ:
        del os.environ["QKIT_LOCAL_CONFIG"]
    print(f"Starting with reset cfg.")
    qkit.cfg['datadir'] = Path(__file__).parent
    qkit.cfg['fid_scan_datadir'] = True
    # No qkit.start()
    # Manually create fid:
    fid = file_info_database.fid()
    fid.recreate_database()
    # Wait for indexing to stop
    import threading
    [thread.join() for thread in threading.enumerate() if thread.name == "creating_db"]
    print(f"Indexed: {fid._get_datadir()}")
    print(f"Breadcrumb: {fid._breadcrumb_creator._breadcrumb_path}")
    # Return reference to File Info Data Base. Type error ignorde because of weird qkit import semantics
    yield fid

    # Cleanup afterwards
    del qkit.cfg
    from qkit.core.lib.file_service.breadcrumbs import derive_breadcrumb_filename
    print(f"Cleaning up Breadcrumbs at {derive_breadcrumb_filename()}")
    if derive_breadcrumb_filename().exists():
        import os
        os.remove(derive_breadcrumb_filename())


def test_datadir_index(fid: 'file_info_database.fid'):
    # Check Indexing of main directory
    assert Path(fid['STUVWX']) == Path(__file__).parent / "STUVWX_dummy.h5"
    # Check Indexing of sub directories
    assert Path(fid['YZ0123']) == Path(__file__).parent / 'subdir' / "YZ0123_dummy.h5"

def test_creation_time_sorting(fid: 'file_info_database.fid'):
    # Check get_last returning the latest UUID. Note: This is a UUID, not a path!
    assert fid.get_last() == "YZ0123"
    assert Path(fid[fid.get_last()]) == Path(__file__).parent / 'subdir' / "YZ0123_dummy.h5"

def test_adding_file_to_index(fid: 'file_info_database.fid'):
    import os
    datadir = Path(__file__).parent
    path = datadir / "Z45678_dummy.h5"
    with open(path, "w"):
        pass
    # The following is replaced with an internal call to speed up testing:
    # fid.add_h5_file(str(path))
    # import threading
    # from threading import Timer
    # [thread.join() for thread in threading.enumerate() if isinstance(thread, Timer)]
    # The propper call, add_h5_file, is conditional on scanning the data dir and, for some reason,
    # introduces a 20s delay to calling _add. We bypass this by calling directly.
    fid._add(str(path))
    try:
        assert fid.get_last() == "Z45678"
        assert Path(fid[fid.get_last()]) == Path(__file__).parent / "Z45678_dummy.h5"

        # Test Breadcrumb creation on file add
        from qkit.core.lib.file_service.breadcrumbs import read_breadcrumbs
        assert read_breadcrumbs(Path(datadir))['Z45678'] == path
    finally:
        os.remove(path)

def test_get_and__get__equal(fid: 'file_info_database.fid'):
    assert fid.get("YZ0123") == fid["YZ0123"]