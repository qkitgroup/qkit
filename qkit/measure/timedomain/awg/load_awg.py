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
from qkit.gui.notebook.Progress_Bar import Progress_Bar
import gc


def load_tabor(sequences, ro_index, sample, reset=True, show_progress_bar=True):
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
    clock = sample.clock

    number_of_sequences = 0
    for seqs in sequences:
        if seqs[0].dtype == np.complex128:
            number_of_sequences += 2
        else:
            number_of_sequences += 1
    if number_of_sequences > awg.numchannels:
        raise ValueError('more sequences than channels')

    qkit.flow.start()

    if reset:
        awg.set('p%i_runmode' % 1, 'SEQ')  ##### How to solve that????
        awg.define_sequence(1, len(ro_index))  #### and that?
        if len(number_of_sequences) > 2:
            awg.set('p%i_runmode' % 2, 'SEQ')  ##### How to solve that????
            awg.define_sequence(2, len(ro_index))
        # amplitude settings of analog output
        awg.set_ch1_offset(0)
        awg.set_ch2_offset(0)
        awg.set_ch1_amplitude(2)
        awg.set_ch2_amplitude(2)

    # update all channels and times
    for i, seqs in enumerate(sequences):  # run through all channels
        # TODO: init progress bar
        if seqs[0].dtype == np.complex128:  # test if I/Q or Z-pulses/homodyne
            for j, seq in enumerate(seqs):
                wf_i = seq.real
                wf_q = seq.imag
                _adjust_wfs_for_tabor(wf_i, wf_q, ro_index, i, j, sample)
        else:
            for j, seq in enumerate(seqs):
                wf_1 = seq
                if i < len(seqs) and sequences[i + 1][0].dtype != np.complex128:
                    wf_2 = seqs[i + 1][j]
                elif i == len(seqs):
                    wf_2 = np.zeros_like(wf_1)
                else:
                    raise TypeError('non-complex and odd waveforms before complex ones')
                _adjust_wfs_for_tabor(wf_1, wf_2, ro_index, i, j, sample)

    gc.collect()

    if reset:
        # enable channels
        # awg.preset()
        awg.set_ch1_status(True)
        awg.set_ch2_status(True)
    qkit.flow.end()
    return np.all([awg.get('ch%i_status' % i) for i in [1, 2]])


def _adjust_wfs_for_tabor(wf1, wf2, ro_index, chpair, segment, sample):
    divisor = 4
    marker1 = np.zeros_like(wf1)
    readout_ind = ro_index[segment] - int(sample.clock * sample.readout_delay)
    marker1[readout_ind:readout_ind + 10] = 1
    begin_zeros = len(wf1) % divisor
    # TODO: minimum waveform is 192 points implement that
    if begin_zeros != 0:
        wf1 = np.append(np.zeros(divisor - begin_zeros), wf1)
        wf2 = np.append(np.zeros(divisor - begin_zeros), wf2)
        marker1 = np.append(np.zeros(divisor - begin_zeros), marker1)
    qkit.flow.sleep()
    sample.awg.wfm_send2(wf1, wf2, marker1, marker1, chpair * 2 - 1, segment + 1)

