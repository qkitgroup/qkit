# JB@KIT 04/2015
# VNA measurement class supporting function dependent measurement


import numpy as np
import logging
import matplotlib.pylab as plt
from scipy.optimize import curve_fit
import time
from time import sleep
import sys
import qt
from qkit.storage import hdf_lib as hdf

from qkit.gui.notebook.Progress_Bar import Progress_Bar


#ttip = qt.instruments.get('ttip')
#vna = qt.instruments.get('vna')
#mw_src1 = qt.instruments.get('mw_src1')
vcoil = qt.instruments.get('vcoil')

##########################################################################################################################

class spectrum(object):

	'''
	useage:
	
	m = spectrum()
	m2 = spectrum(vna_select = 'vna2', mw_src_select = 'mw_src1')   #where 'vna2'/'mw_src1' is the qt.instruments name
	
	m.set_x_parameters(arange(-0.05,0.05,0.01),'flux coil current (mA)',coil.set_current)
	m.set_y_parameters(arange(4e9,7e9,10e6),'excitation frequency (Hz)',mw_src1.set_frequency)
	
	m.gen_fit_function(...)   several times
	
	m.measure_XX()
	'''

	def __init__(self, vna = 'vna', mw_src = 'mw_src1'):

		self.vna = vna
		self.mw_src = mw_src

		self.landscape = None
		self.span = 200e6   #specified in Hz
		self.tdx = 0.002
		self.tdy = 0.002

		self.x_unit = None
		self.y_unit = None
		#self.op='amppha'
		self.data_complex = False
		#self.ref=False
		#self.ref_meas_func=None
		self.comment = None
		self.plot3D = True
		self.plotlive = True

		self.return_dat = False

		self.x_set_obj = None
		self.y_set_obj = None
		self.save_hdf = False
		
	def set_span(self, span):
		self.span = span

	def get_span(self):
		return self.span
		
	def set_save_hdf(self, set_hdf):
		self.save_hdf = set_hdf

	def get_save_hdf(self):
		return self.save_hdf
		
	def set_x_unit(self, x_unit):
		self.x_unit = x_unit

	def get_x_unit(self):
		return self.x_unit

	def set_y_unit(self, y_unit):
		self.y_unit = y_unit

	def get_y_unit(self):
		return self.y_unit

	def set_x_parameters(self, x_vec, x_coordname, x_set_obj, x_unit = None):
		self.x_vec = x_vec
		self.x_coordname = x_coordname
		self.x_set_obj = x_set_obj
		self.delete_fit_function()
		self.set_x_unit(x_unit)
		
	def set_y_parameters(self, y_vec, y_coordname, y_set_obj, y_unit = None):
		self.y_vec = y_vec
		self.y_coordname = y_coordname
		self.y_set_obj = y_set_obj
		self.delete_fit_function()
		self.set_y_unit(y_unit)


	def set_tdx(self, tdx):
		self.tdx = tdx

	def set_tdy(self, tdy):
		self.tdy = tdy

	def get_tdx(self):
		return self.tdx

	def get_tdy(self):
		return self.tdy

	def f_parab(self,x,a,b,c):
		return a*(x-b)**2+c

	def f_hyp(self,x,a,b,c):
		return a*np.sqrt((x/b)**2+c)

	def gen_fit_function(self, curve_f, curve_p, units = '', p0 = [-1,0.1,7]):

		'''
		curve_f: 'parab', 'hyp', specifies the fit function to be employed
		curve_p: set of points that are the basis for the fit in the format [[x1,x2,x3,...],[y1,y2,y3,...]], frequencies in Hz
		units: set this to 'Hz' in order to avoid large values that cause the fit routine to diverge
		p0 (optional): start parameters for the fit, must be an 1D array of length 3 ([a,b,c])
		
		adds a trace to landscape
		'''

		if self.landscape == None:
			self.landscape = []

		x_fit = curve_p[0]
		if units == 'Hz':
			y_fit = np.array(curve_p[1])*1e-9
		else:
			y_fit = np.array(curve_p[1])

		try:
			if curve_f == 'parab':
				popt, pcov = curve_fit(self.f_parab, x_fit, y_fit, p0=p0)
				if units == 'Hz':
					self.landscape.append(1e9*self.f_parab(self.x_vec, *popt))
				else:
					self.landscape.append(self.f_parab(self.x_vec, *popt))
			elif curve_f == 'hyp':
				popt, pcov = curve_fit(self.f_hyp, x_fit, y_fit, p0=p0)
				if units == 'Hz':
					self.landscape.append(1e9*self.f_hyp(self.x_vec, *popt))
				else:
					self.landscape.append(self.f_hyp(self.x_vec, *popt))
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
			self.landscape = np.delete(self.landscape,n,axis=0)

	def plot_fit_function(self, num_points = 100):
		'''
		try:
			x_coords = np.linspace(self.x_vec[0], self.x_vec[-1], num_points)
		except Exception as message:
			print 'no x axis information specified', message
			return
		'''
		if self.landscape != None:
			for trace in self.landscape:
				try:
					#plt.clear()
					plt.plot(self.x_vec, trace)
					plt.fill_between(self.x_vec, trace+float(self.span)/2, trace-float(self.span)/2, alpha=0.5)
				except Exception as m:
					print 'invalid trace...skip'
			plt.axhspan(self.y_vec[0], self.y_vec[-1], facecolor='0.5', alpha=0.5)
			plt.show()
		else:
			print 'No trace generated.'

	def measure_1D(self):
		if self.x_set_obj == None:
			print 'axes parameters not properly set...aborting'
			return
		self._measure('1D')	

	def measure_1D2(self):
		if self.x_set_obj == None:
			print 'axes parameters not properly set...aborting'
			return
		self._measure('1D2')

	def measure_2D(self):
		'''
		measure method to perform the measurement according to landscape, if set
		self.span is the range (in units of the vertical plot axis) data is taken around the specified funtion(s) 
		'''

		if self.x_set_obj == None or self.y_set_obj == None:
			print 'axes parameters not properly set...aborting'
			return
		self._measure('2D')

	def _measure(self, measureFkt = '1D'):
		if measureFkt != '2D':
			y_vec_old=self._exchange1D()

		qt.mstart()
		self.vna.get_all()
		#ttip.get_temperature()

		nop = self.vna.get_nop()
		nop_avg = self.vna.get_averages()
		bandwidth = self.vna.get_bandwidth()
		t_point = nop / bandwidth * nop_avg
		freqpoints = self.vna.get_freqpoints()
		data = []

		if measureFkt == '1D2':
			if not self.save_hdf:
				data = qt.Data(name=('vna_sweep1D2' + self.y_coordname))
				data.add_coordinate(self.y_coordname)
				data.add_coordinate('Frequency')
				data.add_value('Amplitude')
				data.add_value('Phase')
				if self.data_complex == True:
					data.add_value('Real')
					data.add_value('Img')
			else:
				data = hdf.Data(name=('vna_sweep1D2' + self.y_coordname))
				hdf_freq = data.add_coordinate('Frequency', unit = 'Hz', comment = None)
				hdf_freq.add(freqpoints)
				hdf_y = data.add_coordinate(self.y_coordname, unit = self.y_unit, comment = None)
				hdf_y.add(self.y_vec)
				hdf_amp = data.add_value_matrix('Amplitude', x = hdf_y, y=hdf_freq, unit = 'V', comment = None)
				hdf_pha = data.add_value_matrix('Phase', x = hdf_y, y=hdf_freq, unit='rad', comment=None)

		if measureFkt == '1D':
			if not self.save_hdf:
				data = qt.Data(name=('vna_' + self.y_coordname))
				data.add_coordinate(self.y_coordname)

				for i in range(1,nop+1):
					data.add_value(('Point %i Amp' %i))
				for i in range(1,nop+1):
					data.add_value(('Point %i Pha' %i))
			else:
				data = hdf.Data(name=('vna_' + self.y_coordname))
				hdf_points = data.add_coordinate('Point', unit = None, comment = None)
				hdf_y = data.add_coordinate(self.y_coordname, unit = self.y_unit, comment = None)
				point_vec = []
				for i in range(1, nop+1): point_vec = np.append(point_vec, i)
				
				hdf_points.add(point_vec)
				hdf_y.add(self.y_vec)
				hdf_amp = data.add_value_vector('Amplitude', x = hdf_y, unit = 'V', comment = None)
				hdf_pha = data.add_value_vector('Phase', x = hdf_y, unit='rad', comment=None)

		if measureFkt == '2D':
			if self.landscape != None:
				center_freqs = np.array(self.landscape).T
			else:
				center_freqs = []   #load default sequence
				for i in range(len(self.x_vec)):
					center_freqs.append([0])
				'''
prepare an array of length len(x_vec), each segment filled with an array being the number of present traces (number of functions)
				'''
			if not self.save_hdf:
				data = qt.Data(name=('vna_' + self.x_coordname + self.y_coordname))
				data.add_coordinate(self.x_coordname)
				data.add_coordinate(self.y_coordname)

				for i in range(1,nop+1):
					data.add_value(('Point %i Amp' %i))
					for i in range(1,nop+1):
						data.add_value(('Point %i Pha' %i))
			else:
				data=hdf.Data(name=('vna_' + self.x_coordname + self.y_coordname))
				hdf_x = data.add_coordinate(self.x_coordname, unit = self.x_unit, comment = None)
				hdf_x.add(self.x_vec)
				hdf_y = data.add_coordinate(self.y_coordname, unit = self.y_unit, comment = None)
				hdf_y.add(self.y_vec)
				hdf_points = data.add_coordinate('Point', unit = None, comment = None)

				point_vec = []
				for i in range(1, nop+1):
					point_vec = np.append(point_vec, i)
				hdf_points.add(point_vec)
				
				hdf_amp0 = data.add_value_matrix('Amplitude', x = hdf_y, y=hdf_y, unit = 'V', comment = None)
				hdf_pha0 = data.add_value_matrix('Phase', x = hdf_y, y=hdf_y, unit='rad', comment=None)

				for x in self.x_vec:
					name_amp = 'Amplitude_'+str(x)+'_'+str(self.x_unit)
					name_pha = 'Phase_'+str(x)+'_'+str(self.x_unit)
					
					hdf_amp = data.add_value_matrix(name_amp, x = hdf_y, y=hdf_points, unit = 'V', comment = None)
					hdf_pha = data.add_value_matrix(name_pha, x = hdf_y, y=hdf_points, unit='rad', comment=None)

		if self.comment:
			data.add_comment(self.comment)
		if not self.save_hdf: 
			data.create_file()

		if measureFkt =='1D' or self.plotlive:
			plot_amp, plot_pha = self._plot(measureFkt=measureFkt, data=data)

		if measureFkt != '2D':
			self.y_set_obj(self.y_vec[0])
		'''
		now1 = time.time()
		x_it = 0
		'''
		p = Progress_Bar(len(self.x_vec)*len(self.y_vec))

		try:
			for i in range(len(self.x_vec)):
				'''
				if x_it == 1:
					now2 = time.time()
					t = (now2-now1)
					left = (t*np.size(self.x_vec)/60/60);
					if left < 1:
						print('Time left: %f min' %(left*60))
					else:
						print('Time left: %f h' %(left))
				'''
				
				if measureFkt == '2D':
					self.x_set_obj(self.x_vec[i])
					sleep(self.tdx)
					if self.save_hdf:
						name_amp = 'Amplitude_'+str(x)+'_'+str(self.x_unit)
						name_pha = 'Phase_'+str(x)+'_'+str(self.x_unit)

						hdf_amp = data.add_value_matrix(name_amp, x = hdf_y, y=hdf_points, unit = 'V', comment = None)
						hdf_pha = data.add_value_matrix(name_pha, x = hdf_y, y=hdf_points, unit='rad', comment=None)
						save_amp0 = []
						save_pha0 = []
				#x_it+=1

				for y in self.y_vec:
					if measureFkt == '2D' and (np.min(np.abs(center_freqs[i]-y*np.ones(len(center_freqs[i])))) > self.span/2.) and self.landscape != None:   #if point is not of interest (not close to one of the functions)
						data_amp = np.zeros(int(nop))
						data_pha = np.zeros(int(nop))   #fill with zeros
					else:
						self.y_set_obj(y)
						sleep(self.tdy)
						if measureFkt != '2D':
							self.vna.avg_clear()
						sleep(self.vna.get_sweeptime_averages())
						data_amp,data_pha = self.vna.get_tracedata()
						if self.data_complex and measureFkt == '1D2':
							data_real, data_imag = self.vna.get_tracedata('RealImag')

					dat = []
					if measureFkt == '2D': 
						if not self.save_hdf:
							dat = np.append(dat, self.x_vec[i])
							dat = np.append(dat, y)
							dat = np.append(dat,data_amp)
							dat = np.append(dat,data_pha)
							data.add_data_point(*dat)
						else:
							save_amp0 = np.append(save_amp0, data_amp[len(data_amp)/2])
							save_pha0 = np.append(save_pha0, data_pha[len(data_pha)/2])
							if y == self.y_vec[len(self.y_vec)-1]:
								hdf_amp0.append(save_amp0)
								hdf_pha0.append(save_pha0)
							hdf_amp.append(data_amp)
							hdf_pha.append(data_pha)

					if measureFkt == '1D':
						if not self.save_hdf:
							dat = np.append(dat, y)
							dat = np.append(dat,data_amp)
							dat = np.append(dat,data_pha)
							data.add_data_point(*dat)
						else:
							hdf_amp.append(data_amp)
							hdf_pha.append(data_pha)

					if measureFkt == '1D2':
						if not self.save_hdf:
							dat = np.append([y*np.ones(nop)],[freqpoints], axis = 0)
							dat = np.append(dat,[data_amp],axis = 0)
							dat = np.append(dat,[data_pha],axis = 0)
							if self.data_complex == True:
								dat = np.append(dat,[data_real],axis = 0)
								dat = np.append(dat,[data_imag],axis = 0)
							data.add_data_point(*dat)
							data.new_block()
						else:
							hdf_amp.append(data_amp)
							hdf_pha.append(data_pha)
							

					if not self.save_hdf: qt.msleep()
					p.iterate()

				if measureFkt == '2D' and not self.save_hdf: data.new_block()

		finally:
			if measureFkt != '1D' and not self.plotlive:
				plot_amp, plot_pha = self._plot(measureFkt)

			plot_amp.save_png()
			plot_amp.save_gp()
			plot_pha.save_png()
			plot_pha.save_gp()

			data.close_file()
			qt.mend()

		if measureFkt != '2D':
			y_vec_old = self._exchangeXY(y_vec_old)

	def _exchangeXY(self, tmp = None):
		tmp_vec = []
		if tmp:
			self.x_vec = self.y_vec
			self.y_vec = tmp
		else:
			tmp_vec = self.y_vec
			self.y_vec = self.x_vec
			self.x_vec = [0]
		tmp_time = self.tdx
		self.tdx = self.tdy
		self.tdy = tmp_time
		tmp_coordname = self.x_coordname
		self.x_coordname = self.y_coordname
		self.y_coordname = tmp_coordname
		tmp_unit = self.x_unit
		self.x_unit = self.y_unit
		self.y_unit = tmp_unit
		tmp_obj = self.x_set_obj
		self.x_set_obj = self.y_set_obj
		self.y_set_obj = tmp_obj
		return tmp_vec

	def _plot(self, measureFkt, data):
		nop = self.vna.get_nop()
		if measureFkt == '1D':
			plot_amp = qt.Plot2D(data, name='Amplitude', coorddim=0, valdim=int(nop/2)+1)
			plot_pha = qt.Plot2D(data, name='Phase', coorddim=0, valdim=nop+int(nop/2)+1)
		if measureFkt == '1D2':
			plot_amp = qt.Plot3D(data, name='Amplitude 2D2', coorddims=(0,1), valdim=2, style=qt.Plot3D.STYLE_IMAGE)
			plot_amp.set_palette('bluewhitered')
			plot_pha = qt.Plot3D(data, name='Phase 2D2', coorddims=(0,1), valdim=3, style=qt.Plot3D.STYLE_IMAGE)
			plot_pha.set_palette('bluewhitered')
		if measureFkt == '2D':
			if self.plot3D:
				plot_amp = qt.Plot3D(data, name='Amplitude', coorddims=(0,1), valdim=int(nop/2)+2, style=qt.Plot3D.STYLE_IMAGE)
				plot_amp.set_palette('bluewhitered')
				plot_pha = qt.Plot3D(data, name='Phase', coorddims=(0,1), valdim=int(nop/2)+2+nop, style=qt.Plot3D.STYLE_IMAGE)
				plot_pha.set_palette('bluewhitered')
			else:
				plot_amp = qt.Plot2D(data, name='Amplitude', coorddim=1, valdim=int(nop/2)+2)
				plot_pha = qt.Plot2D(data, name='Phase', coorddim=1, valdim=int(nop/2)+2+nop)

		return plot_amp, plot_pha

	def record_trace(self):
		'''
		measure method to record a single (averaged) VNA trace, S11 or S21 according to the setting on the VNA
		
		returns frequency points, data_amp and data_pha when self.return_dat is set
		'''

		qt.mstart()
		self.vna.get_all()
		self.vna.hold(0)   #switch VNA to continuous mode

		print 'recording trace...'
		sys.stdout.flush()

		#creating data object and saving data
		data = qt.Data(name='VNA_tracedata')
		data.add_coordinate('f (Hz)')
		data.add_value('Amplitude (lin.)')
		data.add_value('Phase')
		data.add_value('Real')
		data.add_value('Imag')
		data.create_file()
		
		freq = self.vna.get_freqpoints()
		self.vna.avg_clear()
		sleep(self.vna.get_sweeptime_averages())
		data_amp, data_pha = self.vna.get_tracedata()
		data_real, data_imag = self.vna.get_tracedata('RealImag')

		try:
			for i in np.arange(self.vna.get_nop()):
				f = freq[i]
				am = data_amp[i]
				ph = data_pha[i]
				re = data_real[i]
				im = data_imag[i]
				data.add_data_point(f, am, ph, re, im)
		finally:
			plot_amp = qt.Plot2D(data, name='amplitude', clear=True, needtempfile=True, autoupdate=True, coorddim=0, valdim=1)
			plot_pha = qt.Plot2D(data, name='phase', clear=True, needtempfile=True, autoupdate=True, coorddim=0, valdim=2)
			plot_complex = qt.Plot2D(data, name='Complex Plane', clear=True, needtempfile=True, autoupdate=True, coorddim=3, valdim=4)

			plot_amp.save_png()
			plot_amp.save_gp()
			plot_pha.save_png()
			plot_pha.save_gp()
			plot_complex.save_png()
			plot_complex.save_png()

			data.close_file()
			qt.mend()
		print 'Done.'
		if self.return_dat: return freq, data_amp, data_pha