from qkit.measure.measurement_base import Experiment, MeasurementTypeAdapter, Axis
import numpy as np

X_SWEEP_AXIS = Axis(name='x', range=np.array(range(0, 10)))


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

    @property
    def expected_structure(self) -> list['MeasurementTypeAdapter.MeasurementDescriptor']:
        return [self.sweep_intercept]

    def perform_measurement(self) -> list['MeasurementTypeAdapter.MeasurementData']:
        return [self.sweep_intercept.with_data(self.current_x)]


def test_experiment_creation():
    log_measure = SweepInspectorMeasurement()
    e = Experiment()
    with e.sweep(lambda val: log_measure.x_log(val), X_SWEEP_AXIS) as x_sweep:
        x_sweep.measure(log_measure)
    e.run()
    assert np.array_equal(np.asarray(log_measure.accumulated_data), X_SWEEP_AXIS.range)


def test_filtered_sweep():
    log_measure = SweepInspectorMeasurement()
    e = Experiment()
    with e.sweep(lambda val: log_measure.x_log(val),
                 X_SWEEP_AXIS,
                 axis_filter=lambda r: np.logical_and(r <= 8, r >= 2)) as x_sweep:
        x_sweep.measure(log_measure)
    e.run()
    assert np.array_equal([2, 3, 4, 5, 6, 7, 8], log_measure.accumulated_data)
