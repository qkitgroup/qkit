import time
from dataclasses import dataclass
from enum import Enum
from time import sleep
from typing import override

import numpy as np
import itertools

from qkit.drivers.AbstractIVDevice import AbstractIVDevice
from qkit.measure.unified_measurements import MeasurementTypeAdapter, Axis
from qkit.storage.thin_hdf import HDF5


@dataclass(frozen=True)
class _MeasureMode:
    bias_symbol: str
    bias_unit: str
    measure_symbol: str
    measure_unit: str

class MeasureModes(Enum):
    IV = _MeasureMode('i', 'A', 'v', 'V')
    VI = _MeasureMode('v', 'V', 'i', 'A')

class TransportMeasurement(MeasurementTypeAdapter):

    _measurement_descriptors: list[tuple[MeasurementTypeAdapter.DataDescriptor, MeasurementTypeAdapter.DataDescriptor]]
    _iv_device: AbstractIVDevice
    _mode: MeasureModes
    _sleep: float

    def __init__(self, iv_device: AbstractIVDevice, mode: MeasureModes = MeasureModes.IV, sleep: float = 0):
        super().__init__()
        self._iv_device = iv_device
        self._mode = mode
        self._measurement_descriptors = []
        self._sleep = sleep
        if mode == MeasureModes.IV:
            assert iv_device.get_sweep_mode() == 1
        elif mode == MeasureModes.VI:
            assert iv_device.get_sweep_mode() == 2

    def add_sweep(self, start: float, stop: float, step: float):
        axis = Axis(
            name=f'{self._mode.value.bias_symbol}_{len(self._measurement_descriptors)}',
            unit=self._mode.value.bias_unit,
            range=np.arange(start, stop, step)
        )
        self._measurement_descriptors += (
            MeasurementTypeAdapter.DataDescriptor(
                name=f'{self._mode.value.bias_symbol}_b_{len(self._measurement_descriptors)}',
                unit=self._mode.value.bias_unit,
                axes=(axis,)
            ),
            MeasurementTypeAdapter.DataDescriptor(
                name=f'{self._mode.value.measure_symbol}_{len(self._measurement_descriptors)}',
                unit=self._mode.value.measure_unit,
                axes=(axis,)
            )
        )

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
        self.add_sweep(amplitude + offset, -amplitude + offset, step)
        self.add_sweep(-amplitude + offset, amplitude + offset, -step)

    @override
    @property
    def expected_structure(self) -> tuple['MeasurementTypeAdapter.DataDescriptor', ...]:
        return tuple(itertools.chain(*self._measurement_descriptors))

    @override
    @property
    def default_views(self) -> dict[str, HDF5.DataView]:
        return {
            'IV': HDF5.DataView(
                view_type=HDF5.DataViewType.ONE_D,
                view_sets=list(itertools.chain(
                    HDF5.DataViewSet(
                        x_path= HDF5.DataReference(b.name),
                        y_path= HDF5.DataReference(m.name),
                    ) for (b, m) in self._measurement_descriptors
                ))
            ),
        }

    @override
    def perform_measurement(self) -> tuple['MeasurementTypeAdapter.GeneratedData', ...]:
        results = []
        for (bias, measurement) in self._measurement_descriptors:
            intended_bias_values = bias.axes[0].range
            bias_data, measurement_data = self._iv_device.take_IV(intended_bias_values)
            results.append((
                bias.with_data(bias_data),
                measurement.with_data(measurement_data)
            ))
            time.sleep(self._sleep)
        return tuple(itertools.chain(*results))



