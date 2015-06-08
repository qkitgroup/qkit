import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *

import numpy as np
import matplotlib.pyplot as plt
import copy
import scipy.optimize as spopt
 
def loadspecdata(filename,var_col=0,f_col=1,y1_col=2,y2_col=3,sformat='Real/Imag'):
    '''
    old relict. Might be useful when you want your data in block form. 
    Use loadspecdata2 instead.
    '''
    f = open(filename, 'r')
    data = []
    t=[]
    tempdata = []
    newblock = True
    lines = f.readlines()
    for line in lines:
        if line!='\n':
            if line[0]!='#':
                if newblock==True:
                    newblock = False
                    if len(tempdata)>0:
                        data += [tempdata]
                        tempdata = []
                t = [float(i) for i in line.split()]
                if sformat=='Real/Imag':
                    tempdata+=[[float(t[var_col]),float(t[f_col]),np.complex(float(t[y1_col]),float(t[y2_col]))]]
                if sformat=='Amp/Phase':
                    tempdata+=[[float(t[var_col]),float(t[f_col]),t[y1_col]*np.exp(np.complex(0,t[y2_col]))]]
                if sformat=='Amp[dB]/Phase':
                    tempdata+=[[float(t[var_col]),float(t[f_col]),(10**(float(t[y1_col])/20.))*np.exp(np.complex(0,t[y2_col]))]]                
        else:
            newblock = True
        QApplication.processEvents() #only needed when using this for qt applications
        
    f.close()
    lines = []
    if len(tempdata)>0:
        data += [tempdata]
        newblock = False
        tempdata = []
        
    return data,var_col,f_col,y1_col 

def loadspecdata2(filename,var_col=0,f_col=1,y1_col=2,y2_col=3,sformat='Real/Imag'):
    f=open(filename,'r')
    lines=f.readlines()
    
    firstblock=True
    
    i_data=[]
    f_data=[]
    z_temp=[]
    z_data=[]
    for line in lines:
        if line=='\n':
            if len(z_temp)!=0: 
                firstblock=False
                i_data.append(float(x[var_col]))
                z_data.append(z_temp)
                z_temp=[]
            
        if line!='\n' and line[0]!='#':
            x=line.split()
            
            if firstblock:
                f_data.append(float(x[f_col]))
                
            if sformat=='Real/Imag':
                z_temp.append(np.complex(float(x[y1_col]),float(x[y2_col])))
            if sformat=='Amp/Phase':
                z_temp.append(float(x[y1_col])*np.exp(np.complex(0,float(x[y2_col]))))
            if sformat=='Amp[dB]/Phase':
                z_temp((10**(float(x[y1_col])/20.))*np.exp(np.complex(0,x[y2_col])))
                
    if line!='\n':    
        z_data.append(z_temp) 
        i_data.append(float(x[var_col]))
    
    return i_data,f_data,z_data

def column(matrix, i):
    return [row[i] for row in matrix]

def row(matrix,i):
    return matrix[i]

def S21(f,fr=10e9,Qr=900.0,Qc=1000.,phi=0.,a=1.,alpha=0.,delay=.0):
    return a*np.exp(np.complex(0,alpha))*np.exp(np.complex(0,-2.*np.pi*f*delay))*(1.-Qr/Qc*np.exp(np.complex(0,phi))/np.complex(1,2*Qr*(f-fr)/fr)) 
    
def S21_delay_removed(f,fr=10e9,Qr=900.0,Qc=1000.,phi=0.,a=1.,alpha=0.):
    return a*np.exp(np.complex(0,alpha))*(1.-Qr/Qc*np.exp(np.complex(0,phi))/np.complex(1,2*Qr*(f-fr)/fr)) 

def remove_cable_delay(f_data,z_data, delay):
    return [z_data[i]*np.exp(complex(0,2.*np.pi*f_data[i]*delay)) for i in range(len(f_data))]

def remove_cable_delay_2d(f_data,z_data_2d,delay):
    
    z_new=[]
    for z in z_data_2d:
        
        z_new_temp=[]
        j=0
        
        for z0 in z:
            z_new_temp.append(z0*np.exp(np.complex(0,2.*np.pi*f_data[j]*delay)))
            z_new_temp=list(z_new_temp)
            j+=1
            
        z_new.append(z_new_temp)
    
    return z_new

def st_deviation(residuals):
    n=len(residuals[0])
    st_dev=[]
    for res in residuals:
        sum_0=0
        for t in res:
            sum_0=sum_0+t**2
        st_dev.append(np.sqrt(sum_0/n))
    return st_dev
    
def cut_scan_range(data,x_min,x_max,var_col=0):
    data_new=[]
    i_min=0 
    i_max=0 
    for data0 in data:
        var=column(data0,var_col)
        if x_min<=var[0] and x_max>=var[0]:
            data_new.append(data0)
    
    return data_new
        
def cut_f_range(f_data,z_data,f_min,f_max,f_col=1):
    
    z_new=[]
    f_new=[]
    firstloop=True
    
    for z0 in z_data:
        
        z_new_temp=[]
        i=0       
        for f0 in f_data:
            if f_min<=f0 and f_max>=f0:
                z_new_temp.append(z0[i])
                if firstloop:
                    f_new.append(f0)
            i+=1
        firstloop=False
            
        z_new.append(z_new_temp)
        
    return f_new,z_new
    
def cut_parameters(x,z1,z1_delay,z2_amp,z2_phase,standard_deviation,standard_deviation_phase,results_data,z_raw_data,x_min,x_max):
    i_min=0
    i_max=0
    
    for i in range(0,len(x)):
        if x[i]>=x_min:
            i_min=i
            for j in range(i_min,len(x)):
                if x[j]>=x_max:
                    i_max=j
                    break
            break
    
    x0=x[i_min:i_max+1]
    z10=z1[i_min:i_max+1]
    z1_delay0=z1_delay[i_min:i_max+1]
    z2_amp0=z2_amp[i_min:i_max+1]
    z2_phase0=z2_phase[i_min:i_max+1]
    standard_deviation0=standard_deviation[i_min:i_max+1]
    standard_deviation_phase0=standard_deviation_phase[i_min:i_max+1]
    results_data0=results_data[i_min:i_max+1]
    z_raw_data0=z_raw_data[i_min:i_max+1]
    
    return x0,z10,z1_delay0,z2_amp0,z2_phase0,standard_deviation0,standard_deviation_phase0,results_data0,z_raw_data0
    
def cut_parameters_in_f(y,z1,z1_delay,z2_amp,z2_phase,z_raw_data,x_min,x_max):
    
    i_min=0
    i_max=0
    
    for i in range(0,len(y)):
        if y[i]>=x_min:
            i_min=i
            for j in range(i_min,len(y)):
                if y[j]>=x_max:
                    i_max=j
                    break
            break
       
    z10=np.zeros((len(z1),i_max-i_min+1),dtype=complex)
    z1_delay0=copy.deepcopy(z10)
    z2_amp0=np.zeros((len(z2_amp),i_max-i_min+1))
    z2_phase0=np.zeros((len(z2_phase),i_max-i_min+1))
    y0=np.zeros((len(y),i_max-i_min+1))
    z_raw_data0=[]
    
    y0=y[i_min:i_max+1]
   
    j=0
    for zi in z1:
        z10[j]=zi[i_min:i_max+1]
        z1_delay0[j]=z1_delay[j][i_min:i_max+1]
        z2_amp0[j]=z2_amp[j][i_min:i_max+1]
        z2_phase0[j]=z2_phase[j][i_min:i_max+1]
        z_raw_data0.append(z_raw_data[j][i_min:i_max+1])
        j+=1
      
    return y0,z10,z1_delay0,z2_amp0,z2_phase0,z_raw_data0
    
def fit_skewed_lorentzian_2(f_data,z_data):
    '''
    based on "fit_skewed_lorentzian" from resonator_tools with a few changes regarding
    the start parameters A3a and fra for the iteration. This fit algorithm is specifically 
    designed for "upwards pointing" resonators.
    '''
    amplitude = np.absolute(z_data)
    amplitude_sqr = amplitude**2
    A1a = np.min(amplitude_sqr[0],amplitude_sqr[len(amplitude_sqr)-1])
    A3a = np.max(amplitude_sqr)-A1a
    fra = f_data[np.argmax(amplitude_sqr)]
    def residuals(p,x,y):
        A2, A4, Qr = p
        err = y -(A1a+A2*(x-fra)+(A3a+A4*(x-fra))/(1.+4.*Qr**2*((x-fra)/fra)**2))
        return err
    p0 = [0., 0., 1e3]
    p_final = spopt.leastsq(residuals,p0,args=(np.array(f_data),np.array(amplitude_sqr)))
    A2a, A4a, Qra = p_final[0]
    ##A2a, A4a, Qra = [0., 0., 1e3]

    def residuals2(p,x,y):
        A1, A2, A3, A4, fr, Qr = p
        err = y -(A1+A2*(x-fr)+(A3+A4*(x-fr))/(1.+4.*Qr**2*((x-fr)/fr)**2))
        return err
    p0 = [A1a, A2a , A3a, A4a, fra, Qra]
    p_final = spopt.leastsq(residuals2,p0,args=(np.array(f_data),np.array(amplitude_sqr)))
    #A1, A2, A3, A4, fr, Qr = p_final[0]
    #print p_final[0][5]
    return p_final[0]
    
def skewed_lorentz_function(x,A1,A2,A3,A4,fr,Qr):
    '''
    The skewed lorentz function is parameterized such that it can take negative values
    for some x but the sqaure of the amplitude must be positive obviously. Depending
    on your data the fit might yield parameters that allow the function 
    to intercept the y-axis in some off-resonance areas.
    '''
    x=A1+A2*(x-fr)+(A3+A4*(x-fr))/(1.+4.*Qr**2*((x-fr)/fr)**2)
    if x>=0:
        return np.sqrt(x)
    else:
        return 0.0
        
def convert_to_complex_array(dset_x,dset_y,sformat='Amp[dB]/Phase'):
    
    x=np.array(dset_x)
    y=np.array(dset_y)
    
    if sformat=='Amp[dB]/Phase':
        z=(10**(x/20.))*np.exp(1j*y)
    
    if sformat=='Amp/Phase':
        z=x*np.exp(1j*y)
        
    if sformat=='Real/Imag':
        z=np.array(x)+1j*np.array(y)
        
    return z
        









