from qkit.storage.thin_hdf import HDF5
import tempfile
import os
import pathlib
import numpy as np
import h5py

def test_file_creation():
    with tempfile.TemporaryDirectory(delete=True) as tmpdir:
        print("CWD", tmpdir)
        fname = tmpdir + "/hdf5test.h5"
        data = HDF5(fname, mode="w")
        data.write_text_record('test', "This is a test")
        data.close()

        redata = HDF5(fname, "r")
        assert redata.get_dataset('test')[0] == "This is a test".encode('utf-8')

def test_large_file_creation():
    cwd = __file__
    fname = pathlib.Path(cwd).parent / "large_file.h5"
    data = HDF5(fname, mode="w")
    data.write_text_record('test', "This is a test!")
    data.write_text_record('json', '{"test": true}')

    x_axis = data.create_dataset("x", shape=(1000,))
    y_axis = data.create_dataset("y", shape=(1000,))
    x_axis[:] = range(1000)
    y_axis[:] = range(1000)
    testdata = data.create_dataset("test2", shape=(1000,1000), axes=[x_axis, y_axis])

    testdata[:, :] = np.sin(np.arange(1000) / 10)[:, np.newaxis] * np.cos(np.arange(1000) / 10)[np.newaxis, :]

def test_qviewkit():
    cwd = __file__
    fname = pathlib.Path(cwd).parent / "large_file.h5"
    import qkit.gui.qviewkit.main as qviewkit
    qviewkit.main(['python3', '-f', str(fname)])