# modified and adapted by JB@KIT 04/2015
# time domain measurement class

import qt
import numpy as np
import os.path
import time
import logging
import sys

from qkit.gui.notebook.Progress_Bar import Progress_Bar
#from qkit.plot.plot import plot as qviewkit
from qkit.storage import hdf_lib as hdf

readout = qt.instruments.get('readout')
mspec = qt.instruments.get('mspec')
vcoil = qt.instruments.get('vcoil')

class Measure_td(object):
	
	'''
	useage:
	
	m = Measure_td()
	
	m.set_x_parameters(arange(-0.05,0.05,0.01),'flux coil current (mA)',coil.set_current)
	m.set_y_parameters(arange(4e9,7e9,10e6),'excitation frequency (Hz)',mw_src1.set_frequency)
	
	m.measure_XX()
	'''
	
	def __init__(self, exp_name = ''):
	
		self.exp_name = exp_name

		self.plotLive = True
		self.plot2d = False

		self.plotFast = False
		self.plotTime = True

		self.save_dat = True
		self.save_hdf = False
		
		self.dirname = ''
		self.plotSuffix = ''
		self.comment = ''

		self.iterations = 1

	def set_x_parameters(self, x_vec, x_coordname, x_set_obj, x_unit = ''):
		self.x_vec = x_vec
		self.x_coordname = x_coordname
		self.x_set_obj = x_set_obj
		self.x_unit = x_unit
		
	def set_y_parameters(self, y_vec, y_coordname, y_set_obj, y_unit = ''):
		self.y_vec = y_vec
		self.y_coordname = y_coordname
		self.y_set_obj = y_set_obj
		self.y_unit = y_unit
		
	def measure_1D(self):
		if not self.x_set_obj:
			logging.error('axes parameters not properly set...aborting')
			return
		self._measure_1D = True
		self._measure_2D = False
		self._measure_awg = False

		if not self.dirname:
			self.dirname = self.x_coordname
		if self.exp_name:
			self.dirname += '_'+self.exp_name
		self._file_name = '1d_%s'%(self.dirname)

		self._ndav = readout.readout(False)[0].size
		self._p = Progress_Bar(len(self.x_vec)*self._iterations)

		if self.save_dat:
			self._data_dat = self._prepare_measurement_dat_file(filename = self._filename)
		if self.save_hdf:
			self._data_hdf = self._prepare_measurement_hdf_file(filename=self._file_name, filepath = str(self._data_dat.get_filepath()).replace('.dat','.h5'))
			
		self._measure()
		self._end_measurement()
	
	def measure_2D(self):
		if not self.x_set_obj or not self.y_set_obj:
			logging.error('axes parameters not properly set...aborting')
			return
		self._measure_1D = False
		self._measure_2D = True
		self._measure_awg = False

		if not self.dirname:
			self.dirname = '%s_%s'%(self.x_coordname, self.y_coordname)
		if self.exp_name:
			self.dirname += '_'+self.exp_name
		self._file_name = '2d_%s'%(self.dirname)

		self._ndav = readout.readout(timeTrace = True)[0].size
		self._nsamp = readout._ins._mspec.get_samples()
		self._p = Progress_Bar(len(self.x_vec)*len(self.y_vec)*self._iterations)

		if self.save_dat:
			self._data_dat = self._prepare_measurement_dat_file(filename = self._filename)
			self._time_dat = self._prepare_time_dat_file(filename = 'avgt_%s'%(self.dirname), filepath = str(self._data_dat.get_filepath()).replace('.dat','_time.dat'))
		if self.save_hdf:
			self._data_hdf = self._prepare_measurement_hdf_file(filename=self._file_name, filepath = str(self._data_dat.get_filepath()).replace('.dat','.h5'))
			self._time_hdf = self._prepare_time_hdf_file(filename = 'avgt_%s'%(self.dirname), filepath = str(self._data_dat.get_filepath()).replace('.dat','_time.h5'))
		self._measure()
		self._end_measurement()

	def _prepare_measurement_dat_file(self, filename = '', filepath = '', timestamp = True):
		if not filepath:
			data_dat = qt.Data(name = filename)
		else:
			data_dat = qt.Data(name = filename, path = filepath)
		if self.comment:
			data_dat.add_comment(self.comment)
		data_dat.add_coordinate('# iterations')
		data_dat.add_coordinate(self.x_coordname)
		if self._measure_2D or self._measure_2D_awg:
			data_dat.add_coordinate(self.y_coordname)
		for i in range(self._ndev):
			data_dat.add_value('amp_%d'%i)
		for i in range(self._ndev):
			data_dat.add_value('pha_%d'%i)
		if timestamp:
			data_dat.add_value('timestamp')
		data_dat.create_file()
		return data_dat
		
	def _prepare_measurement_hdf_file(self, filename = '', filepath = '', timestamp = True):
		self._data_hdf = hdf.Data(name=filename, path=filepath)
		self._hdf_x = self._data_hdf.add_coordinate(self.x_coordname, unit = self.x_unit)
		self._hdf_x.add(self.x_vec)

		self._hdf_ndev = self._data_hdf.add_coordinate("# dev")
		self._hdf_ndev.add(range(self.ndev))
		self._hdf_iterations = self._data_hdf.add_coordinate("# iterations")
		self._hdf_iterations.add(range(self.iterations))
		if self._measure_1D or self._measure_1D_awg:
			if timestamp:
				self._hdf_timestamp = self._data_hdf.add_value_matrix('timestamp', x = self._hdf_iterations, y = self._hdf_x, unit = '')
			self._hdf_amp = self._data_hdf.add_value_box('amplitude', x = self._hdf_iterations, y = self._hdf_x, z = self._hdf_ndev, unit = 'V')
			self._hdf_pha = self._data_hdf.add_value_box('phase', x = self._hdf_iterations, y = self._hdf_x, z =  self._hdf_ndev, unit = 'pi')
		if self._measure_2D or self._measure_2D_awg:
			self._hdf_y = self._data_hdf.add_coordinate(self.y_coordname, unit = self.y_unit)
			self._hdf_y.add(self.y_vec)
			if timestamp:
				self._hdf_timestamp = self._data_hdf.add_value_box('timestamp', x = self._hdf_iterations, y = self._hdf_x, z = self._hdf_y, unit = '')
			self._hdf_amp = self._data_hdf.add_value_hyperbox('amplitude', x = self._hdf_iterations, y = self._hdf_x, z = self._hdf_y, alpha = self._hdf_ndev, unit = 'V')
			self._hdf_pha = self._data_hdf.add_value_hyperbox('phase', x = self._hdf_iterations, y = self._hdf_x, z = self._hdf_y, alpha = self._hdf_ndev, unit = 'pi')

	def _prepare_time_dat_file(self, filename = '', filepath = ''):
		time_dat = qt.Data(name=filename, path = filepath)
		if self.comment:
			time_dat.add_comment(self.comment)
		time_dat.add_coordinate(self.x_coordname)
		if self._measure_2D:
			time_dat.add_coordinate(self._y_coordname)
		for i in range(self._nsamp):
			time_dat.add_value('I%3d'%i)
		for i in range(self._nsamp):
			time_dat.add_value('Q%3d'%i)
		time_dat.add_value('timestamp')
		time_dat.create_file()
		return time_dat
		
	def _prepare_time_hdf_file(self, filename = '', filepath = ''):
		time_hdf = hdf.Data(name=filename, path=filename)
		self._hdf_x_time = time_hdf.add_coordinate(self.x_coordname, unit = self.x_unit)
		self._hdf_x_time.add(self.x_vec)
		self._hdf_nsamp = time_hdf.add_coordinate("# sample")
		self._hdf_nsamp.add(np.round(np.array(range(self.nsamp))), 3)
		self._hdf_iterations_time = time_hdf.add_coordinate("# iterations")
		self._hdf_iterations_time.add(range(self.iterations))
		if self._measure_2D or self._measure_2D_awg:
			self._hdf_y_time = time_hdf.add_coordinate(self.y_coordname, unit = self.y_unit)
			self._hdf_y_time.add(self.y_vec)
		
			self._hdf_i = time_hdf.add_value_hyperbox('I', x = self._hdf_iterations_time, y = self._hdf_x_time, z = self._hdf_y_time, alpha = self._hdf_nsamp, unit = '')
			self._hdf_q = time_hdf.add_value_hyperbox('Q', x= self._hdf_iterations_time, y = self._hdf_x_time, z = self._hdf_y_time, alpha = self._hdf_nsamp, unit = '')
			self._hdf_timestamp_time = time_hdf.add_value_box('timestamp', x = self._hdf_iterations, y = self._hdf_x, z = self._hdf_y, unit = '')
		if self._measure_1D or self._measure_1D_awg:
			self._hdf_i = time_hdf.add_value_box('I', x = self._hdf_iterations_time, y = self._hdf_x_time, z = self._hdf_nsamp, unit = '')
			self._hdf_q = time_hdf.add_value_box('Q', x= self._hdf_iterations_time, y = self._hdf_x_time, z = self._hdf_nsamp, unit = '')
			self._hdf_timestamp_time = time_hdf.add_value_matrix('timestamp', x = self._hdf_iterations, y = self._hdf_x, unit = '')
		
	def _measure(self):
		qt.mstart()
		
		self._plots = []
		if self.plotLive:
			self._plot()

		try:
			# measurement loop
			for it in range(self.iterations):
				for x in self.x_vec:
					self.x_set_obj(x)
					if self._measure_2D:
						for y in self.y_vec:
							self.y_set_obj(y)
							dat_amp, dat_pha, Is, Qs = readout.readout(timeTrace = True)
							timestamp = time.time()
							if self.save_dat:
								# save standard data
								dat = np.array([x, y])
								dat = np.append(dat, dat_amp)
								dat = np.append(dat, dat_pha)
								dat = np.append(dat, timestamp)
								self._data_dat.add_data_point(*dat)

								# save time-domain data
								dat = np.array([x, y])
								dat = np.append(dat, Is[:])
								dat = np.append(dat, Qs[:])
								dat = np.append(dat, timestamp)
								self._time_dat.add_data_point(*dat)
							if self.save_hdf:
								self._hdf_amp.append(dat_amp)
								self._hdf_pha.append(dat_pha)
								self._hdf_timestamp.append(timestamp)
								
								self._hdf_timestamp_time.append(timestamp)
								self._hdf_i.append(Is[:])
								self._hdf_q.append(Qs[:])
							self._p.iterate()
	
						if self.plotLive: # point-wise update
							for plot in self._plots:
								plot.update()

						self._data_dat.new_block()
						self._time_dat.new_block()
					if self._measure_1D:
						dat_amp, dat_pha = readout.readout(False)
						timestamp = time.time()
						if self.save_dat:
							dat = np.array([x])
							dat = np.append(dat, dat_amp)
							dat = np.append(dat, dat_pha)
							dat = np.append(dat, timestamp)
							self._data_dat.add_data_point(*dat)
						if self.save_hdf:
							self._hdf_amp.append(dat_amp)
							self._hdf_pha.append(dat_pha)
							self._hdf_timestamp.append(timestamp)
						self._p.iterate()
					if self.plotLive:
						for plot in self._plots:
							plot.update()
		finally:
			for plot in self._plots:
				plot.update()
				plot.save_gp()
				plot.save_png()
			qt.mend()

	def _plot(self):
		if self._measure_1D:
			for i in range(self._ndev):
				plot_amp = qt.Plot2D(self._data_dat, name='amplitude_%d%s'%(i, self.plotSuffix), coorddim=0, valdim=1+i)
				plot_pha = qt.Plot2D(self._data_dat, name='phase_%d%s'%(i, self.plotSuffix), coorddim=0,
 valdim=1+self._ndev+i)
				self._plots.append(plot_amp)
				self._plots.append(plot_pha)
		if self._measure_2D:
			for i in range(self._ndev):
				# standard 2d plot
				if self.plot3d:
					plot_amp = qt.Plot3D(self._data_dat, name='amplitude_%d_3d%s'%(i, self.plotSuffix), coorddims=(0,1), valdim=2+i)
					plot_pha = qt.Plot3D(self._data_dat, name='phase_%d_3d%s'%(i, self.plotSuffix), coorddims=(0,1), valdim=2+self._ndev+i)
					plot_amp.set_palette('bluewhitered')
					plot_pha.set_palette('bluewhitered')
					self._plots.append(plot_amp)
					self._plots.append(plot_pha)
				# time-resolved plot
				if self.plot2d:
					plot_amp_2d = qt.Plot2D(self._data_dat, name='amplitude_%d%s_single'%(i, self.plotSuffix), coorddim=1, valdim=2+i, maxtraces = 2)
					plot_pha_2d = qt.Plot2D(self._data_dat, name='phase_%d%s_single'%(i, self.plotSuffix), coorddim=1, valdim=2+self._ndev+i, maxtraces = 2)
					self._plots.append(plot_amp_2d)
					self._plots.append(plot_pha_2d)

	def _end_measurement(self):
		if self.save_dat:
			print self._data_dat.get_filepath()
			self._data_dat.close_file()
		if self.save_hdf:
			print self._data_hdf.get_filepath()
			self._data_hdf.close_file()

	def measure_1D_AWG(self):
		if not self.x_set_obj:
			logging.error('axes parameters not properly set...aborting')
			return
	
		'''
		x_vec is sequence in AWG
		'''
		self._measure_1D = False
		self._measure_2D = False
		self._measure_1D_awg = True
		self._measure_2D_awg = False


		if not self.dirname:
			self.dirname = self.x_coordname
		if self.exp_name:
			self.dirname += '_'+self.exp_name
		self._file_name = 'avg_%s'%(self.dirname)

		self._ndav = len(readout.get_tone_freq)
		self._nsamp = mspec.get_samples()

		self._p = Progress_Bar(len(self.x_vec)*self.iterations)

		if self.save_dat:
			# create data files for:
			# - time-resolved raw data
			# - time-resolved successive-averaged data
			# - time-averaged data
			# - raw I/Q data
			self._data_raw_dat = self._prepare_measurement_dat_file(filename = self._filename)
			self._data_sum_dat = self._prepare_measurement_dat_file(filename = 'avgs_%s'%(self.dirname), filepath = str(self._data_raw_dat.get_filepath()).replace('.dat','_sum.dat'), timestamp = False)
			self._data_avg_dat = self._prepare_measurement_dat_file(filename = 'avga_%s'%(self.dirname), filepath = str(self._data_raw.get_filepath()).replace('.dat','_avg.dat'), timestamp = False)
			self._time_dat = self._prepare_time_dat_file(filename = 'avgt_%s'%(self.dirname), filepath = str(self._data_raw.get_filepath()).replace('.dat','_time.dat'))

		if self.save_hdf:
			self._data_raw_hdf = self._prepare_measurement_hdf_file(filename=self._file_name, filepath = str(self._data_raw_dat.get_filepath()).replace('.dat','.h5'))
			self._data_sum_hdf = self._prepare_measurement_hdf_file(filename='avgs_%s'%(self.dirname), filepath = str(self._data_sum_dat.get_filepath()).replace('.dat','.h5'), timestamp = False)
			self._data_avg_hdf = self._prepare_measurement_hdf_file(filename='avga_%s'%(self.dirname), filepath = str(self._data_avg_dat.get_filepath()).replace('.dat','.h5'), timestamp = False)
			self._time_hdf = self._prepare_time_hdf_file(filename = 'avgt_%s'%(self.dirname), filepath = str(self._data_raw.get_filepath()).replace('.dat','_time.h5'))
			
		self._measure()
		self._end_measurement()

	def measure_2D_AWG(self):
		if not self.y_set_obj:
			logging.error('axes parameters not properly set...aborting')
			return
	
		'''
		x_vec is sequence in AWG
		'''
		self._measure_1D = False
		self._measure_2D = False
		self._measure_1D_awg = False
		self._measure_2D_awg = True


		if not self.dirname:
			self.dirname = self.x_coordname
		if self.exp_name:
			self.dirname += '_'+self.exp_name
		self._file_name = 'avg_2D_%s'%(self.dirname)

		self._ndav = len(readout.get_tone_freq)
		self._nsamp = mspec.get_samples()

		self._p = Progress_Bar(len(self.y_vec)*len(self.x_vec)*self.iterations)

		if self.save_dat:
			# create data files for:
			# - time-resolved raw data
			# - time-resolved successive-averaged data
			# - time-averaged data
			# - raw I/Q data
			self._data_raw_dat = self._prepare_measurement_dat_file(filename = self._filename)
			self._data_sum_dat = self._prepare_measurement_dat_file(filename = 'avgs_%s'%(self.dirname), filepath = str(self._data_raw_dat.get_filepath()).replace('.dat','_sum.dat'))
			self._data_avg_dat = self._prepare_measurement_dat_file(filename = 'avga_%s'%(self.dirname), filepath = str(self._data_raw.get_filepath()).replace('.dat','_avg.dat'))
			self._time_dat = self._prepare_time_dat_file(filename = 'avgt_%s'%(self.dirname), filepath = str(self._data_raw.get_filepath()).replace('.dat','_time.dat'))

		if self.save_hdf:
			self._data_raw_hdf = self._prepare_measurement_hdf_file(filename=self._file_name, filepath = str(self._data_raw_dat.get_filepath()).replace('.dat','.h5'))
			self._data_sum_hdf = self._prepare_measurement_hdf_file(filename='avgs_%s'%(self.dirname), filepath = str(self._data_sum_dat.get_filepath()).replace('.dat','.h5'))
			self._data_avg_hdf = self._prepare_measurement_hdf_file(filename='avga_%s'%(self.dirname), filepath = str(self._data_avg_dat.get_filepath()).replace('.dat','.h5'))
			self._time_hdf = self._prepare_time_hdf_file(filename = 'avgt_%s'%(self.dirname), filepath = str(self._data_raw.get_filepath()).replace('.dat','_time.h5'))

		self._measure()
		self._end_measurement()


		qt.mstart()
		qt.msleep() # if stop button was pressed by now, abort without creating data files

		plots = []
		for i in range(self._ndev):
			# time-resolved plot
			if self.plotTime:
				plot_amp = qt.Plot3D(self._data_raw_dat, name='amplitude_%d_3d%s'%(i, self.plotSuffix), coorddims=(0,1), valdim=2+i)
				plot_amp.set_palette('bluewhitered')
				plots.append(plot_amp)
				plot_pha = qt.Plot3D(self._data_raw_dat, name='phase_%d_3d%s'%(i, self.plotSuffix), coorddims=(0,1), valdim=2+self._ndev+i)
				plot_pha.set_palette('bluewhitered')
				plots.append(plot_pha)
			# averaged plot
			plot_amp = qt.Plot2D(self._data_sum_dat, name='amplitude_%d%s'%(i, self.plotSuffix), coorddim=1, valdim=2+i, maxtraces = 2)
			plot_pha = qt.Plot2D(self._data_sum_dat, name='phase_%d%s'%(i, self.plotSuffix), coorddim=1, valdim=2+self._ndev+i, maxtraces = 2)
			plots.append(plot_amp)
			plots.append(plot_pha)

		# buffer successive sum for averaged plot
		dat_cmpls = np.zeros((len(self.x_vec), self._ndev), np.complex128)
		dat_ampa = np.zeros_like((len(self.x_vec), self._ndev))
		dat_phaa = np.zeros_like(dat_ampa)
		# save plot even when aborted
		try:
			# measurement loop
			#starttime=time.time()
			for it in range(self.iterations):
				qt.msleep() # better done during measurement (waiting for trigger)
				
				if self.measure_2D_awg:
					self.y_set_obj(self.y_vec[it])

				dat_amp, dat_pha, Is, Qs = readout.readout(timeTrace = True)
				timestamp = time.time()
				
				dat_cmpls += dat_amp * np.exp(1j*dat_pha)
				dat_ampa = np.abs(dat_cmpls/(it+1))
				dat_phaa = np.angle(dat_cmpls/(it+1))

				if self.save_dat:
					# save raw frequency-domain data (qubit points only)
					self._data_raw.new_block()
					self._data_time_dat.new_block()
					self._data_sum_dat.new_block()
					for xi in range(len(self.x_vec)):
						dat = np.array([self.y_vec[it], self.x_vec[xi]])
						dat = np.append(dat, dat_amp[xi, :])
						dat = np.append(dat, dat_pha[xi, :])
						dat = np.append(dat, timestamp)
						self._data_raw_dat.add_data_point(*dat)
						# save time-domain data
						dat = np.array([self.y_vec[it], self.x_vec[xi]])
						dat = np.append(dat, Is[:, xi])
						dat = np.append(dat, Qs[:, xi])
						dat = np.append(dat, timestamp)
						self._data_time_dat.add_data_point(*dat)
						# save successively averaged frequency-domain data
						dat = np.array([it, self.x_vec[xi]])
						dat = np.append(dat, dat_ampa[xi, :])
						dat = np.append(dat, dat_phaa[xi, :])
						self._data_sum_dat.add_data_point(*dat)

				if self.plotLive:
					for plot in plots:
						plot.update()

				self._p.iterate()

		except Exception as e:
			logging.error(e)
		finally:
			for plot in plots:
				plot.update()
				plot.save_gp()
				plot.save_png()

			# save final averaged data in a separate file
			if dat_ampa != None:
				#print 'avg'
				data_avg.create_file(None, '%s_avg.dat'%data_fn, False)
				dat = np.concatenate((np.atleast_2d(self.x_vec).transpose(), dat_ampa, dat_phaa), 1)
				for xi in range(dat.shape[0]):
					data_avg.add_data_point(*dat[xi, :])
				data_avg.close_file()
			#dat_raw = data.get_reshaped_data()
			#dat_avg = dat_raw[0, :, 1]
			#dat_cmpl = np.mean(dat_raw[:, :, 2:2+ndev]*np.exp(1j*dat_raw[:, :, 2+ndev:2+2*ndev]), 0)
			#dat_avg = np.concatenate((dat_raw[0, :, 1:2], np.abs(dat_cmpl), np.angle(dat_cmpl)), 1)
			#data_avg.add_data_point(dat_avg)
			data_raw.close_file()
			data_sum.close_file()
			data_time.close_file()
			
			qt.mend()



"""
def measure_1d2(mspec, x_vec, coordname, set_param_func, comment = None, dirname = None, plotLive = True, plot3d = False):

	'''
	measure I and Q signals in time domain (rather than doinf the FFT and looking at the frequency point (fr +- 30MHz?)
	'''

		qt.mstart()

		if(dirname == None): dirname = coordname
		data = qt.Data(name='spec_%s'%dirname)
		if comment: data.add_comment(comment)
		data.add_coordinate(coordname)
		data.add_coordinate('time')
		#mspec._rate = mspec._dacq.get_spc_samplerate() ##do something!
		rate = mspec.get_samplerate()
		samples = mspec.get_samples()
		dat_time = numpy.arange(0, 1.*samples/rate, 1./rate)
		dat_time = dat_time.reshape((dat_time.shape[0], 1))
		data.add_value('ch0')
		data.add_value('ch1')
		data.create_file()

		if plotLive:
				if plot3d:
						plot_ch0 = qt.Plot3D(data, name='waveform_ch0_3d', coorddims=(0,1), valdim=2)
						plot_ch0.set_palette('bluewhitered')
						plot_ch1 = qt.Plot3D(data, name='waveform_ch1_3d', coorddims=(0,1), valdim=3)
						plot_ch1.set_palette('bluewhitered')
				else:
						plot_ch0 = qt.Plot2D(data, name='waveform_ch0', coorddim=1, valdim=2, maxtraces=2)
						plot_ch1 = qt.Plot2D(data, name='waveform_ch1', coorddim=1, valdim=3, maxtraces=2)

		set_param_func(x_vec[0])

		# save plot even when aborted
		try:
				# measurement loop
				for x in x_vec:
						set_param_func(x)
						# sleep(td)
						qt.msleep() # better done during measurement (waiting for trigger)

						data.new_block()
						dat_x = x*numpy.ones(shape=(samples, 1))
						dat = numpy.append(dat_x, dat_time, axis = 1)
						dat_wave = mspec.acquire()
						dat = numpy.append(dat, dat_wave, axis = 1)
						data.add_data_point(dat)

						if plotLive & ~plot3d:
								plot_ch0.update()
								plot_ch0.save_png()
								plot_ch0.save_gp()
								plot_ch1.update()
								plot_ch1.save_png()
								plot_ch1.save_gp()
				return; # execute finally statement
		finally:
				if(~plotLive | plot3d):
						plot_ch0.update()
						plot_ch0.save_png()
						plot_ch0.save_gp()
						plot_ch1.update()
						plot_ch1.save_png()
						plot_ch1.save_gp()
				data.close_file()
				qt.mend()
"""
