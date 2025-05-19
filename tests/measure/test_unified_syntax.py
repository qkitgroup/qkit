from qkit.measure.measurement_base import Experiment, MeasurementTypeAdapter, Axis
import numpy as np
from typing import override

from qkit.measure.samples_class import Sample

X_SWEEP_AXIS = Axis(name='x', range=np.array(range(0, 10)))
SAMPLE = Sample()


class SweepInspectorMeasurement(MeasurementTypeAdapter):
    sweep_intercept: MeasurementTypeAdapter.MeasurementDescriptor
    current_x: float
    accumulated_data: list[float]

    def __init__(self):
        super().__init__()
        self.sweep_intercept = MeasurementTypeAdapter.MeasurementDescriptor(
            name='sweep_intercept',
            axes=(X_SWEEP_AXIS,)
        )
        self.accumulated_data = []

    def x_log(self, value):
        self.current_x = value
        self.accumulated_data.append(value)

    @override
    @property
    def expected_structure(self) -> list['MeasurementTypeAdapter.MeasurementDescriptor']:
        return [self.sweep_intercept]

    @override
    def perform_measurement(self) -> list['MeasurementTypeAdapter.MeasurementData']:
        return [self.sweep_intercept.with_data(self.accumulated_data)]


def test_experiment_creation():
    log_measure = SweepInspectorMeasurement()
    e = Experiment('creation_test', SAMPLE)
    with e.sweep(lambda val: log_measure.x_log(val), X_SWEEP_AXIS) as x_sweep:
        x_sweep.measure(log_measure)
    e.run()
    assert np.array_equal(np.asarray(log_measure.accumulated_data), X_SWEEP_AXIS.range)


def test_filtered_sweep():
    log_measure = SweepInspectorMeasurement()
    e = Experiment('filter_test', SAMPLE)
    with e.sweep(log_measure.x_log,
                 X_SWEEP_AXIS,
                 axis_filter=lambda r: np.logical_and(r <= 8, r >= 2)) as x_sweep:
        x_sweep.measure(log_measure)
    print(str(e))
    e.run()
    assert np.array_equal([2, 3, 4, 5, 6, 7, 8], log_measure.accumulated_data)

def test_dimensionality_calculations():
    log_measure = SweepInspectorMeasurement()

    e = Experiment('filter_test', SAMPLE)
    assert e.dimensionality == 0, "Default dimensionality should be 0"

    e.measure(log_measure)
    assert e.dimensionality == 1, "1D array of points is 1D"

    e.measure(log_measure)
    assert e.dimensionality == 1, "Two 1D arrays of points is 1D"

    with e.sweep(log_measure.x_log, X_SWEEP_AXIS) as x_sweep:
        x_sweep.measure(log_measure)

    assert e.dimensionality == 2, "Sweep and 1D array is 2D"

class SinusGeneratorMeasurement(MeasurementTypeAdapter):

    signal: MeasurementTypeAdapter.MeasurementDescriptor
    time_axis: Axis
    current_x: float

    def __init__(self):
        super().__init__()
        self.time_axis = Axis(name='time', range=np.linspace(0, 10, 100))
        self.signal = MeasurementTypeAdapter.MeasurementDescriptor(
            name='signal',
            axes=(self.time_axis,)
        )

    def x_log(self, value):
        self.current_x = value

    @property
    def expected_structure(self) -> list['MeasurementTypeAdapter.MeasurementDescriptor']:
        return [self.signal]

    def perform_measurement(self) -> list['MeasurementTypeAdapter.MeasurementData']:
        return [self.signal.with_data(np.sin(self.time_axis.range + self.current_x * 0.2))]

def test_hdf5_file_creation():
    measure = SinusGeneratorMeasurement()
    e = Experiment('file_test', SAMPLE)
    with e.sweep(measure.x_log, X_SWEEP_AXIS) as x_sweep:
        x_sweep.measure(measure)
    print(str(e))
    e.run()