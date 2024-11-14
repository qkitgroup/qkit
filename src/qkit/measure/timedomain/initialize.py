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
from qkit.measure.timedomain import sequence_library as sl
from qkit.measure.timedomain import VirtualAWG as virtual_awg
import ipywidgets as widgets

class InitializeTimeDomain(object):
    def __init__(self,sample):
        self._sample = sample
        
        self._vawg = virtual_awg.VirtualAWG(self._sample)
        
    params = { #typical values are given in (brackets)
            'T_rep':                " repetition rate [s] (200e-6)",
            'exc_T':                " maximum window for manipulation [s]  (20e-6)",
            'readout_tone_length':  " length of readout tone [s]  (400e-09)",

            'clock':                " samplerate for manipulation awg [S/s] (1.2e9)",
            'readout_clock':        " samplerate for readout dac [S/s] (1.2e9)",
            'spec_samplerate':      " samplerate for readout adc [S/s] (1.25e9)",

            'f01':                  " qubit transition frequency [Hz] (5.469e9)",
            'fr':                   " resonator readout frequency [Hz] (9e9)",
            'iq_frequency':         " IQ frequency for manipulation [Hz] (80e6)",

            'mw_power':             " power for the qubit microwave source",
            
            'awg':                  " Instrument: qubit manipulation awg",
            'qubit_mw_src':         " Instrument: qubit manipulation microwave source",
            'readout_awg':          " Instrument: readout awg",
            'readout_mw_src':       " Instrument: readout microwave source",
            'mspec':                " Instrument virtual_measure_spec"
    }
    optional_params = {
            'readout_iq_frequency': [" IQ frequency for readout [Hz]", 30e6],
            'acqu_window':          [" position of the adc recording window as array [start, end]. No longer needed to be divisible by 32. (samples)", [96, 545]],
            'overlap':              [" Overlap between manipulation window and readout pulse.", 0],
            'readout_delay':        [" Time offset of the readout pulse to adjust the timing of the devices", 0],
            'readout_pha':          [" Phase of the readout tone", 0],
            'readout_relamp':       [" relative amplitude of the different readout tones" , 1],
            'spec_input_level':     [" Input range in mV of the spectrum adc card. Restricted to card-dependant values", 250]
    }

    def initialize(self):
        '''
        doc-string tbd

        you will need a valid sample file with the following parameters set:
         
        '''
        
        # Check if we have all necessary parameters in our sample object:
        breakpoint = False
        for p in self.params:
            if p not in self._sample.__dict__:
                logging.error("Please specify '"+p+"' in your sample object:"+self.params[p])
                breakpoint = True
        if breakpoint: raise ValueError("Not all vallues in your sample file are present. I can not continue. Sorry.")

        # If some parameters are not given, that have a good default, set them in the sample object, so that the user knows them.
        for p,v in self.optional_params.iteritems():
            if p not in self._sample.__dict__:
                self._sample.__dict__[p] = v[1]
        #Init the spectrum card
        self._sample.mspec.spec_stop()
        self._sample.mspec.set_segments(1)
        self._sample.mspec.set_blocks(1)
        self._sample.mspec.set_window(0,512)

        if self._sample.readout_mw_src.has_parameter('high_power'):
            self._sample.readout_mw_src.set_high_power(True)
        
        self.update_qubit_mw_src()
        
        self._sample.readout_mw_src.set_power(15)
        self._sample.qubit_mw_src.set_power(0)
        self._sample.readout_mw_src.set_status(True)
        self._sample.qubit_mw_src.set_status(True)

        #qubit awg presets
        if True: #Tabor AWG in 4ch mode
            # Tabor is self triggered
            # SYNC output of Tabor makes sync pulse to Tek
            # TekMarker makes sync pulse for spec card #CHECK
            self._sample.awg.reset()
            #self.set_p1_runmode('SEQ')
            #self.set_p2_runmode('USER')
            for i in range(1,5):
                self._sample.awg.set('ch%i_amplitude'%i,2)
                self._sample.awg.set('ch%i_output'%i,True)
                self._sample.awg.set('ch%i_marker_output'%i,True)
                self._sample.awg.set('ch%i_marker_high'%i,1)
            self._sample.awg.get_all()
            self._sample.awg.set_common_clock(True)
            self._sample.awg.set_clock(self._sample.clock)
            self._sample.readout_awg.set_clock(self._sample.readout_clock)
            self._load_awg_square([100e-9])
            
            if self._sample.awg._numchannels == 4:
                self._sample.awg.set_p1_trigger_time(self._sample.T_rep)
                self._sample.awg.set_p1_sync_output(True)
            else:
                self._sample.awg.set_trigger_time(self._sample.T_rep)
                self._sample.awg.set_sync_output(True)
            if self._sample.T_rep < 1.5 * self._sample.exc_T:
                raise ValueError("Your repetition rate T_rep is too small for the chosen window exc_T.")
            
            if  "Tektronix" in self._sample.readout_awg.get_type() and self._sample.T_rep < 170e-6:
                raise ValueError("You are using the Tektronix AWG as readout. This has a bug and your repetition rate should be >= 200us.")

            for i in range(1,3):
                self._sample.awg.set('p%i_runmode'%i,'USER')   
                self._sample.awg.set('p%i_trigger_mode'%i,'TRIG')
                self._sample.awg.set('p%i_trigger_source'%i,'TIM')
                self._sample.awg.set('p%i_sequence_mode'%i,'STEP')
                self._sample.awg.set('p%i_trigger_delay'%i,0)
                self._sample.awg.set('p%i_runmode'%i,'SEQ')   
            
        #put something into the manipulation awg
        
        self._sample.readout.set_tone_amp(1)
        self._sample.readout.set_LO(np.mean(self._sample.fr)-self._sample.readout_iq_frequency)   #set LO lower and use mixer as a up-converter. For multiplexing set LO to centerfreq - IQ freq
        self._sample.readout.set_tone_freq(np.atleast_1d(self._sample.fr))   #probe tone frequency
        self._sample.readout.set_tone_pha(np.atleast_1d(self._sample.readout_pha))   #phase shift (usually not necessary)
        self._sample.readout.set_tone_relamp(np.atleast_1d(self._sample.readout_relamp))   #relative amplitude of tone

        self.update_timings()

        self._sample.mspec.set_gate_func(gate_func.Gate_Func(awg = self._sample.awg,sample=self._sample).gate_fcn)
        self._sample.mspec.spec_stop()   #stop card before modifying a setting
        self._sample.mspec.set_samplerate(self._sample.spec_samplerate)   
        self._sample.spec_samplerate = self._sample.mspec.get_samplerate() #We want to have the actual samplerate in the sample object

        self.set_spec_input_level(self._sample.spec_input_level)


    def update_timings(self, zero_dac_delay = False):
        self._sample.awg.set('p1_trigger_time',self._sample.T_rep)
        self._sample.awg.set('trigger_time',self._sample.T_rep)
        self._sample.mspec.set_trigger_rate(1/float(self._sample.T_rep))
        self._sample.readout.set_dac_duration(self._sample.readout_tone_length) #length of the readout tone
        self._sample.readout.set_dac_clock(self._sample.clock)
        self._sample.readout.set_dac_delay(0)
        self._sample.readout.update()

    def set_spec_input_level(self,level):
        '''
        possible levels depend on the card and are specified in mV.
        '''
        self._sample.mspec.spec_stop() 
        self._sample.mspec.set_input_amp(level)

    def record_single_trace(self):
        #record single probe tone signal and plot
        self._sample.qubit_mw_src.set_status(0)
        self._sample.mspec.set_window(0,1024)
        self._sample.mspec.set_averages(1)
        self._sample.mspec.set_segments(5)
        samples = self._sample.mspec.acquire()
        plt.figure(figsize=(15,5))
        plt.plot(samples[:,:,0])
        plt.xticks(np.arange(0,self._sample.mspec.get_samples(),32))
        plt.xlim((0,self._sample.mspec.get_samples()))
        plt.grid()
        plt.xlabel('samples (%.0fMHz samplerate: 1sample = %.3gns)'%(self._sample.mspec.get_samplerate()/1e6,1./self._sample.mspec.get_samplerate()*1e9))
        plt.ylabel('amplitude')
        plt.twiny()
        plt.xlabel('nanoseconds')
        plt.xticks(np.arange(0,float(self._sample.mspec.get_samples())/self._sample.mspec.get_samplerate()*1e9,100))
        plt.xlim(0,float(self._sample.mspec.get_samples())/self._sample.mspec.get_samplerate()*1e9)
        plt.ylim(-128,127)
        clips=np.size(np.where(np.array(samples).flatten()==127))+np.size(np.where(np.array(samples).flatten()==-128))
        if clips > 50:
            logging.error("Clipping detected, please reduce amplifier voltage (%r Clips)" %clips)
        elif clips > 0:
            print("In 5 measurements, only %i points had the maximum amplitude. This sounds good, go on."%clips)
        elif np.max(samples)<15:
            raise ValueError("No signal detected. Check your wiring!")
        elif np.max(np.abs(samples)) < 64:
            print("The amplitude never reached half of the maximum of the card. Think about adding an amplifier and check that you are using the smallest spec_input_level.")
        else:
            print("The amplitude seems reasonable. Check the image nevertheless.")
        self._sample.mspec.set_window(*self._sample.acqu_window)
        
    def record_averaged_trace(self):
        #record average signal and plot
        self._sample.mspec.spec_stop()
        self._sample.mspec.set_spec_trigger_delay(0)
        self._sample.mspec.set_samples(1024)
        self._sample.mspec.set_averages(1e4)
        self._sample.mspec.set_segments(1)
        plt.figure(figsize=(15,5))
        plt.plot(self._sample.mspec.acquire())
        plt.xlim((0,self._sample.mspec.get_samples()))
        plt.grid()
        plt.xlabel('samples (%.0fMHz samplerate: 1sample = %.3gns)'%(self._sample.mspec.get_samplerate()/1e6,1./self._sample.mspec.get_samplerate()*1e9))
        if self._sample.mspec.get_samples() > 512:
            plt.xticks(np.arange(0,self._sample.mspec.get_samples(),32))
        else:
            plt.xticks(np.arange(0,self._sample.mspec.get_samples(),16))
        plt.twiny()
        plt.xlabel('nanoseconds')
        plt.xticks(np.arange(0,float(self._sample.mspec.get_samples())/self._sample.mspec.get_samplerate()*1e9,100))
        plt.xlim(0,float(self._sample.mspec.get_samples())/self._sample.mspec.get_samplerate()*1e9)
        plt.ylabel('amplitude')
        self._sample.mspec.set_window(*self._sample.acqu_window)
        
    def align_pulses(self, samples=768):
        #record single probe tone signal and plot
        samples = int(samples/32)*16
        self._sample.mspec.spec_stop()
        self._sample.mspec.set_segments(2)
        self._sample.mspec.set_averages(1e4)
        self._sample.mspec.set_spec_trigger_delay(0)
        self._sample.mspec.set_samples(samples*2)
        self._sample.mspec._dacq.set_post_trigger(samples)
            
        self._sample.qubit_mw_src.set_frequency(self._sample.readout_mw_src.get_frequency())
        sr = self._sample.mspec.get_samplerate()/1e9
        pwr = self._sample.qubit_mw_src.get_power()
        self._sample.qubit_mw_src.set_power(5)
        self._load_awg_square([0,50e-9])
        self._sample.qubit_mw_src.set_status(1)
        msp = self._sample.mspec.acquire()
        self._sample.qubit_mw_src.set_status(0)
        plt.figure(figsize=(15,5))
        plt.plot(np.arange(-samples+32,samples+32),msp[:,:,1])
        plt.plot(np.arange(-samples+32,samples+32),msp[:,:,0],'--k')
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
        self._sample.qubit_mw_src.set_power(pwr)
        
        print("You can now change the self._sample.readout_delay parameter to align the two pulses. The readout pulse should start when the manipulation ends.")
        print("If you are satisfied just press <Enter> or tell me the new delay.")
        plt.show()
        inp = raw_input("readout_delay ({:g}s) = ".format(self._sample.readout_delay))
        if inp == '':
            return
        if np.abs(float(inp)) > 1e-3:
            raise ValueError("Your delay is more than a mili second. I guess you are wrong.")
        self._sample.readout_delay = float(inp)
        self.update_timings()
        self.align_pulses()
        
    def crop_recording_window(self):
        self._sample.mspec.spec_stop()
        self._sample.mspec.set_averages(1e4)
        self._sample.mspec.set_window(0,512)
        self._sample.mspec.set_segments(1)
        msp = self._sample.mspec.acquire()
        
        def pltfunc(start,end,done):
            if done:
                self._sample.acqu_window = [start,end]
                self._sample.mspec.set_window(start,end)
                self._sw.disabled = True
                self._ew.disabled = True
                self._dw.disabled = True
                self._dw.description = "acqu_window set to [{:d}:{:d}]".format(start,end)
            else:
                plt.figure(figsize=(15,5))
                plt.plot(msp)
                plt.axvspan(0,start,color='k',alpha=.2)
                plt.axvspan(end,len(msp),color='k',alpha=.2)
                plt.xlim(0,len(msp))
                plt.show()
        self._sw =  widgets.IntSlider(min=0,max=len(msp),step=1,value=self._sample.acqu_window[0],continuous_update=True)
        self._ew = widgets.IntSlider(min=0,max=len(msp),step=1,value=self._sample.acqu_window[1],continuous_update=True)
        self._dw = widgets.Checkbox(value=False,description="Done!",indent=True)
        self._wgt = widgets.interact(pltfunc,start=self._sw,end=self._ew,done=self._dw)
        self._sample.mspec.set_window(*self._sample.acqu_window)
        
    def check_sidebands(self):
        rec = self._sample.readout.spectrum()
        ro = self._sample.readout.readout()
        plt.figure(figsize=(15,5))
        plt.plot(rec[0],rec[1]/len(rec[1]),'--o')
        ylim = plt.ylim()
        plt.vlines(self._sample.readout.get_LO(),*ylim,color='r')
        for i,fr in enumerate(np.atleast_1d(self._sample.fr)):
            plt.plot([fr],ro[0][i],'+',ms=50,mew=3)
        plt.ylim(0,ylim[1])
        spread = np.ptp(np.append(np.atleast_1d(self._sample.fr),self._sample.readout.get_LO()))*1.2
        plt.xlim([self._sample.readout.get_LO()-spread,self._sample.readout.get_LO()+spread])
        plt.grid()

    def update_qubit_mw_src(self):
        self._sample.qubit_mw_src.set_power(self._sample.mw_power)
        self._sample.qubit_mw_src.set_frequency(self._sample.f01 - self._sample.iq_frequency)
        
    def _load_awg_square(self, times):
        self._vawg.set_sequence(sl.rabi(self._sample, iq_frequency=0), times)
        self._vawg.load(show_progress_bar=False)
