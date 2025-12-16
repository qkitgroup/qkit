import numpy as np

from qkit.measure.unified_measurements import AnalysisTypeAdapter, MeasurementTypeAdapter, DataView, Axis
from qkit.measure.laboneq_measurement import LabOneQMeasurement


class ZIPowerFromAmplitude(AnalysisTypeAdapter):
    """
    An analysis converting the amplitude measurements and axis returned by Zurich Instruments devices into powers (dBm).

    Our other devices usually return power, and most people are used to seeing and working with decibels.
    """

    _convert_datasets: dict[str, str] = None
    _convert_axes: dict[str, str] = None
    _generated_datasets: dict[str, MeasurementTypeAdapter.DataDescriptor] = None

    def __init__(self, output_range: float, convert_datasets: None | dict[str, str] = None, convert_axes: None | dict[str, str] = None):
        self._convert_datasets = convert_datasets
        self._convert_axes = convert_axes
        self._output_range = output_range

    def _should_convert_dataset(self, schema: 'MeasurementTypeAdapter.DataDescriptor') -> bool:
        if self._convert_datasets is None:
            return schema.name.endswith("_mag")
        else:
            return schema.name in self._convert_datasets

    def _map_dataset_name(self, schema: 'MeasurementTypeAdapter.DataDescriptor') -> str:
        assert self._should_convert_dataset(schema)
        if self._convert_datasets is None:
            return schema.name.replace("_mag", "_power")
        else:
            return self._convert_datasets[schema.name]

    def _should_convert_axis(self, axis: Axis) -> bool:
        if self._convert_axes is None:
            return axis.name.startswith("amplitudes")
        else:
            return axis.name in self._convert_axes

    def _map_axis_name(self, axis: Axis) -> str:
        assert self._should_convert_axis(axis)
        if self._convert_axes is None:
            return axis.name.replace("amplitudes", "powers")
        else:
            return self._convert_axes[axis.name]

    @staticmethod
    def amplitude_to_power(amplitudes: np.ndarray) -> np.ndarray:
        return 30 + 20 * np.log10(amplitudes) # Power at 50 Ohm impedance, amplitudes in Volts, dBm

    def _map_axes(self, axes: tuple[Axis, ...]) -> tuple[Axis, ...]:
        return tuple(
            Axis(self._map_axis_name(a), LabOneQMeasurement.calculate_powers(a.range, self._output_range), 'dBm') if self._should_convert_axis(a) else a
            for a in axes
        )

    def expected_structure(self, parent_schema: tuple['MeasurementTypeAdapter.DataDescriptor', ...]) -> tuple[
        'MeasurementTypeAdapter.DataDescriptor', ...]:
        self._generated_datasets: dict[str, MeasurementTypeAdapter.DataDescriptor] = {
            schema.name: MeasurementTypeAdapter.DataDescriptor(self._map_dataset_name(schema), self._map_axes(schema.axes), "dBm?", schema.category)
            for schema in parent_schema if self._should_convert_dataset(schema)
        }
        return tuple(self._generated_datasets.values())

    def default_views(self, parent_schema: tuple['MeasurementTypeAdapter.DataDescriptor', ...]) -> dict[
        str, "DataView"]:
        # We don't add any additional views.
        return dict()

    def perform_analysis(self, data: tuple['MeasurementTypeAdapter.GeneratedData', ...]) -> tuple[
        'MeasurementTypeAdapter.GeneratedData', ...]:
        return tuple(
            self._generated_datasets[datum.descriptor.name].with_data(self.amplitude_to_power(datum.data))
            for datum in data if datum.descriptor.name in self._generated_datasets
        )

