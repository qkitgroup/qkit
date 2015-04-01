#Resonant_circuits_tools.py
#higher level resonant circuit data processing functions
#last update: 17/07/2014 by Jochen Braumueller: jochen.braumueller@kit.edu

import time
import sys
import scipy
import qt
import os
import numpy as np
import math as mt
import qt
import scipy

import scipy.optimize as spopt
from scipy import stats

import resonator_tools as rt
import resonator_tools_xtras as rtx


vna = qt.instruments.get('vna')


def fit_skewed_lorentzian(f_data,z_data, ResPeak):
    amplitude = [np.absolute(z) for z in z_data ]
    amplitude_sqr = [a**2 for a in amplitude]

    if ResPeak==True:
        #print len(amplitude_sqr)
        #print np.max([amplitude_sqr[0],2.])
        A1a = np.max([amplitude_sqr[0],amplitude_sqr[len(amplitude_sqr)-1]])
        A3a = np.max(amplitude_sqr)
        fra = f_data[np.argmax(amplitude_sqr)]
    else:
        A1a = np.min([amplitude_sqr[0],amplitude_sqr[len(amplitude_sqr)-1]])
        A3a = -np.max(amplitude_sqr)
        fra = f_data[np.argmin(amplitude_sqr)]
        
    def residuals(p,x,y):   #skewed Lorentzian fit part 1, Gao thesis page 161
        A2, A4, Qr = p
        err = y -(A1a+A2*(x-fra)+(A3a+A4*(x-fra))/(1.+4.*Qr**2*((x-fra)/fra)**2))
        return err
    
    p0 = [0., 0., 1e3]
    p_final = spopt.leastsq(residuals,p0,args=(np.array(f_data),np.array(amplitude_sqr)))
    A2a, A4a, Qra = p_final[0]
    ##A2a, A4a, Qra = [0., 0., 1e3]

    def residuals2(p,x,y):  #skewed Lorentzian fit part 2, Gao thesis page 161
        A1, A2, A3, A4, fr, Qr = p
        err = y -(A1+A2*(x-fr)+(A3+A4*(x-fr))/(1.+4.*Qr**2*((x-fr)/fr)**2))
        return err
    
    p0 = [A1a, A2a , A3a, A4a, fra, Qra]
    p_final = spopt.leastsq(residuals2,p0,args=(np.array(f_data),np.array(amplitude_sqr)))
    #A1, A2, A3, A4, fr, Qr = p_final[0]
    #print p_final[0][5]
    return p_final[0]

# def fit_delay(f_data,z_data,delay=0.,maxiter=0):
#     def residuals(p,x,y):
#         phasedelay = p
#         z_data_temp = [y[i]*np.exp(np.complex(0,2.*np.pi*phasedelay*x[i])) for i in range(len(x))]
#         xc,yc,r0 = rt.fit_circle(z_data_temp)
#         err = [((z.real-xc)**2+(z.imag-yc)**2-r0**2)**2 for z in z_data_temp]
#         return err
#     p_final = spopt.leastsq(residuals,delay,args=(np.array(f_data),np.array(z_data)),maxfev=maxiter)
#     print 'fit_delay'
#     return p_final[0][0]

# def guess_delay(f_data,z_data):
#     print 'guessing delay function called'
#     def fmod2(a,b,c):
#         '''
#         periodic boundary conditions in interval b shiftet by c
#         example fmod(x,2*pi,-pi) establishes periodic boundary
#         conditions in interval [-pi,+pi]
#         '''
#         return np.fmod(b+np.fmod(a-c,b),b)+c
#     phase = [np.angle(z_data[i]) for i in range(0,len(z_data),1)]
#     phase2 = np.unwrap(phase)
#     gradient, intercept, r_value, p_value, std_err = stats.linregress(np.array(f_data),np.array(phase2))
#     return gradient*(-1.)/(np.pi*2.)

# def get_delay(f_data,z_data,delay, peak, guessdelay, ignoreslope=True):
#     maxval = np.max(np.absolute(z_data))
#     z_data = [z/maxval for z in z_data]
#     A1, A2, A3, A4, fr, Qr = fit_skewed_lorentzian(f_data,z_data, peak)
#     print fr
#     if ignoreslope==True: A2 = 0.
#     z_data = [(np.absolute(z_data[i])-A2*(f_data[i]-fr))/A1 * np.exp(np.complex(0,np.angle(z_data[i]))) for i in range(len(f_data))]
#     if guessdelay==True:
#         print 'guessing delay'
#         delay = guess_delay(f_data,z_data)
#     else:
#         delay=0.
#     delay = fit_delay(f_data,z_data,delay,maxiter=10)
#     #z_data = rt.remove_cable_delay(f_data,z_data,delay)
#     #delay += rt.optimizedelay(f_data,z_data,Qr,fr,maxiter=4) ##doesn't work...but not essential...
#     params = [A1, A2, A3, A4, fr, Qr]
#     return delay, params

def do_calibration(f_data,z_data, ResPeak):
    maxval = np.max(np.absolute(z_data))
    #delay, params = get_delay(f_data,z_data, delay, peak, guessdelay, ignoreslope)
    
    A1, A2, A3, A4, fr, Qr = fit_skewed_lorentzian(f_data,z_data, ResPeak)
    params = [A1, A2, A3, A4, fr, Qr]
    delay=.0

    #params[0] = 1.  #don't ask me why...
    #params[1] = 0.  #don't ask me why...
    amp_norm = params[0]*maxval
    z_data = [(z_data[i]-params[1]*(f_data[i]-params[4]))/amp_norm*np.exp(np.complex(0,2.*np.pi*delay*f_data[i])) for i in range(len(f_data))]
    xc, yc, r0 = rt.fit_circle(z_data)
    zc = np.complex(xc,yc)
    #fitparams = rt.phase_fit_wslope(f_data,rt.center(z_data,zc),0.,params[5],params[4],0.)
    #theta, Qr, fr, slope = fitparams
    fitparams = rt.phase_fit(f_data,rt.center(z_data,zc),0.,np.absolute(params[5]),params[4])
    theta, Qr, fr = fitparams
    beta = rt.periodic_boundary(theta+np.pi,np.pi)
    offrespoint = np.complex(amp_norm*(xc+r0*np.cos(beta)),amp_norm*(yc+r0*np.sin(beta)))
    alpha = np.angle(offrespoint)  #align circle along real axis by alpha 
    a = np.absolute(offrespoint)
    amp_norm = a  # normalization (old amp_norm is approx a, this just makes it better because the off resonant point is defined to be =1)
    return amp_norm, alpha, fr, Qr, params[1], params[4]

def convert_RealImag_to_AmpPha(real, imag):           # added MW. July 29
    #print '--converting real, ima to amplitude and phase'
    real=np.array(real)
    imag=np.array(imag)
    #amp=20*np.log10(np.sqrt(real*real + imag*imag))
    amp=np.sqrt(real*real + imag*imag)
    pha=[]  # added MW. July 28. #why factor 20? MW July 2013.
    for i in np.arange(len(real)):
        if real[i]>=0 and imag[i] >=0:   #1. quadrant
            pha.append(np.arctan(imag[i]/real[i]))
        elif  real[i] <0 and imag[i] >=0:  #2. quadrant
            pha.append(np.arctan(imag[i]/real[i])+ mt.pi)
        elif  real[i] <0 and imag[i] <0:  #3. quadrant
            pha.append(np.arctan(imag[i]/real[i])- mt.pi)
        elif  real[i] >=0 and imag[i]<0:   #4. quadrant
            pha.append(np.arctan(imag[i]/real[i]))          
    return amp, pha

def CircleRotation(fit_data, angle):
    #print '--rotating data to match phase for final plot--'
    return [fit_data[i]/np.exp(np.complex(0,angle)) for i in range(len(fit_data))]


def do_averages(averages, single):
    realMatrix=[]
    imagMatrix=[]
    for i in range(averages):
        print '--taking average %i out of %i' %(i+1, averages)
        qt.mstart()
        real, imag = vna.get_tracedata('RealImag', single)
        qt.mend()
        
        realMatrix.append(real)
        imagMatrix.append(imag)
                
    real=scipy.mean(realMatrix, axis=0)
    imag=scipy.mean(imagMatrix, axis=0)
    return real, imag
    

def remove_cable_delay(f_data,z_data, delay):
    #print '--removing cable delay %.02e sec' %(delay)
    delay=-abs(delay) 
    return [z_data[i]/np.exp(complex(0,2.*np.pi*f_data[i]*delay)) for i in range(len(f_data))]


def data_handling(name, freq, real, imag, amp, pha, averages):
    
    '''
    creating data object and saving data
    '''
    
    
    data = qt.Data(name='S21')
    data.add_coordinate('f (Hz)')
    data.add_value('Amplitude (dBm)')
    data.add_value('Phase')
    data.add_value('Real')
    data.add_value('Imag')
    
    #ts = time.localtime()
    #path = os.path.join(UserDirectory, time.strftime('%Y%m%d', ts))
    #path = os.path.join(path, time.strftime('%H_%M_%S', ts)+'__'+'Transmission_'+str(vna.get_centerfreq()/1e9)+'GHz_'+str(vna.get_power())+'dBm_'+str(vna.get_span()/1e9)+'GHz_ave='+str(averages))
    #datapath = os.path.join(path, 'Transmission_data.dat')
    #data.create_file(filepath=datapath)
    data.create_file()
    
    #z_data=[] to be deleted once checked
    
    try:
        for i in np.arange(vna.get_nop()):
            f = freq[i]
            am = amp[i]
            ph = pha[i]
            re = real[i]
            im = imag[i]
            #z_data.append(complex(float(re),float(im))) to be deleted once checked
            data.add_data_point(f, am, ph, re, im)
            
    finally:
        data.close_file()
    return data


def plot_Amp_Pha(data):
        plotAmp=qt.Plot2D(data, name='S21 AMP', clear=True, needtempfile=True, autoupdate=True, coorddim=0, valdim=1)
        plotPha=qt.Plot2D(data, name='Pha', clear=True, needtempfile=True, autoupdate=True, coorddim=0, valdim=2)
        plotComplex = qt.Plot2D(data, name='Complex Plane', clear=True, needtempfile=True, autoupdate=True, coorddim=3, valdim=4)
              
        plotAmp.save_png()
        plotAmp.save_gp()
        plotPha.save_png()
        plotPha.save_gp()
        plotComplex.save_png()
        plotComplex.save_png()
        

def z_data2real_imag(z_data, freq):       
    real=[]
    imag=[]
    for i in range(len(freq)):
        real.append(z_data[i].real)
        imag.append(z_data[i].imag)
    return real, imag

def real_imag2z_data(real, imag, freq):   
    z_data = [complex(real[i],imag[i]) for i in range(len(freq))]
    return z_data

def Power_Scan_DataPlot_Handling(power_int, power_end):  #added MW. need to check. 
    print '-Power_Scan_DataPlot_Handling started-'

    power = qt.Data(name='Power Scan')
    power.add_coordinate('Power (dBm)')
    power.add_value('Resonant Frequency (GHz)')
    power.add_value('absQc')
    power.add_value('Qc_complex')
    power.add_value('Qr')
    power.add_value('Qi_dia_corr')
    power.add_value('Qi_no_corr')
    power.add_value('phi0')
    power.add_value('chi_square')
    power.add_value('Fit averages')

    #ts = time.localtime()
    #path = os.path.join(UserDirectory,time.strftime('%Y_%m_%d', ts))
    #path = os.path.join(path, time.strftime('%H_%M_%S', ts)+'_'+'Power_Scan '+str(power_int)+'to'+str(power_end)+'dBm')
    #powerpath=os.path.join(path,'_Power_scan.dat')
    #power.create_file(filepath=powerpath)
    power.create_file()
    
    Plot_fr_Qi = qt.plot(power, title='f_r(P)', name='f_r and Q_i Dependence on Power', xlabel='Power [dBm]',  ylabel='resonance frequency f_r [GHz]', clear=True, needtempfile=True, autoupdate=True, Left=True, coorddim=0, valdim=1)
    Plot_fr_Qi.add(power, coorddim=0, valdim=5,  title='Q_i(P)', y2label='internal quality factor', needtempfile=True, autoupdate=True, right=True)

    Plot_Qc_Qr = qt.Plot2D(power, title='Q_c(P)', name='Q_c and Q_r dependence on Power',  xlabel='Power [dBm]', ylabel='coupling quality factor', clear=True, needtempfile=True, autoupdate=True, Left=True, coorddim=0, valdim=2)
    Plot_Qc_Qr.add(power, coorddim=0, valdim=4, title='Q_r(P)', y2label='loaded quality factor', needtempfile=True, autoupdate=True, right=True)
    
    Plot_Err_averages = qt.Plot2D(power, title='chi_square', name='Err and average dependence on Power', xlabel='Power [dBm]', ylabel='chi_square', clear=True, needtempfile=True, autoupdate=True, Left=True, coorddim=0, valdim=8)
    Plot_Err_averages.add(power, coorddim=0, valdim=9, title='Fit averages', y2label='Fit averages', needtempfile=True, autoupdate=True, right=True)
    
    
    data = qt.Data(name='Power Spectrum')
    data.add_coordinate('Power (dBm)')
    data.add_coordinate('Frequency (GHz)')
    data.add_value('Amplitude (dBm)')

    return power, data, Plot_fr_Qi, Plot_Qc_Qr,Plot_Err_averages

def Start_Fitting(freq, z_data, span, ResPeak):
    fit_data, fit_results, z_data_nor=circle_fitting(freq, z_data, span, ResPeak)
    return fit_data, fit_results, z_data_nor  

def save_fitting(freq,z_data, fit_data, fit_results, z_data_nor, path = ""):
    
    amp = 20*np.log10(np.absolute(z_data))
    phase = np.angle(z_data)
    real = np.real(z_data)
    imag = np.imag(z_data)

    amp_fit = 20*np.log10(np.absolute(fit_data))
    phase_fit = np.angle(fit_data)
    real_fit = np.real(fit_data)
    imag_fit = np.imag(fit_data)

    z_data_nor_real = np.real(np.array(z_data_nor))
    z_data_nor_imag = np.imag(np.array(z_data_nor))
    
    PlotNormalizedCircle = qt.plot(z_data_nor_real,z_data_nor_imag,title='Measured normalized Circle',name='Measured normalized Circle',clear=True,needtempfile=True,autoupdate=True,xlabel='Real',ylabel='Imag')

    PlotCircle = qt.plot(real,imag,title='Measured S21',name='Complex Plane w Fit',clear=True,needtempfile=True,autoupdate=True, xlabel='Real',ylabel='Imag')
    PlotCircle.add(real_fit,imag_fit,title='Fitting S21')
    
    PlotAmp = qt.plot(freq/1e9,amp,title='Measured S21',name='Transmission w Fit',clear=True,needtempfile=True,autoupdate=True, xlabel='Frequency (GHz)',ylabel='Amplitude (dBm)')
    PlotAmp.add(freq/1e9,amp_fit,title='Fitting S21 transmission')
    
    PlotPha= qt.plot(freq/1e9,phase,title='Measured S21 ',name='Phase w Fit',clear=True,needtempfile=True,autoupdate=True, xlabel='Frequency (GHz)',ylabel='Phase')
    PlotPha.add(freq/1e9,phase_fit,title='Fitting S21 phase')
    #qt.msleep(0.001)


    PlotNormalizedCircle.save_png()
    PlotCircle.save_png()
    PlotAmp.save_png()    
    PlotPha.save_png()
    '''
    PlotNormalizedCircle.save_jpeg(filepath=path)
    PlotCircle.save_jpeg(filepath=path)
    PlotAmp.save_jpeg(filepath=path)    
    PlotPha.save_jpeg(filepath=path)
    '''
 
def circle_fitting(freq, z_data, span, ResPeak):
    print '-started circle_fitting-'
    print '--running do_calibration--'
    amp_norm, alpha, fr, Qr, A2, frcal = do_calibration(freq, z_data, ResPeak)
    delay=.0
    print "calibrated delay=%.02e, amp_norm=%.02e, alpha=%.02e, fr=%.02e, Qr=%.02e" % (delay, amp_norm, alpha, fr, Qr)
    
    #print '--running do_normalization--'
    z_data_nor = rtx.do_normalization(freq, z_data, delay, amp_norm, alpha, A2, frcal)
    
    #print '--running circlefit--'
    fit_results = rtx.circlefit(freq,z_data_nor,fr,Qr)

    print "Qi_dia_corr=%.2e, Qi_no_corr=%.02e, Qc_complex=%.02e, absQc=%.02e, Qr=%.02e" %(fit_results["Qi_dia_corr"],fit_results["Qi_no_corr"],fit_results["Qc_dia_corr"], fit_results["absQc"], fit_results["Qr"])
    print "fr=%.03e Hz, phi0=%.02e, theta0=%.02e, error (chi_square)=%.02e "%(fit_results["fr"], fit_results["phi0"], fit_results["theta0"], fit_results["chi_square"])

    fit_data = [rtx.S21(f,fit_results["fr"],fit_results["Qr"],fit_results["absQc"],fit_results["phi0"],amp_norm,alpha,delay) for f in freq ]
    
    #fit_data=CircleRotation(fit_data, np.angle(fit_data[0])+np.angle(z_data[0]))
    #fit_data=CircleRotation(fit_data, np.angle(fit_data[0])+np.angle(z_data[0]))
    
    #fit_data=CircleRotation(fit_data, fit_data[0]-np.angle(z_data[0])) ori

    return fit_data, fit_results, z_data_nor 