# load.py
# started by A. Stehli


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
import os.path
import time
import logging
import sys
from qkit.gui.notebook.Progress_Bar import Progress_Bar
import matplotlib.pyplot as plt
import gc


def load_sequence(sequences, times, sample = None, iq = None, awg = None, chpair = 1, reset = True, drive = 'c:', path = '\\waveforms', show_progress_bar = True):
    """
        set awg to sequence mode and push a number of waveforms into the sequencer
        
        Inputs:        
            sequences - List of pulse sequence objects, to be loaded into the awg
            times     - List of pulse sequence objects, to be loaded into the awg
            sample    - sample object
            iq        - Reference to iq mixer instrument. If None (default), the wfm will not be changed. Otherwise, the wfm will be converted via iq.convert()
            reset     - Reset AWG.
        
        for the 6GS/s AWG, the waveform length must be divisible by 64
        for the 1.2GS/s AWG, it must be divisible by 4
        
        chpair: if you use the 4ch Tabor AWG as a single 2ch instrument, you can chose to take the second channel pair here (this can be either 1 or 2).
    """
    if sample is None:
        print("No sample object given.")
    sequences = np.atleast_1d(sequences)
    if awg is None:
        awg = sample.awg
    if hasattr(sample, "clock"):
        clock = sample.clock
    else:
        logging.error("Sample object has no attribute clock.")
    # create new sequence
    if reset:
        if "Tektronix" in awg.get_type():
            awg.set_runmode('SEQ')
            awg.set_seq_length(0)   #clear sequence, necessary?
            awg.set_seq_length(len(sequences))
        elif "Tabor" in awg.get_type():
            awg.set('p%i_runmode'%chpair,'SEQ')
            awg.define_sequence(chpair*2-1, len(sequences)) #AS: Maybe it is worth creating a real reset/preset function in the Tabor treiber?
        
        #amplitude settings of analog output
        awg.set_ch1_offset(0)
        awg.set_ch2_offset(0)
        awg.set_ch1_amplitude(2)
        awg.set_ch2_amplitude(2) #Why does this have to be a variable?

    #generate empty tuples for Tektronix
    wfm_fn = [None,None]
    wfm_pn = [None,None]
    if show_progress_bar: 
        p = Progress_Bar(len(sequences)*(2 if "Tektronix" in awg.get_type() else 1),'Load AWG')   #init progress bar
    
    #update all channels and times
    for i, seq in enumerate(sequences):   #run through all sequences
        wfm_samples = seq.get_waveform(clock)   #generate waveform
        
        #Ajust waveform lengths to be divisible by 16
        if "Tektronix" in awg.get_type():
            sample_length = int(np.ceil(len(wfm_samples)/16.))*16 #Fix markers also!
        elif "Tabor" in awg.get_type():
            sample_length = int(np.ceil(len(wfm_samples)/16.))*16
        else:
            raise ValueError("AWG type not known.")
        wfm_samples = np.append(wfm_samples, np.zeros(sample_length - len(wfm_samples)))
        
        if iq is not None: 
            wfm_samples = iq.convert(wfm_samples)
        else: #homodyne
            wfm_samples = [wfm_samples, np.zeros_like(wfm_samples, dtype=np.int8)]
        
        #Manage Markers:
        if markerseq1 is not None:
            marker1 = markerseq1.get_waveform(clock)
            if len(marker1) is not len(wfm_samples[0]):
                marker1 = np.append(marker1, np.zeros(len(wfm_samples[0]) - len(marker1), dtype = np.int8))
        elif markerseq1 is None:
            marker1 = np.zeros_like(wfm_samples, dtype=np.int8)[0]
        # Set last 10 elements in marker1 to 1 if awg is Tabor -> Used for triggering readout & DAC card
        if "Tabor" in awg.get_type():
            marker1[-10:] = 1
            
        if markerseq2 is not None:
            marker2 = markerseq2.get_waveform(clock)
            if len(marker2) is not len(wfm_samples[1]):
                marker2 = np.append(marker2, np.zeros(len(wfm_samples[1]) - len(marker2), dtype = np.int8))
        elif markerseq2 is None:
            marker2 = np.zeros_like(wfm_samples, dtype=np.int8)[1]

        
        for chan in [0,1]:            
            if "Tektronix" in awg.get_type():
                wfm_fn[chan] = 'ch%d_t%05d'%(chan + 1, i) # filename is kept until changed
                if len(wfm_samples) == 1 and chan == 1:
                    wfm_pn[chan] = '%s%s\\%s'%(drive, path, np.zeros_like(wfm_fn[0]))   #create empty array
                else:
                    wfm_pn[chan] = '%s%s\\%s'%(drive, path, wfm_fn[chan])
                awg.wfm_send(wfm_samples[chan], marker1, marker2, wfm_pn[chan], clock)
                
                awg.wfm_import(wfm_fn[chan], wfm_pn[chan], 'WFM')
                
                # assign waveform to channel/time slot
                awg.wfm_assign(chan+1, i + 1, wfm_fn[chan])
                
                if loop:
                    awg.set_seq_loop(i + 1, np.infty)
            elif "Tabor" in awg.get_type():
                if chan == 1:   #write out both together
                    awg.wfm_send2(wfm_samples[0], wfm_samples[1], marker1, marker2, chpair*2 - 1, i + 1)
                else: continue
            else:
                raise ValueError("AWG type not known.")
            if show_progress_bar: p.iterate()

        gc.collect()

    if reset and "Tektronix" in awg.get_type():
        # enable channels
        awg.set_ch1_status(True)
        awg.set_ch2_status(True)
        awg.set_seq_goto(len(sequences), 1)
        awg.run()
        awg.wait(10, False)
    elif reset and "Tabor" in awg.get_type():
        # enable channels
        #awg.preset()
        awg.set_ch1_status(True)
        awg.set_ch2_status(True)
    return np.all([awg.get('ch%i_status'%i) for i in [1,2]])
