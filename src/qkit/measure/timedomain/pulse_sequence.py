"""Module to provide a high-level possibility to arange pulses for an experiment."""
from enum import Enum
import numpy as np
import inspect
from typing import Dict, Set, List, Union, Callable, Any, Tuple
import logging


plot_enable = False
try:
    import matplotlib.pyplot as plt

    plot_enable = True
except ImportError:
    pass


class Shape(np.vectorize):
    """
    A vectorized function describing a possible shape
    defined on the standardized interval [0,1).
    """

    def __init__(
        self, name: str, func: Callable[[float], float], *args: Any, **kwargs: Any
    ):
        self.name = name
        super(Shape, self).__init__(func, *args, **kwargs)

    def __mul__(self, other):
        return Shape(self.name, lambda x: self.pyfunc(x) * other.pyfunc(x))


class ShapeLibClass(object):
    """
    Object containing pre-defined pulse shapes.
    Currently implemented: rect, gauss
    """

    def __init__(self):
        self.zero = Shape("", lambda x: 0)
        self.rect = Shape("rect", lambda x: np.where(x >= 0 and x < 1, 1, 0))
        self.gauss = (
            Shape("gauss", lambda x: np.exp(-0.5 * np.power((x - 0.5) / 0.166, 2.0)))
            * self.rect
        )
        self.ramp = Shape("ramp", lambda x: x) * self.rect
        self.sqrfct = Shape("sqrfct", lambda x: x ** 2) * self.rect


# Make ShapeLib a singleton:
ShapeLib = ShapeLibClass()


class PulseType(Enum):
    """Type of Pulse object"""

    Pulse = 1
    Wait = 2
    Readout = 3


class ParametrizedValue:
    """
    class for calculating the value of a lambda expression
    value: Type lambda or float
    """

    Type = Union[float, Callable[..., float]]
    """The type of the parametrized values as given by the user."""

    def __init__(self, value: Type, name: str = ""):
        if isinstance(value, int):
            value = float(value)
        self.name = name
        self.value = value
        self._variables: Set[str] = set()
        if callable(value):
            self._variables.update(inspect.getfullargspec(self.value).args)

    def __call__(self, **kwargs: Any) -> float:
        if self.is_parametrized:
            useful_variables: Dict = {}
            for key, value in kwargs.items():
                if key in self.variables:
                    useful_variables[key] = value
            return self.value(**useful_variables)
        else:
            return self.value

    def crop_string(self, function: str) -> str:
        function = function[function.find(":") + 1 :]
        output = function[: function.find(",")]
        output = output.strip(" )\\n']")
        return output

    def __str__(self) -> str:
        if isinstance(self.value, float):
            return str(self.value)
        if self.value.__name__ != "<lambda>":
            function_line = inspect.getsourcelines(self.value)
            function_line_start = str(function_line).find(":") + 1
            return str(function_line)[6 : function_line_start - 1].strip()
        else:
            function = str(inspect.getsourcelines(self.value)[0])
            counter = str(function).count(":")
            if counter == 1:
                return self.crop_string(function)
            elif counter == 2:
                if self.name == "length":
                    if "length" in function:
                        function_start = function.find("length")
                        function = function[function_start:]
                        return self.crop_string(function)
                    else:
                        return self.crop_string(function)
                elif self.name == "amplitude":
                    if "amplitude" in function:
                        function_start = function.find("amplitude")
                        function = function[function_start:]
                        return self.crop_string(function)
                    else:
                        cutting_point = function.find("lambda")
                        function = function[cutting_point + 6 :]
                        function_start = function.find("lambda")
                        function = function[function_start:]
                        return self.crop_string(function)
                else:
                    raise Exception(
                        "unknown Parameter only length and amplitude are supportet"
                    )
            else:
                raise Exception(
                    "too many lambda functions. Only length and amplitude can be lambda functions"
                )

    @property
    def variables(self) -> Set[str]:
        return self._variables

    @property
    def is_parametrized(self) -> bool:
        return callable(self.value)


class Pulse(object):
    """
    Class to describe a single pulse.
    """

    def __init__(
        self,
        length: ParametrizedValue.Type,
        shape: Shape = ShapeLib.rect,
        name: str = None,
        amplitude: ParametrizedValue.Type = 1.0,
        phase: float = 0.0,
        iq_frequency: float = 0.0,
        iq_dc_offset: float = 0.0,
        iq_angle: float = 90.0,
        q_rel: float = 1.0,
        ptype=PulseType.Pulse,
    ):
        """
        Inits a pulse with:
            length:       length of the pulse. This can also be a (lambda) function for variable pulse lengths.
            shape:        pulse shape (i.e. rect, gauss, ...)
            name:         name you want to give your pulse (i.e. pi-pulse, ...)
            amplitude:    relative amplitude of your pulse. This can also be a (lambda) function for variable pulse amplitudes.
            phase:        phase of the pulse in deg. (i.e. 90 for pulse around y-axis of the bloch sphere)
            iq_frequency: IQ-frequency of your pulse for heterodyne mixing (if 0 homodyne mixing is employed)
            iq_dc_offset: complex dc offset for calibrating the IQ-mixer (real part for dc offset of I, imaginary part is dc offset of Q)
            iq_angle:     angle between I and Q in the complex plane (default is 90 deg)
            q_rel:        relative amplitude of Q in respect to I. This is needed for mixer calibration. If q_rel > 1 make sure you are still within the limits of your device.
            type:         The type of the created pulse (from enum PulseType: can be Pulse, Wait or Readout)
        """

        self.shape = shape
        self.name = name or ""
        self.amplitude = ParametrizedValue(amplitude, name="amplitude")
        self.length = ParametrizedValue(length, name="length")
        self.phase = phase
        self.iq_frequency = iq_frequency
        self.iq_dc_offset = iq_dc_offset
        self.iq_angle = iq_angle
        self.q_rel = q_rel
        self.type = ptype

    def __call__(
        self,
        samplerate: float,
        heterodyne: bool = False,
        start_phase: float = 0,
        **variables: Any
    ) -> np.ndarray:
        """
        Returns the pulse envelope for a given frequency and, if length is a function, with given variables as kwargs

        Args:
             samplerate: sample rate for calculating the envelope
             heterodyne: Bool if True returns a complex envelope (defaults to False)
             start_phase: the global phase at which the pulse should start (in rad, defaults to 0)
            **variables: the variables for the length/amplitude function, if any

        Returns:
            envelope of the pulse as numpy array.
        """
        length = self.length(**variables)
        amplitude = self.amplitude(**variables)
        timestep = 1.0 / samplerate

        if length < timestep / 2.0:
            if length != 0:
                logging.warning(
                    "The pulse '{:}' is shorter than {:.2f} ns and thus is omitted.".format(
                        self.name, timestep / 2.0 * 1e9
                    )
                )

            return np.zeros(0)

        time = np.arange(0, length, timestep)
        time_fractions = time / length

        if time_fractions[-1] >= 1.0:
            # This can happen due to float rounding error -> cut it away
            # (the shapes are only defined on [0,1) where 1 is not included)
            time = time[:-1]
            time_fractions = time_fractions[:-1]

        envelope = amplitude * self.shape(time_fractions)
        if not heterodyne or envelope.size == 0 or self.iq_frequency == 0:
            return envelope
        # Empty envelope needs no IQ modulation and
        # for homodyne mixing the envelope is real
        else:
            envelope = envelope * np.exp(
                1.0j
                * (
                    start_phase
                    - np.pi / 180 * self.phase
                    + 2 * np.pi * self.iq_frequency * time
                )
            )

        # account for mixer calibration i.e. dc offset and phase != 90deg between I and Q
        if self.iq_angle != 90 or self.q_rel != 1.0:
            envelope_i = np.real(envelope)
            envelope_q = self.q_rel * np.imag(
                envelope * np.exp(1.0j * np.pi / 180 * (90 - self.iq_angle))
            )
            envelope = envelope_i + 1.0j * envelope_q
        envelope[envelope != 0] += self.iq_dc_offset

        return envelope

    @property
    def variable_names(self) -> Set[str]:
        """A set with the names of all variables necessary to calculate the pulse length and amplitude."""
        return self.length.variables.union(self.amplitude.variables)

    @property
    def is_parametrized(self) -> bool:
        """False if only fixed Values for length/amplitude"""
        return self.length.is_parametrized or self.amplitude.is_parametrized


class PulseSequence(object):
    """
    Class for aranging pulses for a time-domain experiment.
    Sequence objects are callable, returning the sequence envelope for a given time step.
    Add wait as variable times in the experiment.
    Add readout to synchornize different channels in more sophisticated experiments.

    Attributes:
        add:         adds a given pulse to the experiment
        add_wait:    adds a wait time
        add_readout: adds the readout to the experiment
        plot:        plots schematic of the sequence
        get_pulses:  returns list of currently added pulses and their properties.
    """

    def __init__(
        self, sample: Any = None, samplerate: float = None, dc_corr: float = 0
    ):
        """
        Inits PulseSequence with sample and samplerate:
            sample:     Sample object
            samplerate: Samplerate of your device
                        This should already be specified in your sample object as sample.clock
            dc_corr:    DC Voltage bias of the AWG for idling times (Real p)complex dc offset for calibrating the IQ-mixer during idling times.
                        The real part encodes the dc offset of I, the imaginary part is the dc offset of Q.
                        This correction is added to the dc offset during the pulse (i.e. of the pulse object).
        """
        self._sequence: List[List[Pulse]] = []
        self._next_pulse_is_parallel = False
        self._pulses: Dict[str, Pulse] = {}
        self._variables: Set[str] = set()
        self._sample = sample
        self.dc_corr: float = dc_corr
        try:
            self.samplerate = self._sample.clock
        except AttributeError:
            self.samplerate = samplerate

        self._color_palette: List[str] = [
            "C0",
            "C1",
            "C2",
            "C3",
            "C4",
            "C5",
            "C6",
            "C8",
            "C9",
            "r",
            "g",
            "b",
            "y",
            "k",
            "m",
        ]
        self._pulse_cols: Dict[PulseType, str] = {
            PulseType.Readout: "C7",
            PulseType.Wait: "w",
        }

    def __call__(
        self,
        IQ_mixing: bool = False,
        include_readout: bool = False,
        samplerate: float = None,
        **variables: Any
    ) -> Union[Tuple[np.ndarray, int], None]:
        """
        Returns the envelope of the whole pulse sequence for the input time.
        Also returns the index where the readout pulse starts.
        If no readout tone is found it is assumed to be at the end of the sequence.

        Args:
            IQ_mixing:   returns complex valued sequence if IQ_mixing is True (real part encodes I, imaginary part encodes Q)
            include_readout:   If the readout pulse should be included in the resulting waveform
            **variables:    function arguments for time dependent pulse lengths/wait times. Parameter names need to match time function parameters.


        Returns:
            waveform:      numpy array of the squence envelope, if IQ_mixing is True real part is I, imaginary part is Q
            readout_index: index of the readout tone
        """

        if self._variables and self._variables != set(variables.keys()):
            logging.error(
                "Given function arguments do not match with required ones. "
                + "The following keyword arguments are required: {}.".format(
                    ", ".join(self._variables)
                )
            )
            return None

        samplerate = samplerate or self.samplerate
        if not samplerate:
            logging.error("Sequence call requires samplerate.")
            return None

        # build the waveform of this sequence
        full_waveform = np.zeros(0, dtype=np.complex128)
        timestep = 1.0 / samplerate  # minimum time step
        readout_index = 0  # index of the readout in the waveform of the whole sequence
        position_of_next_slice = 0  # index where the next time slice will start
        for time_slice in self._sequence:
            # holds all waveforms that start at the same time (within the same slice)
            wfm_slice = np.zeros(0, dtype=np.complex128)
            # tracks the length of the last waveform in the slice as the next slice will start after that
            last_wfm_length = 0
            for pulse in time_slice:
                # create waveform array of the current pulse
                # adjust global phase relative to the beginning of the sequence
                # (startphase is only relevant when IQ_mixing is True)
                startphase = (
                    2.0 * np.pi * pulse.iq_frequency * position_of_next_slice * timestep
                )  # zero for homodyne mixing
                wfm = pulse(
                    samplerate,
                    start_phase=startphase,
                    heterodyne=IQ_mixing,
                    **variables
                )

                # if (pulse_dict["pulse"].type == PulseType.Readout) and (i == len(self._sequence) - 1):
                #     # if readout is last, omit the wfm (apart from a single digit)
                #     length = timestep

                # Store index if this pulse is a readout pulse (will have the last one at the end)
                if pulse.type == PulseType.Readout:
                    readout_index = position_of_next_slice
                    if not include_readout:
                        # Readout pulses are not taken into account here
                        wfm[:] = 0

                # Store the size of the last waveform in a slice
                # This waveform has skip=False and thus the next slice will start when this pulse is finished
                # even if other pulses of the current slice are longer
                last_wfm_length = len(wfm)

                # Enlarge waveforms to be the same size
                if len(wfm_slice) < len(wfm):
                    wfm_slice.resize(len(wfm))
                else:
                    wfm.resize(len(wfm_slice))
                # Add pulse to waveform of current time slice
                wfm_slice += wfm

            # Resize waveform to be capable of holding current wfm_slice
            new_waveform_length: float = max(
                len(full_waveform), position_of_next_slice + len(wfm_slice)
            )
            full_waveform.resize(new_waveform_length)
            # Add current time slice to global waveform
            full_waveform[
                position_of_next_slice : (position_of_next_slice + len(wfm_slice))
            ] += wfm_slice

            # Update position for next slice (the last waveform has no skip and thus decides the time)
            position_of_next_slice += last_wfm_length

        full_waveform += self.dc_corr

        # make sure first and last point of the waveform go to 0
        full_waveform = np.append(0, full_waveform)
        full_waveform = np.append(full_waveform, 0)

        if not any(np.iscomplex(full_waveform)):
            # No complex information in there, so just return the real part
            full_waveform = np.real(full_waveform)

        return full_waveform, readout_index + 1  # +1 due to leading 0

    def add(self, pulse: Pulse, skip: bool = False):
        """
        Append a pulse to the sequence.

        Args:
            pulse: pulse object
            skip:  if True the next pulse in the sequence will not wait until this pulse is finished (i.e. they happen at the same time)
        """
        # Check if pulse name is valid and unique
        if pulse.name is None or not isinstance(pulse.name, str):
            logging.error("The pulse name has to be a string and must not be None.")
            return self
        elif pulse.name in self._pulses and not self._pulses[pulse.name] is pulse:
            logging.error(
                "Another pulse with the same name ({name}) is already present in the sequence!".format(
                    name=pulse.name
                )
            )
            return self

        # Add the pulse to the pulse dictionary if it is not yet present
        if not pulse.name in self._pulses:
            self._pulses[pulse.name] = pulse

            # Keep track of all variable names: Add them to a set of unique variable names
            self._variables.update(pulse.variable_names)

        if not self._next_pulse_is_parallel:
            # Add empty list for next pulse
            self._sequence.append([])
        # Add pulse to last sequence slice
        self._sequence[-1].append(pulse)

        # If skip is true the next pulse will be scheduled at the same time
        self._next_pulse_is_parallel = skip

        return self

    def add_wait(self, time: ParametrizedValue.Type, name: str = None):
        """
        Add a wait time to the sequence.
        Use a (lambda) function for variable wait times.

        Parameters
        ----------
        self : PulseSequence
            the PulseSequence
        time : ParametrizedValue.Type
            the waiting period as float or function
        name : str, optional
            A special name can be passed for this wait block (by default, wait[#] will be used)
        skip : bool, optional
            if this wait should be parallel to the next item in the sequece, by default False

        Returns
        -------
        PulseSequence
            the PulsSequence with an added waiting period
        """

        def compose_name(index: int) -> str:
            return "wait[{}]".format(index)

        if name is None:
            # Find a unused name for the next wait "pulse"
            wait_index = 0
            while compose_name(wait_index) in self._pulses:
                wait_index += 1
            name = compose_name(wait_index)

        wait_pulse = Pulse(time, shape=ShapeLib.zero, name=name, ptype=PulseType.Wait)
        return self.add(wait_pulse)

    def add_readout(self, pulse: Pulse = None, skip: bool = False):
        """
        Add a readout pulse to the sequence.

        Parameters
        ----------
        skip : bool, optional
            If True the next pulse will follow at the same time as the readout, by default False.
        pulse : Pulse, optional
            pulse: A user-defined readout pulse can be specified if necessary, by default rectangular shaped Pulse with lengtht as specified in sample.

        Returns
        -------
        PulseSequence
            The PulseSequence with an added Readout
        """

        def compose_name(index: int) -> str:
            return "readout[{}]".format(index)

        if pulse is None:
            # Find a unused name for the next readout pulse
            readout_index = 0
            while compose_name(readout_index) in self._pulses:
                readout_index += 1
            name = compose_name(readout_index)

            # Try to determine useful readout tone length
            try:
                readout_length = self._sample.rec_pulselength
            except AttributeError:
                try:
                    readout_length = self._sample.readout_tone_length
                except AttributeError:
                    readout_length = 0.0

            readout_pulse = Pulse(readout_length, name=name, ptype=PulseType.Readout)
        else:
            # If a special pulse is needed, user can add it
            readout_pulse = pulse

            if readout_pulse.type != PulseType.Readout:
                readout_pulse.type = PulseType.Readout
                logging.warning(
                    "The type of the added pulse has to be Readout and was changed accordingly."
                )

        return self.add(readout_pulse, skip)

    @property
    def variable_names(self) -> Set[str]:
        """A set with the names of all variables present in this sequence."""
        return self._variables

    def get_pulses(self) -> List[Dict[str, Any]]:
        """
        Returns a list of all pulses and their properties.
        The properties of each pulse are stored in a dictionary with keys: name, shape, length, skip value
        """
        dict_list: List[Dict[str, Any]] = []
        for time_slice in self._sequence:
            for i, pulse in enumerate(time_slice):
                # This is more for legacy reasons
                dict_list.append(
                    {
                        "name": pulse.name,
                        "shape": pulse.shape.name,
                        "length": pulse.length,
                        "iq_frequency": pulse.iq_frequency,
                        "phase": pulse.phase,
                        "skip": i != len(time_slice) - 1,
                    }
                )
        return dict_list

    @property
    def pulses(self) -> Dict[str, Pulse]:
        """A dictionary containing pulse name as key and pulse as value"""
        return self._pulses

    @property
    def sequence(self) -> List[List[Pulse]]:
        """A List of Lists containing pulses. If pulses are paralles they will be in the same sublist"""
        return self._sequence

    def plot(self):
        """
        Plot a schematic of the stored pulses.
        """
        if not plot_enable:
            raise ImportError("matplotlib not found.")

        fig, ax = plt.subplots()
        amp = 1
        ampmax = 1
        remaining_colors = self._color_palette[:]
        pulse_colors: Dict[str, str] = {}

        for i, time_slice in enumerate(self._sequence):
            for amp, pulse in enumerate(reversed(time_slice)):
                ampmax = max(ampmax, amp + 1)

                # Generate displayed text
                text = "{name}\n{shape}\n{time}".format(
                    name=pulse.name,
                    shape=pulse.shape.name,
                    time=(pulse.length if pulse.type != PulseType.Readout else ""),
                )

                if pulse.iq_frequency not in [0, None]:
                    text += "\n\n f_iq = {:.0f} MHz".format(pulse.iq_frequency / 1e6)
                    if pulse.phase != 0:
                        text += "\n phase = {:.0f} deg".format(pulse.phase)

                # Make sure pulse colors are unique
                if not remaining_colors:
                    remaining_colors = self._color_palette[:]
                    print("All colors already in use...\n Resetting color palette.")
                if pulse.type in self._pulse_cols.keys():
                    # Pulse type is special and has predefined color
                    col = self._pulse_cols[pulse.type]
                elif pulse.name in pulse_colors.keys():
                    # Pulse was in sequence before, take same color again
                    col = pulse_colors[pulse.name]
                else:
                    col = remaining_colors[0]
                    pulse_colors[pulse.name] = col
                    remaining_colors = remaining_colors[1:]

                ax.fill(
                    [i, i, i + 1, i + 1, i],
                    [amp, amp + 1, amp + 1, amp, amp],
                    color=col,
                    alpha=0.3,
                )
                ax.text(
                    i + 0.5,
                    amp + 0.5,
                    text,
                    horizontalalignment="center",
                    verticalalignment="center",
                )

        # make sure plot looks nice and fits on the screen (max number of pulses before scaling down is 9)
        size = 2.0 * min(1.0, 9.0 / len(self._sequence))
        fig.set_figheight(size * ampmax)
        fig.set_figwidth(size * (len(self._sequence) - 1) + 2.0)
        ax.set_xlabel("pulse number")
        ax.set_xticks(np.arange(len(self._sequence)))
        plt.xlim(
            -0.05,
        )
        # hide y ticks
        ax.set_yticks([])
        # hide top and right spines
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        return
