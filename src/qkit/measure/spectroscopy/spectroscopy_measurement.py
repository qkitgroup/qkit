import time

from qkit.measure.unified_measurements import MeasurementTypeAdapter, Axis
from qkit.drivers.AbstractVNA import AbstractVNA

class SpectroscopyMeasurement(MeasurementTypeAdapter):

    _vna: AbstractVNA
    _frequency_axis: Axis

    def __init__(self, vna: AbstractVNA):
        super().__init__()
        self._vna = vna
        self._frequency_axis = Axis(
            name='frequency',
            unit='Hz',
            range=vna.get_freqpoints()
        )

    @staticmethod
    def _phase_descriptor(frequency_axis: Axis):
        return MeasurementTypeAdapter.DataDescriptor(
            name="phase",
            unit="rad",
            axes=(frequency_axis,)
        )

    @staticmethod
    def _amplitude_descriptor(frequency_axis: Axis):
        return MeasurementTypeAdapter.DataDescriptor(
            name="amplitude",
            axes=(frequency_axis,)
        )

    @property
    def expected_structure(self) -> tuple['MeasurementTypeAdapter.DataDescriptor', ...]:
        return (
            self._amplitude_descriptor(self._frequency_axis),
            self._phase_descriptor(self._frequency_axis)
        )

    def perform_measurement(self) -> tuple['MeasurementTypeAdapter.GeneratedData', ...]:
        self._vna.pre_measurement()
        self._vna.start_measurement()
        while not self._vna.ready():
            time.sleep(0.1)
        amp, phase = self._vna.get_tracedata()
        self._vna.post_measurement()
        return (
            self._amplitude_descriptor(self._frequency_axis).with_data(amp),
            self._phase_descriptor(self._frequency_axis).with_data(phase)
        )