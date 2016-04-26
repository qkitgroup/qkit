# JB/MP@KIT 04/2015, 08/2015, 01/2016
# VNA measurement class supporting function dependent measurement

import numpy as np
import logging
import matplotlib.pylab as plt
from scipy.optimize import curve_fit
from time import sleep,time
import sys
import qt

from qkit.storage import hdf_lib as hdf
from qkit.analysis.resonator import Resonator as resonator
from qkit.gui.plot import plot as qviewkit
from qkit.gui.notebook.Progress_Bar import Progress_Bar
import qkit.measure.write_additional_files as waf

##################################################################

class spectrum(object):
    '''
    usage:

    m = spectrum(vna = vna1)
    m2 = spectrum(vna = vna2, mw_src = mw_src1)      #where 'vna2'/'mw_src1' is the qt.instruments name

    m.set_x_parameters(arange(-0.05,0.05,0.01),'flux coil current',coil.set_current, unit = 'mA')
    m.set_y_parameters(arange(4e9,7e9,10e6),'excitation frequency',mw_src1.set_frequency, unit = 'Hz')

    m.gen_fit_function(...)      several times

    m.measure_XX()
    '''

    def __init__(self, vna, exp_name = ''):

        self.vna = vna
        self.exp_name = exp_name

        self.landscape = None
        self.span = 200e6    #[Hz]
        self.tdx = 0.002   #[s]
        self.tdy = 0.002   #[s]

        self.comment = ''
        self.dirname = None

        self.x_set_obj = None
        self.y_set_obj = None

        self.progress_bar = True
        self._fit_resonator = False
        self._plot_comment=""

        self.set_log_function()

    def set_log_function(self, func=None, name = None, unit = None):
        '''
        A function (object) can be passed to the measurement loop which is excecuted after every x iteration in the measurement.
        The return value of the function of type float or similar is stored in a value vector in the h5 file.

        Call without any arguments to delete all log functions. The timestamp is automatically saved.

        func: function object in list form
        name: name of logging parameter appearing in h5 file, default: 'log_param'
        unit: unit of logging parameter, default: ''
        '''

        if name == None:
            try:
                name = ['log_param']*len(func)
            except Exception:
                name = None
        if unit == None:
            try:
                unit = ['']*len(func)
            except Exception:
                unit = None

        self.log_function = []
        self.log_name = []
        self.log_unit = []
        self.log_dtype = []

        if func != None:
            for i,f in enumerate(func):
                self.log_function.append(f)
                self.log_name.append(name[i])
                self.log_unit.append(unit[i])
                self.log_dtype.append('f')

    def set_x_parameters(self, x_vec, x_coordname, x_set_obj, x_unit = ""):
        '''
        Sets parameters for sweep. In a 3D measurement, the x-parameters will be the "outer" sweep.
        For every x value all y values are swept
        Input:
        x_vec (array): conains the sweeping values
        x_coordname (string)
        x_instrument (obj): callable object to execute with x_vec-values (i.e. vna.set_power())
        x_unit (string): optional
        '''
        self.x_vec = x_vec
        self.x_coordname = x_coordname
        self.x_set_obj = x_set_obj
        self.delete_fit_function()
        self.x_unit = x_unit

    def set_y_parameters(self, y_vec, y_coordname, y_set_obj, y_unit = ""):
        '''
        Sets parameters for sweep. In a 3D measurement, the x-parameters will be the "outer" sweep.
        For every x value all y values are swept
        Input:
        y_vec (array): contains the sweeping values
        y_coordname (string)
        y_instrument (obj): callable object to execute with x_vec-values (i.e. vna.set_power())
        y_unit (string): optional
        '''
        self.y_vec = y_vec
        self.y_coordname = y_coordname
        self.y_set_obj = y_set_obj
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

    def _prepare_measurement_vna(self):
        '''
        all the relevant settings from the vna are updated and called
        '''

        self.vna.get_all()
        #ttip.get_temperature()
        self._nop = self.vna.get_nop()
        self._sweeptime_averages = self.vna.get_sweeptime_averages()
        self._freqpoints = self.vna.get_freqpoints()

        try:
            self.vna.hold(0)   #switch VNA to continuous mode
        except AttributeError:
            try:
                self.vna.set_hold(0)
            except Exception as message:
                print 'VNA might be in hold mode', message

    def _prepare_measurement_file(self,trace=False):
        '''
        creates the output .h5-file with distinct dataset structures for each measurement type.
        at this point all measurement parameters are known and put in the output file
        '''

        self._data_file = hdf.Data(name=self._file_name)

        # write logfile and instrument settings
        self._write_settings_dataset()
        self._log = waf.open_log_file(self._data_file.get_filepath())

        self._data_freq = self._data_file.add_coordinate('frequency', unit = 'Hz', dtype='float64')
        self._data_freq.add(self._freqpoints)

        if self._scan_1D:
            self._data_real = self._data_file.add_value_vector('real', x = self._data_freq, unit = '', save_timestamp = True)
            self._data_imag = self._data_file.add_value_vector('imag', x = self._data_freq, unit = '', save_timestamp = True)
            self._data_amp = self._data_file.add_value_vector('amplitude', x = self._data_freq, unit = '', save_timestamp = True)
            self._data_pha = self._data_file.add_value_vector('phase', x = self._data_freq, unit = 'rad', save_timestamp = True)

        if self._scan_2D:
            self._data_x = self._data_file.add_coordinate(self.x_coordname, unit = self.x_unit)
            self._data_x.add(self.x_vec)
            self._data_amp = self._data_file.add_value_matrix('amplitude', x = self._data_x, y = self._data_freq, unit = '', save_timestamp = True)
            self._data_pha = self._data_file.add_value_matrix('phase', x = self._data_x, y = self._data_freq, unit='rad', save_timestamp = True)

            if self.log_function != None:   #use logging
                self._log_value = []
                for i in range(len(self.log_function)):
                    self._log_value.append(self._data_file.add_value_vector(self.log_name[i], x = self._data_x, unit = self.log_unit[i],dtype=self.log_dtype[i]))

            if self._nop < 10:
                """creates view: plot middle point vs x-parameter, for qubit measurements"""
                self._data_amp_mid = self._data_file.add_value_vector('amplitude_midpoint', unit = '', x = self._data_x, save_timestamp = True)
                self._data_pha_mid = self._data_file.add_value_vector('phase_midpoint', unit = 'rad', x = self._data_x, save_timestamp = True)
                #self._view = self._data_file.add_view("amplitude vs. " + self.x_coordname, x = self._data_x, y = self._data_amp[self._nop/2])

        if self._scan_3D:
            self._data_x = self._data_file.add_coordinate(self.x_coordname, unit = self.x_unit)
            self._data_x.add(self.x_vec)
            self._data_y = self._data_file.add_coordinate(self.y_coordname, unit = self.y_unit)
            self._data_y.add(self.y_vec)
            
            if self._nop == 0:   # dos not work yet     # the pnax can measure only one value, saving it in a 2D matrix instead of a 3D box, no timestamp
                self._data_amp = self._data_file.add_value_matrix('amplitude', x = self._data_x, y = self._data_y,  unit = '1',   save_timestamp = False)
                self._data_pha = self._data_file.add_value_matrix('phase',     x = self._data_x, y = self._data_y,  unit = 'rad', save_timestamp = False)
            else:
                self._data_amp = self._data_file.add_value_box('amplitude', x = self._data_x, y = self._data_y, z = self._data_freq, unit = '1', save_timestamp = False)
                self._data_pha = self._data_file.add_value_box('phase', x = self._data_x, y = self._data_y, z = self._data_freq, unit = 'rad', save_timestamp = False)

        if self.comment:
            self._data_file.add_comment(self.comment)

    def _write_settings_dataset(self):
        self._settings = self._data_file.add_textlist('settings')
        settings = waf.get_instrument_settings(self._data_file.get_filepath())
        self._settings.append(settings)

    def measure_1D(self):
        '''
        measure method to record a single (averaged) VNA trace, S11 or S21 according to the setting on the VNA
        '''
        self._scan_1D = True
        self._scan_2D = False
        self._scan_3D = False

        if not self.dirname:
            self.dirname = 'VNA_tracedata'
        self._file_name = self.dirname.replace(' ', '').replace(',','_')
        if self.exp_name:
            self._file_name += '_' + self.exp_name
        self._prepare_measurement_vna()
        self._prepare_measurement_file()

        """opens qviewkit to plot measurement, amp and pha are opened by default"""
        qviewkit.plot(self._data_file.get_filepath(), datasets=['amplitude', 'phase'])
        if self._fit_resonator:
            self._resonator = resonator(self._data_file.get_filepath())

        print 'recording trace...'
        sys.stdout.flush()

        qt.mstart()
        self.vna.avg_clear()
        if self.vna.get_averages() == 1 or self.vna.get_Average() == False:   #no averaging
            self._p = Progress_Bar(1,self.dirname)
            qt.msleep(self.vna.get_sweeptime())      #wait single sweep
            self._p.iterate()
        else:   #with averaging
            self._p = Progress_Bar(self.vna.get_averages(),self.dirname)
            for a in range(self.vna.get_averages()):
                qt.msleep(self.vna.get_sweeptime())      #wait single sweep time
                self._p.iterate()

        data_amp, data_pha = self.vna.get_tracedata()
        data_real, data_imag = self.vna.get_tracedata('RealImag')

        self._data_amp.append(data_amp)
        self._data_pha.append(data_pha)
        self._data_real.append(data_real)
        self._data_imag.append(data_imag)
        if self._fit_resonator:
            self._do_fit_resonator()

        qt.mend()
        self._end_measurement()

    def measure_2D(self):
        '''
        measure method to record a (averaged) VNA trace, S11 or S21 according to the setting on the VNA
        for all parameters x_vec in x_obj
        '''

        if not self.x_set_obj:
            logging.error('axes parameters not properly set...aborting')
            return
        self._scan_1D = False
        self._scan_2D = True
        self._scan_3D = False

        if not self.dirname:
            self.dirname = self.x_coordname
        self._file_name = '2D_' + self.dirname.replace(' ', '').replace(',','_')
        if self.exp_name:
            self._file_name += '_' + self.exp_name

        self._p = Progress_Bar(len(self.x_vec),'2D VNA sweep '+self.dirname)

        self._prepare_measurement_vna()
        self._prepare_measurement_file()

        """opens qviewkit to plot measurement, amp and pha are opened by default"""
        if self._nop < 10:
            qviewkit.plot(self._data_file.get_filepath(), datasets=['amplitude_midpoint', 'phase_midpoint'])
        else:
            qviewkit.plot(self._data_file.get_filepath(), datasets=['amplitude', 'phase'])
        if self._fit_resonator:
            self._resonator = resonator(self._data_file.get_filepath())
        self._measure()
        self._end_measurement()


    def measure_3D(self):
        '''
        measure full window of vna while sweeping x_set_obj and y_set_obj with parameters x_vec/y_vec. sweep over y_set_obj is the inner loop, for every value x_vec[i] all values y_vec are measured.

        optional: measure method to perform the measurement according to landscape, if set
        self.span is the range (in units of the vertical plot axis) data is taken around the specified funtion(s)
        note: make sure to have properly set x,y vectors before generating traces
        '''
        if not self.x_set_obj or not self.y_set_obj:
            logging.error('axes parameters not properly set...aborting')
            return
        self._scan_1D = False
        self._scan_2D = False
        self._scan_3D = True

        if not self.dirname:
            self.dirname = self.x_coordname + ', ' + self.y_coordname
        self._file_name = '3D_' + self.dirname.replace(' ', '').replace(',','_')
        if self.exp_name:
            self._file_name += '_' + self.exp_name

        self._p = Progress_Bar(len(self.x_vec)*len(self.y_vec),'3D VNA sweep '+self.dirname)

        self._prepare_measurement_vna()
        self._prepare_measurement_file()
        """opens qviewkit to plot measurement, amp and pha are opened by default"""
        """only middle point in freq array is plotted vs x and y"""
        qviewkit.plot(self._data_file.get_filepath(), datasets=['amplitude', 'phase'])
        if self._fit_resonator:
            self._resonator = resonator(self._data_file.get_filepath())

        if self.landscape:
            self.center_freqs = np.array(self.landscape).T
        else:
            self.center_freqs = []     #load default sequence
            for i in range(len(self.x_vec)):
                self.center_freqs.append([0])

        self._measure()
        self._end_measurement()

    def _measure(self):
        '''
        measures and plots the data depending on the measurement type.
        the measurement loops feature the setting of the objects and saving the data in the .h5 file.
        '''
        qt.mstart()
        try:
            """
            loop: x_obj with parameters from x_vec
            """
            for i, x in enumerate(self.x_vec):
                self.x_set_obj(x)
                sleep(self.tdx)

                if self._scan_3D:
                    for y in self.y_vec:
                        """
                        loop: y_obj with parameters from y_vec (only 3D measurement)
                        """
                        if (np.min(np.abs(self.center_freqs[i]-y*np.ones(len(self.center_freqs[i])))) > self.span/2.) and self.landscape:    #if point is not of interest (not close to one of the functions)
                            data_amp = np.zeros(int(self._nop))
                            data_pha = np.zeros(int(self._nop))      #fill with zeros
                        else:
                            self.y_set_obj(y)
                            sleep(self.tdy)
                            self.vna.avg_clear()
                            sleep(self._sweeptime_averages)
                            """ measurement """
                            data_amp, data_pha = self.vna.get_tracedata()

                        if self._nop == 0: # this does not work yet.
                           print data_amp[0], data_amp, self._nop
                           self._data_amp.append(data_amp[0])
                           self._data_pha.append(data_pha[0])
                        else:
                           self._data_amp.append(data_amp)
                           self._data_pha.append(data_pha)
                        if self._fit_resonator:
                            self._do_fit_resonator()
                        if self.progress_bar:
                            self._p.iterate()
                            qt.msleep()
                    """
                    filling of value-box is done here.
                    after every y-loop the data is stored the next 2d structure
                    """
                    self._data_amp.next_matrix()
                    self._data_pha.next_matrix()

                if self._scan_2D:
                    self.vna.avg_clear()
                    sleep(self._sweeptime_averages)
                    """ measurement """
                    data_amp, data_pha = self.vna.get_tracedata()
                    self._data_amp.append(data_amp)
                    self._data_pha.append(data_pha)
                    if self._nop < 10:
                        #print data_amp[self._nop/2]
                        self._data_amp_mid.append(float(data_amp[self._nop/2]))
                        self._data_pha_mid.append(float(data_pha[self._nop/2]))
                    if self.log_function != None:
                        for i,f in enumerate(self.log_function):
                            self._log_value[i].append(float(f()))
                    if self._fit_resonator:
                        self._do_fit_resonator()
                    if self.progress_bar:
                        self._p.iterate()
                        qt.msleep()
        finally:
            qt.mend()

    def _end_measurement(self):
        '''
        the data file is closed and filepath is printed
        '''
        print self._data_file.get_filepath()
        qviewkit.save_plots(self._data_file.get_filepath(),comment=self._plot_comment)
        self._data_file.close_file()
        waf.close_log_file(self._log)
        self.dirname = None

    def set_resonator_fit(self,fit_resonator=True,fit_function='',f_min=None,f_max=None):
        '''
        sets fit parameter for resonator

        fit_resonator (bool): True or False, default: True (optional)
        fit_function (string): function which will be fitted to the data (optional)
        f_min (float): lower frequency boundary for the fitting function, default: None (optional)
        f_max (float): upper frequency boundary for the fitting function, default: None (optional)
        fit types: 'lorentzian','skewed_lorentzian','circle_fit_reflection', 'circle_fit_notch','fano'
        '''
        if not fit_resonator:
            self._fit_resonator = False
            return
        self._functions = {'lorentzian':0,'skewed_lorentzian':1,'circle_fit_reflection':2,'circle_fit_notch':3,'fano':5,'all_fits':5}
        try:
            self._fit_function = self._functions[fit_function]
        except KeyError:
            logging.error('Fit function not properly set. Must be either \'lorentzian\', \'skewed_lorentzian\', \'circle_fit_reflection\', \'circle_fit_notch\', \'fano\', or \'all_fits\'.')
        else:
            self._fit_resonator = True
            self._f_min = f_min
            self._f_max = f_max

    def _do_fit_resonator(self):
        '''
        calls fit function in resonator class
        fit function is specified in self.set_fit, with boundaries f_mim and f_max
        only the last 'slice' of data is fitted, since we fit live while measuring.
        '''

        if self._fit_function == 0: #lorentzian
            self._resonator.fit_lorentzian(f_min=self._f_min, f_max = self._f_max)
        if self._fit_function == 1: #skewed_lorentzian
            self._resonator.fit_skewed_lorentzian(f_min=self._f_min, f_max = self._f_max)
        if self._fit_function == 2: #circle_reflection
            self._resonator.fit_circle(reflection = True, f_min=self._f_min, f_max = self._f_max)
        if self._fit_function == 3: #circle_notch
            self._resonator.fit_circle(notch = True, f_min=self._f_min, f_max = self._f_max)
        if self._fit_function == 4: #fano
            self._resonator.fit_fano(f_min=self._f_min, f_max = self._f_max)
        #if self._fit_function == 5: #all fits
            #self._resonator.fit_all_fits(f_min=self._f_min, f_max = self._f_max)

    def delete_fit_function(self, n = None):
        '''
        delete single fit function n (with 0 being the first one generated) or the complete landscape for n not specified
        '''

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

    def set_plot_comment(self, comment):
        '''
        Small comment to add at the end of plot pics for more information i.e. good for wiki entries.
        '''
        self._plot_comment=comment