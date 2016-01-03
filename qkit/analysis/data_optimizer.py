'''
data optimization script JB@KIT 09/2015 jochen.braumueller@kit.edu

The data optimizer is fed with microwave data of both quadratures, typically amplitude and phase.
The goal is to use all available complex data and to return data on a real scale without dropping any information.
This is achieved by considering the data in the complex Gauss plane and calculating the distance of each data point
to the complex value with maximum amplitude. This is a point at one of the ends of the line spanned by the data points
in the complex plane.
This approach is equivalent to a rotation of the principal axis and the projection onto a quadrature with minimum
information loss.

We assume that the possible qubit states |0>, |1> lead to two distinct positions of the resonance dip of our dispersive readout resonator.
The reason that not only two hot spots are visible in a typical qubit measurement is the averaging the adc card does before tranferring a "single"
data point to the measurment script. However, since this averaging takes place in the complex plane, all points recorded in such a measurement
should be located on a line. This justifies the projection of measurement data to an arbitrary axis without any loss in the shape of measured data.
When using the data_optimizer, all measurement values are output with respect to one of the edge points of the line in the complex plane and normalized.
This leads to a possible offset in the x axis parameter.

input: data array of the form the dat_reader returns it: data = [[f1,f2,...,fn],...,[a1,a2,...,an],[ph1,ph2,...,phn],...] together with two column identifiers.
output: data array of the form data_ret = [[f1,f2,...,fn],[n1,n2,...,nn]], with ni denoting normalized values; len(data_ret[i]) = len(data[j]) for all i in len(data_ret), j in len(data)
'''

import numpy as np


def optimize(data, c_amp = 1, c_pha = 2):
	
	'''
	input:
	* data array of the form the dat_reader returns it: data = [[f1,f2,...,fn],...,[a1,a2,...,an],[ph1,ph2,...,phn],...]
	* column identifiers c_amp, c_pha (optional, default: 1,2)
	output:
	* data array of the form data_ret = [[f1,f2,...,fn],[n1,n2,...,nn]], with ni denoting normalized values;
	  len(data_ret[i]) = len(data[j]) for all i in len(data_ret), j in len(data)
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
	