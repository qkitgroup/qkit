# Started by A.Stehli@KIT 04/2018
# time domain virtual AWG class


# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from typing import Dict, List, Generator, Any
import numpy as np
from ipywidgets import interact, widgets, Layout
import logging

import qkit
import qkit.measure.timedomain.pulse_sequence as ps
import qkit.measure.timedomain.awg.load_tawg as load_tawg

PLOT_ENABLE = False
try:
    import matplotlib.pyplot as plt

    PLOT_ENABLE = True
except ImportError:
    pass

# Helper functions
def all_are_same(array):
    """Check if all elements of a list are the same."""
    return all(item == array[0] for item in array)


def _vars_len(variables: Dict[str, List[float]]):
    if variables:
        return len(list(variables.values())[0])
    else:
        return 0  # No variables in dictionary


def dictify_variable_lists(variables):
    # type: (Dict[List[float]]) -> Generator[Dict[float]]
    for i in range(_vars_len(variables)):
        single_variables = {}
        for key in variables.keys():
            single_variables[key] = variables[key][i]
        yield single_variables


class TdChannel(object):
    """
    Class managing the channels for the VirtualAWG class.
    These channels are similar to the channel of an awg.

    Attributes:
        add_sequence:      add sequence maintaining currently stored sequences
        set_sequence:      add sequence deleting previously stored sequences
        delete_sequence:   delete previously stored sequences
        set_interleave:    turn interleaving of sequences on/off

        get_sequence_dict: returns a dictionary containing all important channel attributes
        plot:              plot the pulse sequences

    TODO:
        Add option to compensate linearly (for Bias Tees with finite decay time).
    """

    def __init__(self, sample, name):
        """
        Inits TdChannel with sample and name:
            sample: sample object
            name:   name of the channel
        """
        self.name = name
        self._sample = sample
        self._sequences = []
        self._variables = []  # type: List[Dict[List[float]]]
        self._interleave = False
        # Dictionary for x-axis scaling
        self._x_unit = {"s": 1, "ms": 1e-3, "us": 1e-6, "ns": 1e-9}

    @property
    def sequence_count(self):
        """The number of loaded sequences."""
        return len(self._sequences)

    def add_sequence(
        self, sequence: ps.PulseSequence, **variables: List[float]
    ) -> bool:
        """
        Append sequence to sequences currently stored in channel.

        Args:
            sequence:     sequence object
            **variables:  One or multiple keywords matching the variable names of time functions and each containing a list of values.
                          In a T1 measurement this would be the wait time between pi-pulse and readout tone.
        """
        # Check that lists are given for all necessary variables
        if sequence.variable_names:
            if not variables or sequence.variable_names != set(variables.keys()):
                logging.error(
                    "Lists for the variables of the sequence have to be specified. Given variables do not match with required ones. "
                    + "The following keyword arguments are required: {}.".format(
                        ", ".join(sequence.variable_names)
                    )
                )
                return False

            # Check if all variable lists have the same length and are non-empty
            if not all_are_same([len(v) for v in variables.values()]):
                logging.error("Length of variable lists do not match.")
                return False
            elif _vars_len(variables) == 0:
                logging.error(
                    "The lists containing values of the variables must not be empty."
                )
                return False

        # Add sequence and variable lists to channel
        self._sequences.append(sequence)
        self._variables.append(variables)

        # Check if interleaving should be done and if so, if it is still possible
        if (len(self._sequences) >= 1) and self._interleave:
            if not self.set_interleave():
                logging.error(
                    "Dimension of new time array does not fit previous inputs.\n"
                    + "Interleaving no longer possible."
                )

        return True

    def set_sequence(self, sequence, **variables):
        """
        Set sequence in channel to sequence deleting previously stored sequences.

        Input:
            sequence:     sequence object
            **variables:  One or multiple keywords matching the variable names of time functions and each containing a list of values.
                          In a T1 measurement this would be the wait time between pi-pulse and readout tone.
        """
        # Delete previously stored sequences
        self.delete_sequence()

        # Add new sequence
        return self.add_sequence(sequence, **variables)

    def delete_sequence(self, seq_nr=None):
        """
        Delete sequence number seq_nr (counting from 0).
        If seq_nr is None, all sequences are deleted.

        Args:
            seq_nr: Number of the sequence to be deleted.
        """
        if seq_nr is None:
            self._sequences = []
            self._variables = []
        else:
            self._sequences.pop(seq_nr)
            self._variables.pop(seq_nr)
        return True

    def get_sequence(self, num: int):
        # type: (int) -> Tuple[PulseSequence, Dict[str, List[Any]]]
        """Returns the PulseSequence object and variables for a given index."""
        return self._sequences[num], self._variables[num]

    def get_sequence_dict(self):
        """
        Returns a dictionary featuring all important channel attributes:
            sequence_i: list of all pulses of sequences number i (counting from 0)
            par_i: parameter values for which sequence is called (usually this parameter is a time, e.g. separating two pulses)
            value of the interleave attribute
        """
        seq_dict = {}
        for i in range(len(self._sequences)):
            seq_dict["sequence_%i" % i] = self._sequences[i].get_pulses()
            seq_dict["par_%i" % i] = self._variables[i]
        if seq_dict:
            seq_dict["interleave"] = self._interleave
        return seq_dict

    def set_interleave(self, use_interleave=True):
        """
        Sequences with an equal number of timesteps may be interleaved.
        In order for this to work they must have the same number of time steps.

        Args:
            use_interleave: if true, the sequences in this channel are interleaved.
        """
        # By default, interleave mode is off
        self._interleave = False

        if not use_interleave:
            # Disabling interleave mode always works
            return True

        if not self._variables:
            # If there are no sequences yet, one can also turn on interleave mode
            self._interleave = True
            return True

        # Check if all variable vectors have same length
        # (Only need to check first variable of each vector, as within we already checked during add procedure)
        if not all_are_same([_vars_len(vs) for vs in self._variables]):
            logging.error(
                "Only sequences that have the same number of variables can be interleaved."
            )
            return False

        self._interleave = True
        return True

    @property
    def is_interleaved(self):
        """If the sequences in this channel are to be played interleaved."""
        return self._interleave

    def plot(self, show_quadrature="", x_unit="ns"):
        """
        Plots the sequences stored in channel.
        A slider provides the option to sweep through different time values.
        Readout pulse is fixed at t = 0, where is t>0 before the readout tone.

        Args:
            x_unit: unit of the x-axis in the plot. Options are "s", "ms", "us", "ns".
        """
        show_iq = show_quadrature in ["I", "Q"]
        sequences, readout_indices = self._get_sequences(IQ_mixing=show_iq)
        seq_max = len(readout_indices) - 1

        # If there is no complex information in there, we just present the real part:
        has_complex_values = any([any(np.iscomplex(seq)) for seq in sequences])
        if show_quadrature == "I" or not has_complex_values:
            sequences = [np.real(seq) for seq in sequences]
        elif show_quadrature == "Q":
            sequences = [np.imag(seq) for seq in sequences]

        bounds = self._get_boundaries(sequences, readout_indices, x_unit)

        interact(
            lambda sequence: self._plot_sequence(
                sequences[sequence], readout_indices[sequence], x_unit, bounds
            ),
            sequence=widgets.IntSlider(
                value=0, min=0, max=seq_max, layout=Layout(width="98%", height="50px")
            ),
        )
        return True

    def _plot_sequence(self, seq, ro_ind, x_unit, bounds, col="C0", plot_readout=True):
        """
        The actual plotting of the sequences happens here.

        Input:
            seq:    sequence (as array) to be plotted
            ro_ind: index of the readout in seq
            x_unit: x_unit for the time axis
            bounds: boundaries for the plot (xmin, xmax, ymin, ymax)
        """
        if not PLOT_ENABLE:
            raise ImportError("matplotlib not found.")

        if plot_readout:
            fig = plt.figure(figsize=(18, 6))
        xmin, xmax, ymin, ymax = bounds
        samplerate = self._sample.clock
        time = -(np.arange(0, len(seq) + 1, 1) - ro_ind) / (
            samplerate * self._x_unit[x_unit]
        )
        # make sure last point of the waveform goes to zero
        seq = np.append(seq, 0)

        try:
            readout_tone = self._sample.rec_pulselength
        except AttributeError:
            readout_tone = self._sample.readout_tone_length

        # plot sequence
        plt.plot(time, seq, col)
        plt.fill(time, seq, color=col, alpha=0.2)
        # plot readout
        if plot_readout:
            plt.fill(
                [
                    0,
                    0,
                    -readout_tone / self._x_unit[x_unit],
                    -readout_tone / self._x_unit[x_unit],
                ],
                [0, ymax, ymax, 0],
                color="C7",
                alpha=0.3,
            )
            # add label for readout
            plt.text(
                -0.5 * readout_tone / self._x_unit[x_unit],
                ymax / 2.0,
                "readout",
                horizontalalignment="center",
                verticalalignment="center",
                rotation=90,
                size=14,
            )
        # adjust bounds
        plt.xlim(xmin + 0.005 * abs(xmax - xmin), xmax - 0.006 * abs(xmax - xmin))
        plt.ylim(ymin, ymax + 0.025 * (ymax - ymin))
        plt.xlabel("time " + x_unit)
        return

    def _get_boundaries(self, sequences, readout_indices, x_unit):
        """
        Returns plot boundaries for a given x-unit.

        Args:
            sequences:       list of all sequences stored in the channel
            readout_indices: indices of the readout for each sequence in sequences
            x_unit:          see dictionary

        Returns:
            List of boundaries (xmin, xmax, ymin, ymax)
        """
        try:
            readout_tone = self._sample.rec_pulselength
        except AttributeError:
            readout_tone = self._sample.readout_tone_length

        xmin = max(readout_indices) / (self._x_unit[x_unit] * self._sample.clock)
        xmax = (
            -(
                max(
                    np.array([len(seq) for seq in sequences])
                    - np.array(readout_indices)
                )
                / self._sample.clock
                + readout_tone
            )
            / self._x_unit[x_unit]
        )
        ymin = np.amin(np.concatenate(sequences))
        ymax = np.amax(np.concatenate(sequences))
        bounds = [xmin, xmax, ymin, ymax]
        return bounds

    def _get_sequences(self, IQ_mixing=False):
        """
        Explicitly calculate the waveforms of all sequences at their input time.

        Args:
            IQ_mixing: if true all waveforms are complex arrays where real and imaginary part encode I and Q

        Output:
            List of waveform arrays.
            List of readout indices.
        """

        try:
            samplerate = self._sample.clock
        except:
            samplerate = None

        seq_list = []
        ro_inds = []
        for sequence, variables in zip(self._sequences, self._variables):
            if variables:
                for single_variables in dictify_variable_lists(variables):
                    seq, ro_ind = sequence(
                        IQ_mixing=IQ_mixing, samplerate=samplerate, **single_variables
                    )
                    seq_list.append(seq)
                    ro_inds.append(ro_ind)
            else:
                # No variables
                seq, ro_ind = sequence(IQ_mixing=IQ_mixing, samplerate=samplerate)
                seq_list.append(seq)
                ro_inds.append(ro_ind)

        if not seq_list:
            logging.warning("No sequence stored in channel " + self.name)
            return [np.zeros(1)], [0]

        if self._interleave:
            seqs_temp = []
            ro_inds_temp = []
            time_dim = _vars_len(self._variables[0])
            for i in range(time_dim):
                seqs_temp += seq_list[i::time_dim]
                ro_inds_temp += ro_inds[i::time_dim]
            seq_list = seqs_temp
            ro_inds = ro_inds_temp
        return seq_list, ro_inds


class VirtualAWG(object):
    """
    Class managing multiple manipulation channels for a timedomain experiment (virtual AWG).
    Each channel stores pulse sequences which can be loaded onto your device.
    The readout pulse of each sequences is used to align sequences of multiple channles.

    Important attributes:
        self.channel[nr]: channel object - sequences can be added and plotted
        add_sequences:    add sequence(s) object (see pulse_sequence.py), maintaining currently stored sequences
        set_sequences:    add sequence(s) object (see pulse_sequence.py), deleting previously stored sequences
        delete_sequence:  delete previously stored sequences
        set_interleave:   for a specified channel turn interleaving of sequences on/off

        get_sequence_dicts: returns a dictionary containing all important channel attributes
        plot: plot the pulse sequences of all channels
        load: load sequences of specified channel(s) on your physical device

    TODO:
        Write .load fct to directly load the pulse sequences on a device, i.e. VirtualAWG.load(device).
    """

    def __init__(self, sample, channels=1):
        """
        Inits VirtualAWG with sample and number of channels:
            sample:   sample object
            channels: number of channels of the virtual AWG
        """
        self._sample = sample
        self._num_chans = channels

        self.channels = [None]  # type: List[TdChannel]
        self.channels.extend(
            TdChannel(self._sample, "channel_%i" % (i + 1)) for i in range(channels)
        )

        # Dictionary for x-axis scaling
        self._x_unit = {"s": 1, "ms": 1e-3, "us": 1e-6, "ns": 1e-9}
        # Dictonary for channel colors
        self._chancols = {1: "C0", 2: "C1", 3: "C2", 4: "C3", 5: "C4", 6: "C5", 7: "C6"}

    @property
    def channel_count(self):
        """The number of existing channels."""
        return self._num_chans

    def add_sequence(self, sequence, channel=1, **variables):
        """
        Sequence is added to current sequences.
        If channel is None all sequence is added to all channels.

        Args:
            sequence:     sequence or list of sequences.
            channel:      channel number in which sequence will be loaded.
            **variables:  keyword arguments matching the variable names of time functions and each containing a list of values.

        """
        if channel > self._num_chans:
            print(
                "Channel number {:d} is larger than total number of channels {:d}".format(
                    channel, self._num_chans
                )
            )
            return False
        if channel is not None:
            self.channels[channel].add_sequence(sequence, **variables)
        elif channel is None:
            for channel in self.channels:
                channel.add_sequence(sequence, **variables)
        return True

    def set_sequence(self, sequence, channel=1, **variables):
        """
        Delete previously added sequences, replacing them with sequence.
        If channel is None set all sequences in all channels to sequence.

        Args:
            sequence:     sequence or list of sequences.
            channel:      channel number in which sequence will be loaded.
            **variables:  keyword arguments matching the variable names of time functions and each containing a list of values.

        """
        if channel is not None:
            self.channels[channel].set_sequence(sequence, **variables)
        elif channel is None:
            for channel in self.channels:
                channel.set_sequence(sequence, **variables)
        return True

    def delete_sequence(self, seq_nr, channel=1):
        """
        Delete sequence seq_nr in stated channel.
        If channel is None sequence seq_nr is deleted from all channels.

        Args:
            seq_nr:  number of the sequence to be deleted
            channel: channel number
        """
        if channel is not None:
            self.channels[channel].delete_sequence(seq_nr)
        else:
            for chan in self.channels[1:]:
                chan.delete_sequence(seq_nr)
        return True

    def get_sequence_dicts(self):
        """
        For each channel, returns a dictionary featuring all important channel attributes:
            sequence_i: list of all pulses of sequnces number i (counting from 0)
            time_i: time values for which sequence is called
            value of the interleave attribute
        """
        chan_dicts = []
        for chan in self.channels[1:]:
            chan_dicts.append(chan.get_sequence_dict())
        return chan_dicts

    def set_interleave(self, value=True, channel=1):
        """
        For each channel, sequences with an equal number of timesteps may be interleaved.
        In order for this to work the squences must have the same number of time steps.

        Args:
            value:   if true, the sequences in this channel are interleaved.
            channel: number of the channel where sequences should be interleaved.
                     If channel is None action applies to all channels.
        """
        if channel is not None:
            self.channels[channel].set_interleave(value)
        else:
            for chan in self.channels[1:]:
                chan.set_interleave(value)
        return True

    def plot(self, show_quadrature="", x_unit="ns"):
        """
        Plots the sequences stored in all channels.
        A slider provides the option to sweep through the sequences.
        Readout pulse is fixed at t = 0, where is t>0 before the readout tone.
        By default, the amplitude of each sequence is plotted.
        This may be changed by setting the show_quadrature option to either "I" or "Q".

        Args:
            show_quadrature: set to "I" or "Q" if you want to display either quadrature instead of the amplitude
            x_unit:          unit of the x-axis in the plot (options are "s", "ms", "us", "ns").
        """
        seqs = []
        ro_inds = []
        seq_max = 0
        xmin, xmax, ymin, ymax = 0, 0, 0, 0

        show_iq = show_quadrature in ["I", "Q"]
        for chan in self.channels[1:]:
            sequences, readout_indices = chan._get_sequences(IQ_mixing=show_iq)

            # If there is no complex information in there, we just present the real part:
            has_complex_values = any([any(np.iscomplex(seq)) for seq in sequences])
            if show_quadrature == "I" or not has_complex_values:
                sequences = [np.real(seq) for seq in sequences]
            elif show_quadrature == "Q":
                sequences = [np.imag(seq) for seq in sequences]

            seq_max = max(seq_max, len(readout_indices) - 1)
            seqs.append(sequences)
            ro_inds.append(readout_indices)

            bounds = chan._get_boundaries(sequences, readout_indices, x_unit)
            xmin = max(xmin, bounds[0])
            xmax = min(xmax, bounds[1])
            ymin = min(ymin, bounds[2])
            ymax = max(ymax, bounds[3])

        interact(
            lambda sequence: self._plot_sequences(
                sequence, seqs, ro_inds, x_unit, [xmin, xmax, ymin, ymax]
            ),
            sequence=widgets.IntSlider(
                value=0, min=0, max=seq_max, layout=Layout(width="11in", height="50px")
            ),
        )
        return True

    def _plot_sequences(self, seq_ind, seqs, ro_inds, x_unit, bounds):
        """
        The actual plotting of the sequences happens here.

        Args:
            seqs:            list of sequences to be plotted (i.e. one list of sequence for each channel)
            ro_inds:         indices of the readout
            x_unit:          x_unit for the time axis
            bounds:          boundaries of the plot (xmin, xmax, ymin, ymax)
            show_quadrature: set to "I" or "Q" if you want to display either quadrature instead of the amplitude
        """
        if not PLOT_ENABLE:
            raise ImportError("matplotlib not found.")

        try:
            readout_tone = self._sample.rec_pulselength
        except AttributeError:
            readout_tone = self._sample.readout_tone_length

        fig = plt.figure(figsize=(18, 6))
        xmin, xmax, ymin, ymax = bounds
        samplerate = self._sample.clock
        # plot sequence
        for i, chan in enumerate(self.channels[1:]):
            if len(ro_inds[i]) > seq_ind:
                chan._plot_sequence(
                    seqs[i][seq_ind],
                    ro_inds[i][seq_ind],
                    x_unit,
                    bounds,
                    col=self._chancols[i + 1],
                    plot_readout=False,
                )

            # plot readout
        plt.fill(
            [
                0,
                0,
                -readout_tone / self._x_unit[x_unit],
                -readout_tone / self._x_unit[x_unit],
            ],
            [0, ymax, ymax, 0],
            color="C7",
            alpha=0.3,
        )
        # add label for readout
        plt.text(
            -0.5 * readout_tone / self._x_unit[x_unit],
            ymax / 2.0,
            "readout",
            horizontalalignment="center",
            verticalalignment="center",
            rotation=90,
            size=14,
        )

        # adjust plot limits
        plt.xlim(xmin + 0.005 * abs(xmax - xmin), xmax - 0.006 * abs(xmax - xmin))
        plt.ylim(ymin, ymax + 0.025 * (ymax - ymin))
        plt.xlabel("time " + x_unit)
        return

    def _get_sequences(self, IQ_mixing=False):
        """
        Returns a list of waveforms for each channel, as well as a list of indices for the readout timing.

        Args:
            IQ_mixing: if true all waveforms are complex arrays where real and imaginary part encode I and Q

        Returns:
            list of lists (one for each channel) of numpy arrays
        """
        seqs = []
        ro_inds = []
        for chan in self.channels[1:]:
            sequences, readout_indices = chan._get_sequences(IQ_mixing)
            seqs.append(sequences)
            ro_inds.append(readout_indices)
        return seqs, ro_inds

    def _sync(self):
        """
        Synchronize sequences of all channels to the same readout time.

        Output:
            sequences:       list of synchronized sequences as arrays (one each channel)
            readout_indices: array of new readout indices
        """
        seqs, ro_inds = self._get_sequences(IQ_mixing=True)
        # find maximum readout indices
        lens = [len(ro_ind) for ro_ind in ro_inds]
        readout_indices = np.zeros(max(lens))
        for i in range(0, len(lens)):
            for j in range(lens[i]):
                readout_indices[j] = max(readout_indices[j], ro_inds[i][j])

        ind = 0
        sequences = []
        sequences.extend([] for seq in seqs)
        while any(seqs):
            for i, seq in enumerate(seqs):
                if seq:
                    s = seq.pop(0)
                    temp = np.zeros(int(max(0, readout_indices[ind] - ro_inds[i][ind])))
                    s = np.append(temp, s)
                else:
                    s = np.zeros(0)
                sequences[i].append(s)
            ind += 1
        return sequences, readout_indices

    def load(self, show_progress_bar=True):
        """
        Load the sequences stored in the channels of the virtual AWG to your physical device (awg, fpga).
        Currently only enabled for the tabor awg.
        """
        # Case discrimination:
        if self._sample.awg.get_name() == "tawg":
            sequences, readout_inds = self._sync()
            load_tawg.load_tabor(
                sequences,
                readout_inds,
                self._sample,
                show_progress_bar=show_progress_bar,
            )
        else:
            print("Unknown device type! Unable to load sequences.")
        return True
