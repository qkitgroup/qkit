# Created by A.Stehli@KIT 04/2018
# time domain experiment class

import numpy as np
import matplotlib.pyplot as plt
from ipywidgets import interact, widgets, Layout

import qkit.measure.timedomain.pulse_sequence as ps
#from qkit.measure.timedomain.awg.load import load_sequence as awgload



class TdChannel(object):
    """
    Class managing the channels for TdExperiment.

    Important functions:
        set_sequence:    Add sequence deleting previously stored sequences
        add_sequence:    Add sequence maintaining currently stored sequences
        delete_sequence: Delete previously stored sequences
        plot:            Plot the pulse sequences
    """
    def __init__(self, sample, name):
        """
        Input:
            sample - sample object
            name   - name of the channel
        """
        self.name = name
        self._sample = sample
        self._sequences = []
        self._times = []
        self._interleave = False
        # Dictionary for x-axis scaling
        self._x_unit = { "s": 1, "ms": 1e-3, "us": 1e-6, "ns": 1e-9}

    def add_sequence(self, sequence, *args):
        """
        Append sequence to sequences currently stored in channel.

        Input:
            sequence - sequence object
            *args    - time where sequence is called
        """
        if args is ():
            print("No time given.")
            return False
        len0 = 0
        for arg in args:
            if len0 is 0:
                len0 = len(arg)
            elif len(arg) is not len0:
                print("Dimensions of input arrays do not match.")
                return False
        self._sequences.append(sequence)
        self._times.append(np.vstack((args)).T)
        if (len(self._sequences) >= 1) and self._interleave:
            if not self.interleave():
                print("Dimension of new time array does not fit previous inputs.\nInterleaving no longer possible.")
        return True
    
    def set_sequence(self, sequence, *args):
        """
        Set sequence in channel to sequence deleting previouisly stored sequences.

        Input:
            sequence - sequence object
            *args    - time where sequence is called
        """
        self._sequences = []
        self._times = []
        if args is ():
            print("No time given.")
            return False
        self.add_sequence(sequence, *args)
        return True

    def delete_sequence(self, seq_nr):
        """
        Delete sequence number seq_nr (counting from 0).
        """
        temp = self._sequences.pop(seq_nr)
        temp = self._times.pop(seq_nr)
        return True

    def get_sequence_dict(self):
        """
        Returns a dictionary featuring all important channel attributes:
            - sequence_i -> list of all pulses of sequnces number i (counting from 0)
            - time_i -> time values for which sequence is called
            - value of interleave
        """
        seq_dict = {}
        for i in range(len(self._sequences)):
            seq_dict["sequence_%i"%i] = self._sequences[i].get_pulses()
            seq_dict["time_%i"%i] = self._times[i]
        seq_dict["interleave"] = self._interleave
        return seq_dict

    def interleave(self, value = True):
        """
        Sequences with an equal number of timesteps may be interleaved.
        """
        if value is False:
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

        Input:
            x_unit  - unit of the x-axis in the plot. Options are "s", "ms", "us", "ns".
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
            seq    - sequence (as array) to be plotted
            ro_ind - Index of the readout in seq
            x_unit - x_unit for the time axis
            bounds - min and max values for plot boundaries
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

        Input:
            x_unit - see dictionary
        Output:
            List of boundaries
        """
        xmin = max(readout_indices)/ (self._x_unit[x_unit] * self._sample.clock)
        xmax = - (max(np.array([len(seq) for seq in sequences]) - np.array(readout_indices)) /self._sample.clock + self._sample.readout_tone_length)/self._x_unit[x_unit]
        ymin = np.amin(np.concatenate(sequences))
        ymax = np.amax(np.concatenate(sequences))
        bounds = [xmin, xmax, ymin, ymax]
        return bounds

    def _get_sequences(self):
        """
        Explicitly calculate the waveforms of all sequences at their input time.

        Output:
            List of waveform arrays.
            List of readout indices.
        """
        seq_list = []
        ro_inds = []
        for i in range(len(self._sequences)):
            for time in self._times[i]:
                seq, ro_ind = self._sequences[i](time)
                seq_list.append(seq)
                ro_inds.append(ro_ind)
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
        self.channel[nr]: Channel object - sequences can be added and plotted.
        set_sequences:    Add sequence(s) object (see pulse_sequence.py), deleting previously stored sequences.
        add_sequences:    Add sequence(s) object (see pulse_sequence.py), maintaining currently stored sequences.
        get_sequences:    Returns sequence stored sequences.
        plot:             Plot the pulse sequences in all channels.

    TODO:
        Write .load fct to directly load the pulse sequences on a device, i.e. TdExperiment.load(device).
    """

    def __init__(self, sample, channels = 1):
        """
        input:
            sample   - sample object.
            channels - number of channels used in the experiment.
        """
        if sample is None:
            print("No sample object given.")
            return False
        
        self._sample = sample
        self._num_chans = channels

        self.channels = [None]  # type: List[TdExperimentChannel]
        self.channels.extend(TdChannel(self._sample, "channel_%i"%(i + 1)) for i in range(channels))

        # Dictionary for x-axis scaling
        self._x_unit = { "s": 1, "ms": 1e-3, "us": 1e-6, "ns": 1e-9}
        # Dictonary for channel colors
        self._chancols = {1 : "C0", 2 : "C1", 3 : "C2", 4 : "C3", 5 : "C4", 6 : "C5", 7 : "C6"}
    
    def set_sequence(self, sequence, time, channel = 1):
        """
        Delete previously added sequences, replaxing them with sequence.
        If channel is None set all sequences in all channels to sequence.

        Input:
            sequence - sequence object.
            time     - time where sequence is called
            channel  - channel number in which sequence will be loaded
        
        """
        if channel is not None:
            self.channels[channel].set_sequence(sequence, time)
        elif channel is None:
            for channel in self.channels:
                channel.set_sequence(sequence, time)
        return True

    def add_sequence(self, sequence, time, channel = 1):
        """
        Sequence is added to current sequences.
        If channel is None all sequence is added to all channels.
        
        Input:
            sequence - sequence or list of sequences.
            time     - time where sequence is called
            channel  - channel number in which sequence will be loaded.

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
    
    def delete_sequence(self, seq_nr, channel = 1):
        """
        Delete sequence seq_nr in stated channel.
        If channel is None sequence seq_nr is deleted from all channels.

        Input:
            seq_nr   - number of the sequence to be deleted
            channel  - channel number
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
            - sequence_i -> list of all pulses of sequnces number i (counting from 0)
            - time_i -> time values for which sequence is called
            - value of interleave
        """
        chan_dicts = []
        for chan in self.channels[1:]:
            chan_dicts.append(chan.get_sequence_dict())
        return chan_dicts
    
    def interleave(self, value = True, channel = 1):
        """
        For each channel, sequences with an equal number of timesteps may be interleaved.

        Input:
            value   - value of interleave (True/False)
            channel - channel to be interleaved. If channel is None action applies to all channels.
        """
        if channel is not None:
            self.channels[channel].interleave(value)
        else:
            for chan in self.channels[1:]:
                chan.interleave(value)
        return True

    def plot(self, x_unit = "ns"): 
        """
        Plots the sequences stored in all channels.
        A slider provides the option to sweep through the sequences.
        Readout pulse is fixed at t = 0, where is t>0 before the readout tone.

        Input:
            x_unit  - Unit of the x-axis in the plot. Options are "s", "ms", "us", "ns".
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
        
        Input:
            seqs    - List of sequences to be plotted (i.e. one list of sequence for each channel)
            ro_inds - Indices of the readout
            x_unit  - x_unit for the time axis
            bounds  - min and max values for plot boundaries
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

    def get_sequences(self):
        """
        Returns a list of sequences for each channel, as well as a list of indices for the readout timing.
        """
        seqs = []
        ro_inds = []
        for chan in self.channels[1:]:
            sequences, readout_indices = chan._get_sequences()
            seqs.append(sequences)
            ro_inds.append(readout_indices)
        return seqs, ro_inds

    def _sync(self):
        """
        Synchronize sequences of all channels to the same readout time.

        Output:
            sequences       - list of synchronized sequences as arrays (one each channel)
            readout_indices - array of new readout indices
        """
        seqs, ro_inds = self.get_sequences()
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
    
    def load(self, device, channels = None, readout_channel = None):
        # Case descrimination:
        # actual_load_awg/fpga(self._sequences)
        return False

    def _get_readout_marker(self, channel = None):
        return False