# load_awg.py
# started by M. Jerger and adapted by AS, JB


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
    divisor = 16
    marker1 = np.zeros_like(wf1)
    readout_ind = ro_index[segment] - int(sample.clock * sample.readout_delay)
    marker1[readout_ind:readout_ind + 10] = 1
    begin_zeros = len(wf1) % divisor
    # minimum waveform is 192 points, handled by the Tabor driver
    if begin_zeros != 0:
        wf1 = np.append(np.zeros(divisor - begin_zeros), wf1)
        wf2 = np.append(np.zeros(divisor - begin_zeros), wf2)
        marker1 = np.append(np.zeros(divisor - begin_zeros), marker1)
    qkit.flow.sleep()
    sample.awg.wfm_send2(wf1, wf2, marker1, marker1, chpair * 2 - 1, segment + 1)


def load_tabor(channels, ro_index, sample, reset=True, show_progress_bar=True):
    """
        set awg to sequence mode and push a number of waveforms into the sequencer

        inputs:

        ts: array of times, len(ts) = #sequenzes
        wfm_func: waveform function usually generated via generate_waveform using ts[i]; this can be a tuple of arrays (for channels 0,1, heterodyne mode) or a single array (homodyne mode)
        sample: sample object

        iq: Reference to iq mixer instrument. If None (default), the wfm will not be changed. Otherwise, the wfm will be converted via iq.convert()

        marker: marker array in the form [[ch1m1,ch1m2],[ch2m1,ch2m2]] and all entries arrays of sample length
        markerfunc: analog to wfm_func, set marker to None when used

        for the 6GS/s AWG, the waveform length must be divisible by 64
        for the 1.2GS/s AWG, it must be divisible by 4

        chpair: if you use the 4ch Tabor AWG as a single 2ch instrument, you can chose to take the second channel pair here (this can be either 1 or 2).
    """
    awg = sample.awg
    readout_delay = sample.readout_delay
    number_of_channels = 0
    complex_channel=[]
    for chan in channels:
        if True in (s.dtype == np.complex128 for s in chan):
            number_of_channels += 2
            complex_channel.append(True)
        else:
            number_of_channels += 1
            complex_channel.append(False)
    if number_of_channels > awg.numchannels:
        raise ValueError('more sequences than channels')
    #reordering channels if necessary
    if number_of_channels > 2:
        if complex_channel[:2] == [False, True]:
            logging.warning('Channels reordered! Please do not split complex channels on two different channelpairs.'
                            'Complex channel is on chpair 1')
            channels[:2] = [channels[1], channels[0]]
            complex_channel[:2] = [True, False]
    qkit.flow.start()

    if reset:
        awg.set('p%i_runmode' % 1, 'SEQ')  ##### How to solve that????
        awg.define_sequence(1, len(ro_index))  #### and that?
        if number_of_channels > 2:
            awg.set('p%i_runmode' % 2, 'SEQ')  ##### How to solve that????
            awg.define_sequence(2, len(ro_index))
        # amplitude settings of analog output
        awg.set_ch1_offset(0)
        awg.set_ch2_offset(0)
        awg.set_ch1_amplitude(2)
        awg.set_ch2_amplitude(2)

    #### Loading the waveforms into the AWG, differentiating between all cases ####
    if show_progress_bar:
        p = Progress_Bar(len(ro_index), 'Load AWG')

    if number_of_channels == 1:
        for j, seq in enumerate(channels):
            _adjust_wfs_for_tabor(seq, [0], ro_index, 1, j, sample)
            if show_progress_bar:
                p.iterate()

    elif number_of_channels == 2:
        if complex_channel[0]:
            for j, seq in enumerate(channels):
                _adjust_wfs_for_tabor(seq.real, seq.imag, ro_index, 1, j, sample)
                if show_progress_bar:
                    p.iterate()
        else:
            for j, seq in enumerate(zip(channels)):
                _adjust_wfs_for_tabor(seq[0], seq[1], ro_index, 1, j, sample)
                if show_progress_bar:
                    p.iterate()

    elif number_of_channels == 3:
        if complex_channel[0]:
            for j, seq in enumerate(zip(channels)):
                _adjust_wfs_for_tabor(seq[0].real, seq[0].imag, ro_index, 1, j, sample)
                _adjust_wfs_for_tabor(seq[3], [0], ro_index, 2, j, sample)
                if show_progress_bar:
                    p.iterate()
        elif not complex_channel[0]:
            for j, seq in enumerate(zip(channels)):
                _adjust_wfs_for_tabor(seq[0], seq[1], ro_index, 1, j, sample)
                _adjust_wfs_for_tabor(seq[3], [0], ro_index, 2, j, sample)
                if show_progress_bar:
                    p.iterate()

    else:  # 4 channels
        if complex_channel == [True, True]:
            for j, seq in enumerate(zip(channels)):
                _adjust_wfs_for_tabor(seq[0].real, seq[0].imag, ro_index, 1, j, sample)
                _adjust_wfs_for_tabor(seq[1].real, seq[1].imag, ro_index, 2, j, sample)
                if show_progress_bar:
                    p.iterate()
        elif complex_channel == [True, False, False]:
            for j, seq in enumerate(zip(channels)):
                _adjust_wfs_for_tabor(seq[0].real, seq[0].imag, ro_index, 1, j, sample)
                _adjust_wfs_for_tabor(seq[1], seq[2], ro_index, 2, j, sample)
                if show_progress_bar:
                    p.iterate()
        elif complex_channel == [False, False, True]:
            for j, seq in enumerate(zip(channels)):
                _adjust_wfs_for_tabor(seq[0], seq[1], ro_index, 1, j, sample)
                _adjust_wfs_for_tabor(seq[2].real, seq[2].imag, ro_index, 2, j, sample)
                if show_progress_bar:
                    p.iterate()
        else:
            for j, seq in enumerate(zip(channels)):
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


