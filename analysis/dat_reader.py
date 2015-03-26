'''
data reading and fitting script JB@KIT 01/2015 jochen.braumueller@kit.edu
'''

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import fnmatch
import os, glob
import time

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
		print 'Reading file '+str(nfile)
		data = np.loadtxt(nfile, comments='#').T
		#print 'Reading successful!'
	except Exception as message:
		print 'invalid file name...aborting:', message
		return
		
	return data, nfile


def fit_data(file_name = None, fit_function = 'lorentzian', data_c = 2, ps = None, xlabel = '', ylabel = '', show_plot = True):
	
	'''
	fit the data in file_name to a function specified by fit_function
	leaving file_name to None makes the code try to find the newest .dat file in today's data_dir
	
	fit_function can be 'lorentzian', 'damped_sine', 'sine', 'exp'
	data_c: specifies the data column to be used (next to column 0 that is used as the coordinate axis)
	ps: start parameters (optional)
	xlabel: label for horizontal axis (optional)
	ylabel: label for vertical axis (optional)
	
	returns fit parameters, f in GHz
	
	f_Lorentzian expects its frequency parameter to be stated in GHz
	'''
	
	def f_Lorentzian(f, f0, k, a, offs):
		return np.sign(a) * np.sqrt(np.abs(a*(k/2)**2/((k/2)**2+(f-f0)**2)))+offs
		
	def f_damped_sine(t, fs, Td, a, offs, ph):
		return a*np.exp(-t/Td)*np.sin(2*np.pi*fs*t+ph)+offs
		
	def f_sine(t, fs, a, offs, ph):
		return a*np.sin(2*np.pi*fs*t+ph)+offs
		
	def f_exp(t, Td, a, offs):
		return a*np.exp(-t/Td)+offs


	#load data
	data, nfile = load_data(file_name)


	#check column identifier
	if data_c >= len(data):
		print 'bad data column identifier, out of bonds...aborting'
		return
	
	
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
	
		if ps == None:
			#start parameters
			s_offs = np.mean(np.array([data[data_c,:int(np.size(data,1)/10)],data[data_c,np.size(data,1)-int(np.size(data,1)/10):]])) #offset is calculated from the first and last 10% of the data to improve fitting on tight windows @andre20150318
			if np.abs(np.max(data[data_c]) - np.mean(data[data_c])) > np.abs(np.min(data[data_c]) - np.mean(data[data_c])):
				#expect a peak
				print 'expecting peak'
				s_a = (np.max(data[data_c])-np.mean(data[data_c]))**2
				s_f0 = data[0][np.where(data[data_c] == max(data[data_c]))[0][0]]*freq_conversion_factor
			else:
				print 'expecting dip'
				s_a = -(np.min(data[data_c])-np.mean(data[data_c]))**2
				s_f0 = data[0][np.where(data[data_c] == min(data[data_c]))[0][0]]*freq_conversion_factor
			
			#lorentzian fit
			p0 = [s_f0, 0.006, s_a, s_offs]
		else:
			p0 = ps
			
		try:
			popt, pcov = curve_fit(f_Lorentzian, data[0]*freq_conversion_factor, data[data_c], p0 = p0)
			print 'QL:', np.abs(np.round(float(popt[0])/popt[1]))
		except:
			print 'fit not successful'
			popt = p0
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
		
	elif fit_function == 'damped_sine':
		#plot data
		if show_plot:   plt.plot(data[0],data[data_c],'*')
		x_vec = np.linspace(data[0][0],data[0][-1],400)
	
		if ps == None:
			#start parameters
			s_offs = np.mean(data[data_c][int(0.9*len(data[data_c])):])
			#print s_offs
			a1 = np.abs(np.max(data[data_c]) - s_offs)
			a2 = np.abs(np.min(data[data_c]) - s_offs)
			s_a = np.max([a1,a2])
			#print s_a
			#damping
			a_end = np.abs(np.max(data[data_c][int(0.7*len(data[data_c])):]))   #scan last 20% of values -> final amplitude
			#print a_end
			# -> calculate Td
			t_end = data[0][-1]
			#print t_end
			s_Td = -t_end/(np.log((np.abs(a_end-np.abs(s_offs)))/s_a))
			print 'assume T =', str(np.round(s_Td,4))
			
			#frequency
			#s_fs = 1/data[0][int(np.round(np.abs(1/np.fft.fftfreq(len(data[data_c]))[np.where(np.abs(np.fft.fft(data[data_c]))==np.max(np.abs(np.fft.fft(data[data_c]))[1:]))]))[0])] #@andre20150318
			
			roots = 0
			for dat_p in range(len(data[data_c])-1):
				if np.sign(data[data_c][dat_p] - s_offs) != np.sign(data[data_c][dat_p+1] - s_offs):   #offset line crossing
					roots = roots + 1
			s_fs = float(roots)/(2*data[0][-1])   #number of roots/2 /measurement time
			
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
			
			#damped sine fit
			p0 = [s_fs, s_Td, s_a, s_offs, s_ph]
		else:
			p0 = ps
			
		try:
			popt, pcov = curve_fit(f_damped_sine, data[0], data[data_c], p0 = p0)
		except:
			print 'fit not successful'
			popt = p0
		finally:
			if show_plot:   plt.plot(x_vec, f_damped_sine(x_vec, *popt))
	
	elif fit_function == 'sine':
		#plot data
		if show_plot:   plt.plot(data[0],data[data_c],'*')
		x_vec = np.linspace(data[0][0],data[0][-1],200)
	
		if ps == None:
			#start parameters
			s_offs = np.mean(data[data_c])
			s_a = 0.5*np.abs(np.max(data[data_c]) - np.min(data[data_c]))
			
			#frequency
			#s_fs = 1/data[0][int(np.round(np.abs(1/np.fft.fftfreq(len(data[data_c]))[np.where(np.abs(np.fft.fft(data[data_c]))==np.max(np.abs(np.fft.fft(data[data_c]))[1:]))]))[0])] #@andre20150318
			
			roots = 0
			for dat_p in range(len(data[data_c])-1):
				if np.sign(data[data_c][dat_p] - s_offs) != np.sign(data[data_c][dat_p+1] - s_offs):   #offset line crossing
					roots = roots + 1
			s_fs = float(roots)/(2*data[0][-1])   #number of roots/2 /measurement time
			
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
			
			#sine fit
			p0 = [s_fs, s_a, s_offs, s_ph]
		else:
			p0 = ps
			
		try:
			popt, pcov = curve_fit(f_sine, data[0], data[data_c], p0 = p0)
		except:
			print 'fit not successful'
			popt = p0
		finally:
			if show_plot:   plt.plot(x_vec, f_sine(x_vec, *popt))
			
	elif fit_function == 'exp':
	
		x_vec = np.linspace(data[0][0],data[0][-1],200)
		if ps == None:
			#start parameters
			s_offs = np.mean(data[data_c][int(0.9*len(data[data_c])):])   #average over the last 10% of entries
			s_a = data[data_c][0] - s_offs
			s_Td = np.abs(float(s_a)/np.mean(np.gradient(data[data_c],data[0][1]-data[0][0])[:5]))   #calculate gradient at t=0 which is equal to (+-)a/T
			#s_Td = data[0][-1]/5   #assume Td to be roughly a fifth of total measurement range
			
			#exp fit
			p0 = [s_Td, s_a, s_offs]
		else:
			p0 = ps
			
		try:
			popt, pcov = curve_fit(f_exp, data[0], data[data_c], p0 = p0)
			if xlabel == None:
				print "decay time:",str(popt[0]), 'us'
			else:
				print "decay time:",str(popt[0]), str(xlabel[-4:])
		except:
			print 'fit not successful'
			popt = p0
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
			print 'plot saved:', str(nfile[0:-4])+'_dr.png'
		except Exception as m:
			print 'figure not stored:', m
		plt.show()
	return popt