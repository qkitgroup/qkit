import os

import h5py
import numpy as np
import pytest

from qkit.storage.hdf_file import H5_file


def test_swmr_as_intended():
    f = h5py.File("test.h5", "w", libver="latest")
    f.swmr_mode = True
    f.create_dataset("data", (10,), dtype="i", fillvalue=1)
    # Not closing

    f2 = h5py.File("test.h5", "r", swmr=True)
    assert np.all(f2["data"][:] == 1)

    f.close()
    f2.close()
    os.remove("test.h5")

def test_with_qkit_hfd5():
    f = H5_file(output_file='test.h5', mode='w')
    f.create_dataset("data", (10,), dtype="i")
    f['/entry/data0/data'][:] = 1
    # Not closing

    f2 = H5_file(output_file='test.h5', mode='r')
    assert np.all(f2['/entry/data0/data'][:] == 1)
    f.close_file()
    f2.close_file()
    os.remove('test.h5')

def test_new_qkit_hdf5_no_swmr_read():
    f = H5_file(output_file='test.h5', mode='w')
    f.create_dataset("data", (10,), dtype="i")
    f['/entry/data0/data'][:] = 1
    # Not closing
    
    with pytest.raises(OSError):
        h5py.File("test.h5", "r") # SWMR and file locking are incompatible

    f2 = h5py.File("test.h5", "r", locking=False)
    assert np.all(f2['/entry/data0/data'][:] == 1)
    f.close_file()
    f2.close()
    os.remove('test.h5')

def test_new_qkit_hdf5_after_closing():
    f = H5_file(output_file='test.h5', mode='w')
    f.create_dataset("data", (10,), dtype="i")
    f['/entry/data0/data'][:] = 1
    f.close_file()

    f2 = h5py.File("test.h5", "r") # Corresponds to old qkit
    assert np.all(f2['/entry/data0/data'][:] == 1)
    f2.close()
    os.remove('test.h5')