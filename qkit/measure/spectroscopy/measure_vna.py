# JB@KIT 04/2015
# VNA measurement class supporting function dependent measurement

import numpy as np
import logging
import matplotlib.pylab as plt
from scipy.optimize import curve_fit
#import time
from time import sleep
import sys
import qt

from qkit.storage import hdf_lib as hdf
from qkit.gui.notebook.Progress_Bar import Progress_Bar

#ttip = qt.instruments.get('ttip')
#vcoil = qt.instruments.get('vcoil')

##########################################################################################################################

class spectrum(object):

    '''
    useage:
    
    m = spectrum(vna = 'vna1')
    m2 = spectrum(vna = 'vna2', mw_src = 'mw_src1')   #where 'vna2'/'mw_src1' is the qt.instruments name
    
    m.set_x_parameters(arange(-0.05,0.05,0.01),'flux coil current (mA)',coil.set_current)
    m.set_y_parameters(arange(4e9,7e9,10e6),'excitation frequency (Hz)',mw_src1.set_frequency)
    
    m.gen_fit_function(...)   several times
    
    m.measure_XX()
    '''

    def __init__(self, vna, mw_src = None):

        self.vna = vna
        self.mw_src = mw_src

        self.landscape = None
        self.span = 200e6   #specified in Hz
        self.tdx = 0.002
        self.tdy = 0.002
        self.data_complex = False

        self.comment = None
        self.plot3D = True
        self.plotlive = True

        self.return_dat = False
        
        self.save_hdf = False
                     
    def set_x_parameters(self, x_vec, x_coordname, x_instrument, x_unit = ""):
        self.x_vec = x_vec
        self.x_coordname = x_coordname
        self.x_set_obj = x_instrument
        self.delete_fit_function()
        self.x_unit = x_unit
        
    def set_y_parameters(self, y_vec, y_coordname, y_instrument, y_unit = ""):
        self.y_vec = y_vec
        self.y_coordname = y_coordname
        self.y_set_obj = y_instrument
        self.delete_fit_function()
        self.y_unit = y_unit

    def gen_fit_function(self, curve_f, curve_p, units = '', p0 = [-1,0.1,7]):

        '''
        curve_f: 'parab', 'hyp', specifies the fit function to be employed
        curve_p: set of points that are the basis for the fit in the format [[x1,x2,x3,...],[y1,y2,y3,...]], frequencies in Hz
        units: set this to 'Hz' in order to avoid large values that cause the fit routine to diverge
        p0 (optional): start parameters for the fit, must be an 1D array of length 3 ([a,b,c])
        
        adds a trace to landscape
        '''

        if not self.landscape:
            self.landscape = []

        x_fit = curve_p[0]
        if units == 'Hz':
            y_fit = np.array(curve_p[1])*1e-9
        else:
            y_fit = np.array(curve_p[1])

        try:
            if curve_f == 'parab':
                popt, pcov = curve_fit(self.f_parab, x_fit, y_fit, p0=p0)
                if units == 'Hz':
                    self.landscape.append(1e9*self.f_parab(self.x_vec, *popt))
                else:
                    self.landscape.append(self.f_parab(self.x_vec, *popt))
            elif curve_f == 'hyp':
                popt, pcov = curve_fit(self.f_hyp, x_fit, y_fit, p0=p0)
                if units == 'Hz':
                    self.landscape.append(1e9*self.f_hyp(self.x_vec, *popt))
                else:
                    self.landscape.append(self.f_hyp(self.x_vec, *popt))
            else:
                print 'function type not known...aborting'
                raise ValueError
        except Exception as message:
            print 'fit not successful:', message
            popt = p0

    def delete_fit_function(self, n = None):
        if n:
            self.landscape = np.delete(self.landscape, n, axis=0)
        else:
            self.landscape = None


    def plot_fit_function(self, num_points = 100):
        '''
        try:
            x_coords = np.linspace(self.x_vec[0], self.x_vec[-1], num_points)
        except Exception as message:
            print 'no x axis information specified', message
            return
        '''
        if self.landscape:
            for trace in self.landscape:
                try:
                    #plt.clear()
                    plt.plot(self.x_vec, trace)
                    plt.fill_between(self.x_vec, trace+float(self.span)/2, trace-float(self.span)/2, alpha=0.5)
                except Exception:
                    print 'invalid trace...skip'
            plt.axhspan(self.y_vec[0], self.y_vec[-1], facecolor='0.5', alpha=0.5)
            plt.show()
        else:
            print 'No trace generated.'

    def measure_1D(self):
        if not self.x_set_obj:
            logging.error('axes parameters not properly set...aborting')
            return
        self._scan_1D = True
        self._scan_1D2 = False
        self._scan_2D = False
        self._scan_name = 'vna_sweep1D_'+ self.x_coordname
        self._p = Progress_Bar(len(self.x_vec))
        
        self._prepare_measurement_vna()
        self._prepare_measurement_data_file()
        if self.save_hdf:        
            self._prepare_measurement_hdf_file() 
        
        self._measure()
        
        self._end_measurement()


    def measure_1D2(self):
        if not self.x_set_obj:
            logging.error('axes parameters not properly set...aborting')
            return
        self._scan_1D = False
        self._scan_1D2 = True
        self._scan_2D = False
        self._scan_name = 'vna_sweep1D2_'+ self.x_coordname
        self._p = Progress_Bar(len(self.x_vec))
        
        self._prepare_measurement_vna()
        self._prepare_measurement_data_file()
        if self.save_hdf:        
            self._prepare_measurement_hdf_file()
        
        self._measure()
        
        self._end_measurement()


    def measure_2D(self):
        '''
        measure method to perform the measurement according to landscape, if set
        self.span is the range (in units of the vertical plot axis) data is taken around the specified funtion(s) 
        '''
        if not self.x_set_obj or not self.y_set_obj:
            logging.error('axes parameters not properly set...aborting')
            return
        self._scan_1D = False
        self._scan_1D2 = False
        self._scan_2D = True
        self._scan_name = 'vna_sweep2D_'+ self.x_coordname + '_' + self.y_coordname
        self._p = Progress_Bar(len(self.x_vec)*len(self.y_vec))
        
        self._prepare_measurement_vna()
        self._prepare_measurement_data_file()
        if self.save_hdf:        
            self._prepare_measurement_hdf_file()
            #qkit.gui.qviewkit.plot_hdf(self._data_hdf, datasets=['Amplitude', 'Phase'])
        
        if self.landscape:
            self.center_freqs = np.array(self.landscape).T
        else:
            self.center_freqs = []   #load default sequence
            for i in range(len(self.x_vec)):
                self.center_freqs.append([0])
                
        self._measure()

        self._end_measurement()
        
    def _prepare_measurement_vna(self):
        self.vna.get_all()
        #ttip.get_temperature()
        self._nop = self.vna.get_nop()
        #self._nop_avg = self.vna.get_averages()
        #self._bandwidth = self.vna.get_bandwidth()
        #self._t_point = nop / bandwidth * nop_avg
        self._freqpoints = self.vna.get_freqpoints()

    def _prepare_measurement_data_file(self):
        self._data = qt.Data(name=self._scan_name)
        self._data.add_coordinate(self.x_coordname)
        if self._scan_1D2:
            self._data.add_coordinate('Frequency')
            self._data.add_value('Amplitude')
            self._data.add_value('Phase')
            if self.data_complex:
                self._data.add_value('Real')
                self._data.add_value('Img')        
        else:
            if self._scan_2D:
                self._data.add_coordinate(self.y_coordname)
            for i in range(1,self._nop+1):
                self._data.add_value(('Point %i Amp' %i))
            for i in range(1,self._nop+1):
                    self._data.add_value(('Point %i Pha' %i))
        if self.comment:
            self._data.add_comment(self.comment) 
        self._data.create_file()
    
    def _prepare_measurement_hdf_file(self):
        filename = str(self._data.get_filepath()).replace('.dat','.h5')
        self._data_hdf = hdf.Data(name=self._scan_name, path=filename)
        self._hdf_freq = self._data_hdf.add_coordinate('Frequency', unit = 'Hz', comment = None)
        self._hdf_freq.add(self._freqpoints)
        self._hdf_x = self._data_hdf.add_coordinate(self.x_coordname, unit = self.x_unit, comment = None)
        self._hdf_x.add(self.x_vec)        
        if self._scan_2D:
            self._hdf_y = self._data_hdf.add_coordinate(self.y_coordname, unit = self.y_unit, comment = None)
            self._hdf_y.add(self.y_vec)         
            self._hdf_amp0 = self._data_hdf.add_value_matrix('Amplitude', x = self._hdf_y, y = self._hdf_y, unit = 'V', comment = None)
            self._hdf_pha0 = self._data_hdf.add_value_matrix('Phase', x = self._hdf_y, y = self._hdf_y, unit='rad', comment = None)
        else:
            self._hdf_amp = self._data_hdf.add_value_matrix('Amplitude', x = self._hdf_x, y = self._hdf_freq, unit = 'V', comment = None)
            self._hdf_pha = self._data_hdf.add_value_matrix('Phase', x = self._hdf_x, y = self._hdf_freq, unit='rad', comment = None)
        #if self.comment:
        #    self._data_hdf.add_comment(self.comment) 

    def _measure(self):
        qt.mstart()
        if self._scan_1D or self.plotlive: #and not self.save_hdf:
            plot_amp, plot_pha = self._plot_data_file()
        """
        if not self._scan_2D:
            self.x_set_obj(self.x_vec[0])
        """
        try:
            for x in self.x_vec:
                self.x_set_obj(x)
                sleep(self.tdx)

                dat=[]
                
                if self._scan_2D:
                    if self.save_hdf:
                        name_amp = 'Amplitude_'+str(x)+'_'+str(self.x_unit)
                        name_pha = 'Phase_'+str(x)+'_'+str(self.x_unit)

                        hdf_amp = self._data_hdf.add_value_matrix(name_amp, x = self._hdf_y, y = self._hdf_freq, unit = 'V', comment = None)
                        hdf_pha = self._data_hdf.add_value_matrix(name_pha, x = self._hdf_y, y = self._hdf_freq, unit='rad', comment = None)
                        save_amp0 = []
                        save_pha0 = []

                    for y in self.y_vec:
                        if (np.min(np.abs(self.center_freqs[int(x)]-y*np.ones(len(self.center_freqs[int(x)])))) > self.span/2.) and self.landscape:   
                        #if point is not of interest (not close to one of the functions)
                            data_amp = np.zeros(int(self._nop))
                            data_pha = np.zeros(int(self._nop))   #fill with zeros
                        else:
                            self.y_set_obj(y)
                            sleep(self.tdy)

                            sleep(self.vna.get_sweeptime_averages())
                            data_amp, data_pha = self.vna.get_tracedata()

                        dat = np.append(x, y)
                        dat = np.append(dat,data_amp)
                        dat = np.append(dat,data_pha)
                        self._data.add_data_point(*dat)
                        if self.save_hdf:
                            save_amp0 = np.append(save_amp0, data_amp[len(data_amp)/2])
                            save_pha0 = np.append(save_pha0, data_pha[len(data_pha)/2])
                            if y == self.y_vec[len(self.y_vec)-1]:
                                self._hdf_amp0.append(save_amp0)
                                self._hdf_pha0.append(save_pha0)
                            hdf_amp.append(data_amp)
                            hdf_pha.append(data_pha)
                        qt.msleep(0.1)
                        if self.plotlive:
                            plot_amp.update()
                            plot_pha.update()
                        self._p.iterate()

                if self._scan_1D:
                    self.vna.avg_clear()
                    sleep(self.vna.get_sweeptime_averages())
                    data_amp, data_pha = self.vna.get_tracedata()

                    dat = np.append(x, data_amp)
                    dat = np.append(dat, data_pha)
                    self._data.add_data_point(*dat)
                    if self.save_hdf:
                        self._hdf_amp.append(data_amp)
                        self._hdf_pha.append(data_pha)
                    self._p.iterate()

                if self._scan_1D2:
                    self.vna.avg_clear()
                    sleep(self.vna.get_sweeptime_averages())
                    data_amp, data_pha = self.vna.get_tracedata()
                    if self.data_complex:
                        data_real, data_imag = self.vna.get_tracedata('RealImag')

                    dat = np.append([x*np.ones(self._nop)],[self._freqpoints], axis = 0)
                    dat = np.append(dat,[data_amp],axis = 0)
                    dat = np.append(dat,[data_pha],axis = 0)
                    if self.data_complex == True:
                        dat = np.append(dat,[data_real],axis = 0)
                        dat = np.append(dat,[data_imag],axis = 0)

                    self._data.add_data_point(*dat)
                    self._data.new_block()
                    if self.save_hdf:
                        self._hdf_amp.append(data_amp)
                        self._hdf_pha.append(data_pha)
                    self._p.iterate()
                        
                qt.msleep(0.1)
                if self.plotlive:
                    plot_amp.update()
                    plot_pha.update()
                
                if self._scan_2D: 
                    self._data.new_block()

        finally:
            if self._scan_1D and not self.plotlive: #and not self.save_hdf:
                plot_amp, plot_pha = self._plot_data_file()
                plot_amp.update()
                plot_pha.update()

            plot_amp.save_png()
            plot_amp.save_gp()
            plot_pha.save_png()
            plot_pha.save_gp()
            
            qt.mend()
            
    def _end_measurement(self):
        print self._data.get_filepath()
        self._data.close_file()
        if self.save_hdf:
            print self._data_hdf.get_filepath()
            self._data_hdf.close_file()

    def _plot_data_file(self):
        if self._scan_1D:
            plot_amp = qt.Plot2D(self._data, name='Amplitude', coorddim=0, valdim=int(self._nop/2)+1)
            plot_pha = qt.Plot2D(self._data, name='Phase', coorddim=0, valdim=self._nop+int(self._nop/2)+1)
        if self._scan_1D2:
            plot_amp = qt.Plot3D(self._data, name='Amplitude 1D2', coorddims=(0,1), valdim=2, style=qt.Plot3D.STYLE_IMAGE)
            plot_amp.set_palette('bluewhitered')
            plot_pha = qt.Plot3D(self._data, name='Phase 1D2', coorddims=(0,1), valdim=3, style=qt.Plot3D.STYLE_IMAGE)
            plot_pha.set_palette('bluewhitered')
        if self._scan_2D:
            if self.plot3D:
                plot_amp = qt.Plot3D(self._data, name='Amplitude', coorddims=(0,1), valdim=int(self._nop/2)+2, style=qt.Plot3D.STYLE_IMAGE)
                plot_amp.set_palette('bluewhitered')
                plot_pha = qt.Plot3D(self._data, name='Phase', coorddims=(0,1), valdim=int(self._nop/2)+2+self._nop, style=qt.Plot3D.STYLE_IMAGE)
                plot_pha.set_palette('bluewhitered')
            else:
                plot_amp = qt.Plot2D(self._data, name='Amplitude', coorddim=1, valdim=int(self._nop/2)+2)
                plot_pha = qt.Plot2D(self._data, name='Phase', coorddim=1, valdim=int(self._nop/2)+2+self._nop)

        return plot_amp, plot_pha

    def record_trace(self):
        '''
        measure method to record a single (averaged) VNA trace, S11 or S21 according to the setting on the VNA
        
        returns frequency points, data_amp and data_pha when self.return_dat is set
        '''
        qt.mstart()
        self.vna.get_all()
        self.vna.hold(0)   #switch VNA to continuous mode

        print 'recording trace...'
        sys.stdout.flush()

        #creating data object and saving data
        data = qt.Data(name='VNA_tracedata')
        data.add_coordinate('f (Hz)')
        data.add_value('Amplitude (lin.)')
        data.add_value('Phase')
        data.add_value('Real')
        data.add_value('Imag')
        data.create_file()
        
        freq = self.vna.get_freqpoints()
        self.vna.avg_clear()
        sleep(self.vna.get_sweeptime_averages())
        data_amp, data_pha = self.vna.get_tracedata()
        data_real, data_imag = self.vna.get_tracedata('RealImag')

        try:
            for i in np.arange(self.vna.get_nop()):
                f = freq[i]
                am = data_amp[i]
                ph = data_pha[i]
                re = data_real[i]
                im = data_imag[i]
                data.add_data_point(f, am, ph, re, im)
        finally:
            plot_amp = qt.Plot2D(data, name='amplitude', clear=True, needtempfile=True, autoupdate=True, coorddim=0, valdim=1)
            plot_pha = qt.Plot2D(data, name='phase', clear=True, needtempfile=True, autoupdate=True, coorddim=0, valdim=2)
            plot_complex = qt.Plot2D(data, name='Complex Plane', clear=True, needtempfile=True, autoupdate=True, coorddim=3, valdim=4)

            plot_amp.save_png()
            plot_amp.save_gp()
            plot_pha.save_png()
            plot_pha.save_gp()
            plot_complex.save_png()
            plot_complex.save_png()

            data.close_file()
            qt.mend()
        print 'Done.'
        if self.return_dat: return freq, data_amp, data_pha
            
    def set_span(self, span):
        self.span = span

    def get_span(self):
        return self.span
        
    def set_tdx(self, tdx):
        self.tdx = tdx

    def set_tdy(self, tdy):
        self.tdy = tdy

    def get_tdx(self):
        return self.tdx

    def get_tdy(self):
        return self.tdy

    def f_parab(self,x,a,b,c):
        return a*(x-b)**2+c

    def f_hyp(self,x,a,b,c):
        return a*np.sqrt((x/b)**2+c)