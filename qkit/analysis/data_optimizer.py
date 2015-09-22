'''
data optimization script JB@KIT 09/2015 jochen.braumueller@kit.edu

The data optimizer is fed with microwave data of both quadratures, typically amplitude and phase.
The goal is to use all available complex data and to return data on a real scale without dropping any information.
This is achieved by considering the data in the complex Gauss plane and calculating the distance of each data point
to the complex value with maximum amplitude. This is a point at one of the ends of the line spanned by the data points
in the complex plane.
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
		cdata = np.array(data[1]) * np.exp(1j*np.array(data[2]))
	except IndexError:
		print 'Bad column identifier...aborting.'
	except ValueError:
		print 'Faulty data input, dimension mismatch...aborting.'
	
	#extract complex point with maximum amplitude
	cmax = np.extract(np.abs(cdata) == np.max(np.abs(cdata)),cdata)
	
	#calculate distances
	data_opt = np.abs(cdata - cmax)
	
	#norm and return
	data_opt_n = data_opt - np.min(data_opt)
	data_opt_n /= np.max(data_opt_n)
	return np.array([np.array(data[0]),np.array(data_opt_n)])
	