import time

import pytest

import qkit
qkit.cfg['measurement.unified_measurements.enabled'] = True
from qkit.analysis.numerical_derivative import SavgolNumericalDerivative
from qkit.measure.unified_measurements import Experiment, MeasurementTypeAdapter, Axis, ScalarMeasurement
import numpy as np
from typing import override

from qkit.measure.samples_class import Sample

X_SWEEP_AXIS = Axis(name='x', range=np.array(range(0, 10)))
Y_SWEEP_AXIS = Axis(name='y', range=np.array(range(0, 8)))
SAMPLE = Sample()

class DummyPointMeasurement(MeasurementTypeAdapter):

    def __init__(self, name: str):
        super().__init__()
        self._descriptor = MeasurementTypeAdapter.DataDescriptor(
            name=name,
            axes=tuple()
        )

    @override
    @property
    def expected_structure(self) -> tuple['MeasurementTypeAdapter.DataDescriptor', ...]:
        return (self._descriptor, )

    def perform_measurement(self) -> tuple['MeasurementTypeAdapter.GeneratedData', ...]:
        return (self._descriptor.with_data(1),)


class SweepInspectorMeasurement(MeasurementTypeAdapter):
    sweep_intercept: MeasurementTypeAdapter.DataDescriptor
    current_x: float
    accumulated_data: list[float]

    def __init__(self, sub_name='x', axis=X_SWEEP_AXIS):
        super().__init__()
        self.sweep_intercept = MeasurementTypeAdapter.DataDescriptor(
            name=f'sweep_intercept_{sub_name}',
            axes=(axis,)
        )
        self.accumulated_data = []

    def log(self, value):
        self.current_x = value
        self.accumulated_data.append(value)

    @override
    @property
    def expected_structure(self) -> tuple['MeasurementTypeAdapter.DataDescriptor', ...]:
        return (self.sweep_intercept,)

    @override
    def perform_measurement(self) -> tuple['MeasurementTypeAdapter.GeneratedData', ...]:
        base = np.zeros_like(self.sweep_intercept.axes[0].range)
        base[0:len(self.accumulated_data)] = self.accumulated_data
        return (self.sweep_intercept.with_data(base),)


@pytest.fixture
def dummy_instruments_class():
    class DummyInstruments:
        @staticmethod
        def get_instruments():
            return []
        @staticmethod
        def get_instrument_names():
            return []
    qkit.instruments = DummyInstruments()

def test_experiment_creation(dummy_instruments_class):
    log_measure = SweepInspectorMeasurement()
    e = Experiment('creation_test', SAMPLE)
    with e.sweep(lambda val: log_measure.log(val), X_SWEEP_AXIS) as x_sweep:
        x_sweep.measure(log_measure)
    e.run(open_qviewkit=False)
    assert np.array_equal(np.asarray(log_measure.accumulated_data), X_SWEEP_AXIS.range)


def test_filtered_sweep(dummy_instruments_class):
    log_measure = SweepInspectorMeasurement()
    e = Experiment('filter_test', SAMPLE)
    with e.sweep(log_measure.log,
                 X_SWEEP_AXIS,
                 axis_filter=lambda r: np.logical_and(r <= 8, r >= 2)) as x_sweep:
        x_sweep.measure(log_measure)
    print(str(e))
    e.run(open_qviewkit=False)
    assert np.array_equal([2, 3, 4, 5, 6, 7, 8], log_measure.accumulated_data)


def test_alternative_filtered_sweep(dummy_instruments_class):
    log_measure = SweepInspectorMeasurement()
    e = Experiment('filter_alt_test', SAMPLE)
    with e.sweep(log_measure.log, X_SWEEP_AXIS) as x_sweep:
        x_sweep.filtered(lambda r: np.logical_and(r <= 8, r >= 2))
        x_sweep.measure(log_measure)
    print(str(e))
    e.run(open_qviewkit=False)
    assert np.array_equal([2, 3, 4, 5, 6, 7, 8], log_measure.accumulated_data)

def test_nested_filtered_sweep(dummy_instruments_class):
    log_measure_x = SweepInspectorMeasurement()
    dummy_point = DummyPointMeasurement('dummy_point')
    e = Experiment('filter_alt_test', SAMPLE)
    with e.sweep(log_measure_x.log, X_SWEEP_AXIS) as x_sweep:
        x_sweep.measure(log_measure_x)
        with x_sweep.sweep(lambda v: None, Y_SWEEP_AXIS) as y_sweep:
            y_sweep.filtered(lambda r: r >= x_sweep.current_value)
            y_sweep.measure(dummy_point)
    print(e)
    e.run(open_qviewkit=True)

def test_dimensionality_calculations():
    log_measure = SweepInspectorMeasurement()

    e = Experiment('filter_test', SAMPLE)
    assert e.dimensionality == 0, "Default dimensionality should be 0"

    e.measure(log_measure)
    assert e.dimensionality == 1, "1D array of points is 1D"

    e.measure(log_measure)
    assert e.dimensionality == 1, "Two 1D arrays of points is 1D"

    with e.sweep(log_measure.log, X_SWEEP_AXIS) as x_sweep:
        x_sweep.measure(log_measure)

    assert e.dimensionality == 2, "Sweep and 1D array is 2D"

class SinusGeneratorMeasurement(MeasurementTypeAdapter):

    signal: MeasurementTypeAdapter.DataDescriptor
    time_axis: Axis
    current_x: float

    def __init__(self):
        super().__init__()
        self.time_axis = Axis(name='time', range=np.linspace(0, 10, 100))
        self.signal = MeasurementTypeAdapter.DataDescriptor(
            name='signal',
            axes=(self.time_axis,)
        )

    def x_log(self, value):
        self.current_x = value

    @property
    def expected_structure(self) -> tuple['MeasurementTypeAdapter.DataDescriptor', ...]:
        return (self.signal,)

    def perform_measurement(self) -> tuple['MeasurementTypeAdapter.GeneratedData', ...]:
        return (self.signal.with_data(np.sin(self.time_axis.range + self.current_x * 0.2)),)

def test_hdf5_file_creation(dummy_instruments_class):
    measure = SinusGeneratorMeasurement()
    e = Experiment('file_test', SAMPLE)
    with e.sweep(measure.x_log, X_SWEEP_AXIS) as x_sweep:
        x_sweep.measure(measure)
    print(str(e))
    e.run(open_qviewkit=False)


class DummyIVMeasurement(MeasurementTypeAdapter):

    x_data: np.ndarray
    y_data: np.ndarray
    desired_bias: Axis
    actual_bias: MeasurementTypeAdapter.DataDescriptor
    signal: MeasurementTypeAdapter.DataDescriptor

    @property
    def expected_structure(self) -> tuple['MeasurementTypeAdapter.DataDescriptor', ...]:
        return self.actual_bias, self.signal

    def perform_measurement(self) -> tuple['MeasurementTypeAdapter.GeneratedData', ...]:
        return self.actual_bias.with_data(self.x_data), self.signal.with_data(self.y_data)

    def __init__(self, x_data: np.ndarray, y_data: np.ndarray):
        super().__init__()
        self.x_data = x_data
        self.y_data = y_data
        self.desired_bias = Axis(name='bias', range=x_data, unit='A')
        self.actual_bias = MeasurementTypeAdapter.DataDescriptor(
            name='actual_bias',
            axes=(self.desired_bias,),
            unit='A'
        )
        self.signal = MeasurementTypeAdapter.DataDescriptor(
            name='signal',
            axes=(self.desired_bias,),
            unit='V'
        )

def test_analysis(dummy_instruments_class):
    measure = DummyIVMeasurement(np.linspace(0, 10, 100), np.sin(np.linspace(0, 10, 100)))
    measure.with_analysis(SavgolNumericalDerivative())
    e = Experiment('analysis_test', SAMPLE)
    with e.sweep(lambda val: None, X_SWEEP_AXIS) as x_sweep:
        x_sweep.measure(measure)
    e.run(open_qviewkit=False)

def test_root_scalar_measurement(dummy_instruments_class):
    e = Experiment('root_test', SAMPLE)
    e.measure(DummyPointMeasurement('root_test'))
    e.run(open_qviewkit=False)

def test_time_series(dummy_instruments_class):
    e = Experiment('time_series', Sample())
    with e.timeseries(stop_after=time.time() + 1.0) as t:
        t.measure(ScalarMeasurement(name='signal', getter=lambda: np.random.rand()))
    e.run(open_qviewkit=True)