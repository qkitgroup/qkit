import qt
import numpy as np
import os.path
import time
import logging
import numpy
import sys
import Progress_Bar
import gc


def update(t, wfm_funcs, wfm_channels, sample, drive = 'c:', path = '\\waveforms'):
	'''
		simultaneously perform different experiments on multiple qubits using an awg

		Input:
			t - parameter for wfm_funcs
			wfm_funcs - callable function of 1 parameter that generate waveforms
			wfm_channels - awg channels the waveforms are assigned to
			sample - the Sample instance, where awg and clock are defined
	'''
	awg = sample.get_awg()
	clock = sample.get_clock()
	for i in range(len(wfm_funcs)):
		wfm_func = wfm_funcs[i]
		wfm_channel = wfm_channels[i]
		wfm_samples = wfm_func(t,sample)
		wfm_fn = 'ch%d'%wfm_channel
		marker = np.zeros(wfm_samples.shape, np.int)
		awg.send_waveform(wfm_samples, marker, marker, '%s%s\\%s'%(drive, path, wfm_fn), clock)
		awg.load_waveform(wfm_channel, wfm_fn, drive, path)
	#awg.run() # necessary?



def update_sequence(ts, wfm_funcs, wfm_channels, sample, loop = False, drive = 'c:', path = '\\waveforms', reset = True, marker=None):
	'''
		set awg to sequence mode and push a number of waveforms into the sequencer
		
		for the 6GS/s AWG, the waveform length must be divisible by 64
		for the 1.2GS/s AWG, it must be divisible by 4
	'''
	qt.mstart()
	awg = sample.get_awg()
	clock = sample.get_clock()
	
	#awg_say = awg._ins._visainstrument.write
	#awg_ask = awg._ins._visainstrument.ask
	p = Progress_Bar.Progress_Bar(len(wfm_funcs)*len(ts))
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
			wfm_samples = wfm_func(t, sample)
			#print wfm_samples
			wfm_fn = 'ch%d_t%05d'%(wfm_channel, ti) # filename is kept until changed
			wfm_pn = '%s%s\\%s'%(drive, path, wfm_fn)
			# this results in "low" when the awg is stopped and "high" when it is running 
			
			if marker == None:
				marker1 = np.zeros_like(wfm_samples)
				marker2 = np.zeros_like(wfm_samples)
				
				'''
				marker1 = np.array([int(0) for j in range(len(wfm_samples[chan]))])
				marker2 = np.array([int(0) for j in range(len(wfm_samples[chan]))])
				#make the markers at least 3 ns
				#marker samples
				m_sam = int(clock*3e-9)
				for j in range(m_sam):
					marker1[1+j] = int(1)
					marker2[len(wfm_samples[chan])-1-j] = int(1)
				'''
			else: #or set your own markers
				c_marker1, c_marker2 = marker   #JB 04/2015
				marker1 = c_marker1[ti]
				marker2 = c_marker2[ti]
			
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
			p.iterate()
			#awg_say('SEQ:ELEM%d:JTAR:TYPE %s'%(ti, 'IND'))
			#awg_say('SEQ:ELEM%d:JTAR:IND %d'%(ti, 1))
			#awg_say('SEQ:ELEM%d:GOTO:IND %d'%(ti, 1))

	if(reset):
		# set up looping
		try:
			for channel in wfm_channels:
				awg.set('ch%i_status'%channel,'on')
		except:
			pass
		awg.set_seq_goto(len(ts), 1)
		awg.run()
		awg.wait(10,False)
		
	qt.mend()
	return np.all([awg.get('ch%i_status'%i)=='on' for i in wfm_channels])


def update_2D_sequence(ts, wfm_func, sample, loop = False, drive = 'c:', path = '\\waveforms', reset = True, marker=None): #@andre20150318
	'''
		set awg to sequence mode and push a number of waveforms into the sequencer
		
		wfm_func has to be a tuple of two wfms, for ch1 resp ch2
		
		for the 6GS/s AWG, the waveform length must be divisible by 64
		for the 1.2GS/s AWG, it must be divisible by 4
	'''
	qt.mstart()
	awg = sample.get_awg()
	clock = sample.get_clock()
	
	#awg_say = awg._ins._visainstrument.write
	#awg_ask = awg._ins._visainstrument.ask
	# create new sequence
	if(reset):
		awg.set_runmode('SEQ')
		awg.set_seq_length(0) #awg_say('SEQ:LENG %d'%(0)) # clear sequence
		awg.set_seq_length(len(ts)) #awg_say('SEQ:LENG %d'%(len(ts))) # create empty sequence
		awg.set_ch1_offset(0)
		awg.set_ch2_offset(0)
		awg.set_ch1_amplitude(2)
		awg.set_ch2_amplitude(2)

	# update all channels and times

	wfm_samples_prev = [None,None]
	wfm_fn = [None,None]
	wfm_pn = [None,None]
	p = Progress_Bar.Progress_Bar(len(ts)*2)
	for ti in range(len(ts)):
		qt.msleep()
		t = ts[ti]
		# filter duplicates
		wfm_samples = wfm_func(t,sample)
		
		for chan in (0,1):
			wfm_fn[chan] = 'ch%d_t%05d'%(chan+1, ti) # filename is kept until changed
			wfm_pn[chan] = '%s%s\\%s'%(drive, path, wfm_fn[chan])
			# this results in "low" when the awg is stopped and "high" when it is running 
			
			if marker == None:
				marker1, marker2 = np.zeros_like(wfm_samples)
				'''
				marker1 = np.array([int(0) for j in range(len(wfm_samples[chan]))])
				marker2 = np.array([int(0) for j in range(len(wfm_samples[chan]))])
				#make the markers at least 3 ns
				#marker samples
				m_sam = int(clock*3e-9)
				for j in range(m_sam):
					marker1[1+j] = int(1)
					marker2[len(wfm_samples[chan])-1-j] = int(1)
				'''
			else: #or set your own markers
				c_marker1, c_marker2 = marker[chan]   #JB 04/2015
				marker1 = c_marker1[ti]
				marker2 = c_marker2[ti]
			
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
			p.iterate()
			#awg_say('SEQ:ELEM%d:JTAR:TYPE %s'%(ti, 'IND'))
		#awg_say('SEQ:ELEM%d:JTAR:IND %d'%(ti, 1))
		#awg_say('SEQ:ELEM%d:GOTO:IND %d'%(ti, 1))
		gc.collect()

	if(reset):
		# set up looping
		
		
		# enable channels
		awg.set_ch1_status('on')
		awg.set_ch2_status('on')
		awg.set_seq_goto(len(ts), 1)
		awg.run()
		awg.wait(10,False)
		
		
	qt.mend()
	return np.all([awg.get('ch%i_status'%i)=='on' for i in [1,2]])
