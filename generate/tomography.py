import qt
import numpy as np
import os.path
import time
import logging
import numpy
import sys, gc
import Progress_Bar
import generate.load_awg as load_awg
import generate.generate_waveform as gwf

iq = qt.instruments.get('iq')
print gc.collect()

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
	
def radial(thetas, phis, wfm, sample):
	angles=[[0,0]]
	for i,th in enumerate(thetas):
		angles=np.append(angles,np.array([np.ones(phis[i])*th,np.linspace(0,2*np.pi,phis[i],endpoint=False)]).T,axis=0)
	angles=angles[1:]
	print "You have a tomography resolution of %i points"%len(angles)
	if not os.path.exists(qt.config.get('datadir')+time.strftime("\\%Y%m%d")):
		os.makedirs(qt.config.get('datadir')+time.strftime("\\%Y%m%d"))
	np.savetxt(qt.config.get('datadir')+time.strftime("\\%Y%m%d\\Tomography_%H%M%S.set"),angles)
	sample.update_instruments()
	#wfm2 = append_wfm(wfm,gwf.square(angles[t][0]/np.pi*sample.tpi, sample, angles[t][0]/np.pi*sample.tpi)*np.exp(1j*angles[t][1]))
	#wfm2 = iq.convert(append_wfm(wfm,gwf.square(angles[0][0]/np.pi*sample.tpi, sample, angles[0][0]/np.pi*sample.tpi)*np.exp(1j*angles[0][1])),sample)
	#print wfm2
	#qt.msleep(2)
	load_awg.update_2D_sequence(range(len(angles)), lambda t, sample2: iq.convert(append_wfm(wfm,gwf.square(angles[t][0]/np.pi*sample.tpi, sample, angles[t][0]/np.pi*sample.tpi)*np.exp(1j*angles[t][1]))), sample)

### Use like this:
# thetas = np.linspace(0,2*np.pi, 20)
# phis = [1]+(len(thetas)-1)*[15] #for 15 steps in phi direction (but 0 rotation has only 1 pulse)
# gt.radial(thetas, phis, gwf.square(qubit.tpi, qubit), qubit)
