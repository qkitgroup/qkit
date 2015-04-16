import qt
import numpy as np
import os.path
import time
import logging
import numpy
import sys

def measure_1d(readout, x_vec, coordname, set_param_func, comment = None, dirname = None, plotLive = True, plotSuffix = '', hold = False):
	qt.mstart()

	if(dirname == None): dirname = coordname
	data = qt.Data(name='multi_%s'%dirname)
	if comment: data.add_comment(comment)
	data.add_coordinate(coordname)

	ndev = readout.readout(False)[0].size
	for i in range(ndev):
		data.add_value('amp_%d'%i)
	for i in range(ndev):
		data.add_value('pha_%d'%i)
	data.add_value('timestamp')
	data.create_file()

	plots = []
	if plotLive:
		#if plot3d:
		#	plot_ch0 = qt.Plot3D(data, name='amplitude_3d', coorddims=(0,1), valdim=2)
		#	plot_ch0.set_palette('bluewhitered')
		#	plot_ch1 = qt.Plot3D(data, name='phase_3d', coorddims=(0,1), valdim=3)
		#	plot_ch1.set_palette('bluewhitered')
		#else:
		for i in range(ndev):
			plot_amp = qt.plots.get('amplitude_%d%s'%(i, plotSuffix))
			plot_pha = qt.plots.get('phase_%d%s'%(i, plotSuffix))
			if not plot_amp or not plot_pha:
				plot_amp = qt.Plot2D(name='amplitude_%d%s'%(i, plotSuffix))
				plot_pha = qt.Plot2D(name='phase_%d%s'%(i, plotSuffix))
			elif not hold:
				plot_amp.clear()
				plot_pha.clear()
			plot_amp.add(data, name='amplitude_%d%s'%(i, plotSuffix), coorddim=0, valdim=1+i)
			plot_pha.add(data, name='phase_%d%s'%(i, plotSuffix), coorddim=0, valdim=1+ndev+i)
			plots.append(plot_amp)
			plots.append(plot_pha)

#	set_param_func(x_vec[0])


	# save plot even when aborted
	try:
		# measurement loop
		for x in x_vec:
			set_param_func(x)
			# sleep(td)
			qt.msleep() # better done during measurement (waiting for trigger)

			dat_amp, dat_pha = readout.readout(False)
			dat = np.array([x])
			dat = np.append(dat, dat_amp)
			dat = np.append(dat, dat_pha)
			dat = np.append(dat, time.time())
			data.add_data_point(*dat)

			if plotLive:
				for plot in plots:
					plot.update()
		return; # execute finally statement
	finally:
		for plot in plots:
			plot.update()
			plot.save_gp()
			plot.save_png()
		data.close_file()
		qt.mend()

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


def measure_2d(readout, x_vec, x_coordname, x_set_param_func, y_vec, y_coordname, y_set_param_func, comment = None, dirname = None, plotLive = True, plot2d = False, plot3d = True, plotFast = False, iterations = 1, plotSuffix = ''):
    qt.mstart()

    # create usual data file
    if(dirname == None): dirname = '%s_%s'%(x_coordname, y_coordname)
    data = qt.Data(name='multi_%s'%dirname)
    if(comment): data.add_comment(comment)
    data.add_coordinate(x_coordname)
    data.add_coordinate(y_coordname)
    ndev = readout.readout(timeTrace = True)[0].size
    for i in range(ndev):
        data.add_value('amp_%d'%i)
    for i in range(ndev):
        data.add_value('pha_%d'%i)
    data.add_value('timestamp')
    data.create_file()

    # create time-resolved output
    # data_time columns: [iteration, coordinate, Is[nSamples], Qs[nSamples], timestamp]
    data_time = qt.Data(name='avgt_%s'%dirname)
    if(comment): data_time.add_comment(comment)
    data_time.add_coordinate(x_coordname)
    data_time.add_coordinate(y_coordname)
    for i in range(readout._ins._mspec.get_samples()):
        data_time.add_coordinate('I%3d'%i)
    for i in range(readout._ins._mspec.get_samples()):
        data_time.add_coordinate('Q%3d'%i)
    data_time.add_value('timestamp')

    data_fn, data_fext = os.path.splitext(data.get_filepath())
    data_time.create_file(None, '%s_time.dat'%data_fn, False)

    plots = []
    if plotLive:
        for i in range(ndev):
            # standard 2d plot
            if(plot3d):
                plot_amp = qt.Plot3D(data, name='amplitude_%d_3d%s'%(i, plotSuffix), coorddims=(0,1), valdim=2+i)
                plot_amp.set_palette('bluewhitered')
                plots.append(plot_amp)
                plot_pha = qt.Plot3D(data, name='phase_%d_3d%s'%(i, plotSuffix), coorddims=(0,1), valdim=2+ndev+i)
                plot_pha.set_palette('bluewhitered')
                plots.append(plot_pha)
            # time-resolved plot
            if(plot2d):
                plot_amp_2d = qt.Plot2D(data, name='amplitude_%d%s_single'%(i, plotSuffix), coorddim=1, valdim=2+i, maxtraces = 2)
                plot_pha_2d = qt.Plot2D(data, name='phase_%d%s_single'%(i, plotSuffix), coorddim=1, valdim=2+ndev+i, maxtraces = 2)
                plots.append(plot_amp_2d)
                plots.append(plot_pha_2d)

    #x_set_param_func(x_vec[0])
    #y_set_param_func(y_vec[0])

    # save plot even when aborted
    try:
        for it in range(iterations):
            # measurement loop
            for x in x_vec:
                data.new_block()
                x_set_param_func(x)
                for y in y_vec:
                    y_set_param_func(y)
                    # sleep(td)
                    qt.msleep() # better done during measurement (waiting for trigger)

                    dat_amp, dat_pha, Is, Qs = readout.readout(timeTrace = True)
                    timestamp = time.time()

                    # save standard data
                    dat = np.array([x, y])
                    dat = np.append(dat, dat_amp)
                    dat = np.append(dat, dat_pha)
                    dat = np.append(dat, timestamp)
                    data.add_data_point(*dat)
                    
                    # save time-domain data
                    dat = np.array([x, y])
                    dat = np.append(dat, Is[:])
                    dat = np.append(dat, Qs[:])
                    dat = np.append(dat, timestamp)
                    data_time.add_data_point(*dat)

                if plotLive and plotFast: # point-wise update
                    for plot in plots:
                        plot.update()
            if plotLive and ~plotFast: # trace-wise update
                for plot in plots:
                    plot.update()
            data.new_block()
            data_time.new_block()
        return; # execute finally statement
    finally:
        for plot in plots:
            plot.update()
            plot.save_gp()
            plot.save_png()
        data.close_file()

        qt.mend()


def measure_1d_avg(readout,mspec, x_vec, coordname, iterations = 1, comment = None, dirname = None, plotLive = True, plotTime = True, plotSuffix = ''):
	return measure_2d_awg(readout,mspec, x_vec, coordname, range(iterations), 'iteration', lambda y: True, comment, dirname, plotLive, plotTime, plotSuffix)

def measure_2d_awg(readout,mspec, x_vec, x_coordname, y_vec, y_coordname, y_setfunc, comment = None, dirname = None, plotLive = True, plotTime = True, plotSuffix = ''):
	'''
		1d measurement with low-frequency noise cancellation
	'''
	qt.mstart()
	qt.msleep() # if stop button was pressed by now, abort without creating data files

	# create data files for: 
	# - time-resolved raw data
	# - time-resolved successive-averaged data 
	# - time-averaged data
	# - raw I/Q data
	if(dirname == None): dirname = x_coordname
	data_raw = qt.Data(name='avg_%s'%dirname)
	data_sum = qt.Data(name='avgs_%s'%dirname)
	data_avg = qt.Data(name='avga_%s'%dirname)
	data_time = qt.Data(name='avgt_%s'%dirname)
	
	data_raw.add_coordinate(y_coordname)
	data_sum.add_coordinate(y_coordname)
	data_time.add_coordinate(y_coordname)

	for data in [data_raw, data_sum, data_avg]:
		if comment: data.add_comment(comment)
		data.add_coordinate(x_coordname)
	
		ndev = len(readout.get_tone_freq())
		for i in range(ndev):
			data.add_value('amp_%d'%i)
		for i in range(ndev):
			data.add_value('pha_%d'%i)

	# data_time columns: [iteration, coordinate, Is[nSamples], Qs[nSamples], timestamp]
	if(comment): data_time.add_comment(comment)
	data_time.add_coordinate(x_coordname)
	#for i in range(readout._ins._mspec.get_samples()):rate = mspec.get_samplerate()
	for i in range(mspec.get_samples()):
		data_time.add_coordinate('I%3d'%i)
	#for i in range(readout._ins._mspec.get_samples()):
	for i in range(mspec.get_samples()):
		data_time.add_coordinate('Q%3d'%i)

	# timestamp is only in non-averaged data
	data_raw.add_value('timestamp')
	data_time.add_value('timestamp')
	
	data_raw.create_file()
	data_fn, data_fext = os.path.splitext(data_raw.get_filepath())
	data_sum.create_file(None, '%s_sum.dat'%data_fn, False)
	data_time.create_file(None, '%s_time.dat'%data_fn, False)
	

	plots = []
	for i in range(ndev):
		# time-resolved plot
		if plotTime:
			plot_amp = qt.Plot3D(data_raw, name='amplitude_%d_3d%s'%(i, plotSuffix), coorddims=(0,1), valdim=2+i)
			plot_amp.set_palette('bluewhitered')
			plots.append(plot_amp)
			plot_pha = qt.Plot3D(data_raw, name='phase_%d_3d%s'%(i, plotSuffix), coorddims=(0,1), valdim=2+ndev+i)
			plot_pha.set_palette('bluewhitered')
			plots.append(plot_pha)
		# averaged plot
		plot_amp = qt.Plot2D(data_sum, name='amplitude_%d%s'%(i, plotSuffix), coorddim=1, valdim=2+i, maxtraces = 2)
		plot_pha = qt.Plot2D(data_sum, name='phase_%d%s'%(i, plotSuffix), coorddim=1, valdim=2+ndev+i, maxtraces = 2)
		plots.append(plot_amp)
		plots.append(plot_pha)

	# buffer successive sum for averaged plot
	dat_cmpls = np.zeros((len(x_vec), ndev), np.complex128)
	dat_ampa = np.zeros_like((len(x_vec), ndev))
	dat_phaa = np.zeros_like(dat_ampa)

	# save plot even when aborted
	try:
		# measurement loop
		starttime=time.time()
		for it in range(len(y_vec)):
			qt.msleep() # better done during measurement (waiting for trigger)
			
			y_setfunc(y_vec[it])

			dat_amp, dat_pha, Is, Qs = readout.readout(timeTrace = True)
			timestamp = time.time()

			# save raw frequency-domain data (qubit points only)
			data_raw.new_block()
			for xi in range(len(x_vec)):
				dat = np.array([y_vec[it], x_vec[xi]])
				dat = np.append(dat, dat_amp[xi, :])
				dat = np.append(dat, dat_pha[xi, :])
				dat = np.append(dat, timestamp)
				data_raw.add_data_point(*dat)
			
			# save time-domain data
			data_time.new_block()
			for xi in range(len(x_vec)):
				dat = np.array([y_vec[it], x_vec[xi]])
				dat = np.append(dat, Is[:, xi])
				dat = np.append(dat, Qs[:, xi])
				dat = np.append(dat, timestamp)
				data_time.add_data_point(*dat)

			dat_cmpls += dat_amp * np.exp(1j*dat_pha)
			dat_ampa = np.abs(dat_cmpls/(it+1))
			dat_phaa = np.angle(dat_cmpls/(it+1))
			# save successively averaged frequency-domain data
			data_sum.new_block()
			for xi in range(len(x_vec)):
				dat = np.array([it, x_vec[xi]])
				dat = np.append(dat, dat_ampa[xi, :])
				dat = np.append(dat, dat_phaa[xi, :])
				data_sum.add_data_point(*dat)

			if plotLive:
				for plot in plots:
					plot.update()
			if(it<5 or it%20==0):
				print "(%i/%i) ETA: %s"%(it,len(y_vec),time.ctime( starttime+(time.time()-starttime)/(it+1)*len(y_vec)))
			sys.stdout.flush()
		return; # execute finally statement
	except Exception as e:
		print e
	finally:
		for plot in plots:
			plot.update()
			plot.save_gp()
			plot.save_png()

		# save final averaged data in a separate file
		if(dat_ampa != None):
			data_avg.create_file(None, '%s_avg.dat'%data_fn, False)
			dat = np.concatenate((np.atleast_2d(x_vec).transpose(), dat_ampa, dat_phaa), 1)
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
		
		# return averaged data
		if(dat_ampa != None):
			return np.concatenate((np.atleast_2d(x_vec).transpose(), dat_ampa, dat_phaa), 1)
