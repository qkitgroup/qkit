import enum
from abc import ABC, abstractmethod
from typing import Callable, Optional, Literal

import numpy as np
import scipy.signal

from qkit.measure.unified_measurements import AnalysisTypeAdapter, MeasurementTypeAdapter, DataView

class ResonatorTrackingMethod(ABC):
    @abstractmethod
    def find_resonator(self, data: tuple['MeasurementTypeAdapter.GeneratedData', ...]):
        """
        Determine the resonator frequency from the given data.

        It is up to the implementation to identify the correct trace, and how to derive the resonator frequency.
        """
        pass

class AbsorptionMaximumTracker(ResonatorTrackingMethod):

    _data_index: Optional[int]
    _direction: Literal['maximum', 'minimum']

    def __init__(self, data_index: Optional[int] = None, direction: Literal['maximum', 'minimum'] = 'minimum'):
        self._data_index = data_index
        self._direction = direction

    def find_resonator(self, data: tuple['MeasurementTypeAdapter.GeneratedData', ...]):
        if self._data_index is not None:
            trace = data[self._data_index]
        elif len(data) == 1:
            trace = data[0]
        else:
            # Check if there is any trace named mag or amp (or something like that)
            candidates = [trace for trace in data if "mag" in trace.descriptor.name.lower() or "amp" in trace.descriptor.name.lower()]
            if len(candidates) == 1:
                trace = candidates[0]
            else:
                raise ValueError("Could not find a suitable trace to track the resonator frequency. Specify manually.")
        if self._direction == 'maximum':
            index = np.argmax(trace.data)
        elif self._direction == 'minimum':
            index = np.argmin(trace.data)
        else:
            raise ValueError("Invalid direction. Must be either 'maximum' or 'minimum'.")
        return trace.descriptor.axes[-1].range[index]

class PhaseSlopeTracker(ResonatorTrackingMethod):

    _data_index: Optional[int]

    def __init__(self, data_index: Optional[int] = None):
        self._data_index = data_index

    def find_resonator(self, data: tuple['MeasurementTypeAdapter.GeneratedData', ...]):
        if self._data_index is not None:
            trace = data[self._data_index]
        elif len(data) == 1:
            trace = data[0]
        else:
            # Check if there is any trace named mag or amp (or something like that)
            candidates = [trace for trace in data if "phase" in trace.descriptor.name.lower()]
            if len(candidates) == 1:
                trace = candidates[0]
            else:
                raise ValueError("Could not find a suitable trace to track the resonator frequency. Specify manually.")
        slope = scipy.signal.savgol_filter(np.unwrap(trace.data), 11, 3, deriv=1)
        index = np.argmax(np.abs(slope))
        return trace.descriptor.axes[-1].range[index]


class ResonatorTracker(AnalysisTypeAdapter):

    _tracking_method: ResonatorTrackingMethod
    _data_descriptor: 'MeasurementTypeAdapter.DataDescriptor'
    _listener: Callable[[float], None]

    def __init__(self, tracking_method: ResonatorTrackingMethod, listener: Callable[[float], None] = None):
        """
        Track the resonator frequency using the given tracking method and store it.

        If a listener is given, it will be called with the frequency every time the resonator is tracked.
        """
        super().__init__()
        self._tracking_method = tracking_method
        self._data_descriptor = MeasurementTypeAdapter.DataDescriptor(f"res_frequency", axes=(), unit="Hz", category="analysis")
        self._listener = listener

    def expected_structure(self, parent_schema: tuple['MeasurementTypeAdapter.DataDescriptor', ...]) -> tuple[
        'MeasurementTypeAdapter.DataDescriptor', ...]:
        return (self._data_descriptor,)

    def default_views(self, parent_schema: tuple['MeasurementTypeAdapter.DataDescriptor', ...]) -> dict[
        str, "DataView"]:
        return {}

    def perform_analysis(self, data: tuple['MeasurementTypeAdapter.GeneratedData', ...]) -> tuple[
        'MeasurementTypeAdapter.GeneratedData', ...]:
        freq = self._tracking_method.find_resonator(data)
        if self._listener:
            self._listener(freq)
        return (self._data_descriptor.with_data(freq),)