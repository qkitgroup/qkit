import time
from dataclasses import dataclass
from enum import Enum
from time import sleep

import numpy as np
import itertools

from qkit.drivers.AbstractIVDevice import AbstractIVDevice
from qkit.measure.unified_measurements import MeasurementTypeAdapter, Axis, DataView, DataViewSet, DataReference


@dataclass(frozen=True)
class _MeasureMode:
    bias_symbol: str
    bias_unit: str
    measure_symbol: str
    measure_unit: str

class MeasureModes(Enum):
    """
    TODO DocString BiasSense (?)
    """
    IV = _MeasureMode('i', 'A', 'v', 'V')
    VI = _MeasureMode('v', 'V', 'i', 'A')

class TransportMeasurement(MeasurementTypeAdapter):

    _measurement_descriptors: list[tuple[MeasurementTypeAdapter.DataDescriptor, MeasurementTypeAdapter.DataDescriptor]]
    _sweep_parameters: list[tuple[float, float, float]]
    _iv_device: AbstractIVDevice
    _mode: MeasureModes
    _sleep: float
    _extend_range: bool

    def __init__(self, iv_device: AbstractIVDevice, mode: MeasureModes = MeasureModes.IV, sleep: float = 0, extend_range=False):
        super().__init__()
        self._iv_device = iv_device
        self._mode = mode
        self._measurement_descriptors = []
        self._sweep_parameters = []
        self._sleep = sleep
        self._extend_range = extend_range
        if mode == MeasureModes.IV:
            assert iv_device.get_sweep_bias() == 0
        elif mode == MeasureModes.VI:
            assert iv_device.get_sweep_bias() == 1

    def add_sweep(self, start: float, stop: float, step: float):
        axis = Axis(
            name=f'{self._mode.value.bias_symbol}_b_{len(self._measurement_descriptors)}',
            unit=self._mode.value.bias_unit,
            range=np.arange(start, stop if not self._extend_range else (stop + step/2), step)
        )
        self._sweep_parameters += [(start, stop, step)] # TODO: Refactor by lazy DataDescriptor creation based on sweep parameters
        self._measurement_descriptors += [(
            MeasurementTypeAdapter.DataDescriptor(
                name=f'{self._mode.value.bias_symbol}_{len(self._measurement_descriptors)}',
                unit=self._mode.value.bias_unit,
                axes=(axis,)
            ),
            MeasurementTypeAdapter.DataDescriptor(
                name=f'{self._mode.value.measure_symbol}_{len(self._measurement_descriptors)}',
                unit=self._mode.value.measure_unit,
                axes=(axis,)
            )
        )]

    def add_4_quadrant_sweep(self, start: float, stop: float, step: float, offset: float = 0):
        """
        Adds a four quadrants sweep series with the pattern
            0th: (+<start> --> +<stop>,  <step>) + <offset>
            1st: (+<stop>  --> +<start>, <step>) + <offset>
            2nd: (+<start> --> -<stop>,  <step>) + <offset>
            3rd: (-<stop>  --> +<start>, <step>) + <offset>
            time.sleep(<sleep>)

        Parameters
        ----------
        start: float
            Start value of sweep.
        stop: float
            Stop value of sweep.
        step: float
            Step value of sweep.
        offset: float, optional
            Offset value by which <start> and <stop> are shifted. Default is 0.
        """
        self.add_sweep(start + offset, stop + offset, step)
        self.add_sweep(stop + offset, start + offset, step)
        self.add_sweep(start + offset, - stop + offset, step)
        self.add_sweep(-stop + offset, start + offset, step)

    def add_half_swing_sweep(self, amplitude: float, step: float, offset: float = 0):
        """
        Adds a halfswing sweep series with the pattern
            0th: (+<amplitude> --> -<amplitude, <step>) + <offset>
            1st: (-<amplitude> --> +<amplitude, <step>) + <offset>
            time.sleep(<sleep>)

        Parameters
        ----------
        amplitude: float
            Amplitude value of sweep.
        step: float
            Step value of sweep.
        offset: float
            Offset value by which <start> and <stop> are shifted. Default is 0.
        """
        self.add_sweep(amplitude + offset, -amplitude + offset, -step)
        self.add_sweep(-amplitude + offset, amplitude + offset, step)

    @property
    def expected_structure(self) -> tuple['MeasurementTypeAdapter.DataDescriptor', ...]:
        return tuple(itertools.chain(*self._measurement_descriptors))

    @property
    def default_views(self) -> dict[str, DataView]:
        return {
            'IV': DataView(
                view_params={
                    "labels": ('V', 'I'),
                    'plot_style': 1,
                    'markersize': 5
                },
                view_sets=list(itertools.chain(
                    DataViewSet(
                        x_path = DataReference(b.name if self._mode == MeasureModes.VI else m.name),
                        y_path = DataReference(m.name if self._mode == MeasureModes.VI else b.name),
                    ) for (b, m) in self._measurement_descriptors
                ))
            ),
            'VI': DataView(
                view_params={
                    "labels": ('I', 'V'),
                    'plot_style': 1,
                    'markersize': 5
                },
                view_sets=list(itertools.chain(
                    DataViewSet(
                        x_path = DataReference(b.name if self._mode == MeasureModes.IV else m.name),
                        y_path = DataReference(m.name if self._mode == MeasureModes.IV else b.name),
                    ) for (b, m) in self._measurement_descriptors
                ))
            ),
        }

    def perform_measurement(self) -> tuple['MeasurementTypeAdapter.GeneratedData', ...]:
        results = []
        for ((bias, measurement), sweep_params) in zip(self._measurement_descriptors, self._sweep_parameters):
            bias_data, measurement_data = self._iv_device.take_IV((*sweep_params, self._sleep))
            results.append((
                bias.with_data(bias_data),
                measurement.with_data(measurement_data)
            ))
            time.sleep(self._sleep)
        return tuple(itertools.chain(*results))



