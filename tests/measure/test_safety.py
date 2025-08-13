import os
from pathlib import Path

import numpy as np
import pytest
import qkit
qkit.cfg['measurement.unified_measurements.enabled'] = True
from qkit.measure.unified_measurements import Sweep, Axis, ScalarMeasurement, Experiment
from qkit.storage.thin_hdf import HDF5


class DummyDataSet:

    datastore: np.ndarray
    attrs: dict

    def __init__(self, store):
        self.datastore = store
        self.attrs = {'resizable': False}

    def flush(self):
        pass

    def __getitem__(self, item):
        return self.datastore.__getitem__(item)

    def __setitem__(self, key, value):
        self.datastore.__setitem__(key, value)

class DummyDataFile:

    dataset: DummyDataSet

    def __init__(self, store):
        self.dataset = DummyDataSet(store)

    def get_dataset(self, name, category = 'data'):
        return self.dataset

    def flush(self):
        pass

def test_overwrite_protection():
    """
    Tests that data is written correctly into a Dataset, but that overwrites are caught.
    """
    # Case 1: No data present
    mock_file = DummyDataFile(np.full(shape=(10,), fill_value=np.nan))
    measurement = ScalarMeasurement(name='test', getter=lambda: 1)
    # We are partially mocking a HDF5 file. The type checker doesn't like it, but it's fine.
    # noinspection PyTypeChecker
    measurement.record(mock_file, sweep_indices=(0,))
    assert mock_file.dataset.datastore[0] == 1, "Change was not stored!"
    assert np.all(np.isnan(mock_file.dataset.datastore[1:])), "Too many changed entries!"

    # Case 2: Data is about to be overwritten
    mock_file = DummyDataFile(np.zeros(shape=(10,)))
    measurement = ScalarMeasurement(name='test', getter=lambda: 1)
    with pytest.raises(AssertionError):
        # We are partially mocking a HDF5 file. The type checker doesn't like it, but it's fine.
        # noinspection PyTypeChecker
        measurement.record(mock_file, sweep_indices=(0,))


class CrashAfterNCalls:

    remaining: int

    class IntendedException(Exception):
        pass

    def __init__(self, remaining: int):
        self.remaining = remaining

    def __call__(self, *args, **kwargs):
        self.remaining -= 1
        if self.remaining == 0:
            raise CrashAfterNCalls.IntendedException("Catch this!")
        return 1

def test_save_on_crash():
    """
    Tests that data is not lost if the measurement crashes.
    """
    local_file = Path(__file__).parent / 'test.h5'
    if local_file.exists():
        os.remove(local_file)
    h5_file = HDF5(local_file, 'a')
    h5_file.create_dataset('test', shape=(10,))
    measurement = ScalarMeasurement(name='test', getter=CrashAfterNCalls(3))
    s = Sweep(lambda val: None, axis=Axis(name='x', range=np.arange(10)))
    s.measure(measurement)
    with pytest.raises(CrashAfterNCalls.IntendedException):
        s._run_sweep(h5_file, index_list=tuple())
    h5_file.close()

    h5_file = HDF5(local_file, 'r')
    assert np.all(h5_file.get_dataset('test')[0:2] == 1)
    assert np.all(np.isnan(h5_file.get_dataset('test')[2:]))
    h5_file.close()

