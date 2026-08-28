from typing import Callable

import numpy as np

from qkit.measure.unified_measurements import AnalysisTypeAdapter, MeasurementTypeAdapter


class RabiPeakTracker(AnalysisTypeAdapter):

    def __init__(self, dataset_phrase : str, post_hook: Callable[[float], None]) -> None:
        self.dataset_phrase = dataset_phrase
        self.post_hook = post_hook
        self.result_descriptor = MeasurementTypeAdapter.DataDescriptor("rabi_peak", tuple(), unit='Hz', category='analysis')

    def expected_structure(self, parent_schema: tuple['MeasurementTypeAdapter.DataDescriptor', ...]) -> tuple[
        'MeasurementTypeAdapter.DataDescriptor', ...]:
        return (self.result_descriptor,)

    def perform_analysis(self, data: tuple['MeasurementTypeAdapter.GeneratedData', ...]) -> tuple[
        'MeasurementTypeAdapter.GeneratedData', ...]:
        data = [datum for datum in data if self.dataset_phrase in datum.descriptor.name][0]
        x_axis = data.descriptor.axes[0].range
        signal_strength = np.std(data.data, axis=-1)
        maximum_frequency = x_axis[np.argmax(signal_strength)]
        self.post_hook(maximum_frequency)
        return (self.result_descriptor.with_data(maximum_frequency),)

