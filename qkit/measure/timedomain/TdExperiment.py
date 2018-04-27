# Created by A.Stehli@KIT 04/2018
# time domain experiment class

import numpy as np
import matplotlib.pyplot as plt
from ipywidgets import interact, widgets, Layout

import qkit.measure.timedomain.pulse_sequence as ps
#from qkit.measure.timedomain.awg.load import load_sequence as awgload



class TdChannel(object):
    '''
    Class managing the channels for TdExperiment.

    Important functions:
        set_sequences:    Add sequence deleting previously stored sequences
        add_sequences:    Add sequence maintaining currently stored sequences
        delete_sequences: Delete previously stored sequences
        plot:             Plot the pulse sequences
    '''
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
        '''
        Append sequence to sequences currently stored in channel.

        Input:
            sequence - sequence object
            *args    - time where sequence is called
        '''
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
        '''
        Set sequence in channel to sequence deleting previouisly stored sequences.

        Input:
            sequence - sequence object
            *args    - time where sequence is called
        '''
        self._sequences = []
        self._times = []
        if args is ():
            print("No time given.")
            return False
        self.add_sequence(sequence, *args)
        return True

    def delete_sequence(self, seq_nr):
        '''
        Delete sequence number seq_nr (counting from 0).
        '''
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
            return False
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
            x_unit  - Unit of the x-axis in the plot. Options are "s", "ms", "us", "ns".
        """
        sequences, readout_indices = self._get_sequences()
        seq_max = len(readout_indices) - 1
        
        bounds = self._get_boundaries(sequences, readout_indices, x_unit)

        interact(lambda sequence: self._plot_sequence(sequences[sequence], readout_indices[sequence], x_unit, bounds), 
                sequence = widgets.IntSlider(value = 0, min = 0, max = seq_max, layout = Layout(width = "98%", height = "50px")))
        return True

    def _plot_sequence(self, seq, ro_ind, x_unit, bounds):
        """
        The actual plotting of the sequences happens here.
        
        Input:
            seq    - sequence (as array) to be plotted
            ro_ind - Index of the readout in seq
            x_unit - x_unit for the time axis
            bounds - min and max values for plot boundaries
        """
        fig = plt.figure(figsize=(18,6))
        xmin, xmax, ymin, ymax = bounds
        samplerate = self._sample.clock
        time = -(np.arange(0, len(seq) + 1, 1) - ro_ind) / (samplerate * self._x_unit[x_unit])
        # make sure last point of the waveform goes to zero
        seq = np.append(seq, 0)

        # plot sequence
        plt.plot(time, seq)
        # plot readout
        plt.fill([0, 0, - self._sample.readout_tone_length / self._x_unit[x_unit], - self._sample.readout_tone_length / self._x_unit[x_unit]], 
                [0, ymax, ymax, 0], color = "C7", alpha = 0.3)
        plt.xlim(xmin + 0.005 * abs(xmax - xmin), xmax - 0.006 * abs(xmax - xmin))
        plt.ylim(ymin, ymax + 0.025 * (ymax - ymin))
        plt.xlabel("time " + x_unit)
        # add label for readout
        plt.text(-0.5*self._sample.readout_tone_length / self._x_unit[x_unit], ymax/2.,
                 "readout", horizontalalignment = "center", verticalalignment = "center", rotation = 90, size = 14)
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
        '''
        Explicitly calculate the waveforms of all sequences at their input time.

        Output:
            List of waveform arrays.
            List of readout indices.
        '''
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
        In this class only device types should be descriminated, the actual load fct for awg/fpga's are stored seperately.
    """

    def __init__(self, sample, channels = 1):
        """
        input:
            sample   - Sample object.
            channels - Number of channels used in the experiment.
        """
        if sample is not None:
            self._sample = sample

        self._chan_num = num_channels 
        self._sequences = []
        for ch in range(self._chan_num):
            self._sequences.append([])

        # Boundaries for plotting
        self._xmin = np.zeros(self._chan_num)
        self._xmax = np.zeros(self._chan_num)
        self._ymin = np.zeros(self._chan_num)
        self._ymax = np.zeros(self._chan_num)
        
        # Dictonary for channel colors
        self._chancols = {1 : "C0", 2 : "C1", 3 : "C2", 4 : "C3", 5 : "C4", 6 : "C5", 7 : "C6"}

        self._channels = [None]  # type: List[TdExperimentChannel]
        self._channels.extend([] for i in range(num_channels)) # TdExperimentChannel("C{}".format(i+1))
    
    def set_sequences(self, seq, channel = 1):
        """
        Input:
            seq     - Sequence or list of sequences.
            channel - Channel number in which sequence will be loaded.
        
        Delete previously added sequences, replaxing them with seq.
        If channel is None set all sequences in all channels to seq.
        """
        return False

    def add_sequences(self, seq, channel = 1):
        """
        Input:
            seq     - Sequence or list of sequences.
            channel - Channel number in which sequence will be loaded.

        Sequences seq are added to current sequences.
        If channel is None all sequences are appended by seq.
        """
        if channel > self._chan_num:
            print("Given channel number {:d} is larger than total number of channels {:d}".format(channel, self._chan_num))
            return
        return False

    def get_sequences(self, channel = None):
        """
        Input:
            seq     - Sequence or list of sequences.
            channel - Channel number in which sequence will be loaded.

        Returns list of sequences stored in channel.
        If channel is None all sequences.
        """
        return False

    def plot(self, x_unit = "ns", channel = None):
        """
        Input:
            channel - Channel or list of channels to be plotted. If None the sequences of all channels are plotted. 
            x_unit  - Unit of the x-axis in the plot. Options are "s", "ms", "us", "ns".
            
        Plots the sequences stored in channel. A slider provides the option to sweep through the sequences.
        Readout pulse is displayed as transparent box starting at t = 0 (with multiple readout pulses the first one is fixed at t = 0).
        Positive times (left side) are before, negative times after the readout pulse.
        """
        if channel is None:
            channel = range(self._chan_num)
        else:
            channel = np.atleast_1d(channel) - 1
        
        if max(channel) > self._chan_num:
            print("Given channel number {:d} is larger than total number of channels {:d}".format(channel, self._chan_num))
            return

        seq_max = max([len(x) for x in self._sequences]) - 1
        interact(lambda sequence: self._plot_seq(x_unit, channel, sequence), sequence = widgets.IntSlider(value = 0, min = 0, max = seq_max))
        return

    def _plot_seq(self, x_unit, channels = [0], sequence_ind = 0):
        """
        The actual plotting happens here.
        
        Input:
            channels  - Indices of the channels to be plotted.
            sequence_ind - Index of sequence to be plotted.
        """
        for chan in channels:
            try:
                seq = self._sequences[chan][sequence_ind]
                wfm = seq.get_waveform(self.samplerate)
                readout_time = seq.readout_time
                if seq.readout_time is not None:
                    plt.fill_between(np.array([0, 0 - self._sample.readout_tone_length])/self._x_unit[x_unit], [1, 1],
                    color = self._chancols[chan + 1], alpha = 0.3)
                else:
                    readout_time = 0
            except:
                wfm = np.zeros(2)
                readout_time = 0

            #readout_time0 = max(readout_time, readout_time0)
            time = (np.arange(-1, len(wfm), 1)/self.samplerate - readout_time)/self._x_unit[x_unit]
            wfm = np.append([0], wfm) # Set first point to 0, looks better in plot
            plt.plot(-time, wfm, color = self._chancols[chan + 1])
        
        xmin = max(self._xmin[channels])/self._x_unit[x_unit]
        xmax = -(max(self._xmax[channels]))/self._x_unit[x_unit] # Invert time axis such that t>0 before readout
        plt.xlim(xmin + 0.01*np.abs(xmax - xmin), xmax - 0.01*np.abs(xmax - xmin))
        plt.ylim(1.1*min(self._ymin[channels]), 1.1*max(self._ymax[channels]))
        plt.xlabel("time " + x_unit)
        return
    
    def _as_list(self, seq):
        """
        Return seq as list (if seq is 1d).
        """
        if isinstance(seq, list):
            return seq
        else:
            return [seq]

    def _get_size(self, seq):
        """
        Input:
            seq - Sequence or list of sequences.
        Returns:
        """
        seq = self._as_list(seq)
        xmax, ymin, ymax = 0, 0, 0
        for s in seq:
            xmin = max([s.readout_time for s in seq])
            xmax = max(xmax, s.length - xmin)
            xmax = max(xmax, self._sample.readout_tone_length)
            ymin = min(ymin, min(s.get_waveform(self.samplerate)))
            ymax = max(ymax, max(s.get_waveform(self.samplerate)))
        return xmin, xmax, ymin, ymax

    def load(self, device, channels = None, readout_channel = None):
        # Case descrimination:
        # actual_load_awg/fpga(self._sequences)
        return False

    def _get_readout_marker(self, channel = None):
        return False