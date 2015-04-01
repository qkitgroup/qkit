import qt
import numpy as np
import os.path
import time
import qubit
import logging
import numpy
import sys


# awg-supported multiple measurement system
def awg_envelope(pulse, attack, decay, length, position = None, clock = 1200e6):
	'''
		create an erf-shaped envelope function
		erf(\pm 2) is almost 0/1, erf(\pm 1) is ~15/85%
		
		Input:
			tstart, tstop - erf(-2) times
			attack, decay - attack/decay times
	'''
	import scipy.special
	if(position == None): position = length
	sample_start = int(clock*(position-pulse))
	sample_end = int(clock*position)
	sample_length = int(np.ceil(length*clock))
	wfm = np.ones(sample_length)
	nAttack = int(clock*attack)
	sAttack = 0.5*(1+scipy.special.erf(np.linspace(-2, 2, nAttack)))
	wfm[sample_start:sample_start+nAttack] *= sAttack
	wfm[0:sample_start] *= 0
	nDecay = int(clock*decay)
	sDecay = 0.5*(1+scipy.special.erf(np.linspace(2, -2, nDecay)))
	wfm[(sample_end-nDecay):sample_end] *= sDecay 
	wfm[sample_end:sample_length] *= 0
	return wfm
	
def awg_triangle(pulse, attack, decay, length, position = None, clock = 1200e6):
	'''
		create a pulse with triangular shape
		
		Input:
			pulse, attack, decay - pulse duration, attack and decay times
			length - length of the resulting waveform in seconds
			position - position of the end of the pulse
	'''
	if(position == None): position = length
	sample_start = int(clock*(position-pulse))
	sample_end = int(clock*position)
	sample_length = int(np.ceil(length*clock))
	sample_attack = int(np.ceil(attack*clock)) 
	sample_decay = int(np.ceil(decay*clock))
	wfm = np.zeros(sample_length)
	wfm[sample_start:sample_start+sample_attack] = np.linspace(0, 1, sample_attack)
	wfm[sample_start+sample_attack:sample_end-sample_decay] = 1
	wfm[sample_end-sample_decay:sample_end] = np.linspace(1, 0, sample_decay)
	return wfm

def awg_pulse(pulse, length, position = None, low = 0, high = 1, clock = 1000e6, adddelay=0.,freq=None):
	'''
		generate waveform corresponding to a dc pulse

		Input:
			pulse - pulse duration in seconds
			length - length of the generated waveform
			position - time instant of the end of the pulse
			low - pulse 'off' sample value
			high - pulse 'on' sample value
			clock - sample rate of the DAC
		Output:
			float array of samples
	'''
	if(position == None): position = length
	if(pulse>position): logging.error(__name__ + ' : pulse does not fit into waveform')
	sample_start = int(clock*(position-pulse-adddelay))
	sample_end = int(clock*(position-adddelay))
	sample_length = int(np.ceil(length*clock))
	wfm = low*np.ones(sample_length)
	if(sample_start < sample_end): wfm[int(sample_start)] = high + (low-high)*(sample_start-int(sample_start))
	if freq==None: wfm[int(np.ceil(sample_start)):int(sample_end)] = high
	else:
		for i in range(int(sample_end)-int(np.ceil(sample_start))):
			wfm[i+int(np.ceil(sample_start))] = high*np.sin(2*np.pi*freq/clock*(i))
	if(np.ceil(sample_end) != np.floor(sample_end)): wfm[int(sample_end)] = low + (high-low)*(sample_end-int(sample_end))
	return wfm
	
	
def awg_pulse_gauss(pulse, length, position = None, low = 0, high = 1, clock = 1200e6):
	'''
		generate waveform corresponding to a dc gauss pulse

		Input:
			pulse - pulse duration in seconds
			length - length of the generated waveform
			position - time instant of the end of the pulse
			low - pulse 'off' sample value
			high - pulse 'on' sample value
			clock - sample rate of the DAC
		Output:
			float array of samples
	'''
	if(position == None): position = length
	if(pulse>position): logging.error(__name__ + ' : pulse does not fit into waveform')
	sample_start = clock*(position-pulse)
	sample_end = clock*position
	sample_length = int(np.ceil(length*clock))
	wfm = low*np.ones(sample_length)
	if(sample_start < sample_end): wfm[int(sample_start)] = 0.#high + (low-high)*(sample_start-int(sample_start))
	#wfm[int(np.ceil(sample_start)):int(sample_end)] = high
	pulsesamples = int(int(sample_end)-np.ceil(sample_start))
	for i in range(pulsesamples):
		wfm[np.ceil(sample_start)+i] = high*np.exp(-(i-pulsesamples/2.)**2/(2.*(pulsesamples/5.)**2))
	if(np.ceil(sample_end) != np.floor(sample_end)): wfm[int(sample_end)] = low + (high-low)*(sample_end-int(sample_end))
	return wfm

def awg_function(function, pulse, length, position = None, clock = 1200e6):
	'''
		generate arbitrary waveform pulse

		Input:
			function - function called
			pulse - duration of the signal
			position - time instant of the end of the signal
			length - duration of the waveform
			clock - sample rate of the DAC
		Output:
			float array of samples
	'''
	if(position == None): position = length
	if(pulse>position): logging.error(__name__ + ' : pulse does not fit into waveform')
	sample_start = clock*(position-pulse)
	sample_end = clock*position
	sample_length = int(np.ceil(length*clock))

	wfm = np.zeros(sample_length)
	times = 1./clock*np.arange(0, sample_end-sample_start+1)
	wfm[sample_start:sample_end] = function(times)
	return wfm

def awg_ramsey(delay, pi4_pulse, length, position = None, low = 0, high = 1, clock = 1200e6):
	'''
		generate waveform with two pi/4 pulses and delay in-between

		Input:
			delay - time delay between the pi/4 pulses
			pi4_pulse - length of a pi/4 pulse
			(see awg_pulse for rest)
		Output:
			float array of samples
	'''
	if(position == None): position = length
	if(delay+2*pi4_pulse>position): logging.error(__name__ + ' : ramsey pulses do not fit into waveform')
	wfm = awg_pulse(pi4_pulse, length, position, low, high, clock)
	wfm += awg_pulse(pi4_pulse, length, position-delay-pi4_pulse, low, high, clock)
	return wfm

def awg_upsidedownspinecho(delay, pi4_pulse, pi2_pulse, length, position = None, low = 0, high = 1, clock = 1200e6, readoutpulse=True):
	'''
		generate waveform with two pi/4 pulses, a pi/2 pulse and delays

		(see awg_ramsey for parameter description)
	'''
	if(position == None): position = length
	if(2*delay+pi4_pulse+2*pi2_pulse>position): logging.error(__name__ + ' : spin-echo pulses do not fit into waveform')
	if readoutpulse: wfm = awg_pulse(pi4_pulse, length, position, low, high, clock)
	else: wfm = awg_pulse(pi4_pulse, length, position, low, low, clock)
	wfm += awg_pulse(pi2_pulse, length, position-pi2_pulse, low, high, clock)
	wfm += awg_pulse(pi4_pulse, length, position-delay-pi2_pulse, low, high, clock)
	wfm += awg_pulse(pi2_pulse, length, position-2*delay-pi4_pulse-pi2_pulse-pi2_pulse, low, high, clock)
	return wfm

def awg_secondspinecho(delay, pi4_pulse, pi2_pulse, length, position = None, low = 0, high = 1, clock = 1200e6, readoutpulse=True):
	'''
		generate waveform with two pi/4 pulses, a pi/2 pulse and delays

		(see awg_ramsey for parameter description)
	'''
	if(position == None): position = length
	if(4*delay+pi4_pulse+2*pi2_pulse>position): logging.error(__name__ + ' : spin-echo pulses do not fit into waveform')
	if readoutpulse: wfm = awg_pulse(pi4_pulse, length, position, low, high, clock)
	else: wfm = awg_pulse(pi4_pulse, length, position, low, low, clock)
	wfm += awg_pulse(pi2_pulse, length, position-pi2_pulse, low, high, clock)
	wfm += awg_pulse(pi2_pulse, length, position-2*delay-pi2_pulse, low, high, clock)
	wfm += awg_pulse(pi4_pulse, length, position-3*delay-pi4_pulse-pi2_pulse-pi2_pulse, low, high, clock)
	return wfm
	
def awg_thirdspinecho(delay, pi4_pulse, pi2_pulse, length, position = None, low = 0, high = 1, clock = 1200e6, readoutpulse=True):
	'''
		generate waveform with two pi/4 pulses, a pi/2 pulse and delays

		(see awg_ramsey for parameter description)
	'''
	if(position == None): position = length
	if(5*delay+2*pi4_pulse+3*pi2_pulse>position): logging.error(__name__ + ' : spin-echo pulses do not fit into waveform')
	if readoutpulse: wfm = awg_pulse(pi4_pulse, length, position, low, high, clock)
	else: wfm = awg_pulse(pi4_pulse, length, position, low, low, clock)
	wfm += awg_pulse(pi2_pulse, length, position-pi2_pulse, low, high, clock)
	wfm += awg_pulse(pi2_pulse, length, position-2*delay-pi2_pulse, low, high, clock)
	wfm += awg_pulse(pi2_pulse, length, position-4*delay-2*pi2_pulse, low, high, clock)
	wfm += awg_pulse(pi4_pulse, length, position-5*delay-pi4_pulse-3*pi2_pulse, low, high, clock)
	return wfm
	
def awg_stimulatedecho(waiting_time, pi4_pulse, delay, length, position = None, low = 0, high = 1, clock = 1200e6, readoutpulse=True,adddelay=0., freq=None):
	'''
		generate 3PE waveform: pi/2 - waiting_time - pi/2 - delay - pi/2, stimulated echo appears after another waiting_time

		(see awg_ramsey for parameter description)
	'''
	if(position == None): position = length
	if(delay+4*pi4_pulse+2.*waiting_time>position): logging.error(__name__ + ' : spin-echo pulses do not fit into waveform')
	if readoutpulse: wfm = awg_pulse(pi4_pulse, length, position, low, high, clock,freq=freq)
	else: wfm = awg_pulse(pi4_pulse, length, position, low, low, clock)
	wfm += awg_pulse(pi4_pulse, length, position-1.*waiting_time-pi4_pulse-adddelay, low, high, clock,freq=freq)
	wfm += awg_pulse(pi4_pulse, length, position-delay-2*pi4_pulse-1.*waiting_time-adddelay, low, high, clock,freq=freq)
	wfm += awg_pulse(pi4_pulse, length, position-delay-3*pi4_pulse-2.*waiting_time-adddelay, low, high, clock,freq=freq)
	return wfm

def awg_stimulatedecho_old(waiting_time, pi4_pulse, delay, length, position = None, low = 0, high = 1, clock = 1200e6, readoutpulse=True,adddelay=0., freq=None):
	'''
		generate 3PE waveform: pi/2 - waiting_time - pi/2 - delay - pi/2, stimulated echo appears after another waiting_time

		(see awg_ramsey for parameter description)
	'''
	if(position == None): position = length
	if(delay+4*pi4_pulse+4*waiting_time>position): logging.error(__name__ + ' : spin-echo pulses do not fit into waveform')
	if readoutpulse: wfm = awg_pulse(pi4_pulse, length, position, low, high, clock,freq=freq)
	else: wfm = awg_pulse(pi4_pulse, length, position, low, low, clock)
	wfm += awg_pulse(pi4_pulse, length, position-3*waiting_time-pi4_pulse-adddelay, low, high, clock,freq=freq)
	wfm += awg_pulse(pi4_pulse, length, position-delay-2*pi4_pulse-3*waiting_time-adddelay, low, high, clock,freq=freq)
	wfm += awg_pulse(pi4_pulse, length, position-delay-3*pi4_pulse-4*waiting_time-adddelay, low, high, clock,freq=freq)
	return wfm
	
def awg_spinecho(delay, pi4_pulse, pi2_pulse, length, position = None, low = 0, high = 1, clock = 1000e6, readoutpulse=True,adddelay=0., freq=None):
	'''
		generate waveform with two pi/4 pulses, a pi/2 pulse and delays

		(see awg_ramsey for parameter description)
	'''
	if(position == None): position = length
	if(adddelay+2*delay+2*pi4_pulse+pi2_pulse>position): logging.error(__name__ + ' : spin-echo pulses do not fit into waveform')
	if readoutpulse: wfm = awg_pulse(pi4_pulse, length, position, low, high, clock,freq=freq)
	else: wfm = awg_pulse(pi4_pulse, length, position, low, low, clock,freq=freq)
	wfm += awg_pulse(pi2_pulse, length, position-pi4_pulse-delay-adddelay, low, high, clock,freq=freq)
	wfm += awg_pulse(pi4_pulse, length, position-2*delay-1*pi4_pulse-pi2_pulse-adddelay, low, high, clock,freq=freq)
	#wfm += awg_pulse(pi2_pulse, length, position-pi2_pulse-pi4_pulse-delay-adddelay, low, high, clock,freq=freq)
	#wfm += awg_pulse(pi4_pulse, length, position-2*delay-2*pi4_pulse-pi2_pulse-adddelay, low, high, clock,freq=freq)
	return wfm
	
def awg_secondspinecho_special(delay, pi4_pulse, pi2_pulse, length, position = None, low = 0, high = 1, clock = 1000e6, readoutpulse=True,adddelay=0., freq=None):
	'''
		generate waveform with two pi/4 pulses, a pi/2 pulse and delays

		(see awg_ramsey for parameter description)
	'''
	corr1 = pi4_pulse/2-pi2_pulse/2
	corr2 = pi2_pulse/2-pi2_pulse/2
	if(position == None): position = length
	if(adddelay+2*2*delay+2*pi4_pulse+3*pi2_pulse>position): logging.error(__name__ + ' : spin-echo pulses do not fit into waveform')
	if readoutpulse: wfm = awg_pulse(pi4_pulse, length, position, low, high, clock,freq=freq)
	else: wfm = awg_pulse(pi4_pulse, length, position, low, low, clock,freq=freq)
	wfm += awg_pulse(pi2_pulse, length, position-(delay-corr1)-1*pi4_pulse-1*pi2_pulse-adddelay, low, high, clock,freq=freq)
	wfm += awg_pulse(pi2_pulse, length, position-2*(delay-corr2)-1*(delay-corr1)-1*pi4_pulse-2*pi2_pulse-adddelay, low, high, clock,freq=freq)
	wfm += awg_pulse(pi4_pulse, length, position-2*(delay-corr2)-2*(delay-corr1)-2*pi4_pulse-2*pi2_pulse-adddelay, low, high, clock,freq=freq)
	return wfm
	
def awg_T1ESR(delay, pi4_pulse, length, position = None, low = 0, high = 1, clock = 1200e6, readoutpulse=True):
	'''
		generate waveform with two pi/4 pulses, a pi/2 pulse and delays

		(see awg_ramsey for parameter description)
	'''
	if(position == None): position = length
	if(2*delay+pi4_pulse+pi4_pulse>position): logging.error(__name__ + ' : spin-echo pulses do not fit into waveform')
	if readoutpulse: wfm = awg_pulse(pi4_pulse, length, position, low, high, clock)
	else: wfm = awg_pulse(pi4_pulse, length, position, low, low, clock)
	wfm += awg_pulse(pi4_pulse, length, position-delay-pi4_pulse, low, high, clock)
	wfm += awg_pulse(pi4_pulse, length, position-2*delay-pi4_pulse-pi4_pulse, low, high, clock)
	return wfm
	
	
def awg_gaussspinecho(delay, pi4_pulse, pi2_pulse, length, position = None, low = 0, high = 1, clock = 1200e6, readoutpulse=True,adddelay=0.):
	'''
		generate waveform with two pi/4 pulses, a pi/2 pulse and delays

		(see awg_ramsey for parameter description)
	'''
	if(position == None): position = length
	if(adddelay+2*delay+2*pi4_pulse+pi2_pulse>position): logging.error(__name__ + ' : spin-echo pulses do not fit into waveform')
	if readoutpulse: wfm = awg_pulse(pi4_pulse, length, position, low, high, clock)
	else: wfm = awg_pulse_gauss(pi4_pulse, length, position, low, low, clock)
	wfm += awg_pulse_gauss(pi2_pulse, length, position-delay-pi4_pulse-adddelay, low, high, clock)
	wfm += awg_pulse_gauss(pi4_pulse, length, position-2*delay-pi4_pulse-pi2_pulse-adddelay, low, high, clock)
	return wfm
	
	
def awg_ramsey_decoupled(delay, pi_pulse, pi2_pulse, length, position = None, low = 0, high = 1, clock = 1200e6, even = True):
	'''
		generate waveform with two pi/2 pulses and pi pulses in-between

		Input:
			delay - time delay between the pi/2 pulses
			pi2_pulse - length of a pi/2 pulse
			even = true  allows only an even number of pi pulses
			(see awg_pulse for rest)
		Output:
			float array of samples
	'''
	if(position == None): position = length
	if(delay+2*pi2_pulse>position): logging.error(__name__ + ' : ramsey pulses do not fit into waveform')
	wfm = awg_pulse(pi2_pulse, length, position, low, high, clock)
	n = int(np.trunc(delay/pi_pulse))
	if(even==True) and (n%2==1) :  #if even=true and n odd decrease n by one
		n = n-1
	dt = (delay-pi_pulse*n)/float(2*n)
	for i in range(n):
		wfm += awg_pulse(pi_pulse, length, position-dt*(2*i+1)-pi_pulse*i-pi2_pulse, low, high, clock)
		#print position-dt*(i+1)-pi_pulse*n-pi2_pulse
	wfm += awg_pulse(pi2_pulse, length, position-delay-pi2_pulse, low, high, clock)
	#print position-delay-pi2_pulse
	return wfm

def awg_update(t, wfm_funcs, wfm_channels, awg, drive = 'c:', path = '\\waveforms', clock = 1200e6):
	'''
		simultaneously perform different experiments on multiple qubits using an awg

		Input:
			t - parameter for wfm_funcs
			wfm_funcs - callable function of 1 parameter that generate waveforms
			wfm_channels - awg channels the waveforms are assigned to
			awg - awg device the wfms are assigned to
	'''
	for i in range(len(wfm_funcs)):
		wfm_func = wfm_funcs[i]
		wfm_channel = wfm_channels[i]
		wfm_samples = wfm_func(t)
		wfm_fn = 'ch%d'%wfm_channel
		marker = np.zeros(wfm_samples.shape, np.int)
		awg.send_waveform(wfm_samples, marker, marker, '%s%s\\%s'%(drive, path, wfm_fn), clock)
		awg.load_waveform(wfm_channel, wfm_fn, drive, path)
	#awg.run() # necessary?



def awg_update_sequence(ts, wfm_funcs, wfm_channels, awg, loop = False, drive = 'c:', path = '\\waveforms', clock = 1200e6, reset = True, marker=None):
	'''
		set awg to sequence mode and push a number of waveforms into the sequencer
		
		for the 6GS/s AWG, the waveform length must be divisible by 64
		for the 1.2GS/s AWG, it must be divisible by 4
	'''
	qt.mstart()
	#awg_say = awg._ins._visainstrument.write
	#awg_ask = awg._ins._visainstrument.ask
	starttime=time.time() ##Andre
	# create new sequence
	if(reset):
		awg.set_runmode('SEQ')
		awg.set_seq_length(0) #awg_say('SEQ:LENG %d'%(0)) # clear sequence
		awg.set_seq_length(len(ts)) #awg_say('SEQ:LENG %d'%(len(ts))) # create empty sequence

	# update all channels and times
	for i in range(len(wfm_funcs)):
		wfm_func = wfm_funcs[i]
		wfm_channel = wfm_channels[i]
		wfm_samples_prev = None
		for ti in range(len(ts)):
			qt.msleep()
			t = ts[ti]
			# filter duplicates
			wfm_samples = wfm_func(t)
			if(np.array_equal(wfm_samples, wfm_samples_prev)):
				# waveform was seen before: just set it in the sequencer
				pass
			else:
				# waveform is new: upload to awg
				wfm_samples_prev = wfm_samples
				wfm_fn = 'ch%d_t%05d'%(wfm_channel, ti) # filename is kept until changed
				wfm_pn = '%s%s\\%s'%(drive, path, wfm_fn)
				# this results in "low" when the awg is stopped and "high" when it is running 
				
				if marker==None:
					marker1 = np.array([int(0) for j in range(len(wfm_samples))])
					marker2 = np.array([int(0) for j in range(len(wfm_samples))])
					#make the markers at least 3 ns
					#marker samples
					m_sam = int(clock*3e-9)
					for j in range(m_sam):
						marker1[1+j] = int(1)
						marker2[len(wfm_samples)-1-j] = int(1)
				else: #or set your own markers
					if marker == "none":
						marker1 = np.array([int(0) for j in range(len(wfm_samples))])
						marker2 = np.array([int(0) for j in range(len(wfm_samples))])
					else:
						marker1,marker2 = marker[i]
				
				#this was the old marker def
##				marker = np.ones(wfm_samples.shape, np.int)
##				marker[-1] = 0
				awg.wfm_send(wfm_samples, marker1, marker2, wfm_pn, clock)
				awg.wfm_import(wfm_fn, wfm_pn, 'WFM')
				#awg.send_waveform(wfm_samples, marker, marker, wfm_pn, clock)
				#awg_say('MMEM:IMP "%s", "%s", WFM'%(wfm_fn, wfm_pn)) # import wfm into list
				# assign waveform to channel/time slot
			awg.wfm_assign(wfm_channel, ti+1, wfm_fn)
			#awg_say('SEQ:ELEM%d:WAV%d "%s"'%(ti+1, wfm_channel, wfm_fn))
			if(loop): awg.set_seq_loop(ti+1, np.infty) # awg_say('SEQ:ELEM%d:LOOP:INF '%(ti, int(loop)))
			if (ti<10 or ti%10==0):
				print "(%i/%i) ETA: %s"%(ti+i*len(ts),len(ts)*len(wfm_funcs),time.ctime( starttime+(time.time()-starttime)/(ti+i*len(ts)+1)*len(ts)*len(wfm_funcs)))
			#awg_say('SEQ:ELEM%d:JTAR:TYPE %s'%(ti, 'IND'))
			#awg_say('SEQ:ELEM%d:JTAR:IND %d'%(ti, 1))
			#awg_say('SEQ:ELEM%d:GOTO:IND %d'%(ti, 1))

	if(reset):
		# set up looping
		awg.set_seq_goto(len(ts), 1)
		#awg_say('SEQ:ELEM%d:GOTO:STAT %d'%(len(ts), 1))
		#awg_say('SEQ:ELEM%d:GOTO:IND %d'%(len(ts), 1))
		
		# enable channels
		try:
			time.sleep(0.1)
			for channel in wfm_channels:
				ch_state = 0
				while(ch_state == 0):
					#getattr(awg, 'set_ch%d_status'%channel)('on')
					#awg.wait()
					#if(getattr(awg, 'get_ch%d_status'%channel)() != 'on'):
					ch_state = int(awg_ask(':OUTP%d 1; *WAI; :OUTP%d?'%(channel, channel)))
					if(ch_state != 1):
						print 'failed to enable awg channel %d.'%channel
						time.sleep(0.1)
		except:
			pass
	
		# start awg
		awg.run()
		awg.wait(10,False)
	qt.mend()
	#'SEQ:ELEM%d:LOOP:COUN %d'%(idx, 1)
	#'SEQ:ELEM%d:TWAI %d'%(idx, 1)

def awg_update_2D_sequence(ts, wfm_func, awg, loop = False, drive = 'c:', path = '\\waveforms', clock = 1200e6, reset = True, marker=None): #@andre20150318
	'''
		set awg to sequence mode and push a number of waveforms into the sequencer
		
		wfm_func has to be a tuple of two wfms, for ch1 resp ch2
		
		for the 6GS/s AWG, the waveform length must be divisible by 64
		for the 1.2GS/s AWG, it must be divisible by 4
	'''
	qt.mstart()
	#awg_say = awg._ins._visainstrument.write
	#awg_ask = awg._ins._visainstrument.ask
	# create new sequence
	if(reset):
		awg.set_runmode('SEQ')
		awg.set_seq_length(0) #awg_say('SEQ:LENG %d'%(0)) # clear sequence
		awg.set_seq_length(len(ts)) #awg_say('SEQ:LENG %d'%(len(ts))) # create empty sequence

	# update all channels and times

	wfm_samples_prev = [None,None]
	wfm_fn = [None,None]
	wfm_pn = [None,None]
	starttime=time.time() ##Andre
	for ti in range(len(ts)):
		qt.msleep()
		t = ts[ti]
		# filter duplicates
		wfm_samples = wfm_func(t)
		
		for chan in (0,1):
			if(np.array_equal(wfm_samples[chan], wfm_samples_prev[chan])):
				# waveform was seen before: just set it in the sequencer
				pass
			else:
				# waveform is new: upload to awg
				wfm_samples_prev[chan] = wfm_samples[chan]
				wfm_fn[chan] = 'ch%d_t%05d'%(chan+1, ti) # filename is kept until changed
				wfm_pn[chan] = '%s%s\\%s'%(drive, path, wfm_fn[chan])
				# this results in "low" when the awg is stopped and "high" when it is running 
				
				if marker==None:
					marker1 = np.array([int(0) for j in range(len(wfm_samples[chan]))])
					marker2 = np.array([int(0) for j in range(len(wfm_samples[chan]))])
					#make the markers at least 3 ns
					#marker samples
					m_sam = int(clock*3e-9)
					for j in range(m_sam):
						marker1[1+j] = int(1)
						marker2[len(wfm_samples[chan])-1-j] = int(1)
				else: #or set your own markers
					if marker == "none":
						marker1 = np.array([int(0) for j in range(len(wfm_samples[chan]))])
						marker2 = np.array([int(0) for j in range(len(wfm_samples[chan]))])
					else:
						marker1,marker2 = marker[chan]
				
				#this was the old marker def
	##				marker = np.ones(wfm_samples.shape, np.int)
	##				marker[-1] = 0
				awg.wfm_send(wfm_samples[chan], marker1, marker2, wfm_pn[chan], clock)
				awg.wfm_import(wfm_fn[chan], wfm_pn[chan], 'WFM')
				#awg.send_waveform(wfm_samples, marker, marker, wfm_pn, clock)
				#awg_say('MMEM:IMP "%s", "%s", WFM'%(wfm_fn, wfm_pn)) # import wfm into list
				# assign waveform to channel/time slot
			awg.wfm_assign(chan+1, ti+1, wfm_fn[chan])
			#awg_say('SEQ:ELEM%d:WAV%d "%s"'%(ti+1, wfm_channel, wfm_fn))
			if(loop): awg.set_seq_loop(ti+1, np.infty) # awg_say('SEQ:ELEM%d:LOOP:INF '%(ti, int(loop)))
			if (ti<3 or (ti%10==9 and chan==1)):
				print "(%i/%i) ETA: %s"%(ti*2+chan+1,len(ts)*2,time.ctime( starttime+(time.time()-starttime)/(ti*2+chan+1)*len(ts)*2))
			#awg_say('SEQ:ELEM%d:JTAR:TYPE %s'%(ti, 'IND'))
		#awg_say('SEQ:ELEM%d:JTAR:IND %d'%(ti, 1))
		#awg_say('SEQ:ELEM%d:GOTO:IND %d'%(ti, 1))
	print "Done: ",time.ctime()

	if(reset):
		# set up looping
		awg.set_seq_goto(len(ts), 1)
		#awg_say('SEQ:ELEM%d:GOTO:STAT %d'%(len(ts), 1))
		#awg_say('SEQ:ELEM%d:GOTO:IND %d'%(len(ts), 1))
		
		# enable channels
		try:
			time.sleep(0.1)
			for channel in wfm_channels:
				ch_state = 0
				while(ch_state == 0):
					#getattr(awg, 'set_ch%d_status'%channel)('on')
					#awg.wait()
					#if(getattr(awg, 'get_ch%d_status'%channel)() != 'on'):
					ch_state = int(awg_ask(':OUTP%d 1; *WAI; :OUTP%d?'%(channel, channel)))
					if(ch_state != 1):
						print 'failed to enable awg channel %d.'%channel
						time.sleep(0.1)
		except:
			pass
	
		# start awg
		awg.run()
		awg.wait(10,False)
	qt.mend()
	#'SEQ:ELEM%d:LOOP:COUN %d'%(idx, 1)
	#'SEQ:ELEM%d:TWAI %d'%(idx, 1)


def awg_update_single_optics(wfm_funcs, wfm_channels, awg, clock = 1000e6, marker=None):
	'''
		this one can only output single waveforms but on two channels
		
		works only for the optiawg, unfortunately
	'''

	for wfm_channel in wfm_channels:
		if wfm_channel==1:
			awg.set_ch1_status("off")
			awg.set_ch1_state("stop")
		if wfm_channel==2:
			awg.set_ch2_status("off")
			awg.set_ch2_state("stop")
			
	awg.set_numpoints(len(wfm_funcs[0]))
	
	# update all channels and times
	for i in range(len(wfm_funcs)):
		wfm_func = wfm_funcs[i]
		wfm_channel = wfm_channels[i]
		
		numpoints = len(wfm_func)

		if marker==None:
			marker1 = np.array([int(0) for i in range(numpoints)])
			marker2 = np.array([int(0) for i in range(numpoints)])
			marker1[1] = int(1)
			marker1[2] = int(1)
			marker1[3] = int(1)
			marker2[numpoints-1] = int(1)
			marker2[numpoints-2] = int(1)
			marker2[numpoints-3] = int(1)
		else:
			marker1,marker2 = marker[i]
		filename = 'wfm_ch%d.wfm'%(wfm_channel) # filename is kept until changed
		#awg.delete_file(filename)
		awg.send_waveform(wfm_func,marker1,marker2,filename,clock)
		if wfm_channel==1:
			awg.set_ch1_setfilename(filename)
		if wfm_channel==2:
			awg.set_ch2_setfilename(filename)


	awg.set_ch1_state("run")
	for wfm_channel in wfm_channels:
		if wfm_channel==1:
			awg.set_ch1_status("on")
		if wfm_channel==2:
			awg.set_ch2_status("on")






def awg_gate_fcn(state, awg, pulser = None, ni_daq = None, ni_daq_ch = 'PFI0:0'):
	if(pulser == None and ni_daq == None): raise Exception('either pulser or ni_daq must be given')
	awg_say = awg._ins._visainstrument.write
	if(state):
		time.sleep(0.1)
		if(pulser != None):
			pulser._ins._visainstrument.write(':INIT:CONT 1')
		if(ni_daq != None):
			ni_daq.digital_out(ni_daq_ch, 1)
	else:
		#awg._ins._visainstrument.write('SEQ:JUMP %d'%(1)) # jump to start
		#pulser._ins._visainstrument.write('OUTP1 OFF; OUTP2 OFF;')
		# disable pulser
		if(pulser != None):
			pulser._ins._visainstrument.write(':INIT:CONT 0')
		if(ni_daq != None):
			ni_daq.digital_out(ni_daq_ch, 0)
		time.sleep(0.025)
		#awg._ins._visainstrument.write('SEQ:JUMP %d'%(1)) # jump to start
		# dirty jump to first entry
		awg._ins._visainstrument.ask(':AWGC:STOP; *WAI; :AWGC:RUN; *WAI; *STB?')

		# workaround for jump to first entry
		seq_len = awg.get_seq_length()
		seq_pos = awg.get_seq_position() # no, this is not redundant
		seq_pos = awg.get_seq_position()
		seq_it = 0
		while (seq_pos != 1):
			# count number of tries
			if(seq_it % 5 == 4):
				print 'awg did not reset to first waveform after %d attempts.'%(seq_it+1) 
			seq_it += 1

			awg._ins._visainstrument.ask(':AWGC:STOP; *WAI; :AWGC:RUN; *WAI; *STB?')
			time.sleep(0.05*seq_it)
			
			#awg._ins._visainstrument.write('SEQ:ELEM%d:GOTO:STAT %d'%(seq_pos, 1))
			#if(seq_pos < seq_len):
			#	time.sleep(0.05)
			#	awg._ins._visainstrument.write('SEQ:ELEM%d:GOTO:STAT %d; *WAI'%(seq_pos, 0))
			#time.sleep(0.025)
			try:
				seq_pos = awg.get_seq_position() # no, this is not redundant
				seq_pos = awg.get_seq_position()
			except:
				print('awg does not respond')
				time.sleep(0.1)
				seq_pos = -1
		else:
			if(seq_it > 4):
				print 'awg reached first waveform after %d iterations.'%seq_it
			else:
				pass
				#print 'awg is already at 1.'

	