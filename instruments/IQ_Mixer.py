#Toolset for calibrating and using IQ-Mixers as Single-Sideband-Mixers (SSB)
#Started by Andre Schneider 01/2015 <andre.schneider@student.kit.edu>

from instrument import Instrument
import time
import types
import logging
import qt
import numpy as np
import matplotlib.pyplot as plt
import sys
from copy import copy

class IQ_Mixer(Instrument):

	def __init__(self, name, sample, mixer_name):
		Instrument.__init__(self,name,tags=['virtual'])
		self._sample = sample
		self._FSUP_connected = False
		self._fsup = None
		self.maxage = 360 * 48 * 3600 # Age of calibration data in seconds
		self.interpol_freqspan = 2e9 #Frequency span where interpolated data is used and recalibrated
		self.trust_region = 10e9    #Frequency span where interpolated data is used without recalibration. Do not set this to zero, because calibration will round frequency
		#self._iq_frequency = self._sample.iq_frequency
		self.mixer_name = mixer_name
		
		#Parameters
		self.add_parameter('sideband_frequency', type=types.FloatType,
			flags=Instrument.FLAG_GET, units='Hz',
			minval=1, maxval=20e9)
		
		self.add_parameter('output_power', type=types.FloatType,
			flags=Instrument.FLAG_GET, units='dBm')
			
		self.add_parameter('iq_frequency', type=types.FloatType,
			flags=Instrument.FLAG_GET, units='Hz',
			minval=0, maxval=1e9) # This is only a get variable, because changing requires an update of all sequences in AWG
		
		self.add_parameter('FSUP_connected', type=types.BooleanType,
			flags=Instrument.FLAG_GET)
		
		self.add_function('connect_FSUP')
		self.add_function('disconnect_FSUP')
		#self.add_function(sdafsdfsdf)
	
	IQ0307 = 'IQ0307'  #simply define the currently known mixers so you can see them when pressing tab
	IQ0318 = 'IQ0318'

	
	_ch1_filename='ch1_opt'
	_ch2_filename='ch2_opt'
	_awg_filepath='C:\\waveforms\\'
	(x,y)=(0,0) #initial values for DC offset in Volts
	
	def ch1(self,t):
		return np.cos(t)
	def ch2(self,t):
		return np.sin(t)
		
	def do_get_FSUP_connected(self):
		return self._FSUP_connected
	
	def do_set_sideband_frequency(self,frequency):
		print "Nothing happens here"
		self._sideband_frequency=frequency
		
	def do_get_sideband_frequency(self):
		return self._sideband_frequency
		
	def do_set_output_power(self,power):
		print "Nothing happens here"
		self._output_power=power
		
	def do_get_output_power(self):
		return self._output_power
	
	def do_get_iq_frequency(self):
		'''This returns the iq_frequency which was used for the last call of convert()'''
		return self._iq_frequency
	
	
	def connect_FSUP(self, fsup):
		self._fsup = fsup
		self._FSUP_connected = True
	
	def disconnect_FSUP(self):
		self._FSUP_connected = False
	
	def dcoptimize(self, DC):
		#you need to have a zero-waveform loaded in the awg and turn outputs on!
		if(np.abs(DC[0])>.5 or np.abs(DC[1])>.5):
			qt.msleep()
			return 50
		self._sample.awg.set_ch1_offset(DC[0])
		self._sample.awg.set_ch2_offset(DC[1])
		#qt.msleep(.05)
		self._fsup.sweep()
		return np.around(self._fsup.get_marker_level(1),2) #assuming that marker1 is at leakage frequency
	def xoptimize(self, x):
		#you need to have a zero-waveform loaded in the awg and turn outputs on!
		if(np.abs(x)>.5):
			qt.msleep()
			return 50
		self._sample.awg.set_ch1_offset(x)
		self._fsup.sweep()
		return np.around(self._fsup.get_marker_level(1),2) #assuming that marker1 is at leakage frequency
	def yoptimize(self, y):
		#you need to have a zero-waveform loaded in the awg and turn outputs on!
		if(np.abs(y)>.5):
			qt.msleep()
			return 50
		self._sample.awg.set_ch2_offset(y)
		self._fsup.sweep()
		return np.around(self._fsup.get_marker_level(1),2) #assuming that marker1 is at leakage frequency
	"""
	def phaseoptimize(offset):
		'''
	   # phase offset in radians
		'''
		t=np.linspace(offset,offset+2*np.pi,clock/iq_freq,endpoint=False)
		ch1wfm=amp*ch1(t)
		marker=np.zeros_like(ch1wfm)
		self._sample.awg.wfm_send(ch1wfm,marker,marker,self._awg_filepath+self._ch1_filename,clock)
		self._sample.awg.wfm_import(self._ch1_filename,self._awg_filepath+self._ch1_filename,'WFM')
		self._sample.awg.set_ch1_waveform(self._ch1_filename)
		self._fsup.sweep()
		return self._fsup.get_marker_level(4) #assuming that marker4 is at unwanted sideband
	"""
	def relampoptimize(self, amp):
		self._sample.awg.set_ch1_amplitude(amp)
		self._fsup.sweep()
		return np.around(self._fsup.get_marker_level(4),2) #assuming that marker4 is at unwanted sideband
	
	def focus(self,frequency, marker):
		self._fsup.set_continuous_sweep_mode('off')
		self._fsup.set_centerfreq(frequency)
		self._fsup.set_freqspan(2e2)
		self._fsup.enable_marker(1,'OFF')
		self._fsup.enable_marker(2,'OFF')
		self._fsup.enable_marker(3,'OFF')
		self._fsup.enable_marker(4,'OFF')
		self._fsup.set_marker(marker,frequency)
		self._fsup.set_resolutionBW(200)
		self._fsup.set_videoBW(200)
		sweeptime=self._fsup.get_sweeptime()
		self._fsup.sweep()
		return sweeptime
	
	def load_zeros(self):
		ch1wfm=np.zeros(10)
		ch2wfm=np.zeros(10)
		marker=np.zeros_like(ch1wfm)
		self._sample.awg.wfm_send(ch1wfm,marker,marker,self._awg_filepath+self._ch1_filename,self._sample.clock)
		self._sample.awg.wfm_import(self._ch1_filename,self._awg_filepath+self._ch1_filename,'WFM')
		self._sample.awg.set_ch1_waveform(self._ch1_filename)
		self._sample.awg.set_ch1_offset(0)
		self._sample.awg.set_ch1_amplitude(1)
		self._sample.awg.wfm_send(ch2wfm,marker,marker,self._awg_filepath+self._ch2_filename,self._sample.clock)
		self._sample.awg.wfm_import(self._ch2_filename,self._awg_filepath+self._ch2_filename,'WFM')
		self._sample.awg.set_ch2_waveform(self._ch2_filename)
		self._sample.awg.set_ch2_offset(0)
		self._sample.awg.set_ch2_amplitude(1)
		self._sample.awg.run()
		self._sample.awg.set_ch1_output(1)
		self._sample.awg.set_ch2_output(1)
		
	def load_wfm_init(self):
		t=np.linspace(0,2*np.pi,self._sample.clock/self._sample.iq_frequency,endpoint=False)
		ch1wfm=self.ch1(t)
		ch2wfm=self.ch2(t)
		marker=np.zeros_like(ch1wfm)
		self._sample.awg.wfm_send(ch2wfm,marker,marker,self._awg_filepath+self._ch2_filename,self._sample.clock)
		self._sample.awg.wfm_import(self._ch2_filename,self._awg_filepath+self._ch2_filename,'WFM')
		self._sample.awg.set_ch2_waveform(self._ch2_filename)
		self._sample.awg.wfm_send(ch1wfm,marker,marker,self._awg_filepath+self._ch1_filename,self._sample.clock)
		self._sample.awg.wfm_import(self._ch1_filename,self._awg_filepath+self._ch1_filename,'WFM')
		self._sample.awg.set_ch1_waveform(self._ch1_filename)
		self._sample.awg.run()
		self._sample.awg.set_ch1_output(1)
		self._sample.awg.set_ch2_output(1)

	def optimize_dc(self,frequency,x,y,maxiter=10,verbose=False):
		self.focus(frequency,1)
		for i in range(0,maxiter):
			xold=x
			yold=y
			x=opt.minimize_scalar(lambda x:self.dcoptimize([x,y]),method='golden',tol=0.1).x
			if(verbose): print " %.3f  (%.3f) %.2fdBm"%(x,y,self.dcoptimize([x,y]))
			sys.stdout.flush()
			y=opt.minimize_scalar(lambda y:self.dcoptimize([x,y]),method='golden',tol=0.1).x
			if(verbose): print "(%.3f)  %.3f  %.2fdBm"%(x,y,self.dcoptimize([x,y]))
			sys.stdout.flush()
			if(np.around(xold-x,3)==0 and np.around(yold-y,3)==0):
				if(verbose): print "Finished after %i iterations with delta x: %.5f delta y: %.5f"%(i+1,xold-x,yold-y)
				break  
		return [x,y]

	def optimize_phase(self):
		self.focus(self._sample.f01 - 2* self._sample.iq_frequency,4)
		return opt.minimize_scalar(self.phaseoptimize,method="bounded",bounds=(0,2*np.pi),options={"xatol":.01}).x    
	def optimize_relamp(self):
		self.focus(self._sample.f01 - 2* self._sample.iq_frequency,4)
		return opt.minimize_scalar(self.relampoptimize,method="bounded",bounds=(0,2),options={"xatol":.001}).x

		
	def relampoptimize2(self,amp):
		self._sample.awg.set_ch2_amplitude(amp)
		self._fsup.sweep()
		return np.around(self._fsup.get_marker_level(4),2) #assuming that marker4 is at unwanted sideband

	def findmin(self, function,start,stop,stepsize,plot=False,averages=1):
		a=np.arange(start,stop+stepsize/2,stepsize)
		if(len(a)<2):
		   # print "*************TRYING TO MINIMIZE %s BETWEEN %f and %f => NOT POSSIBLE!*********"%(function,start,stop)
			return start
		b=np.zeros(len(a))
		for u,v in enumerate(a):
			 for i in range(averages):
				b[u]+=function(v)
		b=b/averages        
		if(plot):
			plt.plot(a,b,"k*-")
			plt.show()
		return a[b.argmin()]
		
		
	def minimize(self, function,start,stop,init_stepsize,min_stepsize,initial_averages=1,final_averages=5,verbose=False,hardbounds=False,confirmonly=False,bounds=(-np.inf,np.inf)):
		'''
			returns (value,function value) where function is minimal
			The bounds are not really hard: if this function leaves your bounds, you should increase initial stepsize and initial averages
		'''
		if hardbounds:
			print "HARDBOUNDS is no longer supported, use bounds=(lowe,upper) instead!"
		if confirmonly:
			stepsize=min_stepsize
			x=(start+stop)/2
			initial_averages=final_averages
		else:
			stepsize=init_stepsize
			x=self.findmin(function,start,stop,stepsize,verbose,initial_averages)
			if(verbose): print "stepsize was %f, minimum detected at %f"%(init_stepsize,x)
			if(x==start): x=start-3*stepsize
			elif(x==stop):  x=stop+3*stepsize
			else: stepsize=max(stepsize/10,min_stepsize)
		while True:
			xold=x
			x=self.findmin(function,max(bounds[0],x-3*stepsize),min(bounds[1],x+3*stepsize),stepsize,verbose,initial_averages)
			if(verbose): print "stepsize was %f, minimum detected at %f"%(stepsize,x)
			if(x==xold-3*stepsize):   x-=2*stepsize
			elif(x==xold+3*stepsize): x+=2*stepsize
			else:
				if confirmonly:
					return (x,function(x))
				if (stepsize==min_stepsize):
					break
				stepsize=max(stepsize/5,min_stepsize)    
		if(verbose): print "Finishing with stepsize %f"%(stepsize)                
		x=self.findmin(function,max(bounds[0],x-2*stepsize),min(bounds[1],x+2*stepsize),stepsize,verbose,final_averages)  
		return (x,function(x))
		
	def load_zeros(self):
		ch1wfm=np.zeros(10)
		ch2wfm=np.zeros(10)
		marker=np.zeros_like(ch1wfm)
		self._sample.awg.wfm_send(ch1wfm,marker,marker,self._awg_filepath+self._ch1_filename,self._sample.clock)
		self._sample.awg.wfm_import(self._ch1_filename,self._awg_filepath+self._ch1_filename,'WFM')
		self._sample.awg.set_ch1_waveform(self._ch1_filename)
		self._sample.awg.set_ch1_offset(0)
		self._sample.awg.set_ch1_amplitude(2)
		self._sample.awg.wfm_send(ch2wfm,marker,marker,self._awg_filepath+self._ch2_filename,self._sample.clock)
		self._sample.awg.wfm_import(self._ch2_filename,self._awg_filepath+self._ch2_filename,'WFM')
		self._sample.awg.set_ch2_waveform(self._ch2_filename)
		self._sample.awg.set_ch2_offset(0)
		self._sample.awg.set_ch2_amplitude(2)
		self._sample.awg.run()
		self._sample.awg.set_ch1_output(1)
		self._sample.awg.set_ch2_output(1)    

	def load_wfm(self,sin_phase=0,update_channels=(True,True),init=False,relamp=1.5,relamp2=1.5):
		if(update_channels[0]):
			t1=np.linspace(sin_phase,sin_phase+2*np.pi,self._sample.clock/self._sample.iq_frequency,endpoint=False)
			ch1wfm=self.ch1(t1)
			marker=np.zeros_like(ch1wfm)
			self._sample.awg.wfm_send(ch1wfm,marker,marker,self._awg_filepath+self._ch1_filename,self._sample.clock)
			self._sample.awg.wfm_import(self._ch1_filename,self._awg_filepath+self._ch1_filename,'WFM')
			self._sample.awg.set_ch1_waveform(self._ch1_filename)
		if(update_channels[1]):    
			t2=np.linspace(0,2*np.pi,self._sample.clock/self._sample.iq_frequency,endpoint=False)
			ch2wfm=self.ch2(t2)
			marker=np.zeros_like(ch2wfm)
			self._sample.awg.wfm_send(ch2wfm,marker,marker,self._awg_filepath+self._ch2_filename,self._sample.clock)
			self._sample.awg.wfm_import(self._ch2_filename,self._awg_filepath+self._ch2_filename,'WFM')
			self._sample.awg.set_ch2_waveform(self._ch2_filename)
		if(init):
			self._sample.awg.set_ch1_amplitude(relamp)    
			self._sample.awg.set_ch2_amplitude(relamp2)  
			self._sample.awg.run()
			self._sample.awg.set_ch1_output(1)
			self._sample.awg.set_ch2_output(1)
		

	def phaseoptimize(self,offset):
		'''
		phase offset in radians
		'''
		self.load_wfm(sin_phase=offset,update_channels=(True,False))
		self._fsup.sweep()
		return self._fsup.get_marker_level(4) #assuming that marker4 is at unwanted sideband
			

	def recalibrate(self,dcx,dcy,x,y,phaseoffset,relamp,relamp2):
		self._sample.awg.set_clock(self._sample.clock)
		if not self._FSUP_connected: 
			raise ValueError(('FSUP is possibly not connected. \nIncrease trust_region and maxage to interpolate values or connect FSUP and execute connect_FSUP(fsup)'))
		qt.mstart()
		(hx_amp,hx_phase,hy_amp,hy_phase)=(0,0,0,0)
		mw_freq=self._sample.f01 - self._sample.iq_frequency
		
		#self._sample.awg.stop()
		self._sample.awg.set_ch1_output(0)
		self._sample.awg.set_ch2_output(0)
		self._sample.awg.set_runmode('CONT')
		
		self._sample.qubit_mw_src.set_frequency(mw_freq)
		self._sample.qubit_mw_src.set_power(self._sample.mw_power)
		self._sample.qubit_mw_src.set_status(1)
		
		print "Calibrating %s for Frequency: %.2fGHz (MW-Freq: %.2fGHz), MW Power: %.2fdBm"%(self.mixer_name,self._sample.f01/1e9,mw_freq/1e9,self._sample.mw_power),
		sys.stdout.flush()
		frequencies=[mw_freq-3*self._sample.iq_frequency,mw_freq-2*self._sample.iq_frequency,mw_freq-self._sample.iq_frequency,mw_freq,mw_freq+self._sample.iq_frequency,mw_freq+2*self._sample.iq_frequency,mw_freq+3*self._sample.iq_frequency]
		self.focus(mw_freq,1)
		self.load_zeros()
		(xold,yold)=(np.inf,np.inf)
		while(np.all(np.around((dcx,dcy),3)!=np.around((xold,yold),3))):
			(xold,yold)=(dcx,dcy)
			dcx=self.minimize(self.xoptimize,dcx-.002,dcx+.002,.002,1e-3,final_averages=3,confirmonly=True)[0]
			dcy=self.minimize(self.yoptimize,dcy-.002,dcy+.002,.002,1e-3,final_averages=3,confirmonly=True)[0]
		self.load_wfm(sin_phase=phaseoffset,update_channels=(True,True),relamp=relamp,relamp2=relamp2,init=True)
		
		optimized=[(self.focus(frequencies[i],1), self._fsup.get_marker_level(1))[1] for i in range(len(frequencies))]
		optimized_old=[np.inf,np.inf,np.inf,np.inf]
		while (optimized_old[2]-optimized[2]>1 or optimized_old[3]-optimized[3]>1):
			optimized_old=copy(optimized)
			self.focus(mw_freq,1)
			(xold,yold)=(np.inf,np.inf)
			while(np.all(np.around((x,y),3)!=np.around((xold,yold),3))):
				(xold,yold)=(x,y)
				x=self.minimize(self.xoptimize,x-.002,x+.002,.001,1e-3,final_averages=1,confirmonly=True)[0]
				y=self.minimize(self.yoptimize,y-.002,y+.002,.001,1e-3,final_averages=1,confirmonly=True)[0]
			self.focus(mw_freq-self._sample.iq_frequency,4)        
			phaseoffset=self.minimize(self.phaseoptimize,phaseoffset-.15,phaseoffset+.15,5e-3,5e-3,final_averages=1,confirmonly=True)[0]
			relamp=self.minimize(self.relampoptimize,relamp-.01,relamp+.01,.05,1e-3,final_averages=2,bounds=(.5,2),confirmonly=True)[0]
			relamp2=self.minimize(self.relampoptimize2,relamp2-.01,relamp2+.01,.05,1e-3,final_averages=2,bounds=(.5,2),confirmonly=True)[0]
			optimized=[(self.focus(frequencies[i],1), np.mean([(self._fsup.sweep(),self._fsup.get_marker_level(1))[1] for j in range(5)]))[1] for i in range(len(frequencies))]
			print ".",
			sys.stdout.flush()
		print "Parameters: DC x: %.1fmV, DC y: %.1fmV AC x: %.1fmV, AC y: %.1fmV phase: %.1fdegree Amplitude: %.3fVpp/%.3fVpp"%(dcx*1e3,dcy*1e3,x*1e3,y*1e3,phaseoffset*180/np.pi,relamp,relamp2)
		
		print "Your Sideband has a power of %.3fdBm, Leakage is %.2fdB lower, other sideband is %.2fdB lower.\nThe largest of the higher harmonics is %.2fdB lower."%(optimized[4],optimized[4]-optimized[3],optimized[4]-optimized[2],np.max((optimized[4]-optimized[0],optimized[4]-optimized[1],optimized[4]-optimized[4],optimized[5]-optimized[6])))
		data=np.array([np.append((self._sample.f01,mw_freq,self._sample.mw_power,time.time(),dcx,dcy,x,y,phaseoffset,relamp,relamp2),optimized)])
		try: 
			storedvalues=np.loadtxt(qt.config.get('datadir')+"\\IQMixer\\%s.cal"%self.mixer_name)
			if np.size(storedvalues)<30: #Only one dataset
				storedvalues=[storedvalues]
			# If there was a calibration with the same parameters, remove it
			todelete=[]
			for index,t in enumerate(storedvalues):
				if t[0]==self._sample.f01 and t[1]==mw_freq and t[2]==self._sample.mw_power:
					todelete=np.append(todelete,index)        
					print "\nLast time (%s), there have been the following values:"%(time.ctime(t[3]))
					print "Parameters: DC x: %.1fmV, DC y: %.1fmV phase: %.1fdegree Amplitude: %.3fVpp/%.3fVpp"%(t[6]*1e3,t[7]*1e3,t[8]*180/np.pi,t[9],t[10])
					print "Your Sideband had a power of %.3fdBm, Leakage was %.2fdB lower, other sideband was %.2fdB lower.\nThe largest of the higher harmonics was %.2fdB lower."%(t[15],t[15]-t[14],t[15]-t[13],np.max((t[15]-t[11],t[15]-t[12],t[15]-t[16],t[15]-t[17])))
		   
			storedvalues=np.delete(storedvalues,todelete,axis=0)
			
			
			data=np.append(storedvalues,data)

		except IOError:
			pass
		data=data.reshape((data.size/18,18))
		np.savetxt(qt.config.get('datadir')+"\\IQMixer\%s.cal"%(self.mixer_name),data,("%.2f","%.2f","%.2f","%i","%.3f","%.3f","%.3f","%.3f","%.6f","%.3f","%.3f","%.4f","%.4f","%.4f","%.4f","%.4f","%.4f","%.4f"))
		return data

	def initial_calibrate(self):
		if not self._FSUP_connected: 
			raise ValueError(('FSUP is possibly not connected. \nIncrease trust_region and maxage to interpolate values or connect FSUP and execute connect_FSUP(fsup)'))
		qt.mstart()
		(hx_amp,hx_phase,hy_amp,hy_phase,phaseoffset)=(0,0,0,0,0)
		mw_freq=self._sample.f01 - self._sample.iq_frequency
		
		#self._sample.awg.stop()
		self._sample.awg.set_ch1_output(0)
		self._sample.awg.set_ch2_output(0)
		self._sample.awg.set_runmode('CONT')

		self._sample.qubit_mw_src.set_frequency(mw_freq)
		self._sample.qubit_mw_src.set_power(self._sample.mw_power)
		self._sample.qubit_mw_src.set_status(1)
		
		print "Calibrating %s for Frequency: %.2fGHz (MW-Freq: %.2fGHz), MW Power: %.2fdBm"%(mixer_name,sideband_frequency/1e9,mw_freq/1e9,self._sample.mw_power),
		sys.stdout.flush()
		frequencies=[mw_freq-3*self._sample.iq_frequency,mw_freq-2*self._sample.iq_frequency,mw_freq-self._sample.iq_frequency,mw_freq,mw_freq+self._sample.iq_frequency,mw_freq+2*self._sample.iq_frequency,mw_freq+3*self._sample.iq_frequency]
		self.focus(mw_freq,1)
		self.load_zeros()
		(xold,yold)=(np.inf,np.inf)
		dcx=self.minimize(self.xoptimize,-.02,.02,.01,5e-3,final_averages=1)[0]
		dcy=self.minimize(self.yoptimize,-.02,.02,.01,5e-3,final_averages=1)[0]
		while(np.all(np.around((dcx,dcy),3)!=np.around((xold,yold),3))):
			(xold,yold)=(dcx,dcy)
			dcx=self.minimize(self.xoptimize,dcx-.002,dcx+.002,.002,1e-3,final_averages=3,confirmonly=True)[0]
			dcy=self.minimize(self.yoptimize,dcy-.002,dcy+.002,.002,1e-3,final_averages=3,confirmonly=True)[0]
		self.load_wfm(sin_phase=phaseoffset,update_channels=(True,True),relamp=2,relamp2=2,init=True)
		self.focus(mw_freq,1)
		(xold,yold)=(0,0)
		x=self.minimize(self.xoptimize,-.02,.02,.01,5e-3,final_averages=1)[0]
		y=self.minimize(self.yoptimize,-.02,.02,.01,5e-3,final_averages=1)[0]
		while(np.all(np.around((x,y),3)!=np.around((xold,yold),3))):
			(xold,yold)=(x,y)
			x=self.minimize(self.xoptimize,x-.002,x+.002,.002,2e-3,final_averages=1,verbose=False,confirmonly=True)[0]
			y=self.minimize(self.yoptimize,y-.002,y+.002,.002,2e-3,final_averages=1,verbose=False,confirmonly=True)[0]
		self.focus(mw_freq-self._sample.iq_frequency,4)
		relamp=self.minimize(relampoptimize,0.2,2,.3,10e-3,final_averages=1,bounds=(.5,2))[0]
		relamp2=self.minimize(relampoptimize2,0.2,2,.3,10e-3,final_averages=1,bounds=(.5,2))[0]
		phaseoffset=self.minimize(phaseoptimize,0,1,.2,5e-3,final_averages=1)[0]
		print "->",
		sys.stdout.flush()
		return recalibrate(dcx,dcy,x,y,phaseoffset,relamp,relamp2)
		'''
		optimized=[(self.focus(frequencies[i],1), self._fsup.get_marker_level(1))[1] for i in range(len(frequencies))]
		optimized_old=[np.inf,np.inf,np.inf,np.inf]
		while (optimized_old[2]-optimized[2]>1 or optimized_old[3]-optimized[3]>1):
			optimized_old=copy(optimized)
			self.focus(mw_freq,1)
			(xold,yold)=(np.inf,np.inf)
			while(np.all(np.around((x,y),3)!=np.around((xold,yold),3))):
				(xold,yold)=(x,y)
				x=self.minimize(self.xoptimize,x-.002,x+.002,.001,1e-3,final_averages=1,confirmonly=True)[0]
				y=self.minimize(self.yoptimize,y-.002,y+.002,.001,1e-3,final_averages=1,confirmonly=True)[0]
			self.focus(mw_freq-iq_freq,4)        
			phaseoffset=self.minimize(phaseoptimize,phaseoffset-.15,phaseoffset+.15,5e-3,5e-3,final_averages=1,confirmonly=True)[0]
			relamp=self.minimize(relampoptimize,relamp-.01,relamp+.01,.05,1e-3,final_averages=2,bounds=(.5,2),confirmonly=True)[0]
			relamp2=self.minimize(relampoptimize2,relamp2-.01,relamp2+.01,.05,1e-3,final_averages=2,bounds=(.5,2),confirmonly=True)[0]
			optimized=[(self.focus(frequencies[i],1), np.mean([(self._fsup.sweep(),self._fsup.get_marker_level(1))[1] for j in range(5)]))[1] for i in range(len(frequencies))]
			print ".",
			sys.stdout.flush()
		print "\nParameters: DC x: %.1fmV, DC y: %.1fmV phase: %.1fdegree Amplitude: %.3fVpp/%.3fVpp"%(x*1e3,y*1e3,phaseoffset*180/np.pi,relamp,relamp2)
		print "Your Sideband has a power of %.3fdBm, Leakage is %.2fdB lower, other sideband is %.2fdB lower.\nThe higher harmonics have a mean power of %.2fdBm"%(optimized[4],optimized[4]-optimized[3],optimized[4]-optimized[2],np.mean((optimized[4]-optimized[0],optimized[4]-optimized[1],optimized[4]-optimized[4],optimized[5]-optimized[6])))
		data=np.array([np.append((sideband_frequency,mw_freq,mw_power,time.time(),dcx,dcy,x,y,phaseoffset,relamp,relamp2),optimized)])
		try: 
			storedvalues=np.loadtxt("D:\\IQMixer\\%s.cal"%mixer_name)
			# If there was a calibration with the same parameters, remove it
			todelete=[]
			if np.size(storedvalues)<30: #Only one dataset
				storedvalues=[storedvalues]
			for index,t in enumerate(storedvalues):
				if t[0]==sideband_frequency and t[1]==mw_freq and t[2]==mw_power:
					todelete=np.append(todelete,index)        
					print "\nLast time (%s), there have been the following values:"%(time.ctime(t[3]))
					print "Parameters: DC x: %.1fmV, DC y: %.1fmV phase: %.1fdegree Amplitude: %.3fVpp/%.3fVpp"%(t[6]*1e3,t[7]*1e3,t[8]*180/np.pi,t[9],t[10])
					print "Your Sideband had a power of %.3fdBm, Leakage is %.2fdB lower, other sideband is %.2fdB lower.\nThe higher harmonics are in average %.2fdB lower."%(t[15],t[15]-t[14],t[15]-t[13],np.mean((t[15]-t[11],t[15]-t[12],t[15]-t[16],t[15]-t[17])))
		   
			storedvalues=np.delete(storedvalues,todelete,axis=0)
			
			
			data=np.append(storedvalues,data)

		except IOError:
			pass
		data=data.reshape((data.size/18,18))
		np.savetxt("D:\\IQMixer\%s.cal"%(mixer_name),data,("%.2f","%.2f","%.2f","%i","%.3f","%.3f","%.3f","%.3f","%.6f","%.3f","%.3f","%.4f","%.4f","%.4f","%.4f","%.4f","%.4f","%.4f"))
		return data
		'''

	def calibrate(self,force_recalibration=False):
		'''
			This function automatically looks up, if this mixer has already been calibrated before:
			- If this frequency was calibrated less than maxage secs ago, it will just load this settings
			- If this frequency was calibrated more than maxage secs ago (or if you set force_recalibration=True), it will recalibrate, starting at the old parameters
			- If two adjacent frequencies, not further away than interpol_freqspan have been calibrated, interpolate starting values and recalibrate 
			- You can have the same behaviour as above without recalibrating, if you use trust_region instead of interpol_freqspan
			
		'''
		interpol_freqspan=np.max((self.interpol_freqspan,self.trust_region))/2 #Half of the span in each direction

		try: 
			storedvalues=np.loadtxt(qt.config.get('datadir')+"\\IQMixer\\%s.cal"%self.mixer_name)
			NeedForInterpolation=False
			left_border=-np.inf
			right_border=np.inf
			for index,t in enumerate(storedvalues):
				if t[0]==self._sample.f01 and t[1]==self._sample.f01-self._sample.iq_frequency and t[2]==self._sample.mw_power:
					if time.time()-t[3] > self.maxage or force_recalibration: #Calibration is too old
						print "recalibrating because calibration is too old (%.2f days ago)"%((time.time()-t[3])/24/3600)
						return self.recalibrate(t[4],t[5],t[6],t[7],t[8],t[9],t[10])
					else:
						#print "returning known values"
						return t
					break
				if np.abs(t[0]-self._sample.f01) <= self.interpol_freqspan and t[0]-self._sample.f01 <= 0:
					if left_border== -np.inf:
						left_border=index
						NeedForInterpolation=True
					elif  storedvalues[left_border][0]<t[0]:
						left_border=index
					elif np.abs(storedvalues[right_border][2]-self._sample.mw_power)>np.abs(self._sample.mw_power-t[2]):
						left_border=index
				if np.abs(t[0]-self._sample.f01) <= self.interpol_freqspan and t[0]-self._sample.f01 >= 0:
					if right_border== np.inf:
						right_border=index
						NeedForInterpolation=True
					elif storedvalues[right_border][0]>t[0]:
						right_border=index
					elif np.abs(storedvalues[right_border][2] - self._sample.mw_power) > np.abs(self._sample.mw_power-t[2]):
						right_border=index
			if NeedForInterpolation:
				if (left_border==-np.inf or right_border==+np.inf): #Within interpol_freqspan, not both sides could be found, so we need to do an initial calibration
					print "initial calibration for this frequency required. Your interpol_freqspan is maybe a bit too small"
					return self.initial_calibrate()    
				#print storedvalues[left_border]
				#print storedvalues[right_border]
				#print (sideband_frequency-storedvalues[left_border][0])/(storedvalues[right_border][0]-storedvalues[left_border][0])
				if (left_border==right_border):
					print "recalibrating"
					return self.recalibrate(storedvalues[left_border][4],storedvalues[left_border][5],storedvalues[left_border][6],storedvalues[left_border][7],storedvalues[left_border][8],storedvalues[left_border][9],storedvalues[left_border][10])
				interpolated=storedvalues[left_border]+(storedvalues[right_border]-storedvalues[left_border])*(self._sample.f01-storedvalues[left_border][0])/(storedvalues[right_border][0]-storedvalues[left_border][0])
				if (storedvalues[right_border][0]-storedvalues[left_border][0])<=self.trust_region: #No need for recalibration
					#print "using interpolated values"
					return interpolated
				else: 
					print "recalibrating"
					return self.recalibrate(interpolated[4],interpolated[5],interpolated[6],interpolated[7],interpolated[8],interpolated[9],interpolated[10])
			else:
				print "initial calibration for this frequency required. Think about using the interpol_freqspan option!"
				return self.initial_calibrate()    
			
		except IOError:
			#Mixer has not at all been calibrated before
			print "initial calibration required"
			return self.initial_calibrate()


	def convert(self,wfm):
		'''
		   wfm is an 1D array of complex values with absolute values <=1,
		   where complex phase represents the phase of the later microwave
		   Example: With an iq frequency of 100MHz and a samplerate of 6GS/s you have 
		   60 Samples per wave, corresponding to 6degree phase resolution
		   
		'''
		params=self.calibrate(force_recalibration=False)
		#content of params:(sideband_frequency,mw_freq,mw_power,time.time(),dcx,dcy,x,y,phaseoffset,relamp,relamp2),optimized)
		self._sample.f01 = params[0]
		self._output_power = params[15]
		self._iq_frequency = self._sample.iq_frequency
		dcx,dcy,x,y,phaseoffset,relamp,relamp2=params[4:11]
		t=np.arange(len(wfm))/self._sample.clock
		#Relamp is Peak-to-Peak
		relamp,relamp2=relamp/2,relamp2/2
		return (dcx+np.abs(wfm)*(relamp*self.ch1(2*np.pi*self._sample.iq_frequency*t+np.angle(wfm)+phaseoffset)-dcx+x),dcy+np.abs(wfm)*(relamp2*self.ch2(2*np.pi*self._sample.iq_frequency*t+np.angle(wfm))-dcy+y) )
