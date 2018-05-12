# initialize.py
# collected and adapted by Andre Schneider (S1) 2018/05


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
import ipywidgets as widgets

params = { #typical values are given in (brackets)
        'T_rep':                " repetition rate [s] (200e-6)",
        'exc_T':                " maximum window for manipulation [s]  (20e-6)",
        'readout_tone_length':  " length of readout tone [s]  (400e-09)",

        'clock':                " samplerate for manipulation awg [S/s] (1.2e9)",
        'readout_clock':        " samplerate for readout dac [S/s] (1.2e9)",
        'spec_samplerate':      " samplerate for readout adc [S/s] (1.25e9)",

        'f01':                  " qubit transition frequency [Hz] (5.469e9)",
        'fr':                   " resounator readout frequency [Hz] (9e9)",
        'iq_frequency':         " IQ frequency for manipulation [Hz] (80e6)",
        'readout_iq_frequency': " IQ frequency for readout [Hz] (30e6)",

        'mw_power':             " power for the qubit microwave source",

        'acqu_window':          " position of the adc recording window as arra [start, end]. No longer needed to be divisible by 32. (samples) [96,545]",
        'overlap':              " time in seconds where the manipulation pulse should lap into the readout pulse [s] (1e-6)",

        'awg':                  " Instrument: qubit manipulation awg",
        'qubit_mw_src':         " Instrument: qubit manipulation microwave source",
        'readout_awg':          " Instrument: readout awg",
        'readout_mw_src':       " Instrument: readout microwave source",
        'mspec':                " Instrument virtual_measure_spec"
}
optional_params = {
        'overlap':              [" Overlap between manipulation window and readout pulse.", 0],
        'readout_delay':        [" Time offset of the readout pulse to adjust the timing of the devices", 0],
        'readout_pha':          [" Phase of the readout tone", 0],
        'readout_relamp':       [" relative amplitude of the different readout tones" , 1],
        'spec_input_level':     [" Input range in mV of the spectrum adc card. Restricted to card-dependant values", 250]
}

def initialize(sample):
    '''
    doc-string tbd

    you will need a valid sample file with the following parameters set:
     
    '''
    
    # Check if we have all necessary parameters in our sample object:
    breakpoint = False
    for p in params:
        if p not in sample.__dict__:
            logging.error("Please specify '"+p+"' in your sample object:"+params[p])
            breakpoint = True
    if breakpoint: raise ValueError("Not all vallues in your sample file are present. I can not continue. Sorry.")

    # If some parameters are not given, that have a good default, set them in the sample object, so that the user knows them.
    for p,v in optional_params.iteritems():
        if p not in sample.__dict__:
            sample.__dict__[p] = v[1]
    #Init the spectrum card
    sample.mspec.spec_stop()
    sample.mspec.set_segments(1)
    sample.mspec.set_blocks(1)
    sample.mspec.set_window(0,512)

    if sample.readout_mw_src.has_parameter('high_power'):
        sample.readout_mw_src.set_high_power(True)
    
    update_qubit_mw_src(sample)
    
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
        
        if sample.T_rep < 1.5 * sample.exc_T:
            raise ValueError("Your repetition rate T_rep is too small for the chosen window exc_T.")
        
        if  "Tektronix" in sample.readout_awg.get_type() and sample.T_rep < 170e-6:
            raise ValueError("You are using the Tektronix AWG as readout. This has a bug and your repetition rate should be >= 200us.")

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
    sample.readout.set_tone_pha(np.atleast_1d(sample.readout_pha))   #phase shift (usually not necessary)
    sample.readout.set_tone_relamp(np.atleast_1d(sample.readout_relamp))   #relative amplitude of tone

    update_timings(sample)

    sample.mspec.set_gate_func(gate_func.Gate_Func(awg = sample.awg,sample=sample).gate_fcn)
    sample.mspec.spec_stop()   #stop card before modifying a setting
    sample.mspec.set_samplerate(sample.spec_samplerate)   
    sample.spec_samplerate = sample.mspec.get_samplerate() #We want to have the actual samplerate in the sample object

    set_spec_input_level(sample,sample.spec_input_level)
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
    possible levels depend on the card and are specified in mV.
    '''
    sample.mspec.spec_stop() 
    sample.mspec.set_input_amp(level)

def record_single_trace(sample):
    #record single probe tone signal and plot
    sample.qubit_mw_src.set_status(0)
    sample.mspec.set_window(0,1024)
    sample.mspec.set_averages(1)
    sample.mspec.set_segments(5)
    samples = sample.mspec.acquire()
    plt.figure(figsize=(15,5))
    plt.plot(samples[:,:,0])
    plt.xticks(np.arange(0,sample.mspec.get_samples(),32))
    plt.xlim((0,sample.mspec.get_samples()))
    plt.grid()
    plt.xlabel('samples (%.0fMHz samplerate: 1sample = %.3gns)'%(sample.mspec.get_samplerate()/1e6,1./sample.mspec.get_samplerate()*1e9))
    plt.ylabel('amplitude')
    plt.twiny()
    plt.xlabel('nanoseconds')
    plt.xticks(np.arange(0,float(sample.mspec.get_samples())/sample.mspec.get_samplerate()*1e9,100))
    plt.xlim(0,float(sample.mspec.get_samples())/sample.mspec.get_samplerate()*1e9)
    plt.ylim(-128,127)
    clips=np.size(np.where(np.array(samples).flatten()==127))+np.size(np.where(np.array(samples).flatten()==-128))
    if clips > 50:
        logging.error("Clipping detected, please reduce amplifier voltage (%r Clips)" %clips)
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
    sample.mspec.set_averages(1e4)
    sample.mspec.set_segments(1)
    plt.figure(figsize=(15,5))
    plt.plot(sample.mspec.acquire())
    plt.xlim((0,sample.mspec.get_samples()))
    plt.grid()
    plt.xlabel('samples (%.0fMHz samplerate: 1sample = %.3gns)'%(sample.mspec.get_samplerate()/1e6,1./sample.mspec.get_samplerate()*1e9))
    if sample.mspec.get_samples() > 512:
        plt.xticks(np.arange(0,sample.mspec.get_samples(),32))
    else:
        plt.xticks(np.arange(0,sample.mspec.get_samples(),16))
    plt.twiny()
    plt.xlabel('nanoseconds')
    plt.xticks(np.arange(0,float(sample.mspec.get_samples())/sample.mspec.get_samplerate()*1e9,100))
    plt.xlim(0,float(sample.mspec.get_samples())/sample.mspec.get_samplerate()*1e9)
    plt.ylabel('amplitude')
    sample.mspec.set_window(*sample.acqu_window)
    
def align_windows(sample, samples=768):
    #record single probe tone signal and plot
    samples = int(samples/32)*16
    sample.mspec.spec_stop()
    sample.mspec.set_averages(1e4)
    sample.mspec.set_spec_trigger_delay(0)
    sample.mspec.set_samples(samples*2)
    sample.mspec._dacq.set_post_trigger(samples)
        
    sample.qubit_mw_src.set_frequency(sample.readout_mw_src.get_frequency())
    sr = sample.mspec.get_samplerate()/1e9
    pwr = sample.qubit_mw_src.get_power()
    sample.qubit_mw_src.set_power(5)
    load_awg.update_sequence([50e-9], gwf.square, sample, show_progress_bar=False) # 50ns = 25 Samples, 20 MHz
    sample.qubit_mw_src.set_status(1)
    plt.figure(figsize=(15,5))
    plt.plot(np.arange(-samples+32,samples+32),sample.mspec.acquire())
    sample.qubit_mw_src.set_status(0)
    plt.plot(np.arange(-samples+32,samples+32),sample.mspec.acquire(),'--k')
    plt.xlim((-samples+32,samples+32))
    plt.grid()
    plt.xlabel('samples (%.0fMHz samplerate: 1 sample = %.3gns)'%(sr*1e3,1./sr))
    plt.ylabel('amplitude')
    plt.twiny()
    plt.xlabel('nano seconds')
    duration = float(samples)/sr
    plt.xticks(np.arange(-round(duration,-2),round(duration,-2),100))
    plt.xlim(-duration+32/sr,+duration+32/sr)
    plt.grid(axis='x')
    sample.qubit_mw_src.set_power(pwr)
    
def crop_recording_window(sample):
    sample.mspec.spec_stop()
    sample.mspec.set_averages(1e4)
    sample.mspec.set_window(0,512)
    msp = sample.mspec.acquire()
    
    def pltfunc(start,end,done):
        if done:
            sample.acqu_window = [start,end]
            sample.mspec.set_window(start,end)
            sw.disabled = True
            ew.disabled = True
            dw.disabled = True
            dw.description = "acqu_window set to [{:d}:{:d}]".format(start,end)
        else:
            plt.figure(figsize=(15,5))
            plt.plot(msp)
            plt.axvspan(0,start,color='k',alpha=.2)
            plt.axvspan(end,len(msp),color='k',alpha=.2)
            plt.xlim(0,len(msp))
            plt.show()
    sw =  widgets.IntSlider(min=0,max=len(msp),step=1,value=sample.acqu_window[0],continuous_update=True)
    ew = widgets.IntSlider(min=0,max=len(msp),step=1,value=sample.acqu_window[1],continuous_update=True)
    dw = widgets.Checkbox(value=False,description="Done!",indent=True)
    wgt = widgets.interact(pltfunc,start=sw,end=ew,done=dw)
    sample.mspec.set_window(*sample.acqu_window)
    
def check_sidebands(sample):
    rec = sample.readout.spectrum()
    ro = sample.readout.readout()
    plt.figure(figsize=(15,5))
    plt.plot(rec[0],rec[1],'--o')
    ylim = plt.ylim()
    plt.vlines(sample.readout.get_LO(),*ylim,color='r')
    for i,fr in enumerate(np.atleast_1d(sample.fr)):
        plt.plot([fr],ro[0][i],'+',ms=50,mew=3)
    plt.ylim(0,ylim[1])
    spread = np.ptp(np.append(np.atleast_1d(sample.fr),sample.readout.get_LO()))*1.2
    plt.xlim([sample.readout.get_LO()-spread,sample.readout.get_LO()+spread])
    plt.grid()

def update_qubit_mw_src(sample):
    sample.qubit_mw_src.set_power(sample.mw_power)
    sample.qubit_mw_src.set_frequency(sample.f01 - sample.iq_frequency)