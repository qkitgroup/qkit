from typing import Any

from qkit.drivers.AbstractThermometer import AbstractThermometer
from qkit.measure.measurement_base import MeasurementTypeAdapter


class ThermometryMeasurement(MeasurementTypeAdapter):

    _thermometer: AbstractThermometer
    _channel: Any
    _descriptor: MeasurementTypeAdapter.MeasurementDescriptor


    def __init__(self, thermometer: AbstractThermometer, channel: Any, name: str = "temperature"):
        self._thermometer = thermometer
        self._channel = channel
        self._descriptor = MeasurementTypeAdapter.MeasurementDescriptor(
            name=name,
            unit=self._thermometer.unit,
            axes=tuple()
        )


    @property
    def expected_structure(self) -> tuple['MeasurementTypeAdapter.MeasurementDescriptor', ...]:
        return (
            self._descriptor,
        )

    def perform_measurement(self) -> tuple['MeasurementTypeAdapter.MeasurementData', ...]:
        return (
            self._descriptor.with_data(self._thermometer.get_temperature(self._channel)),
        )