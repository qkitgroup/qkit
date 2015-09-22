'''
data reading and fitting script JB@KIT 01/2015 jochen.braumueller@kit.edu
'''

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
#import fnmatch
import os, glob
import time
import logging

no_do = False
try:
	import data_optimizer as do
except ImportError as m:
	print 'Warning: data optimizer not available.'
	no_do = True

no_qt = False
try:
	import qt
	data_dir_config = qt.config.get('datadir')
except ImportError as message:
	print 'Warning:', message
	no_qt = True


'''
	rootPath = 'D:\\'
	pattern = '*.dat'
	 
	for root, dirs, files in os.walk(rootPath):
		for filename in fnmatch.filter(files, pattern):
			print(os.path.join(root, filename))
'''


def load_data(file_name = None):
	
	'''
	load recent or specified data file and return the data array
	'''
	
	global no_qt
	if file_name == None and no_qt == False:
		#extract newest file in specified folder
		data_dir = os.path.join(data_dir_config, time.strftime('%Y%m%d'))
		try:
			nfile = max(glob.iglob(str(data_dir)+'\*\*.dat'), key=os.path.getctime)   #find newest file in directory
		except ValueError as message:
			print 'no .dat file in todays directory '+str(data_dir)+':', message
			i = 0
			while i < 10:
				data_dir = os.path.join(data_dir_config, time.strftime('%Y%m%d',time.localtime(time.time()-3600*24*(i+1))))   #check older directories
				try:
					nfile = max(glob.iglob(str(data_dir)+'\*\*.dat'), key=os.path.getctime)
					break
				except ValueError:
					print 'no .dat file in the directory '+str(data_dir)
					i = i+1

			if i == 10:
				print 'no .dat files found within the last %i days...aborting' % i
				return
		except Exception as message:
			print message
			return

	elif file_name == None and no_qt == True:
		print 'Cannot retrieve datadir...aborting'
		return
	else:
		nfile = file_name


	try:
		print 'Reading file '+str(nfile).replace('\\','/')
		data = np.loadtxt(nfile, comments='#').T
		#print 'Reading successful!'
	except Exception as message:
		print 'invalid file name...aborting:', message
		return
		
	return data, nfile
	
def _fill_p0(p0,ps):

	'''
	fill estimated p0 with specified initial values (in ps)
	'''
	
	if ps != None:
		try:
			for n in range(len(ps)):
				if ps[n] != None:
					p0[n] = ps[n]
		except Exception as m:
			print 'list of given initial parameters invalid...aborting'
			raise ValueError
	return p0
	
def _extract_initial_oscillating_parameters(data,data_c):
	
	#offset
	# testing last 25% of data for its maximum slope; take offset as last 10% of data for a small slope (and therefore strong damping)
	if np.max(np.abs(np.diff(data[data_c][int(0.75*len(data[data_c])):]))) < 0.3*np.abs(np.max(data[data_c])-np.min(data[data_c]))/(len(data[0][0.75*len(data[0]):])*(data[0][-1]-data[0][0.75*len(data[data_c])])):   #if slope in last part small
		s_offs = np.mean(data[data_c][int(0.9*len(data[data_c])):])
	else:   #larger slope: calculate initial offset from min/max in data
		s_offs = (np.max(data[data_c]) + np.min(data[data_c]))/2
	#print s_offs
	
	#amplitude
	a1 = np.abs(np.max(data[data_c]) - s_offs)
	a2 = np.abs(np.min(data[data_c]) - s_offs)
	s_a = np.max([a1,a2])
	#print s_a
	
	#damping
	a_end = np.abs(np.max(data[data_c][int(0.7*len(data[data_c])):]))   #scan last 30% of values -> final amplitude
	#print a_end
	# -> calculate Td
	t_end = data[0][-1]
	try:
		s_Td = -t_end/(np.log((np.abs(a_end-np.abs(s_offs)))/s_a))
	except RuntimeWarning:
		logging.warning('Invalid value encountered in log. Continuing...')
		s_Td = float('inf')
	if np.abs(s_Td) == float('inf'):
		s_Td = float('inf')
		logging.warning('Consider using the sine fit routine for non-decaying sines.')
	#print 'assume T =', str(np.round(s_Td,4))
	
	#frequency
	#s_fs = 1/data[0][int(np.round(np.abs(1/np.fft.fftfreq(len(data[data_c]))[np.where(np.abs(np.fft.fft(data[data_c]))==np.max(np.abs(np.fft.fft(data[data_c]))[1:]))]))[0])] #@andre20150318
	roots = 0   #number of offset line crossings ~ period of oscillation
	for dat_p in range(len(data[data_c])-1):
		if np.sign(data[data_c][dat_p] - s_offs) != np.sign(data[data_c][dat_p+1] - s_offs):   #offset line crossing
			roots+=1
	s_fs = float(roots)/(2*data[0][-1])   #number of roots/2 /measurement time
	#print s_fs
	
	#phase offset
	dmax = np.abs(data[data_c][0] - np.max(data[data_c]))
	dmean = np.abs(data[data_c][0] - np.mean(data[data_c]))
	dmin = np.abs(data[data_c][0] - np.min(data[data_c]))
	if dmax < dmean:   #start on upper side -> offset phase pi/2
		s_ph = np.pi/2
	elif dmin < dmean:   #start on lower side -> offset phase -pi/2
		s_ph = -np.pi/2
	else:   #ordinary sine
		s_ph = 0
	#print s_ph
	
	return s_offs, s_a, s_Td, s_fs, s_ph


def fit_data(file_name = None, fit_function = 'lorentzian', data_c = 2, ps = None, xlabel = '', ylabel = '', show_plot = True, save_pdf = False, data=None, nfile=None, opt=None):
	
	'''
	fit the data in file_name to a function specified by fit_function
	leaving file_name to None makes the code try to find the newest .dat file in today's data_dir
	
	fit_function can be 'lorentzian', 'damped_sine', 'sine', 'exp'
	data_c: specifies the data column to be used (next to column 0 that is used as the coordinate axis)
	ps: start parameters (optional), can be given in parts, set parameters not specified to None
	xlabel: label for horizontal axis (optional)
	ylabel: label for vertical axis (optional)
	show_plot: show and safe the plot (optional, default = True)
	save_pdf: save plot also as pdf file (optional, default = False)
	data, nfile: pass data object and file name which is used when file_name == 'dat_import'
	opt: bool, set to True if data is to be optimized prior to fitting
	
	returns fit parameters, standard deviations concatenated: [popt1,pop2,...poptn,err_popt1,err_popt2,...err_poptn]
	in case fit does not converge, errors are filled with 'inf'
	WARNING: errors might be returned as 'inf' which is 'nan'
	frequency units in GHz
	
	f_Lorentzian expects its frequency parameter to be stated in GHz
	'''
	
	def f_Lorentzian(f, f0, k, a, offs):
		return np.sign(a) * np.sqrt(np.abs(a**2*(k/2)**2/((k/2)**2+(f-f0)**2)))+offs
		
	def f_damped_sine(t, fs, Td, a, offs, ph):
		return a*np.exp(-t/Td)*np.sin(2*np.pi*fs*t+ph)+offs
		
	def f_sine(t, fs, a, offs, ph):
		return a*np.sin(2*np.pi*fs*t+ph)+offs
		
	def f_exp(t, Td, a, offs):
		return a*np.exp(-t/Td)+offs


	if file_name == 'dat_import':
		print 'use imported data'
	else:
		#load data
		data, nfile = load_data(file_name)

	#check column identifier
	if data_c >= len(data):
		print 'bad data column identifier, out of bonds...aborting'
		return
		
	#data optimization
	if opt:
		if no_do:
			logging.warning('Data is not optimized since package is not loaded.')
		data = do.optimize(data,data_c,data_c+1)
		data_c = 1
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	if fit_function == 'lorentzian':
	
		#check for unit in frequency
		if np.mean(data[0]) > 100:
			print 'frequency given in Hz'
			freq_conversion_factor = 1e-9
		else:
			print 'frequency given in GHz'
			freq_conversion_factor = 1

		#plot data, f in GHz
		if show_plot:   plt.plot(data[0]*freq_conversion_factor,data[data_c],'*')
		x_vec = np.linspace(data[0][0]*freq_conversion_factor,data[0][-1]*freq_conversion_factor,200)
	
		#start parameters ----------------------------------------------------------------------
		s_offs = np.mean(np.array([data[data_c,:int(np.size(data,1)/10)],data[data_c,np.size(data,1)-int(np.size(data,1)/10):]])) #offset is calculated from the first and last 10% of the data to improve fitting on tight windows @andre20150318
		if np.abs(np.max(data[data_c]) - np.mean(data[data_c])) > np.abs(np.min(data[data_c]) - np.mean(data[data_c])):
			#expect a peak
			print 'expecting peak'
			s_a = np.abs((np.max(data[data_c])-np.mean(data[data_c])))
			s_f0 = data[0][np.where(data[data_c] == max(data[data_c]))[0][0]]*freq_conversion_factor
			print s_f0
			print s_a
			print s_offs
		else:
			print 'expecting dip'
			s_a = -np.abs((np.min(data[data_c])-np.mean(data[data_c])))
			s_f0 = data[0][np.where(data[data_c] == min(data[data_c]))[0][0]]*freq_conversion_factor
		
		#estimate peak/dip width
		mid = s_offs + 0.5*s_a   #estimated mid region between base line and peak/dip
		print mid
		m = []   #mid points
		for dat_p in range(len(data[data_c])-1):
			if np.sign(data[data_c][dat_p] - mid) != np.sign(data[data_c][dat_p+1] - mid):   #mid level crossing
				m.append(dat_p)   #frequency of found mid point
		#print m
		if len(m) > 1:
			s_k = (data[0][m[-1]]-data[0][m[0]])*freq_conversion_factor
			print 'assume k = %.2e'%s_k
		else:
			s_k = 0.15*(data[0][-1]-data[0][0])*freq_conversion_factor   #try 15% of window
			
		p0 = _fill_p0([s_f0, s_k, s_a, s_offs],ps)

		#lorentzian fit ----------------------------------------------------------------------
		try:
			popt, pcov = curve_fit(f_Lorentzian, data[0]*freq_conversion_factor, data[data_c], p0 = p0)
			print 'QL:', np.abs(np.round(float(popt[0])/popt[1]))
		except:
			print 'fit not successful'
			popt = p0
			pcov = None
		finally:
			if show_plot:
				plt.plot(x_vec, f_Lorentzian(x_vec, *popt))
				ax = plt.gca()
				if xlabel == '':
					ax.set_xlabel('f (GHz)', fontsize=13)
					pass
				else:
					ax.set_xlabel(str(xlabel), fontsize=13)
				if ylabel == '':
					#ax.set_ylabel('arg(S21) (a.u.)', fontsize=13)
					pass
					
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
	elif fit_function == 'damped_sine':
		#plot data
		if show_plot:   plt.plot(data[0],data[data_c],'*')
		x_vec = np.linspace(data[0][0],data[0][-1],400)
	
		#start parameters ----------------------------------------------------------------------
		s_offs, s_a, s_Td, s_fs, s_ph = _extract_initial_oscillating_parameters(data,data_c)
		p0 = _fill_p0([s_fs, s_Td, s_a, s_offs, s_ph],ps)

		#damped sine fit ----------------------------------------------------------------------
		try:
			popt, pcov = curve_fit(f_damped_sine, data[0], data[data_c], p0 = p0)
		except:
			print 'fit not successful'
			popt = p0
			pcov = None
		finally:
			if show_plot:   plt.plot(x_vec, f_damped_sine(x_vec, *popt))
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	elif fit_function == 'sine':
		#plot data
		if show_plot:   plt.plot(data[0],data[data_c],'*')
		x_vec = np.linspace(data[0][0],data[0][-1],200)
	
		#start parameters ----------------------------------------------------------------------
		s_offs, s_a, s_Td, s_fs, s_ph = _extract_initial_oscillating_parameters(data,data_c)
		s_offs = np.mean(data[data_c])
		s_a = 0.5*np.abs(np.max(data[data_c]) - np.min(data[data_c]))
		p0 = _fill_p0([s_fs, s_a, s_offs, s_ph],ps)
			
		#sine fit ----------------------------------------------------------------------
		try:
			popt, pcov = curve_fit(f_sine, data[0], data[data_c], p0 = p0)
		except:
			print 'fit not successful'
			popt = p0
			pcov = None
		finally:
			if show_plot:   plt.plot(x_vec, f_sine(x_vec, *popt))
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	elif fit_function == 'exp':
	
		x_vec = np.linspace(data[0][0],data[0][-1],200)
		
		#start parameters ----------------------------------------------------------------------
		s_offs = np.mean(data[data_c][int(0.9*len(data[data_c])):])   #average over the last 10% of entries
		s_a = data[data_c][0] - s_offs
		s_Td = np.abs(float(s_a)/np.mean(np.gradient(data[data_c],data[0][1]-data[0][0])[:5]))   #calculate gradient at t=0 which is equal to (+-)a/T
		#s_Td = data[0][-1]/5   #assume Td to be roughly a fifth of total measurement range
		
		p0 = _fill_p0([s_Td, s_a, s_offs],ps)

		#exp fit ----------------------------------------------------------------------
		try:
			popt, pcov = curve_fit(f_exp, data[0], data[data_c], p0 = p0)
			if xlabel == None:
				print "decay time:",str(popt[0]), 'us'
			else:
				print "decay time:",str(popt[0]), str(xlabel[-4:])
		except:
			print 'fit not successful'
			popt = p0
			pcov = None
		finally:
			#plot data
			if show_plot:
				fig, axes = plt.subplots(1, 2, figsize=(15,4))
				
				axes[0].plot(data[0],data[data_c],'*')
				axes[0].plot(x_vec, f_exp(x_vec, *popt))
				if xlabel == '':
					axes[0].set_xlabel('t (us)', fontsize=13)
					pass
				else:
					axes[0].set_xlabel(str(xlabel), fontsize=13)
				if ylabel == '':
					axes[0].set_ylabel('arg(S21) (a.u.)', fontsize=13)
					pass
				else:
					axes[0].set_ylabel(str(ylabel), fontsize=13)
				#axes[0].set_title('exponential decay', fontsize=15)
				axes[0].set_title(str(popt), fontsize=15)
				
				axes[1].plot(data[0],np.abs(data[data_c]-popt[2]),'*')
				axes[1].plot(x_vec, np.abs(f_exp(x_vec, *popt)-popt[2]))   #subtract offset for log plot
				axes[1].set_yscale('log')
				if xlabel == '':
					axes[1].set_xlabel('t (us)', fontsize=13)
					pass
				else:
					axes[1].set_xlabel(str(xlabel), fontsize=13)
				if ylabel == '':
					axes[1].set_ylabel('normalized log(arg(S21)) (a.u.)', fontsize=13)
					pass
				else:
					axes[1].set_ylabel(str(ylabel), fontsize=13)
				
				#axes[1].set_title('exponential decay', fontsize=15)
				fig.tight_layout()
	
	else:
		print 'fit function not known...aborting'
		return
	
	if show_plot:
		if fit_function != 'exp':
			if xlabel != '':
				plt.xlabel(xlabel)
			if ylabel != '':
				plt.ylabel(ylabel)
			plt.title(str(popt),y=1.03)
			
		try:
			plt.savefig(str(nfile[0:-4])+'_dr.png', dpi=300)
			if save_pdf:
				plt.savefig(str(nfile[0:-4])+'_dr.pdf', dpi=300)
			print 'plot saved:', str(nfile[0:-4])+'_dr.png'
		except Exception as m:
			print 'figure not stored:', m
		plt.show()
	
	if pcov == None:
		return np.concatenate((popt,float('inf')*np.ones(len(popt))),axis=1)   #fill up errors with 'inf' in case fit did not converge
	else:
		return np.concatenate((popt,np.sqrt(np.diag(pcov))),axis=1)   #shape of popt and np.sqrt(np.diag(pcov)) is (4,), respectively, so concatenation needs to take place along axis 1