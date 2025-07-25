from typing import Any

from qkit.drivers.AbstractThermometer import AbstractThermometer
from qkit.measure.unified_measurements import MeasurementTypeAdapter


class ThermometryMeasurement(MeasurementTypeAdapter):

    _thermometer: AbstractThermometer
    _channel: Any
    _descriptor: MeasurementTypeAdapter.DataDescriptor


    def __init__(self, thermometer: AbstractThermometer, channel: Any, name: str = "temperature"):
        super().__init__()
        self._thermometer = thermometer
        self._channel = channel
        self._descriptor = MeasurementTypeAdapter.DataDescriptor(
            name=name,
            unit=self._thermometer.unit,
            axes=tuple()
        )


    @property
    def expected_structure(self) -> tuple['MeasurementTypeAdapter.DataDescriptor', ...]:
        return (
            self._descriptor,
        )

    def perform_measurement(self) -> tuple['MeasurementTypeAdapter.GeneratedData', ...]:
        return (
            self._descriptor.with_data(self._thermometer.get_temperature(self._channel)),
        )