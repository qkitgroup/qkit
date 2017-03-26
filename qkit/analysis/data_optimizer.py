'''
data_optimizer.py

data optimization script JB@KIT 09/2015 jochen.braumueller@kit.edu
updates: 03/2017 (JB)

The data optimizer is fed with microwave data of both quadratures, typically amplitude and phase.
It effectively performs a principle axis transformation in the complex plane of all data points
that are located along a line for a typical projective qubit state measurement without single-shot
fidelity and using a ADC acquisition card. Successively, data optimizer returns a projection along
the in-line direction quadrature containing maximum information. Indeally, no information is lost
as no data is left in the orthogonal quadrature.

The algorithm locates one of the edge data points on either end of the line-shaped data point distribution
by summing and maximizing the mutual distances between data points. It then calculates the distance
of each data point with respect to this distinct extremal data point.

We assume that the possible outcomes of a strong and projective quantum measurement, i.e. the qubit
states |0>, |1>, result in two distinct locations in the complex plane, corresponding to signatures
of the dispersive readout resonator. In the absence of single-shot readout fidelity, the pre-averaging
that is perfomed by the ADC card in the complex plane leads to counts in between the piles denoting |0>
and |1>. The points laong this line are distributed due to statistical measurement noise and ultimately
due to the quantum uncertainty. As the averaging takes place in the complex plane, all points recorded
in such a measurement should be located on a line. In case of a phase sensitive reflection measurement
at a high internal quality cavity, points may span a segment of a circle that can be caused by noise
caused measurements of the resonator position away from the two quantumn positions.

The line shape of the data distribution generally justifies the projection of measurement data to an
arbitrary axis without altering the internal data shape.
'''

import numpy as np
import logging

# =================================================================================================================

def optimize(data, c_amp = 1, c_pha = 2, normalize = True):
    
    '''
    input:

        - data: data array of the form the dat_reader returns it:
          data = [[f1,f2,...,fn],...,[a1,a2,...,an],[ph1,ph2,...,phn],...]
        - c_amp, c_pha: columnmn identifiers for amplitude and phase data in the data array
        - normalize: (optional, default: True) data normalization is performed when set to True
        
    output:

        - numpy data array of the form [[x1,x2,...,xn],[v1,v2,...,vn]]
    '''

    #generate complex data array
    try:
        c = np.array(data[1]) * np.exp(1j*np.array(data[2]))
    except IndexError:
        print 'Bad column identifier...aborting.'
    except ValueError:
        print 'Faulty data input, dimension mismatch...aborting.'
    
    #point in complex plane with maximum sumed mutual distances
    s = np.zeros_like(np.abs(c))
    for i in range(len(c)):
        for p in c:
            s[i]+=np.abs(p-c[i])
    cmax = np.extract(s == np.max(s),c)
    
    #calculate distances
    data_opt = np.abs(c - cmax)
    
    if normalize:
        data_opt = (data_opt.transpose() - np.min(data_opt.transpose(),axis=0)).transpose()
        data_opt = (data_opt.transpose() / np.max(data_opt.transpose(),axis=0)).transpose()
        if type(np.mean(data_opt,axis=0)) == np.ndarray:
            logging.warning('Normalization is performed on individual sets.')
        
    return np.array([np.array(data[0]),np.array(data_opt)])
    