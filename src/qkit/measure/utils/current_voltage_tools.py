import time
from dataclasses import dataclass
from typing import TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from qkit.drivers.qdevil_qdacII import qdevil_qdacII


class CurrentControl:
    """
    Assumes half-isolated unbalanced wiring to control the current flowing through flux coils more precisely.

    A typical sample configuration is to have one side of each flux coil connected to a shared sample box ground,
    while the other side is connected to a filtered line. The filtered lines are isolated, but have resistance.
    If the return path has a finite resistance, then there will be cross-talk if there is only voltage control.

    This class attempts to implement current control. We assume we have sole control of the device.
    """



    def __init__(self, qdevil: 'qdevil_qdacII', channels: list[int], test_voltage: float = 0.2):
        self.qdevil = qdevil

        def measure_resistance(channel):
            self.qdevil.set_voltage(channel, test_voltage)
            time.sleep(0.1)
            current = self.qdevil.get_corrected_current(channel)
            return test_voltage / current

        self.resistances = {channel: measure_resistance(channel) for channel in channels}

    def set_indexed_voltages(self, channels, voltages):
        for channel, voltage in zip(channels, voltages):
            self.qdevil.set_voltage(channel, voltage)

    def get_indexed_currents(self, channels):
        return np.asarray([self.qdevil.get_corrected_current(channel) for channel in channels])

    def set_currents(self, setpoints: dict[int, float], rel_epsilon: float = 0.001, max_iter: int = 10):
        assert all([key in self.resistances for key in setpoints.keys()]), "Control lines must be pre-specified!"
        epsilon = np.max(np.abs(np.array(setpoints.values()))) * rel_epsilon

        channels, currents = np.asarray(setpoints.keys()), np.asarray(setpoints.values())
        resistances = np.asarray([self.resistances[channel] for channel in channels])
        guess = resistances * currents
        for i in range(max_iter):
            self.set_indexed_voltages(channels, guess)
            time.sleep(0.1)
            actual_currents = self.get_indexed_currents(channels)
            difference = currents - actual_currents
            if np.all(np.abs(difference) < epsilon):
                return
            guess += difference * resistances
        raise RuntimeError("Did not converge!")

