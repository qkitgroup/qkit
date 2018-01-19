"""Module to provide a high-level possibility to arange pulses for an experiment."""

import collections
import numpy as np


class Shape(np.vectorize):
    """
    A vectorized function describing a possible shape
    defined on the standardized interval [0,1).
    """

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

    def __call__(self, time_fractions):
        # Pulse class can be called like a vectorized function!
        # TODO: Implement frequency shift (then remove error in init)
        return self.amplitude * self.shape(time_fractions)

    def get_envelope(self, samplerate):
        """Returns the envelope of the pulse as array with given time steps."""
        timestep = 1.0 / samplerate
        time_fractions = np.arange(0, self.length, timestep) / self.length
        return self(time_fractions)


class PulseSequence(object):
    """Class to arange pulses for a time-domain experiment."""
    
    def __init__(self):
        self.pulses = dict([])
        self._current_time = 0

    def add(self, pulse):
        """Add a pulse to the sequence."""
        self.pulses[self._current_time] = pulse

    def add_readout(self):
        """Add a readout pulse to the sequence."""
        # TODO Maybe think of better alternative than type mixing?
        self.pulses[self._current_time] = "Readout"
    
    def wait(self, delay):
        """Add a delay (in seconds) to the sequence."""
        self._current_time += delay

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
        """Returns all pulses in an ordered dictionary with starting time as key."""
        return collections.OrderedDict(sorted(self.pulses.items(), key=lambda t: t[0]))

    def get_waveform(self, samplerate):
        """Returns the envelope of the whole pulse sequence with given time steps."""
        timestep = 1.0 / samplerate
        times = np.arange(0, self.length + timestep, timestep)
        waveform = np.zeros(len(times), complex)

        # Sorting the pulse start times makes generating the waveform less expensive
        pulses = self.get_pulse_dict()

        index = 0
        for pulse_time, pulse in pulses.iteritems():
            while times[index] < pulse_time:
                index = index + 1
            # assert: index points to first time where pulse starting at time t plays a role

            if not isinstance(pulse, Pulse):
                # Only a marker pulse -> not visible in waveform
                continue

            sample_length = int(np.ceil(pulse.length / timestep))
            time_fractions = (
                times[index:(index + sample_length)] - pulse_time) / pulse.length
            waveform[index:(index + sample_length)] += pulse(time_fractions)

        return waveform
