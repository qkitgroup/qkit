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

import qkit
import numpy as np
import logging
from qkit.gui.notebook.Progress_Bar import Progress_Bar
import gc


def _adjust_wfs_for_tabor(wf1, wf2, ro_index, chpair, segment, sample):
    """
    This function simply adjust the waveforms, coming from the virtual awg, to fit the requirements of the
    Tabor awg"
    """
    divisor = 16
    marker1 = np.zeros_like(wf1)
    readout_ind = ro_index[segment] - int(sample.clock * sample.readout_delay)  # TODO: check if the sign is correct
    marker1[readout_ind:readout_ind + 10] = 1
    begin_zeros = len(wf1) % divisor
    # minimum waveform is 192 points, handled by the Tabor driver
    if begin_zeros != 0:
        wf1 = np.append(np.zeros(divisor - begin_zeros), wf1)
        wf2 = np.append(np.zeros(divisor - begin_zeros), wf2)
        marker1 = np.append(np.zeros(divisor - begin_zeros), marker1)
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
    number_of_channels = 0
    complex_channel = []
    for chan in channel_sequences:
        if True in (s.dtype == np.complex128 for s in chan):
            number_of_channels += 2
            complex_channel.append(True)
        else:
            number_of_channels += 1
            complex_channel.append(False)
    if number_of_channels > awg.numchannels:
        raise ValueError('more sequences than channels')
    # reordering channels if necessary
    if number_of_channels > 2:
        if complex_channel[:2] == [False, True]:
            logging.warning('Channels reordered! Please do not split complex channels on two different channelpairs.'
                            'Complex channel is on chpair 1')
            channel_sequences[:2] = [channel_sequences[1], channel_sequences[0]]
            complex_channel[:2] = [True, False]
    qkit.flow.start()

    if reset:
        awg.set('p%i_runmode' % 1, 'SEQ')
        awg.define_sequence(1, len(ro_index))
        if number_of_channels > 2:
            awg.set('p%i_runmode' % 2, 'SEQ')
            awg.define_sequence(2, len(ro_index))
        # amplitude settings of analog output
        awg.set_ch1_offset(0)
        awg.set_ch2_offset(0)
        awg.set_ch1_amplitude(2)
        awg.set_ch2_amplitude(2)

    # Loading the waveforms into the AWG, differentiating between all cases
    if show_progress_bar:
        p = Progress_Bar(len(ro_index), 'Load AWG')

    if number_of_channels == 1:
        for j, seq in enumerate(channel_sequences):
            _adjust_wfs_for_tabor(seq, [0], ro_index, 1, j, sample)
            if show_progress_bar:
                p.iterate()

    elif number_of_channels == 2:
        if complex_channel[0]:
            for j, seq in enumerate(channel_sequences):
                _adjust_wfs_for_tabor(seq.real, seq.imag, ro_index, 1, j, sample)
                if show_progress_bar:
                    p.iterate()
        else:
            for j, seq in enumerate(zip(channel_sequences)):
                _adjust_wfs_for_tabor(seq[0], seq[1], ro_index, 1, j, sample)
                if show_progress_bar:
                    p.iterate()

    elif number_of_channels == 3:
        if complex_channel[0]:
            for j, seq in enumerate(zip(channel_sequences)):
                _adjust_wfs_for_tabor(seq[0].real, seq[0].imag, ro_index, 1, j, sample)
                _adjust_wfs_for_tabor(seq[3], [0], ro_index, 2, j, sample)
                if show_progress_bar:
                    p.iterate()
        elif not complex_channel[0]:
            for j, seq in enumerate(zip(channel_sequences)):
                _adjust_wfs_for_tabor(seq[0], seq[1], ro_index, 1, j, sample)
                _adjust_wfs_for_tabor(seq[3], [0], ro_index, 2, j, sample)
                if show_progress_bar:
                    p.iterate()

    else:  # 4 channels
        if complex_channel == [True, True]:
            for j, seq in enumerate(zip(channel_sequences)):
                _adjust_wfs_for_tabor(seq[0].real, seq[0].imag, ro_index, 1, j, sample)
                _adjust_wfs_for_tabor(seq[1].real, seq[1].imag, ro_index, 2, j, sample)
                if show_progress_bar:
                    p.iterate()
        elif complex_channel == [True, False, False]:
            for j, seq in enumerate(zip(channel_sequences)):
                _adjust_wfs_for_tabor(seq[0].real, seq[0].imag, ro_index, 1, j, sample)
                _adjust_wfs_for_tabor(seq[1], seq[2], ro_index, 2, j, sample)
                if show_progress_bar:
                    p.iterate()
        elif complex_channel == [False, False, True]:
            for j, seq in enumerate(zip(channel_sequences)):
                _adjust_wfs_for_tabor(seq[0], seq[1], ro_index, 1, j, sample)
                _adjust_wfs_for_tabor(seq[2].real, seq[2].imag, ro_index, 2, j, sample)
                if show_progress_bar:
                    p.iterate()
        else:
            for j, seq in enumerate(zip(channel_sequences)):
                _adjust_wfs_for_tabor(seq[0], seq[1], ro_index, 1, j, sample)
                _adjust_wfs_for_tabor(seq[2], seq[3], ro_index, 2, j, sample)
                if show_progress_bar:
                    p.iterate()

    gc.collect()

    if reset:
        # enable channels
        # awg.preset()
        awg.set_ch1_status(True)
        awg.set_ch2_status(True)
    qkit.flow.end()
    return np.all([awg.get('ch%i_status' % i) for i in [1, 2]])
