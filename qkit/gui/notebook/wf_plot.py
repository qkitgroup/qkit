'''
wafeform plotter JB@KIT 02/2016 jochen.braumueller@kit.edu

The waveform plotter wf_plot.py visualizes the waveform generated and employed for a measurement.
Prospectively, the plotter may be called by default to save a picture of the pulse sequence.

input: list of waveforms
output: -
'''

'''
+++ Sample marker waveform  +++

zmarker = []
for t in ts:
    zmarker.append(gwf.square(p_idle_time*1e-9 + qubit.tpi + t_idle_after_exc*1e-9, qubit, 
                    position = qubit.exc_T - qubit.overlap*1e-9 - t*1e-6 - t_idle*1e-9)
                   + gwf.square(1e-9*t_idle + qubit.readout_tone_length + t_after_readout, qubit, 
                    position = qubit.exc_T - qubit.overlap*1e-9 + qubit.readout_tone_length + t_after_readout))
zeromarker = np.zeros_like(zmarker)
complete_marker = [[zmarker,zeromarker],[zeromarker,zeromarker]]
complete_zero_marker = [[zeromarker,zeromarker],[zeromarker,zeromarker]]

load_awg.update_sequence(qubit.overlap*1e-9 + 1e-9*t_idle + ts*1e-6, gwf.t1, qubit, iq, marker = complete_marker)
'''

import numpy as np
import matplotlib.pyplot as plt
#import os, glob
import time
import logging

no_qt = False
try:
	import qt
	data_dir_config = qt.config.get('datadir')
except ImportError:
	logging.warning('no qtLAB environment')
	no_qt = True

def wfplot(analog_wfm, seq = 1, complete_marker = None, x_range = None, sample = None):

	font = {'weight' : 'normal', 'size' : 16}
	plt.rc('font', **font)
	labelsize=16
	fig, axis = plt.subplots(figsize=(15,5))

	#extract x axis information
	if sample != None:
		xval = np.linspace(0,sample.exc_T*1e6,int(np.round(sample.exc_T*sample.clock)/4)*4)   #in us
		axis.set_xlabel(r'$time\,(\mathrm{\mu s})$', fontsize=labelsize)
		
		try:
			t = np.arange(0,sample.readout_tone_length,1/sample.readout_clock)
			r1 = np.sin(2*np.pi*t*sample.readout_iq_frequency)
			r2 = np.cos(2*np.pi*t*sample.readout_iq_frequency)
			axis.plot((sample.exc_T-sample.overlap*1e-9)*1e6+range(len(r1)),r1, 'black')
			axis.plot((sample.exc_T-sample.overlap*1e-9)*1e6+range(len(r1)),r2, 'black')
		except:
			logging.warning('readout pulse not plotted: sample parameters not found')
	else:
		axis.set_xlabel('# samples', fontsize=labelsize)
		if isinstance(analog_wfm[seq][0],(list, tuple, np.ndarray)):   #heterodyne mode
			xval = np.arange(0,len(analog_wfm[seq][0]))
		else:
			xval = np.arange(0,len(analog_wfm[seq]))
	
	if isinstance(analog_wfm[seq][0],(list, tuple, np.ndarray)):   #heterodyne mode
		axis.plot(xval,analog_wfm[seq][0], 'red', alpha = 0.7, label='I')
		axis.plot(xval,analog_wfm[seq][1], 'blue', alpha = 0.7, label='Q')
	else:
		axis.fill_between(xval,0,analog_wfm[seq], color='red', alpha=0.7)
		axis.plot(xval,analog_wfm[seq], 'r-', alpha=0.7, label = 'homodyne')
	
	if complete_marker != None:
		clr_dict = {0 : 'grey', 1 : 'magneta', 2 : 'green', 3 : 'tan'}
		if len(np.array(complete_marker).shape) > 2:   #more than one single marker
			markers = np.array(complete_marker).reshape(4,np.array(complete_marker).shape[2],np.array(complete_marker).shape[3])
		else:
			markers = [np.array(complete_marker)]
		
		maxis = axis.twinx()
		for mi, m in enumerate(markers):
			if (m != np.zeros_like(m)).any() and m != None:
				maxis.fill_between(xval, 0, float(4-mi)/2*m[seq], color = clr_dict[mi], alpha = 0.7)
				maxis.plot(xval, float(4-mi)/2*m[seq], color = clr_dict[mi], alpha = 0.7, label = 'm%d'%mi)
		maxis.legend(loc = 1)
				
	axis.legend(loc = 2)
	if xrange != None:
		plt.xlim(x_range)
	fig.tight_layout()
