# virtual_MultiplexingReadout.py
# initiated and written by M. Jerger 2011/2012
# updated by A. Schneider <andre.schneider@kit.edu> and J. Braumueller <jochen.braumueller@kit.edu>, 05/2016, 08/2016

# This script may be regarded as a wrapper, handling data acquisition with the ADC (commonly known here as mspec)
# and readout pulse generation by the DAC (which is the AWG used for generating readout pulses).

# Now, in 2016, the Martinis AWGs are outdated (and still buggy) as they do not provide longer readout pulses
# due to a limitation in memory.
# The script is updated to also be usable with other AWGs (Tabor, Tektronix).

'''
usage:

readout = qt.instruments.create('readout','virtual_MultiplexingReadout',awg=qubit.readout_awg,mixer_up_src=qubit.readout_mw_source,
            mixer_down_src=qubit.readout_mw_source,mspec=mspec,sample=qubit)
'''

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


from instrument import Instrument
#import instruments
import types
import logging
import numpy as np
import scipy.special
from time import sleep
from qkit.measure.timedomain.awg import load_awg as lawg


class virtual_MultiplexingReadout(Instrument):

    def __init__(self, name, awg, mixer_up_src, mixer_down_src, mspec, sample = None, LO_up_power=12, LO_down_power=12):
        Instrument.__init__(self, name, tags=['virtual'])

        #self._instruments = instruments.get_instruments()

        # Add parameters
        self.add_parameter('LO',    type=types.FloatType, flags=Instrument.FLAG_GETSET, units='Hz')
        self.add_parameter('tone_freq', type=types.TupleType, flags=Instrument.FLAG_GETSET, units='Hz')
        self.add_parameter('tone_relamp', type=types.TupleType, flags=Instrument.FLAG_GETSET, units='')
        self.add_parameter('tone_pha', type=types.TupleType, flags=Instrument.FLAG_GETSET, units='rad')
        self.add_parameter('tone_amp', type=types.FloatType, flags=Instrument.FLAG_GETSET, units='V')
        self.add_parameter('adc_clock',     type=types.FloatType, flags=Instrument.FLAG_GET, units='Hz')
        self.add_parameter('dac_clock',     type=types.FloatType, flags=Instrument.FLAG_SET, units='Hz')
        self.add_parameter('dac_duration',  type=types.FloatType, flags=Instrument.FLAG_GETSET, units='s')
        self.add_parameter('dac_channel_I', type=types.IntType, flags=Instrument.FLAG_SET)
        self.add_parameter('dac_channel_Q', type=types.IntType, flags=Instrument.FLAG_SET)
        self.add_parameter('adc_channel_I', type=types.IntType, flags=Instrument.FLAG_SET)
        self.add_parameter('adc_channel_Q', type=types.IntType, flags=Instrument.FLAG_SET)
        self.add_parameter('dac_attack', type=types.FloatType, flags=Instrument.FLAG_SET)
        self.add_parameter('dac_decay', type=types.FloatType, flags=Instrument.FLAG_SET)
        self.add_parameter('global_pha', type=types.FloatType, flags=Instrument.FLAG_SET)
        self.add_parameter('dac_delay', type = types.FloatType, flags=Instrument.FLAG_GETSET)

        self.add_function('update')
        self.add_function('readout')
        self._awg = awg
        #JB obsolete self._awg_drive = awg_drive
        #JB obsolete self._awg_path = awg_path
        self._mixer_up_src = mixer_up_src
        self._mixer_down_src = mixer_down_src
        self._mspec = mspec
        
        if sample == None:
            logging.warning('Sample object was not given for virtual_MultiplexingReadout.')# This is only needed if you need a readout wfm that is as long as the manipulation.')
        self._sample = sample
        
        #check that awg name exists
        try:
            self._awg.get_type()
        except NameError:
            logging.error('Cannot resolve awg name. Provide name attribute in awg instrument driver.')
            raise NameError
            
        if "GHzDAC" == self._awg.get_type():   #Martinis board
            self.do_set_dac_delay(0)
            #self._dac_duration = 10e-9
            
        elif "Tabor_WX1284C" == self._awg.get_type():   #Tabor AWG
            #self._awg.preset() #this sets various things like trigger level, modes etc. Remember to execute this each time you restart the AWG
            self._awg.set_trigger_impedance(50)   #50 Ohms
            self._awg.preset_readout()   #sets runmode = 'AUTO', trigger_mode='TRIG', starts with the end of the manipulation signal
            self.do_set_dac_delay(-1)
        elif "Tektronix" in self._awg.get_type():
            self.do_set_dac_delay(0)
            self._awg.set_ch1_status(True)
            self._awg.set_ch2_status(True)
            self._awg.run()
            self._awg.wait(10,False)
        else:
            logging.error('Specified AWG unknown. Aborting.')
            raise ImportError
            
        ''' default settings '''
        try:
            
            self._mixer_up_src.set_power(LO_up_power)
            self._mixer_down_src.set_power(LO_down_power)
            self._awg.set_clock(self._sample.readout_clock)
            self._dac_clock = self._awg.get_clock()
            
            #self._mspec.set_trigger_rate(1/float(qubit.T_rep))
            self._mspec.spec_stop()
            self._mspec.set_segments(1)
            self._mspec.set_blocks(1)
            self._mspec.set_spec_trigger_delay(0)
            self._mspec.set_samples(1024)
            mspec.spec_stop()
            mspec.set_samplerate(500e6)   #adc samplerate in Hz, 500MHz is maximum
            
            
            self._mspec.spec_stop()   #stop card before modifying a setting
            self._mspec.set_samplerate(500e6)   #adc samplerate in Hz, 500MHz is maximum
            
            self._dac_channel_I = 0
            self._dac_channel_Q = 1
            self._adc_channel_I = 1
            self._adc_channel_Q = 0
            
            self._dac_attack = 0#5e-9
            self._dac_decay = 0#5e-9
            self._phase = 0
            
            self._tone_freq = [30e6]
            self._dac_duration = 400e-9
            
            self.dac_delay = 0
            
        except Exception as m:
            logging.warning('Defaults not set properly: '+str(m))

    def get_all(self):
        self.get_LO()

    def do_get_adc_clock(self):
        '''
            sample rate of the analog to digital converter
        '''
        return self._mspec.get_clock()
    def do_set_dac_clock(self, clock):
        '''
            sample rate of the digital to analog converter
        '''
        self._dac_clock = clock
    def do_set_dac_duration(self, duration):
        '''
            defines the time duration of the signal output on the dac
            this defines the readout pulse length and maximum repetition rate
        '''
        self._dac_duration = duration
    def do_get_dac_duration(self):
        return self._dac_duration
        
    def do_set_dac_channel_I(self, channel):
        '''
            set dac channel that outputs the I signal, -1=None
        '''
        self._dac_channel_I = channel
        if(self._dac_channel_I == -1) and (self._dac_channel_Q == -1):
            logging.warning(__name__ + 'no output signal is produced if both dac_channel_I and dac_channel_Q are none')
    def do_set_dac_channel_Q(self, channel):
        '''
            set dac channel that outputs the Q signal, -1=None
        '''
        self._dac_channel_Q = channel
        if(self._dac_channel_I == -1) and (self._dac_channel_Q == -1):
            logging.warning(__name__ + 'no output signal is produced if both dac_channel_I and dac_channel_Q are none')
    def do_set_adc_channel_I(self, channel):
        '''
            set adc channel that acquires the I signal, -1=None
        '''
        self._adc_channel_I = channel
        if(self._adc_channel_I == -1) and (self._adc_channel_Q == -1):
            logging.warning(__name__ + 'no signal is acquired if both dac_channel_I and dac_channel_Q are none')
    def do_set_adc_channel_Q(self, channel):
        '''
            set adc channel that acquires the Q signal, -1=None
        '''
        self._adc_channel_Q = channel
        if(self._adc_channel_I == -1) and (self._adc_channel_Q == -1):
            logging.warning(__name__ + 'no signal is acquired if -1dac_channel_I and dac_channel_Q are none')

    def do_set_dac_attack(self, attack):
        ''' set attack time of the readout pulse '''
        self._dac_attack = attack

    def do_set_dac_decay(self, decay):
        ''' set decay time of the readout pulse '''
        self._dac_decay = decay

    def do_set_LO(self, frequency):
        self._mixer_up_src.set_frequency(frequency)
        self._mixer_down_src.set_frequency(frequency)
        self._LO = frequency
    def do_get_LO(self):
        return self._LO

    def do_set_tone_amp(self, amp):
        self._tone_amp = amp
    def do_get_tone_amp(self):
        return self._tone_amp

    def do_set_tone_freq(self, freqs):
        self._tone_freq = np.array(freqs)
    def do_get_tone_freq(self):
        return self._tone_freq

    def do_set_tone_relamp(self, amps):
        self._tone_relamp = np.array(amps)
    def do_get_tone_relamp(self):
        return self._tone_relamp

    def do_set_tone_pha(self, phases):
        self._tone_pha = np.array(phases)
    def do_get_tone_pha(self):
        return self._tone_pha

    def do_set_global_pha(self, phase):
        self._phase = float(phase)
    def do_get_global_pha(self):
        return self._phase
        
    def do_set_dac_delay(self,delay):
        '''
        sets the pause time before the dac pulse in s
        a value <= -1 will take sample.exc_T
        '''
        self.dac_delay = delay
    def do_get_dac_delay(self):
        return self.dac_delay
        


    # +++++ ADC acquisition ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    def _acquire_IQ(self):
        '''
        essentially do a mspec.acquire and return I and Q
        '''
        data = self._mspec.acquire().swapaxes(0, 1)
        if(self._adc_channel_I == -1):
            I = np.zeros(data.shape[1:])
        else:
            I = data[self._adc_channel_I]
        if(self._adc_channel_Q == -1):
            Q = np.zeros(data.shape[1:])
        else:
            Q = data[self._adc_channel_Q]
        return I, Q


    def readout(self, timeTrace = False):
        '''
            measure transmission of the tones set
            --> return amplitude and phase data at the given IQ frequency and also the full I and Q time trace if set to true
                using IQ_decode
            
            inputs:
                timeTrace - also output raw trace for further processing
        '''
        Is, Qs = self._acquire_IQ()
        if(len(Is.shape) == 2):
            sig_amp = np.zeros((Is.shape[1], len(self._tone_freq)))
            sig_pha = np.zeros((Is.shape[1], len(self._tone_freq)))
            for idx in range(Is.shape[1]):
                sig_amp[idx, :], sig_pha[idx, :] = self.IQ_decode(Is[:, idx], Qs[:, idx])
        else:
            sig_amp, sig_pha = self.IQ_decode(Is, Qs)
            
        if(timeTrace):
            return sig_amp, sig_pha, Is, Qs
        else:
            return sig_amp, sig_pha


    def spectrum(self, segment = 0):
        '''
            measure transmission of the tones set
        '''
        I, Q = self._acquire_IQ()
        if(len(I.shape) == 2):
            # in segmented mode, take only one segment
            return self.IQ_fft(I[:, segment], Q[:, segment])
        else:
            return self.IQ_fft(I, Q)


    def IQ_fft(self, I, Q, samplerate = None):
        '''
            calculate fourier transform of the acquired waveform

            Input:
                I, Q       - signal acquired at rate samplerate
                samplerate - rate at which I and Q were sampled
        '''
        if(samplerate == None): samplerate = self.get_adc_clock()

        sig_t = np.array(I) + 1j*np.array(Q)
        sig_f = np.fft.fftshift(np.fft.fft(sig_t))
        sig_x = self._LO+np.fft.fftshift(np.fft.fftfreq(sig_t.size, 1./samplerate))

        return sig_x, np.abs(sig_f), np.angle(sig_f)


    def IQ_decode(self, I, Q, freqs = None, samplerate = None, phase = None):
        '''
            calculate fourier transform of the acquired waveform and
            extract amplitude and phase of requested frequency components

            Input:
                I, Q       - signal acquired at rate samplerate
                freqs      - interesting frequency components
                samplerate - rate at which I and Q were sampled
                phase      - apply additional rotation to I+1j*Q

            Output:
                currently three vectors: frequency, amplitude, phase of each fft point
        '''
        if(samplerate == None): samplerate = self.get_adc_clock()
        if(freqs == None): freqs = self._tone_freq
        if(phase == None): phase = self._phase
        freqs = np.array(freqs)-self._LO

        sig_t = (np.array(I) + 1j*np.array(Q))*np.exp(1j*phase)
        sig_f = np.fft.fftshift(np.fft.fft(sig_t))
        #sig_x = np.fft.fftshift(np.fft.fftfreq(sig_t.size, 1./samplerate))
        sig_x_fact = 1.*samplerate/sig_t.size

        # linear interpolation of two fft points
        idxs = 1./sig_x_fact*np.array(freqs) + I.size/2
        idxsH = np.array(np.ceil(idxs), dtype = np.integer)
        idxsL = np.array(np.floor(idxs), dtype = np.integer)
        idxsLw = idxsH-idxs
        idxsHw = np.ones_like(idxsLw)-idxsLw
        sig_amp = idxsHw*np.abs(sig_f[idxsH]) + np.abs(idxsLw*sig_f[idxsL])
        sig_pha = np.angle(sig_f[idxsH]) # usually averages out between two points

        return sig_amp, sig_pha

        
    # +++++ DAC (AWG) settings ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        
    def update(self):
        '''
        General method to update all (DAC) settings
        
        create DAC waveforms and update DAC, set DAC (AWG) to run mode (and switch outputs on)
        using IQ.encode and the hidden method self._update_dac()
        '''
        # calculate required IF frequencies
        tones = np.array(self._tone_freq)
        ntones = len(tones)
        IFtones = tones-self._LO

        # perform sanity check
        IFMax = max(abs(IFtones))
        #print 'IF tones are ', (IFtones/1e6), 'MHz'
        if(IFMax > self._awg.get_clock()/2):
            logging.warning(__name__ + ' : maximum IF frequency of %fMHz is above the limit of the DAC.'%(IFMax/1e6))
        if(IFMax > self._mspec.get_clock()/2):
            logging.warning(__name__ + ' : maximum IF frequency of %fMHz is above the limit of the ADC.'%(IFMax/1e6))

        # build I and Q waveforms and send them to the DAC
        if(self._tone_relamp == None):
            amplitudes = 1./ntones*np.ones(ntones)
        else:
            amplitudes = 1./ntones*self._tone_relamp
        if(self._tone_pha == None):
            phases = np.zeros(ntones)
        else:
            phases = self._tone_pha
        I, Q,m1 = self.IQ_encode(self._dac_duration, IFtones, [amplitudes, amplitudes], [phases, phases], self._dac_clock, self._dac_attack, self._dac_decay)
        self._update_dac([self._dac_channel_I, self._dac_channel_Q], [I, Q],marker1 = [m1,m1],marker2 = [m1,m1])
        
        
    def _update_dac(self, channels, samples, marker1 = None, marker2 = None, drive = None, path = None):
        '''
            update waveform data on the awg

            Input:
                samples - matrix of samples to put on awg channels
                channels - channels to install them on
        '''
        samples = np.array(samples)
        if(marker1 == None):
            marker1 = np.zeros(samples.shape)
            marker1[:,1:10]=1
        if(marker2 == None):
            marker2 = np.zeros(samples.shape)
            marker2[:,1:10]=1

            
        if "GHzDAC" == self._awg.get_type():   #Martinis board
            drive = 'c:'
            path = '\\waveforms'
            for idx in range(0, len(channels)):
                if(channels[idx] == -1): continue # only apply I or Q if the user wishes that
                channel = 1+channels[idx]
                
                fn = drive + path + '\\ch%d'%channel
                self._awg.send_waveform(samples[idx, :], marker1[idx, :], marker2[idx, :], fn, self._dac_clock)
                self._awg.load_waveform(channel, 'ch%d'%channel, drive, path)
                
            # setup channel overall amplitude
            for channel in [self._dac_channel_I, self._dac_channel_Q]:
                getattr(self._awg, 'set_ch%d_amplitude'%(channel+1))(self._tone_amp)
            self._awg.run()
            
        elif "Tabor_WX1284C" == self._awg.get_type():   #Tabor AWG
            self._awg.preset_readout()
            try:
                self._awg.set_clock(self._sample.readout_clock)
            except:
                logging.warning('Clock and amplitude settings not written.')
            self._awg.wfm_send2(samples[0],samples[1],m1 = marker1[0],m2 = marker2[0],seg=1)
            self._awg.define_sequence(1,1)
        elif "Tektronix" in self._awg.get_type():   #Tektronix AWG
            try:
                self._awg.set_clock(self._sample.readout_clock)
                self._awg.set_ch1_amplitude(self._tone_amp)
                self._awg.set_ch2_amplitude(self._tone_amp)
            except:
                logging.warning('Clock and amplitude settings not written.')
            if self._sample:
                lawg.update_sequence([1],lambda t, sample: [samples[0],samples[1]], self._sample, awg = self._awg)
            else:
                logging.error('Please provide sample object in instantiating readout when using Tektronix AWG for readout.')

    def IQ_encode(self, duration, frequencies, amplitudes = None, phases = None, samplerate = None, attack = 2e-9, decay = 2e-9):
        '''
            provide I and Q data that will create a single side band multitone signal
            --> generate sin and cos waveforms for I and Q with IF frequency

            Input:
                amplitudes   - normalized amplitudes (1xN) or I and Q amplitudes (2xN) of each tone
                frequencies  - IF frequencies desired
                duration     - duration of the waveform in real time
                samplerate   - sample rate of the output device
                attack/decay - with of trailing and leading edges

            Output:
                two vectors containing samples for I and Q
        '''

        if(samplerate == None): samplerate = self._dac_clock
        nSamples = int(samplerate*duration)
        indices = np.arange(0, nSamples)
        frequencies = np.array(frequencies)
        omegas = 2.*np.pi*frequencies/samplerate

        if(amplitudes == None):
            amplitudes = np.ones((2, frequencies.size))
        else:
            amplitudes = np.array(amplitudes)
            if (amplitudes.ndim == 1): amplitudes = np.array([amplitudes, amplitudes])
        if(phases == None):
            phases = np.zeros(2, frequencies.size)
        else:
            phases = np.array(phases)
            if (phases.ndim == 1): phases = np.array([phases, phases])
            
        # generate multitone waveform
        I = np.zeros(np.ceil((nSamples+1)/16.)*16)
        Q = np.zeros(np.ceil((nSamples+1)/16.)*16)
        for idx in range(0, frequencies.size):
            I[1:nSamples+1] += amplitudes[0, idx]*np.sin(omegas[idx]*indices+phases[0, idx])
            Q[1:nSamples+1] += amplitudes[1, idx]*np.cos(omegas[idx]*indices+phases[1, idx])
            
        # apply envelope: erf, erf(\pm 2) is almost 0/1, erf(\pm 1) is ~15/85%
        nAttack = int(2*samplerate*attack)
        sAttack = 0.5*(1+scipy.special.erf(np.linspace(-2, 2, nAttack)))
        I[0:nAttack] *= sAttack
        Q[0:nAttack] *= sAttack
        nDecay = int(2*samplerate*decay)
        sDecay = 0.5*(1+scipy.special.erf(np.linspace(2, -2, nDecay)))
        I[(nSamples-nDecay):nSamples] *= sDecay 
        Q[(nSamples-nDecay):nSamples] *= sDecay 
        m1 = np.zeros(len(I),dtype=np.int8)
        m1[1:len(I)-1] = 1
        if self.dac_delay != 0:
            if self.dac_delay <= -1:
                dac_delay = self._sample.exc_T-duration
            else:
                dac_delay = self.dac_delay
            
            I = np.append(np.zeros(int(dac_delay*samplerate/16)*16),I)
            Q = np.append(np.zeros(int(dac_delay*samplerate/16)*16),Q)
            m1 = np.append(np.zeros(int(dac_delay*samplerate/16)*16),m1)
        return I, Q,m1
        