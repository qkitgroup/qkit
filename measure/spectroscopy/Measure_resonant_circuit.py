#Measure_resonant_circuits.py 
#higher level resonant circuit measurement functions
#Started by Martin Weides <martin.weidest@kit.edu>
#last update: 17/07/2014 by Jochen Braumueller: jochen.braumueller@kit.edu

#
#   create VNA before importing this script
#

import ctypes
import time
import logging
import sys
import scipy
import qt
import os
import resonator_tools as rt
import resonator_tools_xtras as rtx
import resonant_circuit_tools as rct
import numpy as np


vna = qt.instruments.get('vna')


def set_vna(centerfreq, span, power, points, IF, averages, delay):
    
    if delay != None:
        vna.set_edel(delay)
    print 'electrical delay set to %.02e sec' %(vna.get_edel())

    if centerfreq != None:
        vna.set_centerfreq(centerfreq)
    print 'Center_freq =: %s Hz' % (vna.get_centerfreq())

    if span != None:
        vna.set_span(span)
    print 'Span =: %s Hz' % (vna.get_span())

    if power != None:
        vna.set_power(power)
    print 'Power =: %s dBm' % (vna.get_power())

    if points != None:
        vna.set_nop(points)
    print 'Points =: %s' % (vna.get_nop())

    if IF != None:
        vna.set_bandwidth(IF)
    print 'IF =: %s' % (vna.get_bandwidth())
    
    if averages != None:
        vna.set_averages(averages)
    print 'averages =: %s' % (vna.get_averages())
    

def transmission(centerfreq = None, span = None, power = None, points = None, IF = None, averages = None, delay = None):

    set_vna(centerfreq, span, power, points, IF, averages, delay)
    freq = vna.get_freqpoints()
    averages = vna.get_averages()
    qt.mstart()
    
    real, imag=rct.do_averages(averages, single=True)

    z_data=rct.real_imag2z_data(real, imag, freq)

    if delay != None:
        z_data=rct.remove_cable_delay(freq, z_data, delay) 
        real, imag=rct.z_data2real_imag(z_data, freq)

    amp, pha=rct.convert_RealImag_to_AmpPha(real, imag)

  
    try:
        data = rct.data_handling('Transmission S21', freq, real, imag, amp, pha, averages)
    finally:
        qt.mend()
        rct.plot_Amp_Pha(data)

  
def data_circle_fitting(centerfreq = None, span = None, power = None, points = None, IF = None, averages = None, delay = None, ResPeak=True, single=True, guessdelay=False):

    set_vna(centerfreq, span, power, points, IF, averages, delay)
    averages = vna.get_averages()
    qt.mstart()
    
    real, imag=rct.do_averages(averages, single)
    freq = vna.get_freqpoints()
    z_data=rct.real_imag2z_data(real, imag, freq)
    delay = vna.get_edel()
 
    if delay != None:
        z_data=rct.remove_cable_delay(freq, z_data, delay) 
        real, imag=rct.z_data2real_imag(z_data, freq)

    #amp, pha=rct.convert_RealImag_to_AmpPha(real, imag)
    #data = rct.data_handling('Transmission S21', freq, real, imag, amp, pha, averages)        
            
    qt.mend()
    
    fit_data, fit_results, z_data_nor=rct.Start_Fitting(freq, z_data, span, ResPeak)
    rct.save_fitting(freq,z_data, fit_data, fit_results, z_data_nor)


def power_scan(power_int, power_end, power_step, centerfreq = None, span = None, power = None, points = None, IF = None, averages = None, delay = None, err_level=1E-2, FitAveragesMax=5, Fit=False, ResPeak=False):
   
    set_vna(centerfreq, span, power_int, points, IF, averages, delay)
    averages = vna.get_averages()
    freq = vna.get_freqpoints()
    
    if Fit==True:     
        power, data, Plot_fr_Qi, Plot_Qc_Qr, Plot_Err_averages = rct.Power_Scan_DataPlot_Handling(power_int, power_end)   #???

    a=1
    for p in np.arange(power_int, np.sign(power_end)*(np.abs(power_end)+0.01), power_step):
        FitAverages=1
        print "------------------------------"
        print 'Number of power step: %i out of %i' %(a, len(np.arange(power_int, np.sign(power_end)*(np.abs(power_end)+0.01), power_step)) )

        vna.set_power(p)
        print 'VNA power settings %.1f dBm' %(vna.get_power())

        real, imag=rct.do_averages(averages, single=True)
        z_data=rct.real_imag2z_data(real, imag, freq)
        z_data=rct.remove_cable_delay(freq, z_data, delay) 
        
        real, imag=rct.z_data2real_imag(z_data, freq)
        amp, pha=rct.convert_RealImag_to_AmpPha(real, imag)
        
        data = rct.data_handling('Transmission S21', freq, real, imag, amp, pha, averages)
        #rct.plot_Amp_Pha(data, path)

        
        if Fit == False:
            print '-No fitting-'
            rct.plot_Amp_Pha(data)
            
        else:   #Fit == True
            ExitFit = False 
            while ExitFit == False:
                fit_data, fit_results, z_data_nor=rct.Start_Fitting(freq, z_data, span, ResPeak)
                if fit_results["chi_square"]<=err_level:
                    print '-Fitting within error bound-'
                    ExitFit=True
                elif FitAverages==FitAveragesMax:
                    print '-Fitting max. averages reached-'
                    ExitFit=True
                else:
                    print '-Keep averaging for fit-'
                    
                    FitAverages=FitAverages+1
                    print '---Number of circle fit steps: %i out of %i' %(FitAverages, FitAveragesMax )
    
                    
                    real_temp, imag_temp=rct.do_averages(averages, single=True)
                    z_data_temp=rct.real_imag2z_data(real_temp, imag_temp, freq)
                    z_data_temp=rct.remove_cable_delay(freq, z_data_temp, delay) 
                    
                    z_data = [z_data[i]*(a-1)/a+z_data_temp[i]/a for i in range(len(freq))]
                    
                
                real, imag=rct.z_data2real_imag(z_data, freq)
                amp, pha=rct.convert_RealImag_to_AmpPha(real, imag) #added MW July 2013
                
                
            power.add_data_point(p,fit_results["fr"]/1e9,fit_results["absQc"],fit_results["Qc_dia_corr"],fit_results["Qr"],fit_results["Qi_dia_corr"],fit_results["Qi_no_corr"],fit_results["phi0"],fit_results["chi_square"], FitAverages)
            rct.save_fitting(freq,z_data, fit_data, fit_results, z_data_nor)
            
        a=a+1
    
        #qt.msleep(0.1)
        #data, path=rct.data_handling('Transmission S21', freq, real, imag, amp, pha, averages)
        #rct.plot_Amp_Pha(data, path)
    
            
    if Fit == True:
        Plot_fr_Qi.save_png()
        Plot_Qc_Qr.save_png()
        Plot_Err_averages.save_png()
        '''
        Plot_fr_Qi.save_jpeg(filepath=powerpath)
        Plot_Qc_Qr.save_jpeg(filepath=powerpath)
        Plot_Err_averages.save_jpeg(filepath=powerpath)
        '''
        power.close_file()
    qt.mend()
    

