'''
Joao and Sergey, Feb 2021, Glasgow

This module is used to calibrate IQ mixers. It determines the optimal relative phase and relative amplitude 
to achieve the desired single sideband and also determines the optimal I and Q dc offsets to suppress the
LO leakage.

The module was created with the use of Tabor WX2184C AWG and MS2830A Anritsu spectrum analyzer.

'''
import numpy as np
import time 
import logging
import matplotlib.pyplot as plt

class IQ_mixer_optimization():

    def __init__(self, sample, control=True, sideband='up', pulse_type='rect', pulse_length=1e-6, delay_length=5e-6):
        '''
            Initialization of class
            Input:
                1. sample class object (Its attributes are required for the operation, e.g. LO, IF, awg object, spectrum analizer
            object and so on.)
                2. True - for the calibration of a mixer connected to the pair 1 (1&2 channels) of the AWG, and False - for the
            calibration of a mixer connected to the pair 2 (3&4 channels) of the AWG.
                3. "up" - for creation of upper sideband on the mixer (lower sideband rejection), and "low" - for creation of lower sideband on the mixer(upper sideband rejection).
                4. "rect" - for rectangular envelope of IQ pulses, and "gauss" - for gaussian envelope of IQ pulses.
                5. length of the pulse
                6. delay between the puulses as they are output from the AWG.
        '''
        self.sample = sample
        self.awg = sample.awg
        self.spec = sample.spectrum_analyzer

        #Optimal values
        self.opt_rel_pha = 0
        self.opt_rel_amp = 1
        self.opt_I_offset = 0
        self.opt_Q_offset = 0

        #select AWG channels and frequencies based on control or readout setup
        #Control == channels 1&2, Readout == channels 3&4
        if control:
            self.IF = sample.iq_frequency 
            self.RF = sample.f01
            self.awg_channel = 1
            self.LO_source = sample.qubit_mw_src
            self.LO_source.set_power(sample.mw_power)
        else:
            self.IF = sample.readout_iq_frequency
            self.RF =  sample.fr
            self.awg_channel = 3
            self.LO_source = sample.readout_mw_src
            self.LO_source.set_power(sample.readout_mw_power)

        #selects which sideband should be present after optimization
        if sideband == 'up':
            self.LO = self.RF - self.IF
            self.uRF = self.LO - self.IF #unwanted sideband
        elif sideband == 'low':
            self.LO = self.RF + self.IF
            self.uRF = self.LO + self.IF
        else:
            raise ValueError("Wrong sideband type. Either 'up' or 'low'")

        #Probe pulse to use when optimizing
        self.pulse_type = pulse_type
        self.pulse_length = pulse_length
        self.delay_length = delay_length

        #Settings for AWG and LO
        self.LO_source.set_frequency(self.LO)
        self.awg.set_common_clock(True)
        self.awg.set_clock(self.sample.clock)
        self.awg.set_p1_runmode('USER')  
        self.awg.set_p1_trigger_mode('CONT')
        #self.awg.set_p1_trigger_time(self.delay_length)

        #Clear AWG memory and load waveforms to be used when optimizing
        self.awg.clear_waveforms()
        
        self.pha_array = np.linspace(0,360,361)
        self.pulse_load(self.pha_array)


    def awg_run(self, off=False, set_par=True):
        '''
            Sets outputs of AWG channels to be on/off
            Input:
                off (optional): Turns outputs off if True
                set_par (optional): sets rel. amplitude and offsets to the optimized values when set to True
        '''
        io= 0 if off else 1
        if self.awg_channel == 1 or self.awg_channel == 2:
            self.awg.set_ch1_output(io)
            self.awg.set_ch2_output(io)
            self.awg.set_ch1_amplitude(1)
            if(set_par):
                self.awg.set_ch2_amplitude(self.opt_rel_amp)
                self.awg.set_ch1_offset(self.opt_I_offset)
                self.awg.set_ch2_offset(self.opt_Q_offset)
        elif self.awg_channel == 3 or self.awg_channel == 4:
            self.awg.set_ch3_output(io)
            self.awg.set_ch4_output(io)
            self.awg.set_ch3_amplitude(1)
            if(set_par):
                self.awg.set_ch4_amplitude(self.opt_rel_amp)
                self.awg.set_ch3_offset(self.opt_I_offset)
                self.awg.set_ch4_offset(self.opt_Q_offset)
        else:
            raise ValueError('Given awg channel is wrong! Please choose from {1,3} options.')


    def spec_config(self, centre_freq, span= 5e6, resBW = 3e3, videoBW = 3e3):
        '''
            Configurations of spectrum analyzer
            Input:
                centre_freq: center frequency
                resBW (optional): resolution bandwidth of spectrum analyzer (controls noise floor level)
                videoBW (optional): video bandwidth of spectrum analyzer (similar to IFBW on VNAs)

        '''
        self.spec.set_centerfreq(centre_freq)
        self.spec.set_freqspan(span)
        self.spec.set_resolutionBW(resBW)
        self.spec.set_videoBW(videoBW)

    def pulse_load(self, rel_pha= [], seg_off = 0):
        '''
            Load all waveforms to be used when optimizing sidebands
            Phase resolution of AWG is 1 degree -> 360 waveforms are loaded at initialization
            Input:
                rel_pha: array with phase points which will create waveforms to be loaded to AWG
                seg_off (optional): segment offset to select with segment the waveform should be loaded to

        '''
        n_samples = int((self.pulse_length+self.delay_length)*self.sample.clock) + 1
        n_samples = n_samples + (16 - n_samples%16)

        waf_I = np.zeros(n_samples)
        waf_Q = np.zeros(n_samples)
        #waf_time = np.linspace(0,n_samples/self.sample.clock,n_samples)

        for ll, phase in enumerate(rel_pha):
            if self.pulse_type == 'rect':
                for ii in range(int(self.pulse_length*self.sample.clock)):
                    waf_I[ii] = np.sin(2*np.pi*self.IF*ii/self.sample.clock + 0)
                    waf_Q[ii] = np.cos(2*np.pi*self.IF*ii/self.sample.clock + phase*np.pi/180)
            elif self.pulse_type == 'gauss':
                t0 = self.pulse_length/2
                sigma = self.pulse_length/6
                for ii in range(int(self.pulse_length*self.sample.clock)):
                    waf_I[ii] = np.exp(-(ii/self.sample.clock-t0)**2/2/sigma**2)*np.sin(2*np.pi*self.IF*ii/self.sample.clock + 0)
                    waf_Q[ii] = np.exp(-(ii/self.sample.clock-t0)**2/2/sigma**2)*np.cos(2*np.pi*self.IF*ii/self.sample.clock + phase*np.pi/180)
            else: 
                #TODO: dc waveform
                pass
            
            self.awg.wfm_send2(waf_I, waf_Q, channel = self.awg_channel, seg = seg_off + ll+1)
            time.sleep(0.1)
            print("\rLoading the waveforms to AWG: "+str(ll+1)+"/"+str(len(rel_pha)), end="", flush=True)

        print("\nLoading is done.")
        #return waf_I, waf_Q, waf_time

    def opt_sideband(self, max_iter = 10):
        '''
            Main function to optimize sidebands
            Input:
                max_ter (optional): maximum number of iterations
            Output:
                rel_pha, rel_amp : optimal values for relative phase and amplitude (also stored in self)
        '''
        self.spec_config(self.uRF)
        self.spec.sweep()
        noise_level = np.mean(self.spec.get_trace()) 
        noise_std = np.std(self.spec.get_trace())
        #print(noise_level, noise_std)

        #Amplitude and phase steps
        amp_step_list = [0.05,0.02,0.01,0.005,0.002,0.001]
        pha_step_list = np.array([20,10,5,2,1])
        pha_step = pha_step_list[0]
        
        #Starting arrays to check
        amp_array = np.linspace(0.05,2,int(1.95/amp_step_list[0])+1)
        pha_array = np.arange(0,361,pha_step_list[0])
                
        self.LO_source.set_status(1)
        self.awg_run()
        
        #Main loop
        count = 0
        while count <= max_iter:

            # phase optimization iteration
            level_array_pha = []
            for ind, pha in enumerate(pha_array):
                self.awg.write(':INST{};:TRAC:SEL{}'.format(self.awg_channel, np.where(self.pha_array==pha)[0][0]+1))
                self.spec.sweep()
                level_array_pha.append(np.max(self.spec.get_trace()))
                print("\r{}: Optimizing relative phase parameter... ".format(count+1)+str(ind+1)+'/'+str(len(pha_array)), end="", flush=True)
                #logging.info(__name__+" :\rOptimizing relative phase parameter... "+str(ind+1)+'/'+str(len(pha_array)), end="", flush=True)

            level = np.min(level_array_pha)

            pha_span = len(pha_array)*pha_step

            if count < len(pha_step_list)-1:
                pha_step = pha_step_list[count+1]
            else:
                pha_step = pha_step_list[-1]

            self.opt_rel_pha = pha_array[level_array_pha.index(level)]

            if self.opt_rel_pha-round(pha_span/4,0) < 0:
                pha_array = np.concatenate((np.arange(0,self.opt_rel_pha+round(pha_span/4,0),pha_step),\
                    np.arange(360 + self.opt_rel_pha-round(pha_span/4,0),360,pha_step)))
            elif self.opt_rel_pha+round(pha_span/4,0) > 360:
                pha_array = np.concatenate((np.arange(self.opt_rel_pha-round(pha_span/4,0),360,pha_step),\
                   np.arange(0,self.opt_rel_pha+round(pha_span/4,0)-360,pha_step)))
            else:
                pha_array = np.arange(self.opt_rel_pha-round(pha_span/4,0),\
                    self.opt_rel_pha+round(pha_span/4,0),pha_step)

            pha_array = np.sort(pha_array)

            if abs(level - noise_level) < 2*noise_std: break
            
            # amplitude optimization iteration
            level_array_amp = []
            self.awg.write(':INST{};:TRAC:SEL{}'.format(self.awg_channel, np.where(self.pha_array==self.opt_rel_pha)[0][0] + 1))
            for i, amp in enumerate(amp_array):
                if self.awg_channel == 1 or self.awg_channel == 2: self.awg.set_ch2_amplitude(amp)
                elif self.awg_channel == 3 or self.awg_channel == 4: self.awg.set_ch4_amplitude(amp)
                else: raise ValueError('Unknown channel number!')
                self.spec.sweep()
                level_array_amp.append(np.max(self.spec.get_trace()))
                print("\r{}: Optimizing relative amplitude parameter... ".format(count+1)+str(i+1)+'/'+str(len(amp_array)), end="", flush=True)
                #print(i,level_array_amp[-1], amp)

            level = np.min(level_array_amp)

            if count < len(amp_step_list)-1:
                amp_step = amp_step_list[count+1]
            else:
                amp_step = amp_step_list[-1]

            opt_rel_amp = amp_array[np.argmin(level_array_amp)]
            self.opt_rel_amp = opt_rel_amp

            if opt_rel_amp - round((amp_array[-1]-amp_array[0])/4,3) < 0.05:
                amp_array = np.arange(0.05, round(amp_array[-1]/2,3), amp_step)
            elif opt_rel_amp + round((amp_array[-1]-amp_array[0])/4,3) > 2:
                amp_array = np.arange(round(amp_array[-1]/2,3), 2, amp_step)
            else:
                amp_array = np.arange(opt_rel_amp - round((amp_array[-1]-amp_array[0])/4,3),\
                    opt_rel_amp + round((amp_array[-1]-amp_array[0])/4,3),\
                        amp_step)

            logging.info(__name__+ ": \nOptimal values after {:d} iteration:\nRelative phase: {:f}; Relative amplitude: {:f}; Sideband level: {:f}."\
                .format(count+1, self.opt_rel_pha, self.opt_rel_amp, level))

            if abs(level - noise_level) < 2*noise_std: break

            if self.awg_channel == 1 or self.awg_channel == 2: self.awg.set_ch2_amplitude(opt_rel_amp)
            elif self.awg_channel == 3 or self.awg_channel == 4: self.awg.set_ch4_amplitude(opt_rel_amp)
            else: raise ValueError('Unknown channel number!')

            count = count + 1
        
        return self.opt_rel_pha, self.opt_rel_amp
    
    def opt_LO_leakage(self, max_iter = 10):
        '''
            Main function to optimize LO leakage
            Input:
                max_ter (optional): maximum number of iterations
            Output:
                I_offset, Q_offset : optimal values for I and Q offsets (also stored in self)
        '''
        self.spec_config(self.LO)
        self.spec.sweep()
        noise_level = np.mean(self.spec.get_trace()) 
        noise_std = np.std(self.spec.get_trace())
        #print(noise_level, noise_std)

        self.pulse_load([self.opt_rel_pha], 361)
        self.awg.write(':INST{};:TRAC:SEL{}'.format(self.awg_channel, 361+1))

        self.LO_source.set_status(1)
        self.awg_run()

        off_step_list = [0.05, 0.02, 0.01, 0.005, 0.002, 0.001]

        I_off_array = np.arange(-1, 1, off_step_list[0])
        Q_off_array = np.arange(-1, 1, off_step_list[0])

        #Main loop
        count = 0
        while count <= max_iter:

            # I offset optimization
            level_array_I_off = []
            
            for i, I_off in enumerate(I_off_array):
                if self.awg_channel == 1 or self.awg_channel == 2: self.awg.set_ch1_offset(I_off)
                elif self.awg_channel == 3 or self.awg_channel == 4: self.awg.set_ch3_offset(I_off)
                else: raise ValueError('Unknown channel number!')
                self.spec.sweep()
                level_array_I_off.append(np.max(self.spec.get_trace()))
                print("\rOptimizing I offset parameter... "+str(i+1)+'/'+str(len(I_off_array)), end="", flush=True)

            level = np.min(level_array_I_off)

            if count < len(off_step_list)-1:
                off_step = off_step_list[count+1]
            else:
                off_step = off_step_list[-1]

            self.opt_I_offset = I_off_array[np.argmin(level_array_I_off)]

            if self.opt_I_offset - round((I_off_array[-1]-I_off_array[0])/4,3) < -1:
                I_off_array = np.arange(-1, round(I_off_array[-1]/2,3), off_step)
            elif self.opt_I_offset + round((I_off_array[-1]-I_off_array[0])/4,3) > 1:
                I_off_array = np.arange(round(I_off_array[-1]/2,3), 1, off_step)
            else:
                I_off_array = np.arange(self.opt_I_offset - round((I_off_array[-1]-I_off_array[0])/4,3),\
                    self.opt_I_offset + round((I_off_array[-1]-I_off_array[0])/4,3),\
                        off_step)

            if abs(level - noise_level) < 3*noise_std: break

            if self.awg_channel == 1 or self.awg_channel == 2: self.awg.set_ch1_offset(self.opt_I_offset)
            elif self.awg_channel == 3 or self.awg_channel == 4: self.awg.set_ch3_offset(self.opt_I_offset)
            else: raise ValueError('Unknown channel number!')

            # Q offset optimization
            level_array_Q_off = []
            
            for i, Q_off in enumerate(Q_off_array):
                if self.awg_channel == 1 or self.awg_channel == 2: self.awg.set_ch2_offset(Q_off)
                elif self.awg_channel == 3 or self.awg_channel == 4: self.awg.set_ch4_offset(Q_off)
                else: raise ValueError('Unknown channel number!')
                self.spec.sweep()
                level_array_Q_off.append(np.max(self.spec.get_trace()))
                print("\rOptimizing Q offset parameter... "+str(i+1)+'/'+str(len(Q_off_array)), end="", flush=True)

            level = np.min(level_array_Q_off)

            if count < len(off_step_list)-1:
                off_step = off_step_list[count+1]
            else:
                off_step = off_step_list[-1]

            self.opt_Q_offset = Q_off_array[np.argmin(level_array_Q_off)]

            if self.opt_Q_offset - round((Q_off_array[-1]-Q_off_array[0])/4,3) < -1:
                Q_off_array = np.arange(-1, round(Q_off_array[-1]/2,3), off_step)
            elif self.opt_Q_offset + round((Q_off_array[-1]-Q_off_array[0])/4,3) > 1:
                Q_off_array = np.arange(round(Q_off_array[-1]/2,3), 1, off_step)
            else:
                Q_off_array = np.arange(self.opt_Q_offset - round((Q_off_array[-1]-Q_off_array[0])/4,3),\
                    self.opt_Q_offset + round((Q_off_array[-1]-Q_off_array[0])/4,3),\
                        off_step)

            logging.info(__name__ + ": \nOptimal values after {:d} iteration:\nI offset: {:f}; Q offset: {:f}; LO level: {:f}."\
                .format(count+1, self.opt_I_offset, self.opt_Q_offset, level))

            if abs(level - noise_level) < 3*noise_std: break

            if self.awg_channel == 1 or self.awg_channel == 2: self.awg.set_ch2_offset(self.opt_Q_offset)
            elif self.awg_channel == 3 or self.awg_channel == 4: self.awg.set_ch4_offset(self.opt_Q_offset)
            else: raise ValueError('Unknown channel number!')


            count = count + 1

        return self.opt_I_offset, self.opt_Q_offset
    
    def optimize_IQ(self, glob_iter = 1):
        '''
            Combine sideband and LO leakage optimization
            Iterate both these procedures multiple times if needed
            Input:
                glob_ter (optional): how many times to run (sideband+LO leakage) optimization procedures
            Output:
                rel_pha, rel_amp, I_offset, Q_offset : optimal values for relative phase, amplitude 
                                                        I offset and Q offset (also stored in self)
        '''
        for i in range(glob_iter):
            self.opt_sideband(max_iter = 8)
            self.opt_LO_leakage(max_iter = 8)
        
        return self.opt_rel_pha, self.opt_rel_amp, self.opt_I_offset, self.opt_Q_offset


    def set_opt_parameters(self, reset=False):
        '''
            Loads pulse with optimal relative phase
            and sets AWG amplitudes and offsets to optimal values
            Input:
                reset (optional): loads a pulse with 0 relative phase, 1 relative amplitude and 0 offsets
        '''
        segment=500

        if(reset): amp, phase, Ioff, Qoff = 1,0,0,0
        else: amp, phase, Ioff, Qoff = self.opt_rel_amp, self.opt_rel_pha, self.opt_I_offset, self.opt_Q_offset

        if self.awg_channel == 1 or self.awg_channel == 2:
            self.awg.set_ch1_offset(Ioff)
            self.awg.set_ch2_offset(Qoff) 
            self.awg.set_ch2_amplitude(amp)
        elif self.awg_channel == 3 or self.awg_channel == 4: 
            self.awg.set_ch3_offset(Ioff)
            self.awg.set_ch4_offset(Qoff)
            self.awg.set_ch4_amplitude(amp)
        else: raise ValueError('Given awg channel is wrong! Please choose from {1,3} options.')

        self.pulse_load([phase],seg_off=segment)
        self.awg.write(':INST{};:TRAC:SEL{}'.format(self.awg_channel, segment))

        logging.info(__name__+": Parameters defined for pulse @segment{}. Optimal values? {}".format(segment, not reset))
        return True

    def check_sidebands(self):
        '''
            Gets traces of spectrum analyzer when optimal parameters are stored in AWG (pulse)

        '''

        self.spec_config(self.LO, span=self.IF*2.2,resBW = 3e3, videoBW = 3e3)
        self.awg_run()
        self.LO_source.set_status(1)
    
        self.set_opt_parameters(reset=True)
        self.spec.sweep()
        trace_reset=self.spec.get_trace()

        self.set_opt_parameters()
        self.spec.sweep()
        trace_opt=self.spec.get_trace()

        self.awg_run(off=True)
        self.LO_source.set_status(0)

        freq_x=self.spec.get_frequencies()
        plt.figure(figsize=(15,5))
        plt.axvline(self.LO, color='r')
        plt.text(self.LO, -35, "LO", rotation=90, verticalalignment='center')
        
        plt.axvline(self.RF, color='r')
        plt.text(self.RF, -35, "RF", rotation=90, verticalalignment='center')

        plt.axvline(self.uRF, color='r')
        plt.text(self.uRF, -35, "uRF", rotation=90, verticalalignment='center')

        plt.subplot(211)
        plt.plot(freq_x,trace_reset,'r', label="No opt")
        plt.xlim([self.LO-self.IF*1.1,self.LO+self.IF*1.1])
        plt.ylabel("Amplitude [dBm]")
        plt.xlabel("Frequency [GHz]")
        plt.legend()

        plt.subplot(212)
        plt.plot(freq_x,trace_opt,'g', label="Opt")

        plt.xlim([self.LO-self.IF*1.1,self.LO+self.IF*1.1])
        plt.ylabel("Amplitude [dBm]")
        plt.xlabel("Frequency [GHz]")
        plt.legend()

