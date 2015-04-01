import numpy as np
from time import sleep
import time
import logging
import matplotlib.pylab as plt
from scipy.optimize import curve_fit

import qt

ttip = qt.instruments.get('ttip')
vna = qt.instruments.get('vna')
mw_src1 = qt.instruments.get('mw_src1')

##############################
#auxilary functions
##############################

def calc_time( a1 = None, a2 = None):

	bandwidth = vna.get_bandwidth()
	av = vna.get_averages()
	nop = vna.get_nop()

	timeforonepoint = 1.0/bandwidth

	sz = 0
	if a1 != None:
		sz += np.size(a1)
	if a2 != None:
		sz = sz * np.size(a2)

	t = timeforonepoint*av*sz*nop/60
	return t

def wait_averages_E5071(t, averages = None, wait_ratio = 0.9, retry_ratio = 0.1, hold_ratio = 10):
	'''
	wait averages to use with VNA E5071C (9.5GHz)
	'''
	vna.avg_clear()
	sleep(vna.get_sweeptime()*vna.get_averages())

def wait_averages(t, averages = None, wait_ratio = 0.9, retry_ratio = 0.1, hold_ratio = 10):
	'''
	clear vna averages and wait until the measurement is complete, use with older VNAs since no parameter 'sweeptime' available
	
	Input:
		t: expected measurement time
		averages: number of averages set on the vna
		wait_ratio: ratio of t after which to first request data
		retry_ratio: rate at which to check for the end of the measurement
		hold_ratio: time after which to issue a STOP/CONTINUE sweep command to the vna
	'''

	# clip waiting times to sensible real-time values
	t_wait = min(10., t*wait_ratio) # <10s
	t_retry = max(50e-3, min(1., t*retry_ratio)) # 50ms to 1s
	t_hold = max(10., t*hold_ratio) # >10s
	
	# initiate averaging
	tstart = time.time()
	vna.avg_clear()
	sleep(0.1)
	print "avg clear!"
	if(averages == None): averages = vna.get_averages()
	time.sleep(t_wait)
	
	#if (not vna.get_Average() or vna.get_avg_type() == 'POIN'): return()
	
	# loop until finished
	while averages <> vna.avg_status():
		logging.info('probing vna.')
		sleep(t_retry)
		if(time.time()-tstart > t_hold):
			if(vna.get_Average() == False):
				logging.warning('got no data from vna after t_hold. averaging was not enabled.')
				vna.set_Average(True)
				time.sleep(t_wait)
			else:
				logging.warning('got no data from vna after t_hold. stop/start sweep.')
				#vna.hold(True)
				#vna.hold(False)
			tstart = time.time()


#############################
# general 1D sweep
#############################

def _sw_1D(x_vec, coordname, set_param_func, hold = False, td=0.002, ref=False, ref_meas_func=None, comment = None, offset = 0,cw=False,cw_user_func=None):

	qt.mstart()
	#vna.get_all()
	#ttip.get_temperature()
	
	if cw:
		nop=1
	else:
		nop = vna.get_nop(query = False)
	
	if(vna.get_Average()):
		nop_avg = vna.get_averages()
	else:
		nop_avg=1
	
	
	bandwidth = vna.get_bandwidth()
	t_point = nop / bandwidth * nop_avg
	
	if(cw):
		freq_points=[1]
	else:
		freq_points = vna.get_freqpoints()

	data = qt.Data(name=('vna_' + coordname))
	data.add_coordinate(coordname)
	#data.add_coordinate('Frequency')

	if comment:
		data.add_comment(comment)
	
	
	
	for i in range(1,nop+1):
		data.add_value(('Point %i Amp' %i))
	for i in range(1,nop+1):
		data.add_value(('Point %i Pha' %i))

	if ref:
		for i in range(1,nop+1):
			data.add_value(('Point %i Amp Orig' %i))
		for i in range(1,nop+1):
			data.add_value(('Point %i Pha Orig' %i))
		for i in range(1,nop+1):
			data.add_value(('Point %i Amp Ref' %i))
		for i in range(1,nop+1):
			data.add_value(('Point %i Pha Ref' %i))

	data.create_file()

	if hold:
		plot_amp = qt.plots.get('Amplitude')
		plot_pha = qt.plots.get('Phase')
		plot_amp.add(data, coorddim=0, valdim=int(nop/2)+1)
		plot_pha.add(data,coorddim = 0, valdim = nop+int(nop/2)+1)
	else:
		plot_amp = qt.Plot2D(data, name='Amplitude', coorddim=0, valdim=int(nop/2)+1)
		plot_pha = qt.Plot2D(data, name='Phase', coorddim=0, valdim=nop+int(nop/2)+1)
		#plot_amp2d = qt.Plot3D(data, name='Amplitude 2D', coorddims=(0,1), valdim=int(nop/2)+1, style=qt.Plot3D.STYLE_IMAGE)
		#plot_amp.set_palette('bluewhitered')

	set_param_func(x_vec[0]) #In case for currentsweep go to starting point

	now_stamp = 0
	now_steps = np.size(x_vec)
	now1 = time.time()

	#Main Measurement Loop
	try:
		if cw:
			vna.set_cw(True)
			vna.set_nop(1)
		for x in x_vec:
			print "set x value to " + str(x)
			set_param_func(x)
			sleep(td)
			if cw:
				wait_averages(t_point/nop, nop_avg)
			else:
				wait_averages(t_point, nop_avg)
				
			data_amp = []
			data_pha = []
			if cw and not (cw_user_func == None):
				
				
				for f in freq_points:
					cw_user_func()
					vna.set_cwfreq(f)
					wait_averages(t_point/nop, nop_avg)
					data_amp1,data_pha1 = vna.get_tracedata()
					data_amp = np.append(data_amp,data_amp1)
					data_pha = np.append(data_pha,data_pha1)
			else:
				print 'measure'
				data_amp,data_pha = vna.get_tracedata()

			dat = []

			if ref:
				ref_meas_func(True)
				sleep(td)
				wait_averages(t_point, nop_avg)
				data_amp_ref,data_pha_ref = vna.get_tracedata()
				ref_meas_func(False)

				dat = np.append(x,data_amp-data_amp_ref)
				dat = np.append(dat,data_pha-data_pha_ref)
				dat = np.append(dat,data_amp)
				dat = np.append(dat,data_pha)
				dat = np.append(dat,data_amp_ref)
				dat = np.append(dat,data_pha_ref)
				data.add_data_point(*dat)        # _one_
			else:
				#unwrap = ((data_pha - data_pharef)>np.pi/2.)
				#unwrap2 = ((data_pha - data_pharef)<-np.pi/2.)
				#for unwra in range(nop):
				#  if unwrap[unwra]:
				#    data_pha[unwra] = data_pha[unwra] - np.pi
				#  if unwrap2[unwra]:
				#    data_pha[unwra] = data_pha[unwra] + np.pi
				dat = np.append((x+offset),data_amp)
				dat = np.append(dat,data_pha)
				data.add_data_point(*dat)  # _one_

			qt.msleep()

			now_stamp += 1
			if now_stamp==5:
				now2 = time.time()
				t = (now2-now1)/5
				left = (t*now_steps/60/60);
				if left < 1:
					print('Time left: %f min' %(left*60))
				else:
					print('Time left: %f h' %(left))
	finally:
		plot_amp.save_png()
		plot_amp.save_gp()
		plot_pha.save_png()
		plot_pha.save_gp()

		#amp.close_file()
		#pha.close_file()
		data.close_file()
		
		if cw:
			vna.set_cw(False)
			vna.set_nop(nop)
		qt.mend()


"""
#############################
# shorcuts for 1D sweep
#############################

def probe_power(x_vec, op='amppha', ref=False,hold = False, ref_meas_func=None):
	coordname='Probe Power'
	set_param_func = zvl.set_power
	_sw_1D(x_vec, coordname, set_param_func, op=op,hold = hold, ref=ref, ref_meas_func=ref_meas_func)

def exct_power(x_vec, mw_src = None ,hold = False, ref=False, ref_meas_func=None, comment = None):
	if mw_src.get_status() == 'off':
		print('Warning: mw_src is turned off.')
	coordname='Excitation Power'
	set_param_func = mw_src.set_power
	_sw_1D(x_vec, coordname, set_param_func, hold = hold,ref=ref, ref_meas_func=ref_meas_func, comment=comment)

def exct_freq(x_vec, op='amppha', mw_src = None,hold = False, ref=False, ref_meas_func=None, comment = None):
	if mw_src.get_status() == 'off':
		print('Warning: mw_src is turned off.')
	coordname='Excitation Frequency'
	set_param_func = mw_src.set_frequency
	_sw_1D(x_vec, coordname, set_param_func, hold = hold,ref=ref, ref_meas_func=ref_meas_func, comment=comment, offset = 0)

def current(x_vec, mag = None, hold = False, ref=False, ref_meas_func=None, offset = 0, comment = None):
	coordname='Current'
	set_param_func = mag.set_current
	_sw_1D(x_vec, coordname, set_param_func,hold = hold, ref=ref, ref_meas_func=ref_meas_func, offset = offset, comment = comment)
"""

def _sw_1D2(x_vec, coordname, set_param_func, hold = False, td=0.002, ref=False, ref_meas_func=None, offset = 0, comment = None, plotlive = True, backgrnd = np.array(0)):

	qt.mstart()
	vna.get_all()

	nop = vna.get_nop(query = False)
	nop_avg = vna.get_averages()
	bandwidth = vna.get_bandwidth()
	t_point = nop / bandwidth * nop_avg
	freqpoints = vna.get_freqpoints()

	data = qt.Data(name=('vna_' + coordname))
	data.add_coordinate(coordname)
	data.add_coordinate('Frequency')
	data.add_value('Amplitude')
	data.add_value('Phase')
	if backgrnd.any():
		data.add_value('Amplitude original')
		data.add_value('Phase original')

	if comment:
		data.add_comment(comment)

	data.create_file()

	if plotlive:
		if hold:
			plot_amp = qt.plots.get('Amplitude 2D2')
			plot_pha = qt.plots.get('Phase 2D')
			plot_amp.add(data,  coorddims=(0,1), valdim=2, style=qt.Plot3D.STYLE_IMAGE)
			plot_pha.add(data,  coorddims=(0,1), valdim=3, style=qt.Plot3D.STYLE_IMAGE)
		else:
			plot_amp = qt.Plot3D(data, name='Amplitude 2D2', coorddims=(0,1), valdim=2, style=qt.Plot3D.STYLE_IMAGE)
			plot_amp.set_palette('bluewhitered')
			plot_pha = qt.Plot3D(data, name='Phase 2D', coorddims=(0,1), valdim=3, style=qt.Plot3D.STYLE_IMAGE)
			plot_pha.set_palette('bluewhitered')

	set_param_func(x_vec[0]) #In case for currentsweep go to starting point

	now_stamp = 0
	now_steps = np.size(x_vec)
	now1 = time.time()

	try:
		#Main Measurement Loop
		for x in x_vec:
			set_param_func(x)
			sleep(td)

			wait_averages(t_point, nop_avg)

			if backgrnd.any():
				data_real,data_imag = vna.get_tracedata(format = 'REALIMAG')
				idat = (data_real+1j*data_imag)
				diff =  idat - backgrnd
				dat = []
				dat = np.append([(x+offset)*np.ones(nop)],[freqpoints], axis = 0)
				dat = np.append(dat,[np.absolute(diff)],axis = 0)
				dat = np.append(dat,[np.angle(diff)],axis = 0)
				dat = np.append(dat,[np.absolute(idat)], axis = 0)
				dat = np.append(dat,[np.angle(idat)], axis = 0)
				data.add_data_point(dat.transpose())
			else:
				data_amp,data_pha = vna.get_tracedata()
				dat = []
				dat = np.append([((x+offset))*np.ones(nop)],[freqpoints], axis = 0)
				dat = np.append(dat,[data_amp],axis = 0)
				dat = np.append(dat,[data_pha],axis = 0)
				data.add_data_point(*dat)

			data.new_block()
			qt.msleep()

			now_stamp += 1
			if now_stamp==5:
				now2 = time.time()
				t = (now2-now1)/5
				left = (t*now_steps/60/60);
				if left < 1:
					print('Time left: %f min ' %(left*60))
				else:
					print('Time left: %f h ' %(left))
	finally:
		if not plotlive:
			if hold:
				plot_amp = qt.plots.get('Amplitude 2D2')
				plot_pha = qt.plots.get('Phase 2D')
				plot_amp.add(data,  coorddims=(0,1), valdim=2, style=qt.Plot3D.STYLE_IMAGE)
				plot_pha.add(data,  coorddims=(0,1), valdim=3, style=qt.Plot3D.STYLE_IMAGE)
			else:
				plot_amp = qt.Plot3D(data, name='Amplitude 2D2', coorddims=(0,1), valdim=2, style=qt.Plot3D.STYLE_IMAGE)
				plot_amp.set_palette('bluewhitered')
				plot_pha = qt.Plot3D(data, name='Phase 2D', coorddims=(0,1), valdim=3, style=qt.Plot3D.STYLE_IMAGE)
				plot_pha.set_palette('bluewhitered')
			plot_amp.update()
			plot_pha.update()
		plot_amp.save_png()
		plot_amp.save_gp()
		plot_pha.save_png()
		plot_pha.save_gp()

		#amp.close_file()
		#pha.close_file()
		data.close_file()

		qt.mend()



#############################
# general 2D sweep
#############################

def _sw_2D(x_vec, x_coordname, x_set_param_func, y_vec, y_coordname, y_set_param_func, tdx = 0.002, tdy = 0.002,
	op='amppha', ref=False, ref_meas_func=None, comment = None, plot3D = True, plotlive = True):

	qt.mstart()
	vna.get_all()
	#ttip.get_temperature()

	_op=op
	
	# Check what kind of sweep we are doing
	'''
	swtype = vna.get_sweep_type()
	if swtype in ('LIN','LOG'):
		nop = vna.get_nop()
	elif swtype == 'POW':
		nop = vna.get_power_nop1()
	else:
		raise ValueError('unsupported sweep type ' +  swtype)
	'''
	nop = vna.get_nop()
	
	nop_avg = vna.get_averages()
	bandwidth = vna.get_bandwidth()
	t_point = nop / bandwidth * nop_avg

	if _op in ['amppha']:
		data = qt.Data(name=('vna_' + x_coordname + y_coordname))
		data.add_coordinate(x_coordname)
		data.add_coordinate(y_coordname)

	else:
		logging.error('unknown option for _sw_2D')
		raise ValueError('unknown parameter')

	if comment:
		data.add_comment(comment)

	for i in range(1,nop+1):
		data.add_value(('Point %i Amp' %i))
	for i in range(1,nop+1):
		data.add_value(('Point %i Pha' %i))

	data.create_file()

	if(plotlive):
		if(plot3D):
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
		for x in x_vec:
			
			#print  'Scanning:', x_vec,'%', x_coordname
			
			if x_it == 1:
				now2 = time.time()
				t = (now2-now1)
				left = (t*np.size(x_vec)/60/60);
				if left < 1:
					print('Time left: %f min' %(left*60))
				else:
					print('Time left: %f h' %(left))
					
			x_set_param_func(x)
			x_it += 1
			sleep(tdx)

			for y in y_vec:
				y_set_param_func(y)
				#print 'Set y-parameter.'
				sleep(tdy)

				wait_averages(t_point, nop_avg)

				data_amp,data_pha = vna.get_tracedata()

				dat = np.append(x,y)
				dat = np.append(dat,data_amp)
				dat = np.append(dat,data_pha)
				data.add_data_point(*dat)  # _one_

				qt.msleep()

			data.new_block()
	finally:
		if(not plotlive):
			if(plot3D):
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

"""
def exctfreq_exctpower(x_vec, y_vec, op='amppha', ref=False, ref_meas_func=None, mw_src= None, comment = None):
	if mw_src.get_status() == 'off':
		print('Warning: mw_src is turned off.')
	x_coordname = 'Excitation Frequency'
	x_set_param_func = mw_src.set_frequency
	y_coordname = 'Excitation power'
	y_set_param_func = mw_src.set_power#lambda val: set_mwamp(val, mwpulse=mwpulse)
	_sw_2D(x_vec, x_coordname, x_set_param_func, y_vec, y_coordname, y_set_param_func, op=op, ref=ref, ref_meas_func=ref_meas_func, comment = comment)

def exctpower_exctfreq(x_vec, y_vec, op='amppha', ref=False, ref_meas_func=None, mw_src= None, comment = None):
	if mw_src.get_status() == 'off':
		print('Warning: mw_src is turned off.')
	y_coordname = 'Excitation Frequency'
	y_set_param_func = mw_src.set_frequency
	x_coordname = 'Excitation power'
	x_set_param_func = mw_src.set_power#lambda val: set_mwamp(val, mwpulse=mwpulse)
	_sw_2D(x_vec, x_coordname, x_set_param_func, y_vec, y_coordname, y_set_param_func, op=op, ref=ref, ref_meas_func=ref_meas_func, comment = comment)

def probepower_exctfreq(x_vec, y_vec, op='amppha', ref=False, ref_meas_func=None, mw_src= None, comment = None):
	if mw_src.get_status() == 'off':
		print('Warning: mw_src is turned off.')
	y_coordname = 'Excitation Frequency'
	y_set_param_func = mw_src.set_frequency
	x_coordname = 'Probe power'
	x_set_param_func = vna.set_power#lambda val: set_mwamp(val, mwpulse=mwpulse)
	_sw_2D(x_vec, x_coordname, x_set_param_func, y_vec, y_coordname, y_set_param_func, op=op, ref=ref, ref_meas_func=ref_meas_func, comment = comment)

def current_frequency(x_vec, y_vec, op='amppha', ref=False, ref_meas_func=None, mw_src= None, mag = None, comment = None):
	if mw_src.get_status() == 'off':
		print('Warning: mw_src is turned off.')
	x_coordname = 'Current'
	x_set_param_func = mag.set_current
	y_coordname = 'Excitation frequency'
	y_set_param_func = mw_src.set_frequency#lambda val: set_mwamp(val, mwpulse=mwpulse)
	_sw_2D(x_vec, x_coordname, x_set_param_func, y_vec, y_coordname, y_set_param_func, op=op, ref=ref, ref_meas_func=ref_meas_func, comment = comment)

def frequency_current(x_vec, y_vec, op='amppha', ref=False, ref_meas_func=None, mw_src= None, mag = None, comment = None):
	y_coordname = 'Current'
	y_set_param_func = mag.set_current
	x_coordname = 'Excitation frequency'
	x_set_param_func = mw_src.set_frequency#lambda val: set_mwamp(val, mwpulse=mwpulse)
	_sw_2D(x_vec, x_coordname, x_set_param_func, y_vec, y_coordname, y_set_param_func, op=op, ref=ref, ref_meas_func=ref_meas_func, comment=comment)

def exctpower_current(x_vec, y_vec, op='amppha', ref=False, ref_meas_func=None, mw_src= None, mag = None, comment = None):
	y_coordname = 'Current'
	y_set_param_func = mag.set_current
	x_coordname = 'Excitation power'
	x_set_param_func = mw_src.set_power
	_sw_2D(x_vec, x_coordname, x_set_param_func, y_vec, y_coordname, y_set_param_func, op=op, ref=ref, ref_meas_func=ref_meas_func, comment = comment)

def probepower_current(x_vec, y_vec, op='amppha', ref=False, ref_meas_func=None, mag = None):
	y_coordname = 'Current'
	y_set_param_func = mag.set_current
	x_coordname = 'Probe power'
	x_set_param_func = lambda val: set_probe_power(val)
	_sw_2D(x_vec, x_coordname, x_set_param_func, y_vec, y_coordname, y_set_param_func, op=op, ref=ref, ref_meas_func=ref_meas_func)
"""

#############################
# general 2D sweep with averaging over frequency points
#############################

def _sw_2D_avg(x_vec, x_coordname, x_set_param_func, y_vec, y_coordname, y_set_param_func, tdx = 0.002, tdy = 0.002, x_ref_meas_func=None, comment = None, plot3D = True, plotlive = True):
	'''
		[...]
		x_ref_meas_func is called for each value in the x vector with parameter True to initiate a reference measurement and with parameter False to conclude a reference measurement, e.g. x_ref_meas_func = lambda t: mw_src5.set_status(not t)
	'''

	qt.mstart()

	nop = vna.get_nop()
	nop_avg = vna.get_averages()
	bandwidth = vna.get_bandwidth()
	t_point = nop / bandwidth * nop_avg

	data = qt.Data(name=('vna_' + x_coordname + y_coordname))
	data.add_coordinate(x_coordname)
	data.add_coordinate(y_coordname)
	data.add_value('Amp Average')
	data.add_value('Pha Average')
	if(x_ref_meas_func != None):
		data.add_value('Amp Average/Ref')
		data.add_value('Pha Average/Ref')
	#data.add_value('Amp StDev')
	#data.add_value('Pha StDev')

	for i in range(1,nop+1):
		data.add_value(('Point %i Amp' %i))
	for i in range(1,nop+1):
		data.add_value(('Point %i Pha' %i))

	if comment:
		data.add_comment(comment)

	data.create_file()

	if(plotlive):
		if(plot3D):
			plot_amp = qt.Plot3D(data, name='Amplitude', coorddims=(0,1), valdim=2, style=qt.Plot3D.STYLE_IMAGE)
			plot_amp.set_palette('bluewhitered')
			plot_pha = qt.Plot3D(data, name='Phase', coorddims=(0,1), valdim=3, style=qt.Plot3D.STYLE_IMAGE)
			plot_pha.set_palette('bluewhitered')
		else:
			plot_amp = qt.Plot2D(data, name='Amplitude', coorddim=1, valdim=2)
			plot_pha = qt.Plot2D(data, name='Phase', coorddim=1, valdim=3)

	try:
		for x in x_vec:
			x_set_param_func(x)
			sleep(tdx)

			# measure reference
			if(x_ref_meas_func != None):
				x_ref_meas_func(True)
				vna.waitt_averages(t_point, nop_avg)
				dat_amp, dat_pha = vna.get_tracedata()
				dat_ref = np.mean( 10**(dat_amp/10)*np.exp(1j*dat_pha) )
				x_ref_meas_func(False)

			for y in y_vec:
				y_set_param_func(y)
				sleep(tdy)

				# acquire data
				wait_averages(t_point, nop_avg)
				dat_amp, dat_pha = vna.get_tracedata()
				dat_avg = np.mean( 10**(dat_amp/10.)*np.exp(1j*dat_pha) )

				# add normalized data
				if(x_ref_meas_func != None):
					if(dat_ref != 0):
						dat_norm = dat_avg/dat_ref
					else:
						dat_norm = dat_avg
					dat = np.concatenate(([x], [y], [10*np.log10(np.abs(dat_norm))], [np.angle(dat_norm)], [10*np.log10(np.abs(dat_avg))], [np.angle(dat_avg)], dat_amp, dat_pha))
				else:
					dat = np.concatenate(([x], [y], [10*np.log10(np.abs(dat_avg))], [np.angle(dat_avg)], dat_amp, dat_pha))

				# write data to file
				data.add_data_point(*dat) 

				qt.msleep()

			data.new_block()
	finally:
		if(not plotlive):
			if(plot3D):
				plot_amp = qt.Plot3D(data, name='Amplitude', coorddims=(0,1), valdim=2, style=qt.Plot3D.STYLE_IMAGE)
				plot_amp.set_palette('bluewhitered')
				plot_pha = qt.Plot3D(data, name='Phase', coorddims=(0,1), valdim=3, style=qt.Plot3D.STYLE_IMAGE)
				plot_pha.set_palette('bluewhitered')
			else:
				plot_amp = qt.Plot2D(data, name='Amplitude', coorddim=1, valdim=2)
				plot_pha = qt.Plot2D(data, name='Phase', coorddim=1, valdim=3)

		plot_amp.save_png()
		plot_amp.save_gp()
		plot_pha.save_png()
		plot_pha.save_gp()

		data.close_file()

		qt.mend()

##########################################################################################################################
# measure 2D class

class spectrum_2D(object):
	
	'''
	use:
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
		self.ref=False
		self.ref_meas_func=None
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
	
	def f_parab(x,a,b,c):
		return a*(x-b)**2+c
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

	def wait_averages_E5071():
		'''
		wait averages to use with VNA E5071C (9.5GHz)
		'''
		vna.avg_clear()
		sleep(vna.get_sweeptime()*vna.get_averages())
			
	def measure(self):
		
		'''
		Can be used as the conventional _sw_2D function without being functionally selective (func == False).
		
		Setting func to True enables and requires to pass fit function parameters in popt_a together with an information segment (on position -1) specifying the
			function to use. Format of popt_a: [[p1,p2,p3,0/1],[p1,p2,p3,0/1],...] (0 for parabolic fit, 1 for hyperbolic fit)
			popt_a can be 2D in case more than one function is involved.
			
			popt_a can be generated using the function gen_fit_function(...) for single functions and subsequently passed as an array:
			popt1 = gen_fit_function(...)
			popt2 = gen_fit_function(...)
			popt3 = gen_fit_function(...)
			...
			popt_a = [popt1,popt2,popt3,...]
			
			span is the range (in units of the vertical plot axis) data is taken around the specified funtion(s) 
		'''


		if landscape != None:
			center_freqs = np.array(landscape).T

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
			if(plot3D):
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
				if(plot3D):
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

