# load_awg.py
# adapted from the old load_awg, started by M. Jerger and adapted by AS, JB
# and now adjusted for the virutal_awg by TW
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

# import qkit  # ToDO: flow comments?
import numpy as np
import logging
from qkit.gui.notebook.Progress_Bar import Progress_Bar
import gc


def _adjust_wfs_for_tabor(wf1, wf2, ro_index, chpair, segment, sample):
    """
    This function simply adjust the waveforms, coming from the virtual awg, to fit the requirements of the
    Tabor awg
    """
    divisor = 16
    readout_ind = int(ro_index[segment] + int(sample.clock * sample.readout_delay))
    # Adjust length to fit marker at arbitrary positions
    if readout_ind + 10 > len(wf1):
        marker1 = np.zeros(readout_ind + 10)
        marker1[readout_ind:readout_ind + 10] = 1
        wf1 = np.append(wf1, np.zeros(readout_ind + 10 - len(wf1)))
        wf2 = np.append(wf2, np.zeros(readout_ind + 10 - len(wf2)))
    elif readout_ind < 0:
        marker1 = np.append(np.zeros(np.abs(readout_ind)), np.zeros_like(wf1))
        marker1[0:10] = 1
        wf1 = np.append(np.zeros(np.abs(readout_ind)), wf1)
        wf2 = np.append(np.zeros(np.abs(readout_ind)), wf2)
    else:
        marker1 = np.zeros_like(wf1)
        marker1[readout_ind:readout_ind + 10] = 1
    # for single channel pulses
    if len(wf1) > len(wf2):
        wf2 = np.append(wf2, np.zeros(len(wf1)-len(wf2)))
    
    # all wfms start and end with 0
    wf1 = np.append(0, wf1)
    wf1 = np.append(wf1, 0)
    wf2 = np.append(0, wf2)
    wf2 = np.append(wf2, 0)
    marker1 = np.append(0, marker1)
    marker1 = np.append(marker1, 0)
        
    end_zeros = len(wf1) % divisor
    # minimum waveform is 192 points, handled by the Tabor driver
    if end_zeros != 0:
        wf1 = np.append(np.zeros(divisor - end_zeros), wf1)
        wf2 = np.append(np.zeros(divisor - end_zeros), wf2)
        marker1 = np.append(np.zeros(divisor - end_zeros), marker1)
    sample.awg.wfm_send2(wf1, wf2, marker1, marker1, chpair * 2 - 1, segment + 1)


def load_tabor(channel_sequences, ro_index, sample, reset=True, show_progress_bar=True):
    """
    This function takes the data, coming from virtual awg, and loads them into the awg
    :param channel_sequences: This must be a list of list, i.e., a list of channels each containing the sequences
    :param ro_index: coming from virtual awg, for each sequence there is a ro_index letting the awg know, when to
                     send the trigger.
    :param sample: you should know this
    :param reset: simply sets the awg_channel active, probably not needed
    :param show_progress_bar: enables the progress bar
    :return:
    """
    awg = sample.awg
    awg.clear_waveforms()
    number_of_channels = 0
    complex_channel = []
    for chan in channel_sequences:
        if True in (s.dtype == np.complex128 for s in chan):
            number_of_channels += 2
            complex_channel.append(True)
        else:
            number_of_channels += 1
            complex_channel.append(False)
    if number_of_channels > awg._numchannels:
        raise ValueError('more sequences than channels')
    # reordering channels if necessary
    if number_of_channels > 2:
        if complex_channel[:2] == [False, True]:
            logging.warning('Channels reordered! Please do not split complex channels on two different channelpairs.'
                            'Complex channel is on chpair 1')
            channel_sequences[:2] = [channel_sequences[1], channel_sequences[0]]
            complex_channel[:2] = [True, False]
    #qkit.flow.start()

    if reset:
        _reset(awg, number_of_channels, ro_index)
    # Loading the waveforms into the AWG, differentiating between all cases
    if show_progress_bar:
        p = Progress_Bar(len(ro_index), 'Load AWG')

    if number_of_channels == 1:
        for j, seq in enumerate(channel_sequences[0]):
            _adjust_wfs_for_tabor(seq, [0], ro_index, 1, j, sample)
            if show_progress_bar:
                p.iterate()

    elif number_of_channels == 2:
        if complex_channel[0]:
            for j, seq in enumerate(channel_sequences[0]):
                _adjust_wfs_for_tabor(seq.real, seq.imag, ro_index, 1, j, sample)
                if show_progress_bar:
                    p.iterate()
        else:
            for j, seq in enumerate(zip(channel_sequences[0], channel_sequences[1])):
                _adjust_wfs_for_tabor(seq[0], seq[1], ro_index, 1, j, sample)
                if show_progress_bar:
                    p.iterate()

    elif number_of_channels == 3:
        if complex_channel[0]:
            for j, seq in enumerate(zip(channel_sequences[0], channel_sequences[1])):
                _adjust_wfs_for_tabor(seq[0].real, seq[0].imag, ro_index, 1, j, sample)
                _adjust_wfs_for_tabor(seq[1], [0], ro_index, 2, j, sample)
                if show_progress_bar:
                    p.iterate()
        else:
            for j, seq in enumerate(zip(channel_sequences[0], channel_sequences[1], channel_sequences[2])):
                _adjust_wfs_for_tabor(seq[0], seq[1], ro_index, 1, j, sample)
                _adjust_wfs_for_tabor(seq[2], [0], ro_index, 2, j, sample)
                if show_progress_bar:
                    p.iterate()

    else:  # 4 channels
        if complex_channel == [True, True]:
            for j, seq in enumerate(zip(channel_sequences[0], channel_sequences[1])):
                _adjust_wfs_for_tabor(seq[0].real, seq[0].imag, ro_index, 1, j, sample)
                _adjust_wfs_for_tabor(seq[1].real, seq[1].imag, ro_index, 2, j, sample)
                if show_progress_bar:
                    p.iterate()
        elif complex_channel == [True, False, False]:
            for j, seq in enumerate(zip(channel_sequences[0], channel_sequences[1], channel_sequences[2])):
                _adjust_wfs_for_tabor(seq[0].real, seq[0].imag, ro_index, 1, j, sample)
                _adjust_wfs_for_tabor(seq[1], seq[2], ro_index, 2, j, sample)
                if show_progress_bar:
                    p.iterate()
        elif complex_channel == [False, False, True]:
            for j, seq in enumerate(zip(channel_sequences[0], channel_sequences[1], channel_sequences[2])):
                _adjust_wfs_for_tabor(seq[0], seq[1], ro_index, 1, j, sample)
                _adjust_wfs_for_tabor(seq[2].real, seq[2].imag, ro_index, 2, j, sample)
                if show_progress_bar:
                    p.iterate()
        else:
            for j, seq in enumerate(zip(channel_sequences[0], channel_sequences[1],
                                        channel_sequences[2], channel_sequences[3])):
                _adjust_wfs_for_tabor(seq[0], seq[1], ro_index, 1, j, sample)
                _adjust_wfs_for_tabor(seq[2], seq[3], ro_index, 2, j, sample)
                if show_progress_bar:
                    p.iterate()

    gc.collect()

    if number_of_channels <= 2:
        num_channels = [1, 2]
    else:
        num_channels = [1, 2, 3, 4]
    return np.all([awg.get('ch%i_status' % i) for i in num_channels])


def _reset(awg, num_channels, ro_index):
    awg.set('p%i_runmode' % 1, 'SEQ')
    awg.define_sequence(1, len(ro_index))
    awg.set_ch1_status(True)
    awg.set_ch2_status(True)
    awg.set_ch1_offset(0)
    awg.set_ch2_offset(0)
    awg.set_ch1_amplitude(2)
    awg.set_ch2_amplitude(2)
    awg.set_ch1_marker_output(True)
    awg.set_ch1_marker_high(1)
    awg.set_ch2_marker_output(True)
    awg.set_ch2_marker_high(1)
    if num_channels > 2:
        awg.set('p%i_runmode' % 2, 'SEQ')
        awg.define_sequence(3, len(ro_index))
        awg.set_ch3_status(True)
        awg.set_ch4_status(True)
        awg.set_ch3_offset(0)
        awg.set_ch4_offset(0)
        awg.set_ch3_amplitude(2)
        awg.set_ch4_amplitude(2)
        awg.set_ch3_marker_output(True)
        awg.set_ch3_marker_high(1)
        awg.set_ch4_marker_output(True)
        awg.set_ch4_marker_high(1)
