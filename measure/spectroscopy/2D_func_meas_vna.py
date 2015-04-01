# JB@KIT 03/2015
#2D VNA measurement class for function dependent measuring


import numpy as np
from time import sleep
import time
import logging
import matplotlib.pylab as plt
from scipy.optimize import curve_fit

import qt

#ttip = qt.instruments.get('ttip')
vna = qt.instruments.get('vna')
mw_src1 = qt.instruments.get('mw_src1')

##########################################################################################################################
# measure 2D class

class spectrum_2D(object):
	
	'''
	useage:
	
	flux_freq_spectrum = spectrum2D()
	
	flux_freq_spectrum.set_x_parameters(arange(-0.05,0.05,0.01),'flux coil current (mA)',coil.set_current)
	flux_freq_spectrum.set_x_parameters(arange(4e9,7e9,10e6),'excitation frequency (Hz)',mw_src1.set_frequency)
	
	flux_freq_spectrum.gen_fit_function(...)   several times
	
	flux_freq_spectrum.measure()
	'''
	
	def __init__(self):

		self.landscape = None
		self.span = 100e6
		self.tdx = 0.002
		self.tdy = 0.002,
		#self.op='amppha'
		#self.ref=False
		#self.ref_meas_func=None
		self.comment = None
		self.plot3D = True
		self.plotlive = True
		
	def set_x_parameters(self, x_vec, x_coordname, x_set_obj):
		self.x_vec = x_vec
		self.x_coordname = x_coordname
		self.x_set_obj = x_set_obj
		
	def set_y_parameters(self, y_vec, y_coordname, y_set_obj):
		self.y_vec = y_vec
		self.y_coordname = y_coordname
		self.y_set_obj = y_set_obj
		
	def set_tdx(self, tdx):
		self.tdx = tdx
		
	def set_tdy(self, tdy):
		self.tdy = tdy
		
	def get_tdx(self):
		return self.tdx
		
	def get_tdy(self):
		return self.tdy
	
	@staticmethod
	def f_parab(x,a,b,c):
		return a*(x-b)**2+c
	@staticmethod
	def f_hyp(x,a,b,c):
		return a*np.sqrt((x/b)**2+c)
		
	def gen_fit_function(self, curve_f, curve_p, p0 = [-1,0.1,7]):
	
		'''
		curve_f: 'parab', 'hyp', specifies the fit function to be employed
		curve_p: set of points that are the basis for the fit in the format [[x1,x2,x3,...][y1,y2,y3,...]]
		p0 (optional): start parameters for the fit, must be an 1D array of length 3 ([a,b,c])
		
		adds a trace to landscape
		'''
		
		if self.landscape == None:
			self.landscape = []
		
		x_fit = curve_p[0]
		y_fit = curve_p[1]#*1e-9   #f in GHz
		
		try:
			if curve_f == 'parab':
				popt, pcov = curve_fit(f_parab, x_fit, y_fit, p0=p0)
				landscape.append(f_parab(self.x_vec, *popt))
			elif curve_f == 'hyp':
				popt, pcov = curve_fit(f_hyp, x_fit, y_fit, p0=p0)
				landscape.append(f_hyp(self.x_vec, *popt))
			else:
				print 'function type not known...aborting'
				raise ValueError
		except Exception as message:
			print 'fit not successful:', message
			popt = p0

	def delete_fit_function(self, n = None):
		if n == None:
			self.landscape = None
		else:
			self.landscape.remove(self.landscape[n])
			
	def plot_fit_function(self, num_points = 100):

		try:
			x_coords = np.linspace(self.x_vec[0], self.x_vec[-1], num_points)
		except Exception as message:
			print 'no x axis information specified', message
			return
		
		for trace in self.landscape:
			plt.plot(x_coords, trace)
			
			
	def func():
		if self.landscape == None:
			return False
		else:
			return True

	@staticmethod
	def wait_averages():#
		'''
		wait averages to use with VNA E5071C (9.5GHz)
		'''
		vna.avg_clear()
		sleep(vna.get_sweeptime()*vna.get_averages())
			
	def measure(self):
		
		'''
		measure method to perform the measurement according to landscape, if set
		self.span is the range (in units of the vertical plot axis) data is taken around the specified funtion(s) 
		'''

		if landscape != None:
			center_freqs = np.array(landscape).T
		'''
		prepare an array of length len(x_vec), each segment filled with an array being the number of present traces (number of functions)
		'''

		qt.mstart()
		vna.get_all()
		#ttip.get_temperature()

		nop = vna.get_nop()
		nop_avg = vna.get_averages()
		bandwidth = vna.get_bandwidth()
		t_point = nop / bandwidth * nop_avg

		data = qt.Data(name=('vna_' + x_coordname + y_coordname))
		data.add_coordinate(x_coordname)
		data.add_coordinate(y_coordname)

		if self.comment:
			data.add_comment(self.comment)

		for i in range(1,nop+1):
			data.add_value(('Point %i Amp' %i))
		for i in range(1,nop+1):
			data.add_value(('Point %i Pha' %i))

		data.create_file()

		if(self.plotlive):
			if(self.plot3D):
				plot_amp = qt.Plot3D(data, name='Amplitude', coorddims=(0,1), valdim=int(nop/2)+2, style=qt.Plot3D.STYLE_IMAGE)
				plot_amp.set_palette('bluewhitered')
				plot_pha = qt.Plot3D(data, name='Phase', coorddims=(0,1), valdim=int(nop/2)+2+nop, style=qt.Plot3D.STYLE_IMAGE)
				plot_pha.set_palette('bluewhitered')
			else:
				plot_amp = qt.Plot2D(data, name='Amplitude', coorddim=1, valdim=int(nop/2)+2)
				plot_pha = qt.Plot2D(data, name='Phase', coorddim=1, valdim=int(nop/2)+2+nop)

		now1 = time.time()
		x_it = 0

		try:
			for i in range(len(self.x_vec)):
				if x_it == 1:
					now2 = time.time()
					t = (now2-now1)
					left = (t*np.size(self.x_vec)/60/60);
					if left < 1:
						print('Time left: %f min' %(left*60))
					else:
						print('Time left: %f h' %(left))
							
				self.x_set_obj(self.x_vec[i])
				sleep(self.tdx)
				x_it+=1

				for y in self.y_vec:
					if (np.min(np.abs(center_freqs[i]-y*np.ones(len(center_freqs[i])))) <= self.span/2.) and func():   #if point is not of interest (not close to one of the functions)
						data_amp = np.zeros(int(nop))
						data_pha = np.zeros(int(nop))
					else:
						self.y_set_obj(y)
						sleep(self.tdy)
						wait_averages(t_point, nop_avg)
						data_amp,data_pha = vna.get_tracedata()

					dat = np.append(self.x_vec[i],y)
					dat = np.append(dat,data_amp)
					dat = np.append(dat,data_pha)
					data.add_data_point(*dat)  # _one_

					qt.msleep()

				data.new_block()
		finally:
			if(not self.plotlive):
				if(self.plot3D):
					plot_amp = qt.Plot3D(data, name='Amplitude', coorddims=(0,1), valdim=int(nop/2)+2, style=qt.Plot3D.STYLE_IMAGE)
					plot_amp.set_palette('bluewhitered')
					plot_pha = qt.Plot3D(data, name='Phase', coorddims=(0,1), valdim=int(nop/2)+2+nop, style=qt.Plot3D.STYLE_IMAGE)
					plot_pha.set_palette('bluewhitered')
				else:
					plot_amp = qt.Plot2D(data, name='Amplitude', coorddim=1, valdim=int(nop/2)+2)
					plot_pha = qt.Plot2D(data, name='Phase', coorddim=1, valdim=int(nop/2)+2+nop)

			plot_amp.save_png()
			plot_amp.save_gp()
			plot_pha.save_png()
			plot_pha.save_gp()

			data.close_file()

			qt.mend()

