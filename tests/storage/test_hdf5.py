from pathlib import Path
from pytest import fixture
import h5py
import numpy as np
from qkit.measure.measurement_base import MeasureBase
from qkit.storage.store import Data
import tempfile

@fixture(scope="session", autouse=True)
def setup():
    import os
    import pathlib
    from qkit.install.install import create_base_structure
    cwd = pathlib.Path(os.getcwd())
    print("CWD", cwd)
    create_base_structure(cwd)

@fixture
def testdata():
    return np.random.randint(-10, 10, size=(3, 3, 3))

def test_file_creation(testdata):
    with tempfile.TemporaryDirectory() as dir:
        fname = Path(dir) / "hdf5test.h5"

        # Create a test file
        datafile = Data(fname, mode="w")

        x_coord = datafile.add_coordinate("x")
        x_coord.add([0, 1, 2])
        y_coord = datafile.add_coordinate("y")
        y_coord.add([3, 4, 5])
        z_coord = datafile.add_coordinate("z")
        z_coord.add([6, 7, 8])

        # Create a 1D test structure
        dataset1D = datafile.add_value_vector("test1d", x_coord, folder="data")
        dataset1D.append(testdata[0, 0])

        ## Create a 2D test structure
        dataset2D = datafile.add_value_matrix("test2d", x_coord, y_coord, folder="data")
        for x in range(testdata.shape[1]):
            dataset2D.append(testdata[0, x])
        
        # Create a 3D test structure
        dataset3D = datafile.add_value_box("test3d", x_coord, y_coord, z_coord, folder="data")
        for x in range(testdata.shape[0]):
            for y in range(testdata.shape[1]):
                dataset3D.append(testdata[x, y])
            dataset3D.next_matrix() # Breaks without this call

        # Close the file for read back
        datafile.flush()
        datafile.close()

        # Read it back
        datafile = Data(fname)
        assert np.array_equal(datafile.data.test1d[:], testdata[0, 0]), "Failed saving 1D data"
        assert np.array_equal(datafile.data.test2d[:], testdata[0]), "Failed saving 2D data"
        assert np.array_equal(datafile.data.test3d[:], testdata), "Failed saving 3D data"


def test_measurement_average_over_metadata(tmp_path):
    path = tmp_path / "measurement.h5"
    frequency = MeasureBase.Coordinate("frequency", "Hz", [1, 2])
    voltage = MeasureBase.Data("voltage", [frequency])
    averaged = MeasureBase.Data("averaged", [frequency], average_over="repetitions")

    with Data(path, mode="w") as datafile:
        voltage.create_dataset(datafile).append([0.5, 1.5])
        averaged.create_dataset(datafile).append([2.0, 4.0])

    with h5py.File(path, "r") as saved:
        group = saved["entry/data0"]
        np.testing.assert_array_equal(group["voltage"][:], [0.5, 1.5])
        assert "average_over" not in group["voltage"].attrs
        np.testing.assert_array_equal(group["averaged"][:], [2.0, 4.0])
        assert group["averaged"].attrs["average_over"] == "repetitions"
