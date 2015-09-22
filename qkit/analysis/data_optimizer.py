'''
data optimization script JB@KIT 09/2015 jochen.braumueller@kit.edu

The data optimizer is fed with microwave data of both quadratures, typically amplitude and phase.
The goal is to use all available complex data and to return data on a real scale without dropping any information.
This is achieved by considering the data in the complex Gauss plane and calculating the distance of each data point
to the average complex value, lying in the middle of the line that is spanned in the complex plane.
This approach is equivalent to a rotation of the principal axis and the projection onto a quadrature with minimum
information loss.

input: data array of the form the dat_reader returns it: data = [[f1,f2,...,fn],...,[a1,a2,...,an],[ph1,ph2,...,phn],...] together with two column identifiers.
output: data array of the form data_ret = [[f1,f2,...,fn],[n1,n2,...,nn]], with ni denoting normalized values; len(data_ret[i]) = len(data[j]) for all i in len(data_ret), j in len(data)
'''

import numpy as np
import os, glob
import time
import logging

no_qt = False
try:
	import qt
	data_dir_config = qt.config.get('datadir')
except ImportError as message:
	print 'Warning:', message
	no_qt = True


def optimize(data, c_amp = 1, c_pha = 2):
	
	'''
	input: data array of the form the dat_reader returns it: data = [[f1,f2,...,fn],...,[a1,a2,...,an],[ph1,ph2,...,phn],...] together with two column identifiers.
	output: data array of the form data_ret = [[f1,f2,...,fn],[n1,n2,...,nn]], with ni denoting normalized values; len(data_ret[i]) = len(data[j]) for all i in len(data_ret), j in len(data)
	'''

	#generate complex data array
	try:
		cdata = data[c_amp] + np.exp(1j*data[c_pha])
	except IndexError:
		print 'Bad column identifier...aborting.'
	except ValueError:
		print 'Faulty data input, dimension mismatch...aborting.'
	
	
	
	
	if file_name == 'dat_import':
		print 'use imported data'
	else:
		#load data
		data, nfile = load_data(file_name)

	#check column identifier
	if data_c >= len(data):
		print 'bad data column identifier, out of bonds...aborting'
		return
	
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