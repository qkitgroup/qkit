# JB/MP@KIT 04/2015, 08/2015
# VNA measurement class supporting function dependent measurement

import numpy as np
import logging
import matplotlib.pylab as plt
from scipy.optimize import curve_fit
#import time
from time import sleep
import sys
import qt

from qkit.storage import hdf_lib as hdf
from qkit.analysis.resonator import Resonator as resonator
from qkit.gui.plot import plot as qviewkit
from qkit.gui.notebook.Progress_Bar import Progress_Bar

##################################################################

class spectrum(object):
	'''
	usage:

	m = spectrum(vna = vna1)
	m2 = spectrum(vna = vna2, mw_src = mw_src1)	  #where 'vna2'/'mw_src1' is the qt.instruments name

	m.set_x_parameters(arange(-0.05,0.05,0.01),'flux coil current',coil.set_current, unit = 'mA')
	m.set_y_parameters(arange(4e9,7e9,10e6),'excitation frequency',mw_src1.set_frequency, unit = 'Hz')

	m.gen_fit_function(...)	  several times

	m.measure_XX()
	'''

	def __init__(self, vna, exp_name = ''):

		self.vna = vna
		self.exp_name = exp_name

		self.landscape = None
		self.span = 200e6	#[Hz]
		self.tdx = 0.002   #[s]
		self.tdy = 0.002   #[s]
		self.data_complex = False

		self.comment = ''
		self.dirname = None
		self.plot3D = True
		self.plotlive = True

		self.x_set_obj = None
		self.y_set_obj = None

		self.return_dat = False

		self.save_dat = True
		self.save_hdf = False
		self.progress_bar = True
		self._fit_resonator = False
		self._plot_comment=""

	def set_x_parameters(self, x_vec, x_coordname, x_instrument, x_unit = ""):
		'''
		Sets parameters for sweep. In a 2D measurement, the x-parameters will be the "outer" sweep.
		For every x value all y values are swept
		Input:
		x_vec (array): conains the sweeping values
		x_coordname (string)
		x_instrument (obj): callable object to execute with x_vec-values (i.e. vna.set_power())
		x_unit (string): optional
		'''
		self.x_vec = x_vec
		self.x_coordname = x_coordname
		self.x_set_obj = x_instrument
		self.delete_fit_function()
		self.x_unit = x_unit

	def set_y_parameters(self, y_vec, y_coordname, y_instrument, y_unit = ""):
		'''
		Sets parameters for sweep. In a 2D measurement, the x-parameters will be the "outer" sweep.
		For every x value all y values are swept
		Input:
		y_vec (array): contains the sweeping values
		y_coordname (string)
		y_instrument (obj): callable object to execute with x_vec-values (i.e. vna.set_power())
		y_unit (string): optional
		'''
		self.y_vec = y_vec
		self.y_coordname = y_coordname
		self.y_set_obj = y_instrument
		self.delete_fit_function()
		self.y_unit = y_unit

	def set_plot_comment(self, comment):
		'''
		Small comment to add at the end of plot pics for more information i.e. good for wiki entries.
		'''
		self._plot_comment=comment

	def gen_fit_function(self, curve_f, curve_p, units = '', p0 = [-1,0.1,7]):
		'''
		curve_f: 'parab', 'hyp', specifies the fit function to be employed
		curve_p: set of points that are the basis for the fit in the format [[x1,x2,x3,...],[y1,y2,y3,...]], frequencies in Hz
		units: set this to 'Hz' in order to avoid large values that cause the fit routine to diverge
		p0 (optional): start parameters for the fit, must be an 1D array of length 3 ([a,b,c])

		adds a trace to landscape
		'''

		if not self.landscape:
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
		'''
		delete single fit function n (with 0 being the first one generated) or the complete landscape for n not specified
		'''

		if n:
			self.landscape = np.delete(self.landscape, n, axis=0)
		else:
			self.landscape = None


	def plot_fit_function(self, num_points = 100):
		'''
		try:
			x_coords = np.linspace(self.x_vec[0], self.x_vec[-1], num_points)
		except Exception as message:
			print 'no x axis information specified', message
			return
		'''
		if self.landscape:
			for trace in self.landscape:
				try:
					#plt.clear()
					plt.plot(self.x_vec, trace)
					plt.fill_between(self.x_vec, trace+float(self.span)/2, trace-float(self.span)/2, alpha=0.5)
				except Exception:
					print 'invalid trace...skip'
			plt.axhspan(self.y_vec[0], self.y_vec[-1], facecolor='0.5', alpha=0.5)
			plt.show()
		else:
			print 'No trace generated.'

	def measure_1D(self):
		'''
		measure central point of awg window while sweeping one parameter x
		'''

		if not self.x_set_obj:
			logging.error('axes parameters not properly set...aborting')
			return
		self._scan_1D = True
		self._scan_1D2 = False
		self._scan_2D = False
		self.data_complex = False

		if self.dirname == None:
			self.dirname = self.x_coordname.replace(' ', '')
		self._file_name = '1D_' + self.dirname
		if self.exp_name:
			self._file_name += '_' + self.exp_name

		self._p = Progress_Bar(len(self.x_vec),self.dirname)

		self._prepare_measurement_vna()
		if self.save_dat:
			self._prepare_measurement_dat_file()
		if self.save_hdf:
			self._prepare_measurement_hdf_file()
			"""opens qviewkit to plot measurement, amp and pha are opened by default"""
			qviewkit.plot(self._data_hdf.get_filepath(), datasets=['amplitude', 'phase'])
			if self._fit_resonator:
				self._resonator = resonator(self._data_hdf)

		self._measure()
		self._end_measurement()


	def measure_1D2(self):
		'''
		measure full window of vna while sweeping x_set_obj with parameters x_vec
		'''

		if not self.x_set_obj:
			logging.error('axes parameters not properly set...aborting')
			return
		self._scan_1D = False
		self._scan_1D2 = True
		self._scan_2D = False
		self.data_complex = False

		if self.dirname == None:
			self.dirname = self.x_coordname.replace(' ', '')
		self._file_name = '1D2_' + self.dirname
		if self.exp_name:
			self._file_name += '_' + self.exp_name

		self._p = Progress_Bar(len(self.x_vec),self.dirname)

		self._prepare_measurement_vna()
		if self.save_dat:
			self._prepare_measurement_dat_file()
		if self.save_hdf:
			self._prepare_measurement_hdf_file()
			"""opens qviewkit to plot measurement, amp and pha are opened by default"""
			qviewkit.plot(self._data_hdf.get_filepath(), datasets=['amplitude', 'phase'])
			if self._fit_resonator:
				self._resonator = resonator(self._data_hdf)

		self._measure()
		self._end_measurement()


	def measure_2D(self):
		'''
		measure full window of vna while sweeping x_set_obj and y_set_obj with parameters x_vec/y_vec. sweep over y_set_obj is the inner loop, for every value x_vec[i] all values y_vec are measured.

		optional: measure method to perform the measurement according to landscape, if set
		self.span is the range (in units of the vertical plot axis) data is taken around the specified funtion(s)
		note: make sure to have properly set x,y vectors before generating traces
		'''
		if not self.x_set_obj or not self.y_set_obj:
			logging.error('axes parameters not properly set...aborting')
			return
		self._scan_1D = False
		self._scan_1D2 = False
		self._scan_2D = True
		self.data_complex = False

		if self.dirname == None:
			self.dirname = self.x_coordname.replace(' ', '') + '_' + self.y_coordname.replace(' ', '')
		self._file_name = '2D_' + self.dirname
		if self.exp_name:
			self._file_name += '_' + self.exp_name

		self._p = Progress_Bar(len(self.x_vec)*len(self.y_vec),self.dirname)

		self._prepare_measurement_vna()
		if self.save_dat:
			self._prepare_measurement_dat_file()
		if self.save_hdf:
			self._prepare_measurement_hdf_file()
			if self._fit_resonator:
				self._resonator = resonator(self._data_hdf)

		if self.landscape:
			self.center_freqs = np.array(self.landscape).T
		else:
			self.center_freqs = []	 #load default sequence
			for i in range(len(self.x_vec)):
				self.center_freqs.append([0])

		self._measure()
		self._end_measurement()

	def set_fit(self,fit_resonator=True,fit_function='',f_min=None,f_max=None):
		'''
		sets fit parameter for resonator

		fit_resonator (bool): True or False, default: True (optional)
		fit_function (string): function which will be fitted to the data (optional)
		f_min (float): lower frequency boundary for the fitting function, default: None (optional)
		f_max (float): upper frequency boundary for the fitting function, default: None (optional)
		'''
		if not fit_resonator:
			self._fit_resonator = False
			return
		self._functions = {'lorentzian':0,'skewed_lorentzian':1,'circle_fit':2,'fano':3,'all_fits':4}
		try:
			self._fit_function = self._functions[fit_function]
		except KeyError:
			logging.error('Fit function not properly set. Must be either \'lorentzian\', \'skewed_lorentzian\', \'circle_fit\', \'fano\', or \'all_fits\'.')
		else:
			self._fit_resonator = True
			self._f_min = f_min
			self._f_max = f_max

	def _do_fit_resonator(self):
		'''
		calls fit function in resonator class
		fit function is specified in self.set_fit, with boundaries f_mim and f_max
		only the last 'slice' of data is fitted, since we fit live while measuring.
		'''

		if self._fit_function == self._function['lorentzian']:
			self._resonator.fit_lorentzian(f_min=self._f_min, f_max = self._f_max)
		if self._fit_function == self._function['skewed_lorentzian']:
			self._resonator.fit_skewed_lorentzian(f_min=self._f_min, f_max = self._f_max)
		if self._fit_function == self._function['circle']:
			self._resonator.fit_circle(f_min=self._f_min, f_max = self._f_max)
		if self._fit_function == self._function['fano']:
			self._resonator.fit_fano(f_min=self._f_min, f_max = self._f_max)
		#if self._fit_function == self._function['all_fits']:
			#self._resonator.fit_all_fits(f_min=self._f_min, f_max = self._f_max)

	def _prepare_measurement_vna(self):
		'''
		all the relevant settings from the vna are updated and called
		'''

		self.vna.get_all()
		#ttip.get_temperature()
		self._nop = self.vna.get_nop()
		self._sweeptime_averages = self.vna.get_sweeptime_averages()
		self._freqpoints = self.vna.get_freqpoints()

	def _prepare_measurement_dat_file(self, trace=False):
		'''
		creates the output .dat-file with distict structure for each meaurement type.
		
		trace indicates single trace recording, x_coordinate needs not to be written
		'''

		self._data_dat = qt.Data(name=self._file_name)
		if self.comment:
			self._data_dat.add_comment(self.comment)
		if not trace: self._data_dat.add_coordinate(self.x_coordname + ' '+self.x_unit)
		if self._scan_1D2:
			self._data_dat.add_coordinate('Frequency (Hz)')
			self._data_dat.add_value('Amplitude (V)')
			self._data_dat.add_value('Phase (pi)')
			if self.data_complex:
				self._data_dat.add_value('Real')
				self._data_dat.add_value('Img')
		else:
			if self._scan_2D:
				self._data_dat.add_coordinate(self.y_coordname + ' ' +self.y_unit)
			for i in range(1,self._nop+1):
				self._data_dat.add_value(('Point %i Amp' %i))
			for i in range(1,self._nop+1):
				self._data_dat.add_value(('Point %i Pha' %i))

		self._data_dat.create_file()

	def _prepare_measurement_hdf_file(self,trace=False):
		'''
		creates the output .h5-file with distinct dataset structures for each measurement type.
		the filename is borrowed from the .dat-file to put them into the same folder.
		at this point all measurement parameters are known and put in the output file
		'''
		if self.save_dat:
			filename = str(self._data_dat.get_filepath()).replace('.dat','.h5')
		else:
			filename = str(self._file_name) + '.h5'
		self._data_hdf = hdf.Data(name=self._file_name, path=filename)
		self._hdf_freq = self._data_hdf.add_coordinate('frequency', unit = 'Hz')
		self._hdf_freq.add(self._freqpoints)
		if not trace:
			self._hdf_x = self._data_hdf.add_coordinate(self.x_coordname, unit = self.x_unit)
			self._hdf_x.add(self.x_vec)
		self._hdf_real = self._data_hdf.add_value_vector('real', x = self._hdf_freq, unit = '')
		self._hdf_imag = self._data_hdf.add_value_vector('imag', x = self._hdf_freq, unit = '')
		if trace:
			self._hdf_real = self._data_hdf.add_value_vector('amplitude', x = self._hdf_freq, unit = 'V')
			self._hdf_imag = self._data_hdf.add_value_vector('phase', x = self._hdf_freq, unit = 'rad')
		elif self._scan_2D:
			self._hdf_y = self._data_hdf.add_coordinate(self.y_coordname, unit = self.y_unit)
			self._hdf_y.add(self.y_vec)
			self._hdf_amp = self._data_hdf.add_value_box('amplitudes', x = self._hdf_x, y = self._hdf_y, z = self._hdf_freq, unit = 'V')
			self._hdf_pha = self._data_hdf.add_value_box('phases', x = self._hdf_x, y = self._hdf_y, z = self._hdf_freq, unit = 'rad')
		else:
			self._hdf_amp = self._data_hdf.add_value_matrix('amplitude', x = self._hdf_x, y = self._hdf_freq, unit = 'V')
			self._hdf_pha = self._data_hdf.add_value_matrix('phase', x = self._hdf_x, y = self._hdf_freq, unit='rad')
		if self.comment:
			self._data_hdf.add_comment(self.comment)

	def _measure(self):
		'''
		measures and plots the data depending on the measurement type.
		the measurement loops feature the setting of the objects and saving the data in the
		.dat and/or .h5 files.
		'''
		qt.mstart()
		if not self.save_hdf or self._scan_2D:
			'''
			we use our own qviewkit for liveplotting the data. plotting a 2D scan is
			not yet implemented.
			'''
			if self.plotlive:
				self._plot_dat_file()

		try:
			"""
			loop: x_obj with data from x_vec
			"""
			for i, x in enumerate(self.x_vec):
				self.x_set_obj(x)
				sleep(self.tdx)
				dat=[]

				if self._scan_2D:
					for y in self.y_vec:
						"""
						loop: x_obj with data from x_vec (only 2D measurement)
						"""
						if (np.min(np.abs(self.center_freqs[i]-y*np.ones(len(self.center_freqs[i])))) > self.span/2.) and self.landscape:	#if point is not of interest (not close to one of the functions)
							data_amp = np.zeros(int(self._nop))
							data_pha = np.zeros(int(self._nop))	  #fill with zeros
						else:
							self.y_set_obj(y)
							sleep(self.tdy)
							self.vna.avg_clear()
							sleep(self._sweeptime_averages)
							""" measurement """
							data_amp, data_pha = self.vna.get_tracedata()
						if self.save_dat:
							dat = np.append(x, y)
							dat = np.append(dat,data_amp)
							dat = np.append(dat,data_pha)
							self._data_dat.add_data_point(*dat)
							self._data_dat.new_block()
						if self.save_hdf:
							self._hdf_amp.append(data_amp)
							self._hdf_pha.append(data_pha)
							if self._fit_resonator:
								self._do_fit_resonator()

						if self.plotlive and not self.save_hdf:
							qt.msleep(0.1)
							self._plot_amp.update()
							self._plot_pha.update()
						if self.progress_bar:
							self._p.iterate()

				if self._scan_1D:
					self.vna.avg_clear()
					sleep(self._sweeptime_averages)
					""" measurement """
					data_amp, data_pha = self.vna.get_tracedata()
					if self.save_dat:
						dat = np.append(x, data_amp)
						dat = np.append(dat, data_pha)
						self._data_dat.add_data_point(*dat)
					if self.save_hdf:
						self._hdf_amp.append(data_amp)
						self._hdf_pha.append(data_pha)
						if self._fit_resonator:
							self._do_fit_resonator()
					if self.progress_bar:
						self._p.iterate()

				if self._scan_1D2:
					self.vna.avg_clear()
					sleep(self._sweeptime_averages)
					""" measurement """
					data_amp, data_pha = self.vna.get_tracedata()
					if self.save_dat:
						dat = np.append([x*np.ones(self._nop)],[self._freqpoints], axis = 0)
						dat = np.append(dat,[data_amp],axis = 0)
						dat = np.append(dat,[data_pha],axis = 0)
						self._data_dat.add_data_point(*dat)
						self._data_dat.new_block()
					if self.save_hdf:
						self._hdf_amp.append(data_amp)
						self._hdf_pha.append(data_pha)
						if self._fit_resonator:
							self._do_fit_resonator()
					if self.progress_bar:
						self._p.iterate()

				if not self.save_hdf and self.plotlive:
					qt.msleep(0.1)
					self._plot_amp.update()
					self._plot_pha.update()

		finally:
			if self.save_dat:
				if not self.plotlive:
					self._plot_dat_file()
					self._plot_amp.update()
					self._plot_pha.update()

				self._plot_amp.save_png()
				self._plot_amp.save_gp()
				self._plot_pha.save_png()
				self._plot_pha.save_gp()

			qt.mend()

	def _end_measurement(self):
		'''
		the data files are closed and their filepaths are printed
		'''
		if self.save_dat:
			print self._data_dat.get_filepath()
			self._data_dat.close_file()
		if self.save_hdf:
			print self._data_hdf.get_filepath()
			qviewkit.save_plots(self._data_hdf.get_filepath(),comment=self._plot_comment)
			self._data_hdf.close_file()

	def _plot_dat_file(self):
		'''
		plots measured data in gnuplot:
		1D: amp/pha vs x_vec (1D plot for middle freqpoint)
		1D2: freq vs x_vec (color plot with amp/pha trace color coded)
		2D: x_vec vs y_vec (color plot with amp/pha of middle freqpoint color coded)
		'''
		if self._scan_1D:
			self._plot_amp = qt.Plot2D(self._data_dat, name='Amplitude', coorddim=0, valdim=int(self._nop/2)+1)
			self._plot_pha = qt.Plot2D(self._data_dat, name='Phase', coorddim=0, valdim=self._nop+int(self._nop/2)+1)
		if self._scan_1D2:
			self._plot_amp = qt.Plot3D(self._data_dat, name='Amplitude 1D2', coorddims=(0,1), valdim=2, style=qt.Plot3D.STYLE_IMAGE)
			self._plot_amp.set_palette('bluewhitered')
			self._plot_pha = qt.Plot3D(self._data_dat, name='Phase 1D2', coorddims=(0,1), valdim=3, style=qt.Plot3D.STYLE_IMAGE)
			self._plot_pha.set_palette('bluewhitered')
		if self._scan_2D:
			if self.plot3D:
				self._plot_amp = qt.Plot3D(self._data_dat, name='Amplitude', coorddims=(0,1), valdim=int(self._nop/2)+2, style=qt.Plot3D.STYLE_IMAGE)
				self._plot_amp.set_palette('bluewhitered')
				self._plot_pha = qt.Plot3D(self._data_dat, name='Phase', coorddims=(0,1), valdim=int(self._nop/2)+2+self._nop, style=qt.Plot3D.STYLE_IMAGE)
				self._plot_pha.set_palette('bluewhitered')
			else:
				self._plot_amp = qt.Plot2D(self._data_dat, name='Amplitude', coorddim=1, valdim=int(self._nop/2)+2)
				self._plot_pha = qt.Plot2D(self._data_dat, name='Phase', coorddim=1, valdim=int(self._nop/2)+2+self._nop)

	def record_trace(self):
		'''
		measure method to record a single (averaged) VNA trace, S11 or S21 according to the setting on the VNA

		returns frequency points, data_amp and data_pha when self.return_dat is set
		'''
		qt.mstart()
		self._prepare_measurement_vna()
		try:
			self.vna.hold(0)   #switch VNA to continuous mode
		except AttributeError:
			try:
				self.vna.set_hold(0)
			except Exception as message:
				print 'VNA might be in hold mode', message

		print 'recording trace...'
		sys.stdout.flush()

		#use 1D2 functions
		self._scan_1D = False
		self._scan_1D2 = True
		self._scan_2D = False
		self.data_complex = True

		#creating data object
		self.dirname = 'VNA_tracedata'
		self._file_name = self.dirname
		if self.exp_name:
			self._file_name += '_' + self.exp_name
		self._prepare_measurement_dat_file(trace=True)

		self.vna.avg_clear()
		if self.vna.get_averages() == 1 or self.vna.get_Average() == False:   #no averaging
			p = Progress_Bar(1,self.dirname)
			qt.msleep(self.vna.get_sweeptime())	  #wait single sweep
			p.iterate()
		else:   #with averaging
			p = Progress_Bar(self.vna.get_averages(),self.dirname)
			for a in range(self.vna.get_averages()):
				qt.msleep(self.vna.get_sweeptime())	  #wait single sweep time
				p.iterate()

		data_amp, data_pha = self.vna.get_tracedata()
		data_real, data_imag = self.vna.get_tracedata('RealImag')

		if self.save_dat:
			for i in np.arange(self._nop):
				self._data_dat.add_data_point(self._freqpoints[i], data_amp[i], data_pha[i], data_real[i], data_imag[i])
		if self.save_hdf:
			self._prepare_measurement_hdf_file(trace=True)
			self._hdf_amp.append(data_amp)
			self._hdf_pha.append(data_pha)
			self._hdf_real.append(data_real)
			self._hdf_imag.append(data_imag)
			if self._fit_resonator:
				self._do_fit_resonator()

		plot_amp = qt.Plot2D(self._data_dat, name='amplitude', clear=True, needtempfile=True, autoupdate=True, coorddim=0, valdim=1)
		plot_pha = qt.Plot2D(self._data_dat, name='phase', clear=True, needtempfile=True, autoupdate=True, coorddim=0, valdim=2)
		plot_complex = qt.Plot2D(self._data_dat, name='Complex Plane', clear=True, needtempfile=True, autoupdate=True, coorddim=3, valdim=4)

		plot_amp.save_png()
		plot_amp.save_gp()
		plot_pha.save_png()
		plot_pha.save_gp()
		plot_complex.save_png()
		plot_complex.save_png()

		self._data_dat.close_file()
		qt.mend()
		#print 'Done.'
		if self.return_dat: return self._freqpoints, data_amp, data_pha

	def set_span(self, span):
		self.span = span

	def get_span(self):
		return self.span

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
