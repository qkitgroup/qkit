"""Module to provide a high-level possibility to arange pulses for an experiment."""

import numpy as np
import collections


class Shape(np.vectorize):
    """
    A vectorized function describing a possible shape
    defined on the standardized interval [0,1).
    """
    # TODO: Add multiplication later

    def __mul__(self, other):
        return Shape(lambda x: self.pyfunc(x) * other.pyfunc(x))


class ShapeLib(object):
    """Object containing pre-defined pulse shapes."""

    def __init__(self):
        self.rect = Shape(lambda x: np.where(x >= 0 and x < 1, 1, 0))
        self.gauss = Shape(
            lambda x: np.exp(-0.5 * np.power((x - 0.5) / 0.166, 2.0))
        ) * self.rect


# Make ShapeLib a singleton:
ShapeLib = ShapeLib()


class Pulse(object):
    """Class to describe a single pulse."""

    def __init__(self, length, shape=ShapeLib.rect, amplitude=1, frequency_shift=0):
        self.length = length  # type: float
        self.shape = shape  # type: Shape
        self.amplitude = amplitude  # type: complex
        self.frequency_shift = frequency_shift  # type: float

        if frequency_shift != 0:
            raise ValueError("Non-zero frequency shift is not yet supported.")

    def get_envelope(self, timestep):
        """Returns the envelope of the pulse as array with given time steps."""
        # TODO: Implement frequency shift (then remove error in init)
        time_fractions = np.arange(0, self.length, timestep) / self.length
        return self.amplitude * self.shape(time_fractions)


class PulseSequence(object):
    """Class to arange pulses for a time-domain experiment."""
    pulses = dict([])

    def add(self, time, pulse):
        """Add a pulse starting at a given time to the sequence."""
        self.pulses[time] = pulse

    def add_readout(self, time):
        """Add a readout pulse to the sequence."""
        # TODO Maybe think of better alternative than type mixing?
        self.pulses[time] = "Readout"

    @property
    def length(self):
        """The current length of the sequence."""
        if not self.pulses:
            # If no pulses in the dictionary the length of the sequence is zero.
            return 0
        # find out how long the sequence is
        return np.max([
            t + (p.length if isinstance(p, Pulse) else 0)
            for t, p in self.pulses.iteritems()
        ])

    def get_pulse_dict(self):
        return collections.OrderedDict(sorted(self.pulses.items(), key=lambda t: t[0]))

    def get_waveform(self, timestep):
        """Returns the envelope of the whole pulse sequence with given time steps."""
        times = np.arange(0, self.length + timestep, timestep)
        waveform = np.zeros(len(times), complex)

        # Sorting the pulse start times makes generating the waveform less expensive
        pulses = self.get_pulse_dict()

        index = 0
        for pulse_time, pulse in pulses.iteritems():
            # As times are floats, strict equality checks are senseless
            # so we use np.isclose to match nearly equal time values
            while not np.isclose(times[index], pulse_time, rtol=0, atol=timestep / 10) \
                    and times[index] < pulse_time:
                index = index + 1
            # assert: index points to first time where pulse starting at time t plays a role

            if not isinstance(pulse, Pulse):
                # Only a marker pulse -> not visible in waveform
                continue

            pulse_envelope = pulse.get_envelope(timestep)
            waveform[index:(index + len(pulse_envelope))] += pulse_envelope

        return waveform
