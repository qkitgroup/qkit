import qt
import numpy as np
import os.path
import time
import logging
import numpy
import sys
from qkit.gui.notebook.Progress_Bar import Progress_Bar
import gc
#from qkit.measure.timedomain.awg import generate_waveform as gwf


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


def update_sequence(ts, wfm_func, sample, loop = False, drive = 'c:', path = '\\waveforms', reset = True, marker=None, markerfunc=None): #@andre20150318
	'''
		set awg to sequence mode and push a number of waveforms into the sequencer
		
		inputs:
		
		ts: array of times, len(ts) = #sequenzes
		wfm_func: waveform function usually generated via generate_waveform using ts[i]; this can be a touple of arrays (for channels 0,1, heterodyne mode) or a single array (homodyne mode)
		sample: sample object
		
		marker: marker array in the form [[ch1m1,ch1m2],[ch2m1,ch2m2]] and all entries arrays of sample length
		markerfunc: analog to wfm_func, set marker to None when used
		
		for the 6GS/s AWG, the waveform length must be divisible by 64
		for the 1.2GS/s AWG, it must be divisible by 4
	'''
	qt.mstart()
	awg = sample.get_awg()
	clock = sample.get_clock()
	
	# create new sequence
	if reset:
		awg.set_runmode('SEQ')
		awg.set_seq_length(0)   #clear sequence, necessary?
		awg.set_seq_length(len(ts))   #create empty sequence
		
		#amplitude settings of analog output
		awg.set_ch1_offset(0)
		awg.set_ch2_offset(0)
		awg.set_ch1_amplitude(2)
		awg.set_ch2_amplitude(2)

	#generate empty tuples
	wfm_samples_prev = [None,None]
	wfm_fn = [None,None]
	wfm_pn = [None,None]
	p = Progress_Bar(len(ts)*2)   #init progress bar
	
	#update all channels and times
	for ti in range(len(ts)):   #run through all sequences
		qt.msleep()
		t = ts[ti]
		# filter duplicates
		wfm_samples = wfm_func(t,sample)   #generate waveform
		if not isinstance(wfm_samples[0],(list, tuple, np.ndarray)):   #homodyne
			wfm_samples = [wfm_samples]
		
		for chan in [0,1]:
			if markerfunc != None:   #use markerfunc
				try:
					if markerfunc[chan][0] == None:
						marker1 = np.zeros_like(wfm_samples, dtype=np.int8)[0]
					else:
						marker1 = markerfunc[chan][0](t,sample)
					
					if markerfunc[chan][1] == None:
						marker2 = np.zeros_like(wfm_samples, dtype=np.int8)[0]
					else:
						marker2 = markerfunc[chan][1](t,sample)
				
				except TypeError:   #only one markerfunc given
					marker1, marker2 = np.zeros_like(wfm_samples, dtype=np.int8)
					if chan == 0:
						marker1 = markerfunc(t,sample)
					
			elif marker == None:   #fill up with zeros
				marker1, marker2 = np.zeros_like(wfm_samples, dtype=np.int8)
			else: #or set your own markers
				c_marker1, c_marker2 = marker[chan]
				marker1 = c_marker1[ti]
				marker2 = c_marker2[ti]
				
			wfm_fn[chan] = 'ch%d_t%05d'%(chan+1, ti) # filename is kept until changed
			if len(wfm_samples) == 1 and chan == 1:
				wfm_pn[chan] = '%s%s\\%s'%(drive, path, np.zeros_like(wfm_fn[0]))   #create empty array
				awg.wfm_send(np.zeros_like(wfm_samples[0]), marker1, marker2, wfm_pn[chan], clock)
			else:
				wfm_pn[chan] = '%s%s\\%s'%(drive, path, wfm_fn[chan])
				#this results in "low" when the awg is stopped and "high" when it is running
				awg.wfm_send(wfm_samples[chan], marker1, marker2, wfm_pn[chan], clock)
			
			awg.wfm_import(wfm_fn[chan], wfm_pn[chan], 'WFM')
			
			# assign waveform to channel/time slot
			awg.wfm_assign(chan+1, ti+1, wfm_fn[chan])
			
			if(loop):
				awg.set_seq_loop(ti+1, np.infty)
			p.iterate()

		#gc.collect()

	if reset:
		# enable channels
		awg.set_ch1_status('on')
		awg.set_ch2_status('on')
		awg.set_seq_goto(len(ts), 1)
		awg.run()
		awg.wait(10,False)
		
		
	qt.mend()
	return np.all([awg.get('ch%i_status'%i)=='on' for i in [1,2]])
