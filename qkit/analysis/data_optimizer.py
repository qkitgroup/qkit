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

Errors are calculated projected on the axis complex data points are aligned along. Data is normalized
prior to returning.
'''

import matplotlib.pyplot as plt
import numpy as np
import logging

# =================================================================================================================

def optimize(data, c_amp = 1, c_pha = 2, show_complex_plot = False):
    '''
    input:

        - data: data array of the form the dat_reader returns it:
          data = [[f1,f2,...,fn],...,[a1,a2,...,an],[ph1,ph2,...,phn],...]
          columns are to be two-dimensional raw data entries in order to enable error extraction,
          average data is accepted
        - c_amp, c_pha: columnmn identifiers for amplitude and phase data in the data array
        - show_complex_plot: (bool) (optional, default: False) plots the data points in the complex plane
                             if True, only in case the data columns in data are 1D
        
    output:

        - numpy data array with x values, data values and entries
          of the form [[x1,x2,...,xn],[v1,v2,...,vn],[e1,e2,...,en]] if raw data was given
    '''

    #generate complex data array
    try:
        c_raw = np.array(data[c_amp]) * np.exp(1j*np.array(data[c_pha]))
    except IndexError:
        print 'Bad column identifier...aborting.'
    except ValueError:
        print 'Faulty data input, dimension mismatch...aborting.'

    if len(c_raw.shape) > 1:
        #calculate mean of complex data
        c = np.mean(c_raw,axis=0)
    else:   #given data is already averaged
        c = c_raw

    #point in complex plane with maximum sumed mutual distances
    s = np.zeros_like(np.abs(c))
    for i in range(len(c)):
        for p in c:
            s[i]+=np.abs(p-c[i])
    cmax = np.extract(s == np.max(s),c)

    #calculate distances
    data_opt = np.abs(c - cmax)

    if len(c_raw.shape) > 1:
        #calculate errors in line direction

        #find maximum complex point in maximum distance
        d = 0
        for p in c:
            if np.abs(p-cmax) > d:
                d = np.abs(p-cmax)
                cdist = p
        #find unit vector in line direction
        vunit = (cdist - cmax)/np.abs(cdist - cmax)

        #calculate projected distances via dot product, projecting along the data direction
        #errors via std
        dist_proj = [0]*len(c)
        errs = np.zeros_like(c)
        for i,ci in enumerate(c_raw.T):   #for each iteration
            dist_proj[i] = [np.abs(np.vdot([np.real(vunit),np.imag(vunit)],[np.real(cr)-np.real(c[i]),np.imag(cr)-np.imag(c[i])])) for cr in ci]
            errs[i] = np.std(dist_proj[i])/np.sqrt(len(dist_proj[i]))
    
    #normalize optimized data
    data_opt -= np.min(data_opt)
    maxv = np.max(data_opt)
    data_opt /= maxv
    if len(c_raw.shape) > 1:
        errs /= maxv
        
    #gauss plane plot
    if show_complex_plot:
        if len(c_raw.shape) > 1:
            plt.figure(figsize=(10,13))
            ax1 = plt.subplot2grid((4, 1), (0, 0))
            ax2 = plt.subplot2grid((4, 1), (1, 0), rowspan = 3)
            ax1.errorbar(data_opt,np.zeros_like(data_opt),xerr=errs,color='blue',fmt='o',elinewidth=0.8,capsize=5,markersize=8,ecolor='red')
            ax1.plot([0],[0],'*',color='red',markersize=20)
            prange = np.max(data_opt)-np.min(data_opt)
            ax1.set_xlim(np.min(data_opt)-0.05*prange,np.max(data_opt)+0.05*prange)
            ax2.plot(np.real(c),np.imag(c),'.')
            ax2.plot(np.real(c)[:10],np.imag(c)[:10],'.',color='r')   #show first 10 data points in red
            ax2.plot(np.real(cmax),np.imag(cmax),'*',color='black',markersize=15)
        else:
            plt.figure(figsize=(10,10))
            plt.plot(np.real(c),np.imag(c),'.')
            plt.plot(np.real(c)[:10],np.imag(c)[:10],'.',color='r')   #show first 10 data points in red
            plt.plot(np.real(cmax),np.imag(cmax),'*',color='black',markersize=15)
        
    if len(c_raw.shape) > 1: return np.array([np.array(data[0]),np.array(data_opt),errs])
    else: return np.array([np.array(data[0]),np.array(data_opt)])
    