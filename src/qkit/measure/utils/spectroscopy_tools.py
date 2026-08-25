from abc import ABC, abstractmethod
from typing import Callable, Optional, Literal, Any

import numpy as np
from numpy import signedinteger
from scipy import signal

from qkit.measure.unified_measurements import AnalysisTypeAdapter, MeasurementTypeAdapter, DataView

class ResonatorTrackingMethod(ABC):

    _data_index: Optional[int]
    _fallback_phrases: list[str]

    def __init__(self, fallback_phrases: list[str], data_index: Optional[int] = None):
        self._data_index = data_index
        self._fallback_phrases = fallback_phrases

    def _select_data(self, data: tuple['MeasurementTypeAdapter.GeneratedData', ...]) -> MeasurementTypeAdapter.GeneratedData:
        if self._data_index is not None:
            return data[self._data_index]
        elif len(data) == 1:
            return data[0]
        else:
            # Check if there is any trace named mag or amp (or something like that)
            candidates = [trace for trace in data if any([phrase in trace.descriptor.name.lower() for phrase in self._fallback_phrases])]
            if len(candidates) == 1:
                return candidates[0]
            else:
                raise ValueError("Could not find a suitable trace to track the resonator frequency. Specify manually.")

    @abstractmethod
    def find_resonance(self, data: tuple['MeasurementTypeAdapter.GeneratedData', ...]):
        """
        Determine the resonator frequency from the given data.

        It is up to the implementation to identify the correct trace, and how to derive the resonator frequency.
        """
        pass

class AbsorptionMaximumTracker(ResonatorTrackingMethod):

    _direction: Literal['maximum', 'minimum']

    def __init__(self, data_index: Optional[int] = None,
                 direction: Literal['maximum', 'minimum'] = 'minimum'):
        super().__init__(['mag', 'amp'], data_index)
        self._direction = direction

    def find_resonance(self, data: tuple['MeasurementTypeAdapter.GeneratedData', ...]):
        trace = self._select_data(data)
        if self._direction == 'maximum':
            index = np.argmax(trace.data)
        elif self._direction == 'minimum':
            index = np.argmin(trace.data)
        else:
            raise ValueError("Invalid direction. Must be either 'maximum' or 'minimum'.")
        return trace.descriptor.axes[-1].range[index]

class PhaseSlopeTracker(ResonatorTrackingMethod):

    def __init__(self, data_index: Optional[int] = None):
        super().__init__(['phase'], data_index)

    def find_resonance(self, data: tuple['MeasurementTypeAdapter.GeneratedData', ...]):
        trace = self._select_data(data)
        slope = signal.savgol_filter(np.unwrap(trace.data), 11, 3, deriv=1)
        index = np.argmax(np.abs(slope))
        return trace.descriptor.axes[-1].range[index]

class ModelGuidedExtremumTracker(ResonatorTrackingMethod):
    """
    Track the strongest extremum, biased by a model. This server to track qubit resonances in noisy environments.
    """
    _model: Callable[[], float]
    _bias_scale: float

    def __init__(self, model: Callable[[], float], fallback_phrases: list[str], bias_scale: float = 2e6, filter_scale= 2e6,
                 data_index: Optional[int] = None):
        """
        :param model: Callable[[], float] A function returning the expected resonance frequency.
        :param bias_scale: Scale factor for biasing deviations from the base line.
        :param data_index: An optional integer specifying the index of the data to track.
        """
        super().__init__(fallback_phrases, data_index)
        self._model = model
        self._bias_scale = bias_scale
        self._filter_scale = filter_scale

    def _find_peak(self, data: np.ndarray, frequencies: np.ndarray) -> signedinteger[Any]:
        sos = signal.butter(1, 1 / self._filter_scale, btype='highpass', output='sos')
        filtered = signal.sosfilt(sos, data)
        model_deviation = frequencies - self._model()
        gaussian = np.exp(- model_deviation ** 2 / (2 * self._bias_scale ** 2))
        return np.argmax(np.abs(filtered * gaussian))

    def find_resonance(self, data: tuple['MeasurementTypeAdapter.GeneratedData', ...]):
        trace = self._select_data(data)
        # derive a baseline by smoothing at the bias scale.
        return trace.descriptor.axes[-1].range[self._find_peak(trace.data, trace.descriptor.axes[0].range)]


class ResonanceTracker(AnalysisTypeAdapter):

    _tracking_method: ResonatorTrackingMethod
    _data_descriptor: 'MeasurementTypeAdapter.DataDescriptor'
    _listener: Callable[[float], None]

    def __init__(self, tracking_method: ResonatorTrackingMethod, listener: Callable[[float], None] = None, resonance_name: str = "res"):
        """
        Track the resonator frequency using the given tracking method and store it.

        If a listener is given, it will be called with the frequency every time the resonator is tracked.
        """
        super().__init__()
        self._tracking_method = tracking_method
        self._data_descriptor = MeasurementTypeAdapter.DataDescriptor(f"{resonance_name}_frequency", axes=(), unit="Hz", category="analysis")
        self._listener = listener

    def expected_structure(self, parent_schema: tuple['MeasurementTypeAdapter.DataDescriptor', ...]) -> tuple[
        'MeasurementTypeAdapter.DataDescriptor', ...]:
        return (self._data_descriptor,)

    def default_views(self, parent_schema: tuple['MeasurementTypeAdapter.DataDescriptor', ...]) -> dict[
        str, "DataView"]:
        return {}

    def perform_analysis(self, data: tuple['MeasurementTypeAdapter.GeneratedData', ...]) -> tuple[
        'MeasurementTypeAdapter.GeneratedData', ...]:
        freq = self._tracking_method.find_resonance(data)
        if self._listener:
            self._listener(freq)
        return (self._data_descriptor.with_data(freq),)