"""Module to provide a high-level possibility to arange pulses for an experiment."""

import numpy as np
import matplotlib.pyplot as plt
from inspect import getargspec as getargspec
from inspect import getsourcelines as getsourcelines
import logging

class Shape(np.vectorize):
    """
    A vectorized function describing a possible shape
    defined on the standardized interval [0,1).
    """
    def __init__(self, name, func, *args, **kwargs):
        self.name = name
        super(Shape, self).__init__(func, *args, **kwargs)

    def __mul__(self, other):
        return Shape(self.name, lambda x: self.pyfunc(x) * other.pyfunc(x))


class ShapeLib(object):
    """
    Object containing pre-defined pulse shapes.
    Currently implemented: rect, gauss
    """

    def __init__(self):
        self.rect = Shape("rect", lambda x: np.where(x >= 0 and x < 1, 1, 0))
        self.gauss = Shape("gauss", lambda x: np.exp(-0.5 * np.power((x - 0.5) / 0.166, 2.0))) * self.rect


# Make ShapeLib a singleton:
ShapeLib = ShapeLib()


class Pulse(object):
    """
    Class to describe a single pulse.
    """

    def __init__(self, length, shape=ShapeLib.rect, name = None, amplitude=1, frequency_shift=0):
        """
        Input:
            length          - length of the pulse. This can also be a (lambda) function for variable pulse lengths.
            shape           - pulse shape (i.e. rect, gauss, ...)
            name            - name you want to give your pulse (i.e. pi-pulse, ...)
            amplitude       - relative amplitude of your pulse
            frequency_shift - frequency shift of your pulse (currently not implemented)
        """
        self.length = length  # type: float or string
        self.shape = shape
        self.name = name
        self.amplitude = amplitude  # type: complex
        self.frequency_shift = frequency_shift  # type: float

        if frequency_shift != 0:
            raise ValueError("Non-zero frequency shift is not yet supported.")

    def __call__(self, time_fractions):
        # Pulse class can be called like a vectorized function!
        # TODO: Implement frequency shift (then remove error in init)
        return self.amplitude * self.shape(time_fractions)

    def get_envelope(self, samplerate):
        """
        Returns the envelope of the pulse as array with given time steps.
        """
        timestep = 1.0 / samplerate
        if callable(self.length):
            print("This pulse has a variable length.")
            return 0
        time_fractions = np.arange(0, self.length, timestep) / self.length
        return self(time_fractions)


class PulseSequence(object):
    """
    Class for aranging pulses for a time-domain experiment.
    Sequence objects are callable, returning the sequence envelope for a given time step.

    Important functions:
        add         - adds a given pulse to the experiment
        add_wait    - adds a wait time
        add_readout - adds the readout to the experiment
        plot        - plots schematic of the sequence
        get_pulses  - returns list of currently added pulses and their properties.
    Add wait as variable times in the experiment.
    Add readout to let devices know when readout happens and to synchornize different channels.
    """
    
    def __init__(self, sample = None, samplerate = None):
        """
        Input:
            sample     - Sample object
            samplerate - Samplerate of your device
        """
        self._pulses = []
        self._sample = sample
        if self._sample:
            self.samplerate = sample.clock
        else:
            self.samplerate = samplerate
        self._varnum = 0
        self._cols = ["C0" ,"C1", "C2", "C3", "C4", "C5", "C6", "C8", "C9", "r", "g", "b", "y", "k", "m"]
        self._cols_temp = self._cols[:]
        self._pulse_cols = {"readout": "C7", "wait": "w"}

    def __call__(self, *args):
        """
        Returns the envelope of the whole pulse sequence for the input time.
        Also returns the index where the readout pulse starts. 
        If no readout tone is found it is assumed to be at the end of the sequence.
        """
        readout_index = -1
        if len(args) < self._varnum:
            print("Insufficient number of arguments.")
            return
        elif len(args) > self._varnum:
            print("To many arguments given. Omitting excess arguments.")
            args = args[:self._varnum]
        
        if not self.samplerate:
            print("Sequence call requires samplerate.")
            return

        timestep = 1.0 / self.samplerate
        waveform = np.zeros(1)
        index = 1 #index of current waveform
        length = 0 #length of current waveform

        for pulse_dict in self._pulses:
            # Determine length of the pulse
            if isinstance(pulse_dict["length"], float):
                length = pulse_dict["length"]
            elif callable(pulse_dict["length"]):
                length = pulse_dict["length"](*args)
            elif pulse_dict["length"] is None:
                length = 0
            if (pulse_dict["name"] is "readout") and (self._pulses[-1] is pulse_dict):
                length = 0
            # write pulse into sequence
            if pulse_dict["name"] is "wait":
                wfm = np.zeros(int(round(length * self.samplerate)))
            elif pulse_dict["name"] is "readout":
                wfm = np.zeros(int(round(length * self.samplerate)))
                readout_index = index
            else:
                if length > 0.5*timestep:
                    wfm = pulse_dict["pulse"](np.arange(0, length, timestep) / length)
                else:
                    wfm = np.zeros(0)
            
            if (length < 0.5*timestep) and (length != 0):
                logging.warning("{:}-pulse is shorter than {:.2f} nanoseconds and thus is omitted.".format(pulse_dict["name"], 0.5*timestep*1e9))

            # Append wfm to waveform: Make sure waveform is long enough and account for skipping
            wfm = np.atleast_1d(wfm)
            waveform = np.append(waveform, np.zeros(max(0, len(wfm) - len(waveform) + index)))
            waveform[index:index + len(wfm)] += wfm
            if not pulse_dict["skip"]:
                index = len(waveform)
        
        if readout_index == -1:
            readout_index = len(waveform)

        return waveform, readout_index

    def add(self, pulse, skip = False):
        """
        Add a pulse object to the sequence.
        If skip is True the next pulse in the sequence will not wait until this pulse is finished (i.e. they happen at the same time).
        """
        pulse_dict = {}
        if pulse.name in ["readout", "wait"]:
            print(pulse.name + " is not permitted as pulse name.")
            print("Pulse name set to None.")
            pulse_dict["name"] = None
        else:
            pulse_dict["name"] = pulse.name
        pulse_dict["shape"] = pulse.shape.name
        if isinstance(pulse.length, float):
            pulse_dict["length"] = pulse.length
        elif callable(pulse.length):
            pulse_dict["length"] = pulse.length
            varnum = len(getargspec(pulse.length)[0])
            if self._varnum is 0:
                self._varnum = varnum
            elif self._varnum is varnum:
                pass
            else:
                print("Number of variable does not match previously added pulses/wait times!")
                return self
        else:
            print("Pulse length not understood.")
            return self
        pulse_dict["pulse"] = pulse
        pulse_dict["skip"] = skip
        self._pulses.append(pulse_dict)
        return self

    def add_wait(self, time):
        """
        Add a wait time to the sequence.
        Using a (lambda) function makes the wait time variable.
        """
        pulse_dict = {}
        pulse_dict["name"] = "wait"
        
        if callable(time):
            pulse_dict["length"] = time
            varnum = len(getargspec(time)[0])
            if self._varnum is 0:
                self._varnum = varnum
            elif self._varnum is varnum:
                pass
            else:
                print("Number of variable does not match previously added pulses/wait times!")
                return self
        elif isinstance(time, float):
            pulse_dict["length"] = time
        else:
            print("Pulse length not understood.")
            return self
        pulse_dict["skip"] = False
        self._pulses.append(pulse_dict)
        return self

    def add_readout(self, skip = False):
        """
        Add a readout pulse to the sequence.
        If skip is True the next pulse will follow at the same time as the readout.
        """
        pulse_dict = {}
        pulse_dict["name"] = "readout"
        if self._sample:
            readout_tone_length = self._sample.readout_tone_length
        else:
            readout_tone_length = None
        pulse_dict["length"] = readout_tone_length
        pulse_dict["skip"] = skip
        self._pulses.append(pulse_dict)
        return self

    def get_pulses(self):
        """
        Returns a list of all pulses and their properties. 
        The properties of each pulse are stored in a dictionary, containing its name, shape, length and skip parameter.
        """
        dict_list = []
        for pulse_dict in self._pulses:
            temp = {}
            temp["name"] = pulse_dict["name"]
            if temp["name"] not in ["readout", "wait"]:
                temp["shape"] = pulse_dict["shape"]
            temp["length"] = self._pulselength_as_str(pulse_dict["length"])
            if pulse_dict["name"] is not "wait":
                temp["skip"] = pulse_dict["skip"]
            dict_list.append(temp)
        return dict_list
    
    def plot(self):
        """
        Plot a schematic of the stored pulses.
        """        
        fig, ax = plt.subplots()
        i = -1
        amp = 1
        ampmax = 1
        col = None

        for pulse_dict in self._pulses:
            if pulse_dict["skip"]:
                i -= 1
                if i < 0:
                    i = 0
                amp += 1
                ampmax = max(ampmax, amp)
            else:
                i += 1
                amp = 1
            #Generate displayed text
            text = ""
            if pulse_dict["name"] is not None:
                text += pulse_dict["name"]
            try:
                text += "\n" + pulse_dict["shape"]
            except:
                pass
            text += "\n" + self._pulselength_as_str(pulse_dict["length"])
            #Make sure pulse colors are unique
            if self._cols_temp is []:
                self._cols_temp = self._cols[:]
                print("All colors already in use...\n Resetting color palette.")
            if pulse_dict["name"] is None:
                col = self._cols_temp[0]
                self._cols_temp = self._cols_temp[1:]
            elif pulse_dict["name"] not in self._pulse_cols.keys():
                col = self._cols_temp[0]
                self._pulse_cols[pulse_dict["name"]] = col
                self._cols_temp = self._cols_temp[1:]
            else:
                col = self._pulse_cols[pulse_dict["name"]]
            
            ax.fill([i, i, i + 1, i + 1, i], [amp - 1, amp, amp, amp - 1, amp - 1], color = col, alpha = 0.3)
            ax.text(i+0.5, amp - 0.5, text, horizontalalignment = "center", verticalalignment = "center")
        
        # make sure plot looks nice and fits on the screen (max number of pulses before scaling down is 9)
        size = 2.*min(1., 9./(i + 1))
        fig.set_figheight(size * ampmax)
        fig.set_figwidth(size * i + 2.)
        ax.set_xlabel("pulse number")
        ax.set_xticks(np.arange(i + 1))
        plt.xlim(-0.05, )
        # hide y ticks
        ax.set_yticks([])
        # hide top and right spines
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        return

    def _pulselength_as_str(self, pulse_length):
        # Note: currently only works for lambda functions.
        length = None
        if callable(pulse_length):
            fct_code = getsourcelines(pulse_length)[0][0]
            fct_start = fct_code.find(":") + 1
            fct_end = len(fct_code) - fct_code[::-1].find(")") - 1 # find last bracket
            length = fct_code[fct_start : fct_end]
            fct_end = length.find(",")
            if fct_end is not -1:
                length = length[: fct_end]
        elif isinstance(pulse_length, float):
            length = pulse_length
        if length is None:
            return ""
        return str(length).strip()