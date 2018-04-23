# initialize.py
# collected and adapted by Andre Schneider (S1)


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

import matplotlib.pyplot as plt
import logging
import numpy as np
from qkit.measure.timedomain import gate_func
import qkit.measure.timedomain.awg.load_awg as load_awg
import qkit.measure.timedomain.awg.generate_waveform as gwf

def initialize(sample):
    '''
    doc-string tbd

    you will need a valid sample file with the following parameters set:
     
    '''
    
    #Check if we have all necessary parameters in our sample object:
    params = ['T_rep',# repetition rate (s)
        'exc_T',#   2e-05
        'readout_tone_length',#   4e-07

        'clock',#   1200000000.0 samples per second for awg
        'readout_clock',#   1200000000.0
        'spec_samplerate',#   1250000000.0

        'f01',#   5469700000.0
        'fr',#   9e9
        'iq_frequency',#   80000000.0
        'readout_iq_frequency',#   30000000.0

        'mw_power',         # power for the qubit microwave source

        'acqu_window',     # [start, end] (samples)
        'overlap',          # time in seconds where the manipulation pulse should lap into the readout pulse

        'awg',              # Instrument for qubit manipulation
        'qubit_mw_src',     # Instrument 'mw_src_manip'
        'readout_awg',      # Instrument 'tekawg'
        'readout_mw_src',   # Instrument 'mw_src_readout'   
        'mspec'             # Instrument             
    ]

    breakpoint = False
    for p in params:
        if p not in sample.__dict__:
            logging.error("Please specify '"+p+"' in your sample object.")
            breakpoint = True
    if breakpoint: raise ValueError("Not all vallues in your sample file are present. I can not continue. Sorry.")

    #Init the spectrum card
    sample.mspec.spec_stop()
    sample.mspec.set_segments(1)
    sample.mspec.set_blocks(1)
    sample.mspec.set_window(0,512)

    sample.readout_mw_src.enable_high_power = True #CHECK
    sample.qubit_mw_src.enable_high_power   = True #CHECK
    sample.readout_mw_src.set_parameter_bounds('power',-20,30) #for the anritzu sources #CHECK
    sample.qubit_mw_src.set_parameter_bounds('power',-20,30)

    sample.update_instruments() #this could be seen as obsolete once this script is ready #CHECK

    sample.readout_mw_src.set_power(15)
    sample.qubit_mw_src.set_power(0)
    sample.readout_mw_src.set_status(True)
    sample.qubit_mw_src.set_status(True)

    #qubit awg presets
    if True: #Tabor AWG in 4ch mode
        # Tabor is self triggered
        # SYNC output of Tabor makes sync pulse to Tek
        # TekMarker makes sync pulse for spec card #CHECK
        sample.awg.reset()
        #self.set_p1_runmode('SEQ')
        #self.set_p2_runmode('USER')
        for i in range(1,5):
            sample.awg.set('ch%i_amplitude'%i,2)
            sample.awg.set('ch%i_output'%i,True)
            sample.awg.set('ch%i_marker_output'%i,True)
            sample.awg.set('ch%i_marker_high'%i,1)
        sample.awg.get_all()
        sample.awg.set_common_clock(True)
        sample.awg.set_clock(sample.clock)
        sample.readout_awg.set_clock(sample.readout_clock)
        load_awg.update_sequence([100e-9],gwf.square,sample,show_progress_bar=False)

        sample.awg.set_p1_trigger_time(sample.T_rep)
        sample.awg.set_p1_sync_output(True)

        for i in range(1,3):
            sample.awg.set('p%i_runmode'%i,'USER')   
            sample.awg.set('p%i_trigger_mode'%i,'TRIG')
            sample.awg.set('p%i_trigger_source'%i,'TIM')
            sample.awg.set('p%i_sequence_mode'%i,'STEP')
            sample.awg.set('p%i_trigger_delay'%i,0)
            sample.awg.set('p%i_runmode'%i,'SEQ')   
        
    #put something into the manipulation awg
    
    sample.readout.set_tone_amp(1)
    sample.readout.set_LO(np.mean(sample.fr)-sample.readout_iq_frequency)   #set LO lower and use mixer as a up-converter. For multiplexing set LO to centerfreq - IQ freq
    sample.readout.set_tone_freq(np.atleast_1d(sample.fr))   #probe tone frequency
    sample.readout.set_tone_pha([ sample.__dict__.get('readout_pha',0) ])   #phase shift (usually not necessary)      -0.1 is nice 1.3
    sample.readout.set_tone_relamp([ sample.__dict__.get('readout_relamp',1) ])   #relative amplitude of tone

    update_timings(sample)

    sample.mspec.set_gate_func(gate_func.Gate_Func(awg = sample.awg,sample=sample).gate_fcn)
    sample.mspec.spec_stop()   #stop card before modifying a setting
    sample.mspec.set_samplerate(sample.spec_samplerate)   
    sample.spec_samplerate = sample.mspec.get_samplerate() #We want to have the actual samplerate in the sample object

    set_spec_input_level(sample,sample.__dict__.get('spec_input_level',250))
    #record_single_trace(sample)


def update_timings(sample, zero_dac_delay = False):
    sample.awg.set('p1_trigger_time',sample.T_rep)
    sample.awg.set('trigger_time',sample.T_rep)
    sample.mspec.set_trigger_rate(1/float(sample.T_rep))
    sample.readout.set_dac_duration(sample.readout_tone_length) #length of the readout tone
    sample.readout.set_dac_clock(sample.clock)
    if zero_dac_delay: sample.readout.set_dac_delay(sample.exc_T*0.9)
    else: sample.readout.set_dac_delay(-1)
    sample.readout.update()

def set_spec_input_level(sample,level):
    '''
    level can be one of 200,500,1000,2500
    '''
    sample.mspec.spec_stop() 
    sample.mspec.set_input_amp(level)

def record_single_trace(sample):
    #record single probe tone signal and plot
    sample.qubit_mw_src.set_status(0)
    sample.mspec.set_window(0,1024)
    sample.mspec.set_averages(1)
    sample.mspec.start_with_trigger()
    plt.figure(figsize=(15,5))
    plt.plot(sample.mspec.acquire())
    plt.xticks(np.arange(0,sample.mspec.get_samples(),32))
    plt.xlim((0,sample.mspec.get_samples()))
    plt.grid()
    plt.xlabel('samples (%.0fMHz samplerate: 1sample = %.3gns)'%(sample.mspec.get_samplerate()/1e6,1./sample.mspec.get_samplerate()*1e9))
    plt.ylabel('amplitude')
    plt.twiny()
    plt.xlabel('seconds')
    plt.xticks(np.arange(0,float(sample.mspec.get_samples())/sample.mspec.get_samplerate()*1e9,100))
    plt.xlim(0,float(sample.mspec.get_samples())/sample.mspec.get_samplerate()*1e9)
    plt.ylim(-128,127)
    samples=[sample.mspec.acquire() for i in range(5)]
    clips=np.size(np.where(np.array(samples).flatten()==127))+np.size(np.where(np.array(samples).flatten()==-128))
    if clips > 50:
         raise ValueError("Clipping detected, please reduce amplifier voltage (%r Clips)" %clips)
    elif clips > 0:
        print "In 5 measurements, only %i points had the maximum amplitude. This sounds good, go on."%clips
    elif np.max(samples)<15:
        raise ValueError("No signal detected. Check your wiring!")
    elif np.max(np.abs(samples)) < 64:
        print "The amplitude never reached half of the maximum of the card. Think about adding an amplifier and check that you are using the smallest spec_input_level."
    else:
        print "The amplitude seems reasonable. Check the image nevertheless."
    sample.mspec.set_window(*sample.acqu_window)
    
def record_averaged_trace(sample):
    #record average signal and plot
    sample.mspec.spec_stop()
    sample.mspec.set_spec_trigger_delay(0)
    sample.mspec.set_samples(1024)
    sample.mspec.set_averages(1e3)
    sample.mspec.set_segments(1)
    sample.mspec.start_with_trigger()
    plt.figure(figsize=(18,7))
    plt.plot(sample.mspec.acquire())
    plt.xlim((0,sample.mspec.get_samples()))
    plt.grid()
    plt.xlabel('samples (%.0fMHz samplerate: 1sample = %.3gns)'%(sample.mspec.get_samplerate()/1e6,1./sample.mspec.get_samplerate()*1e9))
    if sample.mspec.get_samples() > 512:
        plt.xticks(np.arange(0,sample.mspec.get_samples(),32))
    else:
        plt.xticks(np.arange(0,sample.mspec.get_samples(),16))
    plt.twiny()
    plt.xlabel('seconds')
    plt.xticks(np.arange(0,float(sample.mspec.get_samples())/sample.mspec.get_samplerate()*1e9,100))
    plt.xlim(0,float(sample.mspec.get_samples())/sample.mspec.get_samplerate()*1e9)
    plt.ylabel('amplitude')
    
def align_windows(sample, samples=768):
    #record single probe tone signal and plot
    sample.mspec.set_averages(1e3)
    sample.mspec.set_spec_trigger_delay(0)
    sample.mspec.set_samples(samples)
    #spec.stop()
    #spec.set_post_trigger(256)
    plt.figure(figsize=(18,7))
    sample.qubit_mw_src.set_status(1)
    #qt.msleep(1)
    plt.plot(sample.mspec.acquire())
    sample.qubit_mw_src.set_status(0)
    #qt.msleep(1)
    plt.plot(sample.mspec.acquire(),'--k')
    plt.xticks(np.arange(0,sample.mspec.get_samples(),16))
    #plt.xticks(np.arange(0,sample.mspec.get_samples(),20))
    plt.xlim((0,sample.mspec.get_samples()))
    plt.grid()
    plt.xlabel('samples (%.0fMHz samplerate: 1sample = %.3gns)'%(sample.mspec.get_samplerate()/1e6,1./sample.mspec.get_samplerate()*1e9))
    plt.ylabel('amplitude')
    plt.twiny()
    plt.xlabel('nano seconds')
    plt.xticks(np.arange(0,float(sample.mspec.get_samples())/sample.mspec.get_samplerate()*1e9,100))
    plt.xlim(0,float(sample.mspec.get_samples())/sample.mspec.get_samplerate()*1e9)
    plt.grid(axis='x',c='r')
    
def check_sidebands(sample):
    rec = sample.readout.spectrum()
    plt.figure(figsize=(20,10))
    plt.plot(rec[0],rec[1],'--o')
    ylim = plt.ylim()
    plt.plot([sample.fr,sample.fr],[0,np.max(rec[1])*1.5],'g')
    plt.plot([sample.readout.get_LO(),sample.readout.get_LO()],[0,np.max(rec[1])*1.5],'r')
    plt.plot([0,10e9],[sample.readout.readout()[0][0]]*2,'g')
    plt.ylim(ylim)
    plt.xlim([sample.readout.get_LO()-sample.readout_iq_frequency*1.5,sample.readout.get_LO()+sample.readout_iq_frequency*1.5])
    plt.grid()
