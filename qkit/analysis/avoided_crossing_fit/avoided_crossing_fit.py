#!/usr/bin/python
# Filename: crossing_fit.py

version = '0.1'

'''
Avoided crossing module (ASt@KIT 2016):
    Contains:
    
        crossing_fct: Function of an avoided crossing (as given by theory (Jaynes-Cummings type coupling)). Useful for plotting fits etc.
        
        plot_curves: Plot crossings of given functions in given range.
        
        crossing_plot: Plot crossing, with data in x and y range of data.
        
        crossing_fit: Fit avoided crossing to peak data.
    
        Several simple functions for fitting and plotting.
'''

import os, sys, time
import logging

import numpy as np

import matplotlib.pyplot as plt

import scipy.constants as sc
import scipy.optimize as fit
import scipy.ndimage as scd

import inspect

def c_line(x, a):
    return a+0*x
# ================================================================================================================= 

def s_line(x,a,b):
    return a*x + b
# ================================================================================================================= 

def parabola(x, a, b, c):
    return a*(x-b)**2 + c
# ================================================================================================================= 

def f01_transmon(x, w0, L_eff, I_ext, djj):
    '''
    w0 = maximum frequency without detuning,
    L_eff = 2*pi*effective inductance/Phi0
    I_ext = offset_flux (rather effective external bias current) at 0 current (i.e. x = 0)
    djj = junction anharmonicity
    ''' 
    return w0 * ((((np.cos(L_eff*(x - I_ext)))**2)**.5)*(1+(djj**2)*(np.tan(L_eff*(x - I_ext)))**2)**.5)**.5
# ================================================================================================================= 

def _reshape_params(fcts, pars):
    fct_par_ind = 0
    fct_params = []
    for fct in fcts:
        fct_par_num = len(inspect.getargspec(fct)[0])-1
        fct_params.append(pars[fct_par_ind:fct_par_ind + fct_par_num])
        fct_par_ind += fct_par_num
        
        
    fct_params.append(pars[fct_par_ind:])
    return fct_params
# ================================================================================================================= 

def _dim_check(x, y, fcts):
    status = True
    xlen = len(x)
    ylen = len(y)
    flen = len(fcts)
    message = ""
    
    if xlen != ylen:
        status = False
        message = "Number of x and y arrays does not match."
    if xlen != flen:
        status = False
        message = "Number of x arrays and functions does not match."
    if ylen != flen:
        status = False
        message = "Number of y arrays and functions does not match."
    
    
    return xlen, ylen, flen, status, message
# ================================================================================================================= 

def crossing_fct(x, fcts, fct_params, show_output = True):
    flen = len(fcts)
    fct_pars = fct_params[:-1]
    g = np.atleast_1d(np.array(fct_params[-1]))
    

    if flen > len(fct_pars) or flen < len(fct_pars):
        if show_output:
            print "Number of parameters does not fit number of functions!"
        return x
    
    if len(g) < (flen**2-flen)/2:
        if show_output:
            print "Number of coupling constants too small (should be "+str((flen**2-flen)/2)+"), filling with zeros."
        g = np.append(g,np.zeros(flen**2-flen)/2-np.size(g))
    
    if len(g) > (flen**2-flen)/2:
        if show_output:
            print "Coupling constant array too long. Cutting off last entries."
        g = g[:(flen**2-flen)/2]
    
    #Create the nondiagonal symmetric interaction matrix
    int_mat = np.zeros((flen, flen))
    
    
    for i in range(flen-1):
        int_mat[i, i+1:] = g[:np.size(int_mat[i,i+1:])]
        g = g[flen-1-i:]

    int_mat = int_mat+int_mat.T
    
    func_vals = np.zeros((np.size(x), flen))
    
    x = np.atleast_1d(x)
    for n in range(np.size(x)):
        #Create diagonal parts of the matrix
        d_mat = np.zeros((flen, flen))
        i = 0
        for fct in fcts:
            d_mat[i,i] = fct(x[n], *fct_pars[i])
            i+=1
        
        mat = d_mat + int_mat
        func_vals[n, :] = np.linalg.eigvalsh(mat)
        
    return func_vals
# ================================================================================================================= 

def _deviation(pars, x, y, fcts):
    
    dev = []
    fct_number = len(np.atleast_1d(fcts))
    x = np.atleast_1d(x)
    y = np.atleast_1d(y)
    
    
    fct_params = _reshape_params(fcts, pars)
    
    i=0
    for fct in fcts:
        if (i <= len(x)) and (len(x[i]) != 0):
            dev = np.append(dev, y[i]-crossing_fct(x[i], fcts, fct_params, show_output = False)[:,i])
        i+=1
    
    return dev
# ================================================================================================================= 

def crossing_fit(x, y, fcts = [c_line, s_line], guess = [1], show_plot = True, save_plot = False, show_fitdata = True):
    '''
    Input is:
        x: List of x arrays (i.e. [x1, x2, ...]). 
        y: List of y arrays (i.e. [y1, y2, ...]). Please divide by 1e9 if values are in GHz (elsewise leasts quares sometimes crashes).
        fcts: List of primal functions (i.e. [c_line, s_line, prabola, ...]). You can also write your own functions. Just make sure they are defined like:
            def myfct(x, a, b, c, ...) and not with an array as input parameter.
        show_plot: Shows plot.
        show_fitdata: Shows fit data.
    Output:
        fit parameters and covariance matrix.

    Returns:
        fit_params: Array containing the fit parameters.
        pcov: Array containing covariance matrix of the fit parameters. To get standard deviation use np.diag(pcov)**.5 .
    '''

    xlen, ylen, flen, status, message = _dim_check(x, y, fcts)
    
    xlen_tot = 0
    if (type(x) != list) and (type(y) != list):
        print len(x),len(y)

        if (len(x) != len(y)):
            raise ValueError("x and y array must have same dimension.")
            
        xlen = 1
        ylen = 1
        flen = 1
        fcts = np.atleast_1d(fcts)
        xlen_tot = len(x)
        status = True
        
    if not status:
        raise ValueError(message)
    
    for i in range(xlen):
        xlen_tot += len(x[i])
        if len(x[i]) != len(y[i]):
            raise ValueError("Length of x array "+str(i)+" corresponding y array does not match.")
    
    fct_par_num = 0
    for fct in fcts:
        fct_par_num += len(inspect.getargspec(fct)[0]) - 1
    
    fct_par_num += (flen**2-flen)/2
    
    
    if len(guess) < fct_par_num: 
        print "Number of guess parameters does not match number of function parameters + number of coupling constants."
        print "Filling remaining array with ones."
        guess = guess + [1]*(fct_par_num - len(guess)) 
    
    
    if len(guess) > fct_par_num:
        print "Number of guess parameters does not match number of function parameters + number of coupling constants."
        print "Cutting off last "+str(len(guess) - fct_par_num) + " elements."
        guess = guess[:fct_par_num]
        

    fit_params, pcov, infodict, message, ier = fit.leastsq(_deviation, guess, args =(x, y, fcts), full_output = 1)
    
    
    #Multiply covariance matrix pcov with reduced chi squared to get error
    if pcov != None:
        pcov *= sum(_deviation(fit_params, x, y, fcts)**2)/(xlen_tot - float(len(guess)))

    #Change coupling to always have +sign
    fit_params[len(fit_params)-(flen**2-flen)/2:] = np.abs(fit_params[len(fit_params)-(flen**2-flen)/2:])
    
    if show_fitdata:
        i = 0
        par_ind = 0
        for fct in fcts:
            print("Parameter curve " + str(i+1) + " (" + (fct.__name__) + "):")
            for p in inspect.getargspec(fct)[0][1:]:
                try:
                    print(p+" = ( {0:7.3f} +- {1:8.3f})".format(fit_params[par_ind], np.abs(np.diag(pcov)[par_ind])**0.5))
                except:
                    print(p+" = ( {0:7.3f})".format(fit_params[par_ind]))
                par_ind += 1
            i += 1
        print("Coupling strengths:")
        i = 0
        for cs in fit_params[par_ind:]:   #JB: cs not in use?!
            try:
                print("g["+ str(i)+"] = ( {0:7.4f} +- {1:8.4f})".format(fit_params[par_ind], np.abs(np.diag(pcov)[par_ind])**0.5))
            except:   #JB: global except clause is not nice, catch ValueError maybe and an empty g entry in fit_params separately...
                print("g["+ str(i)+"] = ( {0:7.4f} +- {1:8.4f})".format(fit_params[par_ind]))
            i += 1
            par_ind += 1
    
    fit_params = _reshape_params(fcts, fit_params)
    
    if show_plot:
        crossing_plot(x, y, fcts, fit_params, save_plot = save_plot)
    
    
    return fit_params, pcov
# ================================================================================================================= 

def crossing_plot(x, y, fcts, fit_params, cols = False, marker = "*", save_plot = False, ax=None):
    '''
    Input is:
        x: List of x arrays (i.e. [x1, x2, ...]). 
        y: List of y arrays (i.e. [y1, y2, ...]). Please divide by 1e9 if values are in GHz.
        fcts: List of primal functions (i.e. [c_line, s_line, prabola, ...]).
        fit_params: Fit parameters as given by crossing_fit.
        marker: Marker shape for fit data. Set to False if you don't want to plot experimental values.
        cols: List of colors you want to use (i.e. ["r", "b", ...]).
    Output:
        Saves plot if you choose so.
    '''
    
    if not cols:
        cols = ["b", "r", "g", "k", "c", "m", "y"]
    
    xlen, ylen, flen, status, message = _dim_check(x, y, fcts)
    if not status:
        raise ValueError(message)
    
    #Get plot boundaries
    xmin, xmax = np.amin(np.concatenate(x)), np.amax(np.concatenate(x))
    ymin, ymax = np.amin(np.concatenate(y)), np.amax(np.concatenate(y))
    
    #Plot
    if not ax:
    	fig, ax = plt.subplots(figsize = (16, 8))
    xlin = np.linspace(xmin, xmax, 300)
    


    for i in range(len(x)):
        ax.plot(xlin, crossing_fct(xlin, fcts, fit_params, show_output = False)[:, i], cols[i], linewidth = 1)
        if marker:
            ax.plot(x[i], y[i], cols[i]+marker, markersize = 7)
    
    dx, dy = 0.05*(xmax - xmin), 0.05*(ymax - ymin)
    plt.xlim(xmin - dx, xmax + dx)
    plt.ylim(ymin - dy, ymax + dy)
    if save_plot:
        plt.savefig("crossing_fit_plot.png")
# ================================================================================================================= 

def plot_curves(x, fcts, fit_params, cols = False, lw = 1, ax = None):
    '''
    Input is:
        x: Linspace for plotting or boundaries for plot (default = 1000 points). 
        fcts: List of primal functions (i.e. [c_line, s_line, prabola, ...]).
        fit_params: Fit parameters as given by crossing_fit.
        cols: List of colors you want to use (i.e. ["r", "b", ...]).
        lw: Linewidth in plot.
    Output:
        Plots curves in current plot window.
    '''
    
    if not cols:
        cols = ["b", "r", "g", "k", "c", "m", "y"]
    
    if len(np.atleast_1d(fcts)) != len(fit_params) -1:
        return ValueError("Number of fcts and fit_parameters does not match.")
    
    if len(fit_params[-1]) != (len(fcts)**2 - len(fcts))/2:
        return ValueError("Number of coupling constants does not fit number of functions.")
    
    if len(x) == 2:
        x = np.linspace(x[0], x[1], 1000)
    if not ax:
	fig, ax = plt.subplots(figsize = (16, 8))
    for i in range(len(fcts)):
        ax.plot(x, crossing_fct(x, fcts, fit_params, show_output = False)[:, i], cols[i], linewidth = lw)
# ================================================================================================================= 



# End of crossing_fit.py