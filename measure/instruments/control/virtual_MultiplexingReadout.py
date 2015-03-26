from instrument import Instrument
import instruments
import types
import logging
import numpy as np
import scipy.special
from time import sleep

class virtual_MultiplexingReadout(Instrument):

	def __init__(self, name, awg, mixer_up_src, mixer_down_src, mspec, awg_drive = 'c:', awg_path = '\\waveforms'):
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
		self.add_parameter('dac_duration',  type=types.FloatType, flags=Instrument.FLAG_SET, units='s')
		self.add_parameter('dac_channel_I', type=types.IntType, flags=Instrument.FLAG_SET)
		self.add_parameter('dac_channel_Q', type=types.IntType, flags=Instrument.FLAG_SET)
		self.add_parameter('adc_channel_I', type=types.IntType, flags=Instrument.FLAG_SET)
		self.add_parameter('adc_channel_Q', type=types.IntType, flags=Instrument.FLAG_SET)

		self._awg = awg
		self._awg_drive = awg_drive
		self._awg_path = awg_path

		self._mixer_up_src = mixer_up_src
		self._mixer_down_src = mixer_down_src
		self._mspec = mspec

		self._dac_channel_I = 0
		self._dac_channel_Q = 1
		self._adc_channel_I = 0
		self._adc_channel_Q = 1

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

    # tone setup
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





	def update(self):
		# calculate required IF frequencies
		tones = np.array(self._tone_freq)
		ntones = len(tones)
		IFtones = tones-self._LO

		# perform sanity check
		IFMax = max(abs(IFtones))
		print 'IF tones are ', (IFtones/1e6), 'MHz'
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
		I, Q = self.IQ_encode(self._dac_duration, IFtones, [amplitudes, amplitudes], [phases, phases], self._dac_clock)
		self._update_dac([self._dac_channel_I, self._dac_channel_Q], [I, Q])
		# setup channel overall amplitude
		for channel in [self._dac_channel_I, self._dac_channel_Q]:
			getattr(self._awg, 'set_ch%d_amplitude'%(channel+1))(self._tone_amp)
		self._awg.run()



	def _acquire_IQ(self):
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



	def _update_dac(self, channels, samples, marker1 = None, marker2 = None, drive = None, path = None):
		'''
			update waveform data on the awg

			Input:
				samples - matrix of samples to put on awg channels
				channels - channels to install them on

			Output:
				currently none
		'''
		samples = np.array(samples)
		if(drive == None): drive = self._awg_drive
		if(path == None): path = self._awg_path
		if(marker1 == None): marker1 = np.zeros(samples.shape)
		if(marker2 == None): marker2 = np.zeros(samples.shape)

		for idx in range(0, len(channels)):
			if(channels[idx] == -1): continue # only apply I or Q if the user wishes that
			channel = 1+channels[idx]
			fn = drive + path + '\\ch%d'%channel
			self._awg.send_waveform(samples[idx, :], marker1[idx, :], marker2[idx, :], fn, self._dac_clock)
			self._awg.load_waveform(channel, 'ch%d'%channel, drive, path)



	def IQ_encode(self, duration, frequencies, amplitudes = None, phases = None, samplerate = None, attack = 2e-9, decay = 2e-9):
		'''
			provide I and Q data that will create a single side band multitone signal

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
		I = np.zeros(nSamples)
		Q = np.zeros(nSamples)
		for idx in range(0, frequencies.size):
			I += amplitudes[0, idx]*np.sin(omegas[idx]*indices+phases[0, idx])
			Q += amplitudes[1, idx]*np.cos(omegas[idx]*indices+phases[1, idx])
		# apply envelope: erf, erf(\pm 2) is almost 0/1, erf(\pm 1) is ~15/85%
		nAttack = int(2*samplerate*attack)
		sAttack = 0.5*(1+scipy.special.erf(np.linspace(-2, 2, nAttack)))
		I[0:nAttack] *= sAttack
		Q[0:nAttack] *= sAttack
		nDecay = int(2*samplerate*decay)
		sDecay = 0.5*(1+scipy.special.erf(np.linspace(2, -2, nDecay)))
		I[(nSamples-nDecay):nSamples] *= sDecay 
		Q[(nSamples-nDecay):nSamples] *= sDecay 
		return I, Q



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



	def IQ_decode(self, I, Q, freqs = None, samplerate = None):
		'''
			calculate fourier transform of the acquired waveform and
			extract amplitude and phase of requested frequency components

			Input:
				I, Q       - signal acquired at rate samplerate
				freqs      - interesting frequency components
				samplerate - rate at which I and Q were sampled

			Output:
				currently three vectors: frequency, amplitude, phase of each fft point
		'''
		if(samplerate == None): samplerate = self.get_adc_clock()
		if(freqs == None): freqs = self._tone_freq
		freqs = np.array(freqs)-self._LO

		sig_t = np.array(I) + 1j*np.array(Q)
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
