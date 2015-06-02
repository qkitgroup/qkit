import qt
import numpy as np
import os.path
import time
import logging
import numpy
import sys, gc
#from gui.notebook.Progress_Bar import Progress_Bar
import qkit.measure.timedomain.awg.load_awg as load_awg
import qkit.measure.timedomain.awg.generate_waveform as gwf

iq = qt.instruments.get('iq')
gc.collect()

def concatenate_pulses(pulse_durations,phases, positions,sample):
    '''
        generate waveform with varoius pulses

        Input:
            pulse_durations - 1d array of pulse lengths (in s)
            phases - 1d array of phases of the pulses (in rad)
            positions - 1d array of the pulse position, measured in s from the end of the pulse to the end of the wfm (smallest distance)
        NOTE that all input arrays have to be of the same length!
        
            length - length of the wfm (in s), also known as exc_T
        
        Output:
            (complex) float array of samples
    '''
    if not(len(pulse_durations)==len(phases) and len(phases)==len(positions)):
        raise ValueError("Input Arrays do not have the same size: pulse_durations: %i, phases: %i, positions: %i"%
            (len(pulse_durations),len(phases),len(positions)))
    
    #if(pulses*(delay+pi2_x_pulse)-delay > length): logging.error(__name__ + ' : x-pulses do not fit into waveform')
    
    phases=np.exp(1j*np.array(phases))

    wfm = np.zeros_like(gwf.square(0, sample),dtype=np.complex)    

    for i in range(len(pulse_durations)):
        wfm += gwf.square(pulse_durations[i], sample, position= length-positions[i])*phases[i]
    return wfm
	
def append_wfm(large_wfm, appendix):
	return np.append(large_wfm[len(appendix):],appendix)
	

def length(thetas, phis, wfm = None, sample = None):
	'''
		returns the number of tomography steps.
		You will need this for your measurement.
	'''
	angles=[[0,0]]
	for i,th in enumerate(thetas):
		angles=np.append(angles,np.array([np.ones(phis[i])*th,np.linspace(0,2*np.pi,phis[i],endpoint=False)]).T,axis=0)
	angles=angles[1:]
	return len(angles)
	
def radial(thetas, phis, wfm, sample, marker = None, delay = 0, markerfunc = None):
	angles=[[0,0]]
	for i,th in enumerate(thetas):
		angles=np.append(angles,np.array([np.ones(phis[i])*th,np.linspace(0,2*np.pi,phis[i],endpoint=False)]).T,axis=0)
	angles=angles[1:]
	if not os.path.exists(qt.config.get('datadir')+time.strftime("\\%Y%m%d")):
		os.makedirs(qt.config.get('datadir')+time.strftime("\\%Y%m%d"))
	np.savetxt(qt.config.get('datadir')+time.strftime("\\%Y%m%d\\Tomography_%H%M%S.set"),angles)
	sample.update_instruments()
	if marker == None:
		new_marker = None
	else:
		new_marker = [[],[],[],[]]
		if marker.shape[0] == 4: #each marker is defined
			for i in range(len(marker)):
				new_marker[i] = [ append_wfm(marker[i],np.zeros_like(gwf.square(0, sample, angle[0]/np.pi*sample.tpi + delay))) for angle in angles ]
		else:
			new_marker[0] = [ append_wfm(marker,np.zeros_like(gwf.square(0, sample,  angle[0]/np.pi*sample.tpi + delay))) for angle in angles ]
			new_marker[1:4]=[ np.zeros_like(new_marker[0]) for i in range(3) ]
		new_marker = [[new_marker[0],new_marker[1]],[new_marker[2],new_marker[3]]]
	result = load_awg.update_2D_sequence(range(len(angles)), lambda t, sample2: iq.convert(append_wfm(wfm,gwf.square(angles[t][0]/np.pi*sample.tpi, sample, angles[t][0]/np.pi*sample.tpi + delay)*np.exp(1j*angles[t][1]))), sample, marker = new_marker, markerfunc=markerfunc)
	print "You have a tomography resolution of %i points"%len(angles)
	return result

### Use like this:
# thetas = np.linspace(0,2*np.pi, 20)
# phis = [1]+(len(thetas)-1)*[15] #for 15 steps in phi direction (but 0 rotation has only 1 pulse)
# gt.radial(thetas, phis, gwf.square(qubit.tpi, qubit), qubit)

def threepoint(ts, wfm_func, sample, loop = False, drive = 'c:', path = '\\waveforms', reset = True, marker=None, markerfunc = None):
	#marker stuff
	wfm = [ append_wfm(wfm_func(t,sample),gwf.square(sample.tpi2,sample,sample.tpi2)*phase) for phase in [0,1,1j] for t in ts]
	#ts = np.array([ts,ts,ts]).flatten()
	ts = range(3*len(ts))
	if marker!= None:
		marker = np.append(np.append(marker,marker,axis=2),marker,axis=2)
	return load_awg.update_2D_sequence(ts, lambda t, sample: iq.convert(wfm[t]), sample, loop = loop, drive = drive, path = path, reset = reset, marker=marker ,markerfunc=markerfunc)