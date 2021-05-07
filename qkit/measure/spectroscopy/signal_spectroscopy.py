# spectroscopy.py spectroscopy measurement class for use with a signal analyzer instead of a VNA
# based on spectroscopy.py
# TW 2018

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


import numpy as np
import logging
from time import sleep,time
import sys
import threading

import qkit
if qkit.module_available("matplotlib"):
    import matplotlib.pylab as plt
if qkit.module_available("scipy"):
    from scipy.optimize import curve_fit
from qkit.storage import store as hdf
from qkit.gui.plot import plot as qviewkit
from qkit.gui.notebook.Progress_Bar import Progress_Bar
from qkit.measure.measurement_class import Measurement
import qkit.measure.write_additional_files as waf


class spectrum(object):
    """
    usage: similar to the old spectroscopy file.However class generates hdf vectors/matrices depending on the number
    of traces of your signal_analyzer.

    m = spectrum(sig_analyzer = specki)

    m.set_x_parameters(arange(-0.05,0.05,0.01),'flux coil current',coil.set_current, unit = 'mA')
    m.set_y_parameters(arange(4e9,7e9,10e6),'excitation frequency',mw_src1.set_frequency, unit = 'Hz')

    m.gen_fit_function(...)      several times

    m.measure_XX()
    functions that must be additionally implemented in your signal analyzer's driver
    get_y_unit(trace) - returns y-unit of your trace
    get_active_traces() - returns number of traces
    get_trace_name(trace) - returns name of your trace
    """

    def __init__(self, sig_analyzer, exp_name='', sample=None):

        self.sig_analyzer = sig_analyzer
        self.averaging_start_ready = "start_measurement" in self.sig_analyzer.get_function_names() \
                                     and "ready" in self.sig_analyzer.get_function_names()
        if not self.averaging_start_ready: logging.warning(
            __name__ + ': With your signal analyzer driver (' + self.sig_analyzer.get_type() + '),'
                        ' I can not see when a measurement is complete. '
                        'So I only wait for a specific time and hope the VNA has finished. '
                        'Please consider implemeting the necessary functions into your driver.')
        self.exp_name = exp_name
        self._sample = sample

        self.landscape = None
        self.span = 200e6  # [Hz]
        self.tdx = 0.002  # [s]
        self.tdy = 0.002  # [s]

        self.comment = ''
        self.dirname = None

        self.x_set_obj = None
        self.y_set_obj = None

        self.progress_bar = True
        self._plot_comment = ""

        self.set_log_function()

        self.open_qviewkit = True
        self.qviewkit_singleInstance = False

        self._measurement_object = Measurement()
        self._measurement_object.measurement_type = 'spectroscopy'
        self._measurement_object.sample = self._sample

        self._qvk_process = False


    def set_log_function(self, func=None, name=None, unit=None, log_dtype=None):
        '''
        A function (object) can be passed to the measurement loop which is excecuted before every x iteration
        but after executing the x_object setter in 2D measurements and before every line (but after setting
        the x value) in 3D measurements.
        The return value of the function of type float or similar is stored in a value vector in the h5 file.

        Call without any arguments to delete all log functions. The timestamp is automatically saved.

        func: function object in list form
        name: name of logging parameter appearing in h5 file, default: 'log_param'
        unit: unit of logging parameter, default: ''
        log_dtype: h5 data type, default: 'f' (float32)
        '''

        if name == None:
            try:
                name = ['log_param'] * len(func)
            except Exception:
                name = None
        if unit == None:
            try:
                unit = [''] * len(func)
            except Exception:
                unit = None
        if log_dtype == None:
            try:
                log_dtype = ['f'] * len(func)
            except Exception:
                log_dtype = None

        self.log_function = []
        self.log_name = []
        self.log_unit = []
        self.log_dtype = []

        if func != None:
            for i, f in enumerate(func):
                self.log_function.append(f)
                self.log_name.append(name[i])
                self.log_unit.append(unit[i])
                self.log_dtype.append(log_dtype[i])

    def set_x_parameters(self, x_vec, x_coordname, x_set_obj, x_unit=""):
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

    def set_y_parameters(self, y_vec, y_coordname, y_set_obj, y_unit=""):
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

    def gen_fit_function(self, curve_f, curve_p, units='', p0=[-1, 0.1, 7]):
        '''
        curve_f: 'parab', 'hyp', specifies the fit function to be employed
        curve_p: set of points that are the basis for the fit in the format [[x1,x2,x3,...],[y1,y2,y3,...]], frequencies in Hz
        units: set this to 'Hz' in order to avoid large values that cause the fit routine to diverge
        p0 (optional): start parameters for the fit, must be an 1D array of length 3 ([a,b,c,d]),
           where for the parabula p0[3] will be ignored
        The parabolic function takes the form  y = a*(x-b)**2 + c , where (a,b,c) = p0
        The hyperbolic function takes the form y = sqrt[ a*(x-b)**2 + c ], where (a,b,c) = p0

        adds a trace to landscape
        '''
        if not qkit.module_available("scipy"):
            raise ImportError('scipy not available.')

        if not self.landscape:
            self.landscape = []

        x_fit = curve_p[0]
        if units == 'Hz':
            y_fit = np.array(curve_p[1]) * 1e-9
        else:
            y_fit = np.array(curve_p[1])

        try:
            multiplier = 1
            if units == 'Hz':
                multiplier = 1e9

            fit_fct = None
            if curve_f == 'parab':
                fit_fct = self.f_parab
            elif curve_f == 'hyp':
                fit_fct = self.f_hyp
            elif curve_f == 'lin':
                fit_fct = self.f_lin
                p0 = p0[:2]
            else:
                print('function type not known...aborting')
                raise ValueError

            popt, pcov = curve_fit(fit_fct, x_fit, y_fit, p0=p0)
            self.landscape.append(multiplier * fit_fct(self.x_vec, *popt))

        except Exception as message:
            print('fit not successful:', message)
            popt = p0

    def _prepare_measurement_sig_analyzer(self):
        '''
        all the relevant settings from the vna are updated and called
        '''

        self.sig_analyzer.get_all()
        # ttip.get_temperature()
        self._nop = self.sig_analyzer.get_nop()
        self._sweeptime_averages = self.sig_analyzer.get_sweeptime_averages()
        self._freqpoints = self.sig_analyzer.get_freqpoints()
        self.num_traces = self.sig_analyzer.get_active_traces()
        self.traces_names = []
        self.units = []
        for i in range(self.num_traces):
            self.traces_names.append(self.sig_analyzer.get_trace_name(i+1))  # must be implemented in driver
            self.units.append(self.sig_analyzer.get_y_unit(i+1))  # must also be impelmented

        if self.averaging_start_ready:
            self.sig_analyzer.pre_measurement()

    def _prepare_measurement_file(self):
        '''
        creates the output .h5-file with distinct dataset structures for each measurement type.
        at this point all measurement parameters are known and put in the output file
        '''

        self._data_file = hdf.Data(name=self._file_name, mode='a')
        self._measurement_object.uuid = self._data_file._uuid
        self._measurement_object.hdf_relpath = self._data_file._relpath
        self._measurement_object.instruments = qkit.instruments.get_instrument_names()

        self._measurement_object.save()
        self._mo = self._data_file.add_textlist('measurement')
        self._mo.append(self._measurement_object.get_JSON())

        # write logfile and instrument settings
        self._write_settings_dataset()
        self._log = waf.open_log_file(self._data_file.get_filepath())
        self._data_freq = self._data_file.add_coordinate('frequency', unit='Hz')
        self._data_freq.add(self._freqpoints)
        self._data = []  # empty list as we have a variable number of channels

        if self._scan_1D:
            for i in range(self.num_traces):
                self._data.append(self._data_file.add_value_vector(self.traces_names[i], x=self._data_freq,
                                                                   unit=self.units[i], save_timestamp=True))
        if self._scan_2D:
            self._data_x = self._data_file.add_coordinate(self.x_coordname, unit=self.x_unit)
            self._data_x.add(self.x_vec)
            for i in range(self.num_traces):
                self._data.append(self._data_file.add_value_matrix(self.traces_names[i], x=self._data_x,
                                                                   y=self._data_freq, unit=self.units[i],
                                                                   save_timestamp=True))
            if self.log_function != None:  # use logging
                self._log_value = []
                for i in range(len(self.log_function)):
                    self._log_value.append(
                        self._data_file.add_value_vector(self.log_name[i], x=self._data_x, unit=self.log_unit[i],
                                                         dtype=self.log_dtype[i]))

        if self._scan_3D:
            self._data_x = self._data_file.add_coordinate(self.x_coordname, unit=self.x_unit)
            self._data_x.add(self.x_vec)
            self._data_y = self._data_file.add_coordinate(self.y_coordname, unit=self.y_unit)
            self._data_y.add(self.y_vec)
            for i in range(self.num_traces):
                self._data.append(self._data_file.add_value_box(self.traces_names[i], x=self._data_x, y = self._data_y,
                                                                   z=self._data_freq, unit=self.units[i],
                                                                   save_timestamp=True))
            if self.log_function != None:  # use logging
                self._log_value = []
                for i in range(len(self.log_function)):
                    self._log_value.append(
                        self._data_file.add_value_vector(self.log_name[i], x=self._data_x, unit=self.log_unit[i],
                                                         dtype=self.log_dtype[i]))

        if self.comment:
            self._data_file.add_comment(self.comment)

        if self.qviewkit_singleInstance and self.open_qviewkit and self._qvk_process:
            self._qvk_process.terminate()  # terminate an old qviewkit instance

    def _write_settings_dataset(self):
        self._settings = self._data_file.add_textlist('settings')
        settings = waf.get_instrument_settings(self._data_file.get_filepath())
        self._settings.append(settings)

    def measure_1D(self, rescan=True, web_visible=True):
        '''
        measure method to record a single (averaged) VNA trace, S11 or S21 according to the setting on the VNA
        rescan: If True (default), the averages on the VNA are cleared and a new measurement is started.
                If False, it will directly take the data from the VNA without waiting.
        '''
        self._scan_1D = True
        self._scan_2D = False
        self._scan_3D = False
        self._scan_time = False

        self._measurement_object.measurement_func = 'measure_1D'
        self._measurement_object.x_axis = 'frequency'
        self._measurement_object.y_axis = ''
        self._measurement_object.z_axis = ''
        self._measurement_object.web_visible = web_visible

        if not self.dirname:
            self.dirname = 'signal_analyzer_tracedata'
        self._file_name = self.dirname.replace(' ', '').replace(',', '_')
        if self.exp_name:
            self._file_name += '_' + self.exp_name
        self._prepare_measurement_sig_analyzer()
        self._prepare_measurement_file()

        """opens qviewkit to plot measurement, amp and pha are opened by default"""
        if self.open_qviewkit:
            self._qvk_process = qviewkit.plot(self._data_file.get_filepath(), datasets=self.traces_names)
        print('recording trace...')
        sys.stdout.flush()

        qkit.flow.start()
        if rescan:
            if self.averaging_start_ready:
                self.sig_analyzer.start_measurement()
                ti = time()
                if self.progress_bar: self._p = Progress_Bar(self.sig_analyzer.get_averages(), self.dirname,
                                                             self.sig_analyzer.get_sweeptime())
                qkit.flow.sleep(.2)
                while not self.sig_analyzer.ready():
                    if time() - ti > self.sig_analyzer.get_sweeptime(query=False):
                        if self.progress_bar: self._p.iterate()
                        ti = time()
                    qkit.flow.sleep(.2)
                if self.progress_bar:
                    while self._p.progr < self._p.max_it:
                        self._p.iterate()
            else:  # not tested!!!!!!
                self.sig_analyzer.avg_clear()
                if self.sig_analyzer.get_averages() == 1 or self.sig_analyzer.get_Average() == False:  # no averaging
                    if self.progress_bar: self._p = Progress_Bar(1, self.dirname, self.sig_analyzer.get_sweeptime())
                    qkit.flow.sleep(self.sig_analyzer.get_sweeptime())  # wait single sweep
                    if self.progress_bar: self._p.iterate()
                else:  # with averaging
                    if self.progress_bar: self._p = Progress_Bar(self.sig_analyzer.get_averages(), self.dirname,
                                                                 self.sig_analyzer.get_sweeptime())
                    if "avg_status" in self.sig_analyzer.get_function_names():
                        for a in range(self.sig_analyzer.get_averages()):
                            while self.sig_analyzer.avg_status() <= a:
                                qkit.flow.sleep(.2)  # maybe one would like to adjust this at a later point
                            if self.progress_bar: self._p.iterate()
                    else:  # old style
                        for a in range(self.sig_analyzer.get_averages()):
                            qkit.flow.sleep(self.sig_analyzer.get_sweeptime())  # wait single sweep time
                            if self.progress_bar: self._p.iterate()

        for i in range(self.num_traces):
            self._data[i].append(self.sig_analyzer.get_tracedata(i+1))

        qkit.flow.end()
        self._end_measurement()

    def measure_2D(self, web_visible=True):
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
        self._scan_time = False

        self._measurement_object.measurement_func = 'measure_2D'
        self._measurement_object.x_axis = self.x_coordname
        self._measurement_object.y_axis = 'frequency'
        self._measurement_object.z_axis = ''
        self._measurement_object.web_visible = web_visible

        if not self.dirname:
            self.dirname = self.x_coordname
        self._file_name = '2D_' + self.dirname.replace(' ', '').replace(',', '_')
        if self.exp_name:
            self._file_name += '_' + self.exp_name

        if self.progress_bar: self._p = Progress_Bar(len(self.x_vec), '2D signal analyzer sweep ' + self.dirname,
                                                     self.sig_analyzer.get_sweeptime_averages())

        self._prepare_measurement_sig_analyzer()
        self._prepare_measurement_file()

        """opens qviewkit to plot measurement, amp and pha are opened by default"""

        if self.open_qviewkit: self._qvk_process = qviewkit.plot(self._data_file.get_filepath(),
                                                                 datasets=self.traces_names)
        self._measure()

    def measure_3D(self, web_visible=True):
        '''
        measure full window of vna while sweeping x_set_obj and y_set_obj with parameters x_vec/y_vec.
        sweep over y_set_obj is the inner loop, for every value x_vec[i] all values y_vec are measured.

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
        self._scan_time = False

        self._measurement_object.measurement_func = 'measure_3D'
        self._measurement_object.x_axis = self.x_coordname
        self._measurement_object.y_axis = self.y_coordname
        self._measurement_object.z_axis = 'frequency'
        self._measurement_object.web_visible = web_visible

        if not self.dirname:
            self.dirname = self.x_coordname + ', ' + self.y_coordname
        self._file_name = '3D_' + self.dirname.replace(' ', '').replace(',', '_')
        if self.exp_name:
            self._file_name += '_' + self.exp_name

        if self.progress_bar: self._p = Progress_Bar(len(self.x_vec) * len(self.y_vec), '3D signal analyzer sweep ' +
                                                     self.dirname, self.sig_analyzer.get_sweeptime_averages())
        self._prepare_measurement_sig_analyzer()
        self._prepare_measurement_file()
        """opens qviewkit to plot measurement, amp and pha are opened by default"""
        """only middle point in freq array is plotted vs x and y"""
        if self.open_qviewkit: self._qvk_process = qviewkit.plot(self._data_file.get_filepath(),
                                                                 datasets = self.traces_names)

        ### ???
        if self.landscape:
            self.center_freqs = np.array(self.landscape).T
        else:
            self.center_freqs = []  # load default sequence
            for i in range(len(self.x_vec)):
                self.center_freqs.append([0])

        self._measure()


    def _measure(self):
        '''
        measures and plots the data depending on the measurement type.
        the measurement loops feature the setting of the objects and saving the data in the .h5 file.
        '''
        qkit.flow.start()
        try:
            """
            loop: x_obj with parameters from x_vec
            """
            for ix, x in enumerate(self.x_vec):
                self.x_set_obj(x)
                sleep(self.tdx)

                if self.log_function != None:
                    for i, f in enumerate(self.log_function):
                        self._log_value[i].append(float(f()))

                #### not tested
                if self._scan_3D:
                    for y in self.y_vec:
                        """
                        loop: y_obj with parameters from y_vec (only 3D measurement)
                        """
                        if (np.min(np.abs(self.center_freqs[ix] - y * np.ones(len(self.center_freqs[
                                                                                      ix])))) > self.span / 2.) and self.landscape:  # if point is not of interest (not close to one of the functions)
                            data = []
                            for i in range(self.num_traces):
                                data.append(np.zeros(int(self._nop)))
                        else:
                            self.y_set_obj(y)
                            sleep(self.tdy)
                            if self.averaging_start_ready:
                                self.sig_analyzer.start_measurement()
                                qkit.flow.sleep(.2)  # just to make sure, the ready command does not *still* show ready
                                while not self.sig_analyzer.ready():
                                    qkit.flow.sleep(.2)
                            else:
                                self.sig_analyzer.avg_clear()
                                qkit.flow.sleep(self._sweeptime_averages)

                            # if "avg_status" in self.sig_analyzer.get_function_names():
                            #       while self.sig_analyzer.avg_status() < self.sig_analyzer.get_averages():
                            #            qkit.flow.sleep(.2) #maybe one would like to adjust this at a later point

                            """ measurement """
                            for i in range(self.num_traces):
                                self._data[i].append(self.sig_analyzer.get_tracedata(i+1))

                        if self.progress_bar:
                            self._p.iterate()
                        qkit.flow.sleep()
                    """
                    filling of value-box is done here.
                    after every y-loop the data is stored the next 2d structure
                    """
                    for i in range(self.num_traces):
                        self._data[i].next_matrix()

                if self._scan_2D:
                    if self.averaging_start_ready:
                        self.sig_analyzer.start_measurement()
                        qkit.flow.sleep(.2)  # just to make sure, the ready command does not *still* show ready
                        while not self.sig_analyzer.ready():
                            qkit.flow.sleep(.2)
                    else:
                        self.sig_analyzer.avg_clear()
                        qkit.flow.sleep(self._sweeptime_averages)
                    """ measurement """
                    for i in range(self.num_traces):
                        self._data[i].append(self.sig_analyzer.get_tracedata(i+1))

                    if self.progress_bar:
                        self._p.iterate()
                    qkit.flow.sleep()
        finally:
            self._end_measurement()
            qkit.flow.end()

    def _end_measurement(self):
        '''
        the data file is closed and filepath is printed
        '''
        print(self._data_file.get_filepath())
        # qviewkit.save_plots(self._data_file.get_filepath(),comment=self._plot_comment) #old version where we have to wait for the plots
        t = threading.Thread(target=qviewkit.save_plots, args=[self._data_file.get_filepath(), self._plot_comment])
        t.start()
        self._data_file.close_file()
        waf.close_log_file(self._log)
        self.dirname = None
        if self.averaging_start_ready: self.sig_analyzer.post_measurement()


    def delete_fit_function(self, n=None):
        '''
        delete single fit function n (with 0 being the first one generated) or the complete landscape for n not specified
        '''

        if n:
            self.landscape = np.delete(self.landscape, n, axis=0)
        else:
            self.landscape = None

    def plot_fit_function(self, num_points=100):
        '''
        try:
            x_coords = np.linspace(self.x_vec[0], self.x_vec[-1], num_points)
        except Exception as message:
            print 'no x axis information specified', message
            return
        '''
        if not qkit.module_available("matplotlib"):
            raise ImportError("matplotlib not found.")
        if self.landscape:
            for trace in self.landscape:
                try:
                    # plt.clear()
                    plt.plot(self.x_vec, trace)
                    plt.fill_between(self.x_vec, trace + float(self.span) / 2, trace - float(self.span) / 2, alpha=0.5)
                except Exception:
                    print('invalid trace...skip')
            plt.axhspan(self.y_vec[0], self.y_vec[-1], facecolor='0.5', alpha=0.5)
            plt.show()
        else:
            print('No trace generated.')

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

    def f_parab(self, x, a, b, c):
        return a * (x - b) ** 2 + c

    def f_hyp(self, x, a, b, c):
        "hyperbolic function with the form y = sqrt[ a*(x-b)**2 + c ]"
        return np.sqrt(a * (x - b) ** 2 + c)

    def f_lin(self, x, a, b):
        return a * x + b

    def set_plot_comment(self, comment):
        '''
        Small comment to add at the end of plot pics for more information i.e. good for wiki entries.
        '''
        self._plot_comment = comment
