# Created by A.Stehli@KIT 04/2018
# time domain experiment class

import numpy as np
import matplotlib.pyplot as plt
from ipywidgets import interact, widgets, Layout
import logging

import qkit.measure.timedomain.pulse_sequence as ps
#from qkit.measure.timedomain.awg.load import load_sequence as awgload



class TdChannel(object):
    """
    Class managing the channels for TdExperiment.
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
        self._times = []
        self._interleave = False
        # Dictionary for x-axis scaling
        self._x_unit = { "s": 1, "ms": 1e-3, "us": 1e-6, "ns": 1e-9}

    def add_sequence(self, sequence, *times):
        """
        Append sequence to sequences currently stored in channel.

        Args:
            sequence: sequence object
            *times:   time steps where sequence is called. Usually this is a single array of time steps.
                      In a T1 measurement this would be the wait time between pi-pulse and readout tone.
        """
        if not times:
            print("No time given.")
            return False
        len0 = 0
        for time in times:
            time = np.atleast_1d(time)
            if len0 is 0:
                len0 = len(time)
            elif len(time) is not len0:
                print("Dimensions of input arrays do not match.")
                return False
        self._sequences.append(sequence)
        self._times.append(np.vstack((times)).T)
        if (len(self._sequences) >= 1) and self._interleave:
            if not self.set_interleave():
                print("Dimension of new time array does not fit previous inputs.\nInterleaving no longer possible.")
        return True
    
    def set_sequence(self, sequence, *times):
        """
        Set sequence in channel to sequence deleting previouisly stored sequences.

        Input:
            sequence: sequence object
            *times:   time steps where sequence is called. Usually this is a single array of time steps.
                      In a T1 measurement this would be the wait time between pi-pulse and readout tone.
        """
        self._sequences = []
        self._times = []
        if not times:
            print("No time given.")
            return False
        self.add_sequence(sequence, *times)
        return True

    def delete_sequence(self, seq_nr):
        """
        Delete sequence number seq_nr (counting from 0).

        Args:
            seq_nr: Number of the sequence to be deleted.
        """
        temp = self._sequences.pop(seq_nr)
        temp = self._times.pop(seq_nr)
        return True

    def get_sequence_dict(self):
        """
        Returns a dictionary featuring all important channel attributes:
            sequence_i: list of all pulses of sequnces number i (counting from 0)
            time_i: time values for which sequence is called
            value of the interleave attribute
        """
        seq_dict = {}
        for i in range(len(self._sequences)):
            seq_dict["sequence_%i"%i] = self._sequences[i].get_pulses()
            seq_dict["time_%i"%i] = self._times[i]
        if seq_dict:
            seq_dict["interleave"] = self._interleave
        return seq_dict

    def set_interleave(self, value = True):
        """
        Sequences with an equal number of timesteps may be interleaved.
        In order for this to work they must have the same number of time steps.

        Args:
            value: if true, the sequences in this channel are interleaved.
        """
        if value is False:
            self._interleave = False
            return True
        if not self._times:
            self._interleave = True
            return True
        len0 = len(self._times[0])
        for time in self._times[1:]:
            if len(time) is not len0:
                print("Only sequences with an equal number of timesteps may be interleaved.")
                self._interleave = False
                return False
        self._interleave = True
        return True
    
    def plot(self, x_unit = "ns"): 
        """
        Plots the sequences stored in channel.
        A slider provides the option to sweep through different time values.
        Readout pulse is fixed at t = 0, where is t>0 before the readout tone.

        Args:
            x_unit: unit of the x-axis in the plot. Options are "s", "ms", "us", "ns".
        """
        sequences, readout_indices = self._get_sequences()
        seq_max = len(readout_indices) - 1
        bounds = self._get_boundaries(sequences, readout_indices, x_unit)
        
        interact(lambda sequence: self._plot_sequence(sequences[sequence], readout_indices[sequence], x_unit, bounds), 
                sequence = widgets.IntSlider(value = 0, min = 0, max = seq_max, layout = Layout(width = "98%", height = "50px")))
        return True

    def _plot_sequence(self, seq, ro_ind, x_unit, bounds, col = "C0", plot_readout = True):
        """
        The actual plotting of the sequences happens here.
        
        Input:
            seq:    sequence (as array) to be plotted
            ro_ind: index of the readout in seq
            x_unit: x_unit for the time axis
            bounds: boundaries for the plot (xmin, xmax, ymin, ymax)
        """
        if plot_readout:
            fig = plt.figure(figsize = (18, 6))
        xmin, xmax, ymin, ymax = bounds
        samplerate = self._sample.clock
        time = -(np.arange(0, len(seq) + 1, 1) - ro_ind) / (samplerate * self._x_unit[x_unit])
        # make sure last point of the waveform goes to zero
        seq = np.append(seq, 0)

        # plot sequence
        plt.plot(time, seq, col)
        plt.fill(time, seq, color = col, alpha = 0.2)
        # plot readout
        if plot_readout:
            plt.fill([0, 0, - self._sample.readout_tone_length / self._x_unit[x_unit], - self._sample.readout_tone_length / self._x_unit[x_unit]], 
                    [0, ymax, ymax, 0], color = "C7", alpha = 0.3)        
            # add label for readout
            plt.text(-0.5*self._sample.readout_tone_length / self._x_unit[x_unit], ymax/2.,
                    "readout", horizontalalignment = "center", verticalalignment = "center", rotation = 90, size = 14)
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
        xmin = max(readout_indices)/ (self._x_unit[x_unit] * self._sample.clock)
        xmax = - (max(np.array([len(seq) for seq in sequences]) - np.array(readout_indices)) /self._sample.clock + self._sample.readout_tone_length)/self._x_unit[x_unit]
        ymin = np.amin(np.concatenate(sequences))
        ymax = np.amax(np.concatenate(sequences))
        bounds = [xmin, xmax, ymin, ymax]
        return bounds

    def _get_sequences(self, IQ_mixing = False):
        """
        Explicitly calculate the waveforms of all sequences at their input time.
        
        Args:
            IQ_mixing: if true all waveforms are complex arrays where real and imaginary part encode I and Q

        Output:
            List of waveform arrays.
            List of readout indices.
        """
        seq_list = []
        ro_inds = []
        for i in range(len(self._sequences)):
            for time in self._times[i]:
                seq, ro_ind = self._sequences[i](time, IQ_mixing = IQ_mixing)
                seq_list.append(seq)
                ro_inds.append(ro_ind)
        if not seq_list:
            logging.warning("No sequence stored in channel " + self.name)
            return [np.zeros(1)], [0]
        if self._interleave:
            seqs_temp = []
            ro_inds_temp = []
            time_dim = len(self._times[0])
            for i in range(time_dim):
                seqs_temp += seq_list[i::time_dim]
                ro_inds_temp += ro_inds[i::time_dim]
            seq_list = seqs_temp
            ro_inds = ro_inds_temp
        return seq_list, ro_inds


class TdExperiment(object):
    """
    Class managing multiple manipulation channels for a timedomain experiment.
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
        Write .load fct to directly load the pulse sequences on a device, i.e. TdExperiment.load(device).
    """

    def __init__(self, sample, channels = 1):
        """
        Inits TdExperiment with sample and number of channels:
            sample:   sample object
            channels: number of channels for the experiment
        """        
        self._sample = sample
        self._num_chans = channels

        self.channels = [None]  # type: List[TdExperimentChannel]
        self.channels.extend(TdChannel(self._sample, "channel_%i"%(i + 1)) for i in range(channels))

        # Dictionary for x-axis scaling
        self._x_unit = { "s": 1, "ms": 1e-3, "us": 1e-6, "ns": 1e-9}
        # Dictonary for channel colors
        self._chancols = {1 : "C0", 2 : "C1", 3 : "C2", 4 : "C3", 5 : "C4", 6 : "C5", 7 : "C6"}
    
    def add_sequence(self, sequence, time, channel = 1):
        """
        Sequence is added to current sequences.
        If channel is None all sequence is added to all channels.
        
        Args:
            sequence: sequence or list of sequences.
            time:     time where sequence is called
            channel:  channel number in which sequence will be loaded.

        """
        if channel > self._num_chans:
            print("Channel number {:d} is larger than total number of channels {:d}".format(channel, self._num_chans))
            return False
        if channel is not None:
            self.channels[channel].add_sequence(sequence, time)
        elif channel is None:
            for channel in self.channels:
                channel.add_sequence(sequence, time)
        return True
   
    def set_sequence(self, sequence, time, channel = 1):
        """
        Delete previously added sequences, replaxing them with sequence.
        If channel is None set all sequences in all channels to sequence.

        Args:
            sequence: sequence object.
            time:     time where sequence is called
            channel:  channel number in which sequence will be loaded
        
        """
        if channel is not None:
            self.channels[channel].set_sequence(sequence, time)
        elif channel is None:
            for channel in self.channels:
                channel.set_sequence(sequence, time)
        return True
    
    def delete_sequence(self, seq_nr, channel = 1):
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
    
    def set_interleave(self, value = True, channel = 1):
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

    def plot(self, x_unit = "ns"): 
        """
        Plots the sequences stored in all channels.
        A slider provides the option to sweep through the sequences.
        Readout pulse is fixed at t = 0, where is t>0 before the readout tone.

        Args:
            x_unit: unit of the x-axis in the plot (options are "s", "ms", "us", "ns").
        """
        seqs = []
        ro_inds = []
        seq_max = 0
        xmin, xmax, ymin, ymax = 0, 0, 0, 0
        for chan in self.channels[1:]:
            sequences, readout_indices = chan._get_sequences()
            seq_max = max(seq_max, len(readout_indices) - 1)
            seqs.append(sequences)
            ro_inds.append(readout_indices)

            bounds = chan._get_boundaries(sequences, readout_indices, x_unit)
            xmin = max(xmin, bounds[0])
            xmax = min(xmax, bounds[1])
            ymin = min(ymin, bounds[2])
            ymax = max(ymax, bounds[3])
        
        
        interact(lambda sequence: self._plot_sequences(sequence, seqs, ro_inds, x_unit, [xmin, xmax, ymin, ymax]), 
                sequence = widgets.IntSlider(value = 0, min = 0, max = seq_max, layout = Layout(width = "11in", height = "50px")))
        return True

    def _plot_sequences(self, seq_ind, seqs, ro_inds, x_unit, bounds):
        """
        The actual plotting of the sequences happens here.
        
        Args:
            seqs:    list of sequences to be plotted (i.e. one list of sequence for each channel)
            ro_inds: indices of the readout
            x_unit:  x_unit for the time axis
            bounds:  boundaries of the plot (xmin, xmax, ymin, ymax)
        """
        fig = plt.figure(figsize=(18,6))
        xmin, xmax, ymin, ymax = bounds
        samplerate = self._sample.clock
        # plot sequence
        for i, chan in enumerate(self.channels[1:]):
            if len(ro_inds[i]) > seq_ind:
                chan._plot_sequence(seqs[i][seq_ind], ro_inds[i][seq_ind], x_unit, bounds, col = self._chancols[i + 1], plot_readout = False)
        
            # plot readout
        plt.fill([0, 0, - self._sample.readout_tone_length / self._x_unit[x_unit], - self._sample.readout_tone_length / self._x_unit[x_unit]], 
                [0, ymax, ymax, 0], color = "C7", alpha = 0.3)
        # add label for readout
        plt.text(-0.5*self._sample.readout_tone_length / self._x_unit[x_unit], ymax/2.,
                "readout", horizontalalignment = "center", verticalalignment = "center", rotation = 90, size = 14)
        
        # adjust plot limits
        plt.xlim(xmin + 0.005 * abs(xmax - xmin), xmax - 0.006 * abs(xmax - xmin))
        plt.ylim(ymin, ymax + 0.025 * (ymax - ymin))
        plt.xlabel("time " + x_unit)
        return

    def _get_sequences(self, IQ_mixing = False):
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
    
    def load(self, device):
        """
        !!! Currently dissabled !!!
        Load the sequences stored in channels to your physical device (awg, fpga).

        Args:
            device:   name of your physical device
        """
        # Case descrimination:
        # actual_load_awg/fpga(self._sequences)
        return False