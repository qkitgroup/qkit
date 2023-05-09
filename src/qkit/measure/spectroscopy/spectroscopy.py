# spectroscopy.py spectroscopy measurement class for use with a vector network analyzer
# JB/MP/AS@KIT 04/2015, 08/2015, 01/2016

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
from time import sleep, time
import sys
import threading

import qkit
if qkit.module_available("matplotlib"):
    import matplotlib.pylab as plt
if qkit.module_available("scipy"):
    from scipy.optimize import curve_fit
    from scipy.interpolate import interp1d, UnivariateSpline
from qkit.storage import store as hdf
from qkit.analysis.resonator import Resonator as resonator
from qkit.gui.plot import plot as qviewkit
from qkit.gui.notebook.Progress_Bar import Progress_Bar
from qkit.measure.measurement_class import Measurement
import qkit.measure.write_additional_files as waf


##################################################################

class spectrum(object):
    """
    Class for spectroscopy measurements with a VNA
    usage:
    m = spectrum(vna = vna1)

    m.set_x_parameters(arange(-0.05,0.05,0.01),'flux coil current',coil.set_current, unit = 'mA')  outer scan in 3D
    m.set_y_parameters(arange(4e9,7e9,10e6),'excitation frequency',mw_src1.set_frequency, unit = 'Hz')

    m.landscape.generate_fit_function_xy(...) for 3D scan, can be called several times and appends the current landscape
    m.landscape.generate_fit_function_xz(...) for 2D or 3D scan, adjusts the vna freqs with respect to x

    m.measure_XX()
    """

    def __init__(self, vna, exp_name='', sample=None):

        self.vna = vna
        self.averaging_start_ready = "start_measurement" in self.vna.get_function_names() and "ready" in self.vna.get_function_names()
        if not self.averaging_start_ready: logging.warning(
            __name__ + ': With your VNA instrument driver (' + self.vna.get_type() + '), I can not see when a measurement is complete. So I only wait for a specific time and hope the VNA has finished. Please consider implemeting the necessary functions into your driver.')
        self.exp_name = exp_name
        self._sample = sample
        self.landscape = Landscape(vna=vna,spec=self)
        self.tdx = 0.002  # [s]
        self.tdy = 0.002  # [s]

        self.vna_poll_interval = 0.1 # interval in seconds in which the vna is queried to be ready.

        self.comment = ''
        self.dirname = None

        self.x_set_obj = None
        self.y_set_obj = None
        self.x_vec = None
        self.y_vec = None

        self.progress_bar = True
        self._fit_resonator = False
        self._plot_comment = ""

        self.set_log_function()
        self.set_log_function_2D()

        self.open_qviewkit = True
        self.qviewkit_singleInstance = False

        self._measurement_object = Measurement()
        self._measurement_object.measurement_type = 'spectroscopy'
        self._measurement_object.sample = self._sample
        self.measurement_object_axis_name = 'frequency'

        self._qvk_process = False
        self._scan_dim = None
        self._scan_time = False

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
    
    def set_log_function_2D(self, func=None, name=None, unit=None, y=None, y_name=None, y_unit=None, log_dtype=None):
        '''
        A function (object) can be passed to the measurement loop which is excecuted before every x iteration
        but after executing the x_object setter in 2D measurements and before every line (but after setting
        the x value) in 3D measurements.
        The return values of the function of type 1D-list or similar is stored in a value matrix in the h5 file.

        Call without any arguments to delete all log functions. The timestamp is automatically saved.

        func: function object in list form, returning a list each
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

        self.log_function_2D = []
        self.log_name_2D = []
        self.log_unit_2D = []
        self.log_y_2D = []
        self.log_y_name_2D = []
        self.log_y_unit_2D = []
        self.log_dtype_2D = []

        if func != None:
            for i, _ in enumerate(func):
                self.log_function_2D.append(func[i])
                self.log_name_2D.append(name[i])
                self.log_unit_2D.append(unit[i])
                self.log_dtype_2D.append(log_dtype[i])
                self.log_y_2D.append(y[i])
                self.log_y_name_2D.append(y_name[i])
                self.log_y_unit_2D.append(y_unit[i])

    def set_x_parameters(self, x_vec, x_coordname, x_set_obj, x_unit=""):
        """
        Sets parameters for sweep. In a 3D measurement, the x-parameters will be the "outer" sweep.
        For every x value all y values are swept
        Input:
        x_vec (array): conains the sweeping values
        x_coordname (string)
        x_instrument (obj): callable object to execute with x_vec-values (i.e. vna.set_power())
        x_unit (string): optional
        """
        self.x_vec = x_vec
        self.x_coordname = x_coordname
        self.x_unit = x_unit
        self.x_set_obj = x_set_obj
        if self.landscape.xylandscapes:
            self.landscape.delete_landscape_function_xy()
            logging.warning('xy landscape has been deleted')
        if self.landscape.xzlandscape_func:
            self.landscape.delete_landscape_function_xz()
            logging.warning('xz landscape has been deleted')

    def set_y_parameters(self, y_vec, y_coordname, y_set_obj, y_unit="", delete_landscape=True):
        """
        Sets parameters for sweep. In a 3D measurement, the x-parameters will be the "outer" sweep.
        For every x value all y values are swept
        Input:
        y_vec (array): contains the sweeping values
        y_coordname (string)
        y_instrument (obj): callable object to execute with x_vec-values (i.e. vna.set_power())
        y_unit (string): optional
        delete_landscape: True (default) if previously generated xz-landscape should be deleted
        """
        self.y_vec = y_vec
        self.y_coordname = y_coordname
        self.y_set_obj = y_set_obj
        self.y_unit = y_unit
        if self.landscape.xylandscapes:
            self.landscape.delete_landscape_function_xy()
            logging.warning('xy landscape has been deleted')
        if self.landscape.xzlandscape_func and delete_landscape:
            self.landscape.delete_landscape_function_xz()
            logging.warning('xz landscape has been deleted. You can switch this off if you whish.')

    def _prepare_measurement_vna(self):
        '''
        all the relevant settings from the vna are updated and called
        '''

        self.vna.get_all()
        # ttip.get_temperature()
        self._nop = self.vna.get_nop()
        self._sweeptime_averages = self.vna.get_sweeptime_averages()
        if self._scan_dim == 1 or not self.landscape.xzlandscape_func: # normal scan
            self._freqpoints = self.vna.get_freqpoints()
        else:
            self._freqpoints = self.landscape.get_freqpoints_xz()
        if self.averaging_start_ready: self.vna.pre_measurement()

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
        if not self._scan_time:
            self._data_freq.add(self._freqpoints)
            sweep_vector = self._data_freq
        else:
            self._data_freq.add([self.vna.get_centerfreq()])
            self._data_time = self._data_file.add_coordinate('time', unit='s')
            self._data_time.add(np.arange(0, self._nop, 1) * self.vna.get_sweeptime() / (self._nop - 1))
            sweep_vector = self._data_time

        if self._scan_dim == 1:
            self._data_real = self._data_file.add_value_vector('real', x=sweep_vector, unit='', save_timestamp=True)
            self._data_imag = self._data_file.add_value_vector('imag', x=sweep_vector, unit='', save_timestamp=True)
            self._data_amp = self._data_file.add_value_vector('amplitude', x=sweep_vector, unit='arb. unit',
                                                              save_timestamp=True)
            self._data_pha = self._data_file.add_value_vector('phase', x=sweep_vector, unit='rad',
                                                              save_timestamp=True)

        if self._scan_dim == 2:
            self._data_x = self._data_file.add_coordinate(self.x_coordname, unit=self.x_unit)
            self._data_x.add(self.x_vec)
            self._data_amp = self._data_file.add_value_matrix('amplitude', x=self._data_x, y=sweep_vector,
                                                              unit='arb. unit', save_timestamp=True)
            self._data_pha = self._data_file.add_value_matrix('phase', x=self._data_x, y=sweep_vector, unit='rad',
                                                              save_timestamp=True)

            if self.log_function != None:  # use logging
                self._log_value = []
                for i in range(len(self.log_function)):
                    self._log_value.append(
                        self._data_file.add_value_vector(self.log_name[i], x=self._data_x, unit=self.log_unit[i],
                                                         dtype=self.log_dtype[i]))

            if self._nop < 10:
                """creates view: plot middle point vs x-parameter, for qubit measurements"""
                self._views = [
                    self._data_file.add_view("amplitude_midpoint",x=self._data_x,y=self._data_amp,
                                             view_params=dict(transpose=True,default_trace=self._nop // 2,linecolors=[(200,200,100)])),
                    self._data_file.add_view("phase_midpoint", x=self._data_x, y=self._data_pha,
                                             view_params=dict(transpose=True, default_trace=self._nop // 2, linecolors=[(200, 200, 100)]))
                ]

        if self._scan_dim == 3:
            self._data_x = self._data_file.add_coordinate(self.x_coordname, unit=self.x_unit)
            self._data_x.add(self.x_vec)
            self._data_y = self._data_file.add_coordinate(self.y_coordname, unit=self.y_unit)
            self._data_y.add(self.y_vec)

            if self._nop == 0:  # saving in a 2D matrix instead of a 3D box HR: does not work yet !!! test things before you put them online.
                self._data_amp = self._data_file.add_value_matrix('amplitude', x=self._data_x, y=self._data_y,
                                                                  unit='arb. unit', save_timestamp=False)
                self._data_pha = self._data_file.add_value_matrix('phase', x=self._data_x, y=self._data_y, unit='rad',
                                                                  save_timestamp=False)
            else:
                self._data_amp = self._data_file.add_value_box('amplitude', x=self._data_x, y=self._data_y,
                                                               z=sweep_vector, unit='arb. unit',
                                                               save_timestamp=False)
                self._data_pha = self._data_file.add_value_box('phase', x=self._data_x, y=self._data_y,
                                                               z=sweep_vector, unit='rad', save_timestamp=False)

            if self.log_function != None:  # use logging
                self._log_value = []
                for i in range(len(self.log_function)):
                    self._log_value.append(
                        self._data_file.add_value_vector(self.log_name[i], x=self._data_x, unit=self.log_unit[i],
                                                         dtype=self.log_dtype[i]))

            if self.log_function_2D != None:  # use 2D logging
                self._log_y_value_2D = []
                for i in range(len(self.log_y_name_2D)):
                    if self.log_y_name_2D[i] not in self.log_y_name_2D[:i]:  # add y coordinate for 2D logging
                        self._log_y_value_2D.append(self._data_file.add_coordinate(self.log_y_name_2D[i], unit=self.log_y_unit_2D[i], folder='data'))  # possibly use "data1"
                        self._log_y_value_2D[i].add(self.log_y_2D[i])
                    else:  # use y coordinate for 2D logging if it is already added
                        self._log_y_value_2D.append(self._log_y_value_2D[np.squeeze(np.argwhere(self.log_y_name_2D[i] == np.array(self.log_y_name_2D[:i])))])
                
                self._log_value_2D = []
                for i in range(len(self.log_function_2D)):
                    self._log_value_2D.append(
                        self._data_file.add_value_matrix(self.log_name_2D[i], x=self._data_x, y=self._log_y_value_2D[i], unit=self.log_unit_2D[i],
                                                         dtype=self.log_dtype_2D[i], folder='data'))  # possibly use "data1"

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
        self._scan_dim = 1

        self._measurement_object.measurement_func = 'measure_1D'
        self._measurement_object.x_axis = self.measurement_object_axis_name
        self._measurement_object.y_axis = ''
        self._measurement_object.z_axis = ''
        self._measurement_object.web_visible = web_visible

        if not self.dirname:
            self.dirname = 'VNA_tracedata'
        self._file_name = self.dirname.replace(' ', '').replace(',', '_')
        if self.exp_name:
            self._file_name += '_' + self.exp_name
        self._prepare_measurement_vna()
        self._prepare_measurement_file()

        """opens qviewkit to plot measurement, amp and pha are opened by default"""
        if self.open_qviewkit:
            self._qvk_process = qviewkit.plot(self._data_file.get_filepath(), datasets=['amplitude', 'phase'])
        if self._fit_resonator:
            self._resonator = resonator(self._data_file.get_filepath())

        qkit.flow.start()
        if rescan:
            if self.averaging_start_ready:
                self.vna.start_measurement()
                ti = time()
                if self.progress_bar:
                    self._p = Progress_Bar(self.vna.get_averages(), self.dirname, self.vna.get_sweeptime())
                qkit.flow.sleep(.2)
                while not self.vna.ready():
                    if time() - ti > self.vna.get_sweeptime(query=False):
                        if self.progress_bar: self._p.iterate()
                        ti = time()
                    qkit.flow.sleep(.2)
                if self.progress_bar:
                    while self._p.progr < self._p.max_it:
                        self._p.iterate()
            else:
                self.vna.avg_clear()
                if self.vna.get_averages() == 1 or self.vna.get_Average() == False:  # no averaging
                    if self.progress_bar: self._p = Progress_Bar(1, self.dirname, self.vna.get_sweeptime())
                    qkit.flow.sleep(self.vna.get_sweeptime())  # wait single sweep
                    if self.progress_bar: self._p.iterate()
                else:  # with averaging
                    if self.progress_bar:
                        self._p = Progress_Bar(self.vna.get_averages(), self.dirname, self.vna.get_sweeptime())
                    if "avg_status" in self.vna.get_function_names():
                        for a in range(self.vna.get_averages()):
                            while self.vna.avg_status() <= a:
                                qkit.flow.sleep(.2)  # maybe one would like to adjust this at a later point
                            if self.progress_bar: self._p.iterate()
                    else:  # old style
                        for a in range(self.vna.get_averages()):
                            qkit.flow.sleep(self.vna.get_sweeptime())  # wait single sweep time
                            if self.progress_bar: self._p.iterate()

        data_amp, data_pha = self.vna.get_tracedata()
        data_real, data_imag = self.vna.get_tracedata('RealImag')

        self._data_amp.append(data_amp)
        self._data_pha.append(data_pha)
        self._data_real.append(data_real)
        self._data_imag.append(data_imag)
        if self._fit_resonator:
            self._do_fit_resonator()

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
        if self.landscape.xzlandscape_func:  # The vna limits need to be adjusted, happens in the frequency wrapper
            self.x_set_obj = self.landscape.vna_frequency_wrapper(self.x_set_obj)
        if len(self.x_vec) == 0:
            logging.error('No points to measure given. Check your x vector... aborting')
            return
        self._scan_dim = 2

        self._measurement_object.measurement_func = 'measure_2D'
        self._measurement_object.x_axis = self.x_coordname
        self._measurement_object.y_axis = self.measurement_object_axis_name
        self._measurement_object.z_axis = ''
        self._measurement_object.web_visible = web_visible

        if not self.dirname:
            self.dirname = self.x_coordname
        self._file_name = '2D_' + self.dirname.replace(' ', '').replace(',', '_')
        if self.exp_name:
            self._file_name += '_' + self.exp_name

        if self.progress_bar: self._p = Progress_Bar(len(self.x_vec), '2D VNA sweep ' + self.dirname,
                                                     self.vna.get_sweeptime_averages())

        self._prepare_measurement_vna()
        self._prepare_measurement_file()

        """opens qviewkit to plot measurement, amp and pha are opened by default"""
        if self._nop < 10:
            self._data_file.hf.hf.attrs['default_ds'] =['views/amplitude_midpoint', 'views/phase_midpoint']
        else:
            self._data_file.hf.hf.attrs['default_ds'] = ['data0/amplitude_midpoint', 'data0/phase_midpoint']
        
        if self.open_qviewkit:
            self._qvk_process = qviewkit.plot(self._data_file.get_filepath(),datasets=list(self._data_file.hf.hf.attrs['default_ds']))
        if self._fit_resonator:
            self._resonator = resonator(self._data_file.get_filepath())
        self._measure()

    def measure_3D(self, web_visible=True):
        '''
        measure full window of vna while sweeping x_set_obj and y_set_obj with parameters x_vec/y_vec. sweep over y_set_obj is the inner loop, for every value x_vec[i] all values y_vec are measured.

        optional: measure method to perform the measurement according to landscape, if set
        self.span is the range (in units of the vertical plot axis) data is taken around the specified funtion(s)
        note: make sure to have properly set x,y vectors before generating traces
        '''
        if not self.x_set_obj or not self.y_set_obj:
            logging.error('axes parameters not properly set...aborting')
            return
        if len(self.x_vec) * len(self.y_vec) == 0:
            logging.error('No points to measure given. Check your x ad y vector... aborting')
            return
        if self.landscape.xzlandscape_func:  # The vna limits need to be adjusted, happens in the frequency wrapper
            self.x_set_obj = self.landscape.vna_frequency_wrapper(self.x_set_obj)

        self._scan_dim = 3

        self._measurement_object.measurement_func = 'measure_3D'
        self._measurement_object.x_axis = self.x_coordname
        self._measurement_object.y_axis = self.y_coordname
        self._measurement_object.z_axis = self.measurement_object_axis_name
        self._measurement_object.web_visible = web_visible

        if not self.dirname:
            self.dirname = self.x_coordname + ', ' + self.y_coordname
        self._file_name = '3D_' + self.dirname.replace(' ', '').replace(',', '_')
        if self.exp_name:
            self._file_name += '_' + self.exp_name

        self._prepare_measurement_vna()
        self._prepare_measurement_file()
        """opens qviewkit to plot measurement, amp and pha are opened by default"""
        """only middle point in freq array is plotted vs x and y"""
        if self.open_qviewkit: self._qvk_process = qviewkit.plot(self._data_file.get_filepath(),
                                                                 datasets=['amplitude', 'phase'])
        if self._fit_resonator:
            self._resonator = resonator(self._data_file.get_filepath())

        if self.progress_bar:
            if self.landscape.xylandscapes:
                truth = np.full((len(self.y_vec), len(self.x_vec)), False)  # first, nothing is selected:
                for e in self.landscape.xylandscapes:
                    if not e['blacklist']:
                        truth = np.logical_or(truth,
                                              (np.abs(self.y_vec[:, np.newaxis] - e['center_points']) <= e['y_span'] / 2) *  # check y span
                                              (e['x_range'][0] <= self.x_vec) * (self.x_vec <= e['x_range'][1])) # check x range
    
                for e in self.landscape.xylandscapes:
                    if e['blacklist']:  # exclude blacklisted areas
                        truth = np.logical_and(truth,
                                               np.logical_not(
                                                  (np.abs(self.y_vec[:, np.newaxis] - e['center_points']) <= e['y_span'] / 2) *
                                                  (e['x_range'][0] <= self.x_vec) * (self.x_vec <= e['x_range'][1]))
                                               )
                points = np.sum(truth)
            else:
                points = len(self.x_vec) * len(self.y_vec)
            self._p = Progress_Bar(points, '3D VNA sweep ' + self.dirname, self.vna.get_sweeptime_averages())

        self._measure()

    def set_cw_time_measurement(self, status):
        """
        Activates or deactivates timetrace measurements. Sets the VNA in constant cw mode to measure over time
        and adjusts the sweep vector name for the measurement object
        :param status: (bool) True = timetrace active, False = timetrace inactive
        :param web_visible:
        :return:
        """

        if status:
            self.vna.set_sweep_type('CW')
            self._scan_time = True
            self.measurement_object_axis_name = 'time'

        if status is False:
            self.vna.set_sweep_type('LIN')
            self._scan_time = False
            self.measurement_object_axis_name = 'frequency'

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

                if self.log_function_2D != None:
                    for i, f in enumerate(self.log_function_2D):
                        self._log_value_2D[i].append(f())

                if self._scan_dim == 3:
                    for y in self.y_vec:
                        # loop: y_obj with parameters from y_vec (only 3D measurement)
                        if self.landscape.xylandscapes and not self.landscape.perform_measurement_at_point(x, y, ix):
                            # if point is not of interest (not close to one of the functions)
                            data_amp = np.full(int(self._nop), np.NaN, dtype=np.float16)
                            data_pha = np.full(int(self._nop), np.NaN, dtype=np.float16)  # fill with NaNs
                        else:
                            self.y_set_obj(y)
                            sleep(self.tdy)
                            if self.averaging_start_ready:
                                self.vna.start_measurement()
                                # Check if the VNA is STILL in ready state, then add some delay.
                                # If you manually decrease the poll_inveral, I guess you know what you are doing and will disable this safety query.
                                if self.vna_poll_interval >= 0.1 and self.vna.ready():
                                    logging.debug("VNA STILL ready... Adding delay")
                                    qkit.flow.sleep(
                                        .2)  # just to make sure, the ready command does not *still* show ready

                                while not self.vna.ready():
                                    qkit.flow.sleep(min(self.vna.get_sweeptime_averages(query=False) / 11., self.vna_poll_interval))
                            else:
                                self.vna.avg_clear()
                                qkit.flow.sleep(self._sweeptime_averages)

                            # if "avg_status" in self.vna.get_function_names():
                            #       while self.vna.avg_status() < self.vna.get_averages():
                            #            qkit.flow.sleep(.2) #maybe one would like to adjust this at a later point

                            """ measurement """
                            if not self.landscape.xzlandscape_func:  # normal scan
                                data_amp, data_pha = self.vna.get_tracedata()
                            else:
                                data_amp, data_pha = self.landscape.get_tracedata_xz(x)
                            if self.progress_bar:
                                self._p.iterate()

                        if self._nop == 0:  # this does not work yet.
                            print(data_amp[0], data_amp, self._nop)
                            self._data_amp.append(data_amp[0])
                            self._data_pha.append(data_pha[0])
                        else:
                            self._data_amp.append(data_amp)
                            self._data_pha.append(data_pha)
                        if self._fit_resonator:
                            self._do_fit_resonator()
                        qkit.flow.sleep()
                    """
                    filling of value-box is done here.
                    after every y-loop the data is stored the next 2d structure
                    """
                    self._data_amp.next_matrix()
                    self._data_pha.next_matrix()

                if self._scan_dim == 2:
                    if self.averaging_start_ready:
                        self.vna.start_measurement()
                        if self.vna.ready():
                            logging.debug("VNA STILL ready... Adding delay")
                            qkit.flow.sleep(.2)  # just to make sure, the ready command does not *still* show ready

                        while not self.vna.ready():
                            qkit.flow.sleep(min(self.vna.get_sweeptime_averages(query=False) / 11., .2))
                    else:
                        self.vna.avg_clear()
                        qkit.flow.sleep(self._sweeptime_averages)
                    """ measurement """
                    if not self.landscape.xzlandscape_func:  # normal scan
                        data_amp, data_pha = self.vna.get_tracedata()
                    else:
                        data_amp, data_pha = self.landscape.get_tracedata_xz(x)
                    self._data_amp.append(data_amp)
                    self._data_pha.append(data_pha)

                    if self._fit_resonator:
                        self._do_fit_resonator()
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
        if self.averaging_start_ready: self.vna.post_measurement()

    def set_resonator_fit(self, fit_resonator=True, fit_function='', f_min=None, f_max=None):
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
        self._functions = {'lorentzian': 0, 'skewed_lorentzian': 1, 'circle_fit_reflection': 2, 'circle_fit_notch': 3,
                           'fano': 4, 'all_fits': 5}
        try:
            self._fit_function = self._functions[fit_function]
        except KeyError:
            logging.error(
                'Fit function not properly set. Must be either \'lorentzian\', \'skewed_lorentzian\', \'circle_fit_reflection\', \'circle_fit_notch\', \'fano\', or \'all_fits\'.')
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

        if self._fit_function == 0:  # lorentzian
            self._resonator.fit_lorentzian(f_min=self._f_min, f_max=self._f_max)
        elif self._fit_function == 1:  # skewed_lorentzian
            self._resonator.fit_skewed_lorentzian(f_min=self._f_min, f_max=self._f_max)
        elif self._fit_function == 2:  # circle_reflection
            self._resonator.fit_circle(reflection=True, f_min=self._f_min, f_max=self._f_max)
        elif self._fit_function == 3:  # circle_notch
            self._resonator.fit_circle(notch=True, f_min=self._f_min, f_max=self._f_max)
        elif self._fit_function == 4:  # fano
            self._resonator.fit_fano(f_min=self._f_min, f_max=self._f_max)
        elif self._fit_function == 5: #all fits
            logging.warning("Please performe fits individually, fit all is currently not supported.")
        # self._resonator.fit_all_fits(f_min=self._f_min, f_max = self._f_max)
        else:
            logging.error("Fit function set in spectrum.set_resonator_fit is not supported. Must be either \'lorentzian\', \'skewed_lorentzian\', \'circle_fit_reflection\', \'circle_fit_notch\', \'fano\', or \'all_fits\'.")

    def set_tdx(self, tdx):
        self.tdx = tdx

    def set_tdy(self, tdy):
        self.tdy = tdy

    def get_tdx(self):
        return self.tdx

    def get_tdy(self):
        return self.tdy

    def set_plot_comment(self, comment):
        '''
        Small comment to add at the end of plot pics for more information i.e. good for wiki entries.
        '''
        self._plot_comment = comment

    def gen_fit_function(self, curve_f, curve_p, x_range=None, span=None, p0=[-1, 0.1, 7], units=''):
        """
        Generates an xy landscape fit for 3D scan. Function is deprecated and calls landscape.generate_fit_function
        curve_f: 'spline', '2pt' 'lin, 'parab', 'hyp', specifies the fit function to be employed
        curve_p: set of points that are the basis for the fit in the format [[x1,x2,x3,...],[y1,y2,y3,...]], frequencies in Hz
        span: specify span for the generated fit_function, if not given default of self.span is used
        x_range: specify x_range for the function in the format [x_min, x_max]
        p0 (optional): start parameters for the fit, must be an 1D array of length 3 ([a,b,c,d]),
           where for the parabula p0[3] will be ignored
        units: set this to 'Hz' in order to avoid large values that cause the fit routine to diverge
        The parabolic function takes the form  y = a*(x-b)**2 + c , where (a,b,c) = p0
        The hyperbolic function takes the form y = sqrt[ a*(x-b)**2 + c ], where (a,b,c) = p0

        adds a trace to landscape
        """
        logging.warning("This function is deprecated. Better to use landscape.generate_fit_function_xy")
        self.landscape.generate_fit_function_xy(curve_f=curve_f, curve_p=curve_p, x_range=x_range, y_span=span, p0=p0, units=units)

    def delete_fit_function(self, n=None):
        """
        legacy support for delete_xy_landscape_function. Please use the other function in the future
        delete single fit function n (with 0 being the first one generated) or the complete landscape for n not specified
        :param n: index of single fit function to be deleted
        :return:
        """
        logging.warning('This function is deprecated for clarity purposes.'
                        ' Please use delete_xy_landscape_function in the future')
        self.landscape.delete_landscape_function_xy(n=n)

    def plot_fit_function(self):
        """
        legeacy support for landscape.plot_fit_function_xy. Please use the other function in the future.
        Plots the landscape
        :return:
        """
        self.landscape.plot_xy_landscape()

    def measure_timetrace(self):
        logging.error("This function does no longer exist. Use set_cw_time_mesurement() "
                      "followed by the standard measure functions")


class Landscape:
    """
    Class for landscape scans in combination with spectroscopy. spectrum gnerates an instance of Landscape in __init__
    Use this instance to generate your fit_functions/landscape for your measurement.
    Instance stores the landscape(functions), lets you plot them, checks if points are to be measured and adjusts
    the vna frequencies.
    """
    def __init__(self, vna, spec):
        self.vna = vna
        self.spec = spec # The spectroscopy object
        self.xylandscapes = []  # List containing dicts
        self.xzlandscape_func = None
        self.xz_freqpoints = None
        self.y_span_default = 200e6  # this is for the xy landscape scan, i.e., span of your y_parameter, e.g, mw_frequency
        self.z_span = self.vna.get_span()  # This is for the xz landscape scan i.e. span of vna is adjusted w/ resp to x

    def generate_fit_function_xy(self, curve_f, curve_p, x_range=None, y_span=None, blacklist=False, p0=[-1, 0.1, 7], units=''):
        """
        Use this function if you keep your vna span fixed but want to add a landscape to your x and y parameter.
        I.e., for given x parameter not all y parameters are swept but only those that lie within the specified y-span
        around the fit function.
        Adds a trace to landscape
        curve_f: 'spline', 'lin_spline' 'lin, 'parab', 'hyp', 'transmon' specifies the fit function to be employed
        curve_p: set of points that are the basis for the fit in the format [[x1,x2,x3,...],[y1,y2,y3,...]], frequencies in Hz
        x_range: specify x_range for the function in the format [x_min, x_max]
        y_span: specify the span of your y_axis for the generated fit_function,
                if not given default of self.span is used, if negative the span will be excluded from the measurement
                interesting for overlaping regions
        blacklist: Use this parameter to explicitly exclude a section from the measurement (previously done by negative span)
        p0 (optional): start parameters for the fit, must be an 1D array of length 3 ([a,b,c,d]),
           where for the parabula p0[3] will be ignored
        units: set this to 'Hz' in order to avoid large values that cause the fit routine to diverge

        The parabolic function takes the form  y = a*(x-b)**2 + c , where (a,b,c) = p0
        The hyperbolic function takes the form y = sqrt[ a*(x-b)**2 + c ], where (a,b,c) = p0

        """
        if not qkit.module_available("scipy"):
            raise ImportError('scipy not available.')

        if units == 'Hz':
            multiplier = 1e9
        else:
            multiplier = 1
        x_fit = np.array(curve_p[0])
        y_fit = np.array(curve_p[1])
        if x_range is None:
            x_range = [self.spec.x_vec[0], self.spec.x_vec[-1]]
        if y_span is None:
            y_span = self.y_span_default
        if y_span < 0:
            y_span = -y_span
            blacklist = True
            logging.warning('Using a negative span in generate_fit_function_xy is deprecated. Please use blacklist = True instead for more clarity.')

        try:
            if curve_f == 'lin_spline':
                f = interp1d(x_fit, y_fit, fill_value="extrapolate")
                center_points = f(self.spec.x_vec)
            elif curve_f == 'spline':
                center_points =  UnivariateSpline(x_fit, y_fit)(self.spec.x_vec)
            else:  # curve_fit procedure differs from splines
                if curve_f == 'parab':
                    fit_fct = self.f_parab
                elif curve_f == 'hyp':
                    fit_fct = self.f_hyp
                elif curve_f == 'lin':
                    fit_fct = self.f_lin
                    p0 = p0[:2]
                elif curve_f == 'transmon':
                    fit_fct = self.f_transmon
                else:
                    raise ValueError('function type not known...aborting')
                popt, pcov = curve_fit(fit_fct, x_fit, y_fit / multiplier, p0=p0)
                center_points = multiplier * fit_fct(self.spec.x_vec, *popt)
        except Exception as message:
            print('fit not successful:', message)
        else:
            self.xylandscapes.append({
                'center_points':center_points,
                'y_span':y_span,
                'x_range':[np.min(x_range), np.max(x_range)],
                'blacklist':blacklist
                })
        
    def generate_fit_function_xz(self, curve_f, curve_p, z_span=None, p0=[-1, 0.1, 7]):
        """
        Use this function if you want to adjust your vna span with respect to your x-values, useful if you want to
        track your fresonator, e.g., shifting resonance due qubit resonator coupling or fmr measurements. It works
        in a 2d and 3d scan.
        :param curve_f: fit_function (str) such as 'lin_spline', 'spline', 'parab', 'hyp', 'lin'
        :param curve_p: Valeus to fit in the form [[x0,x1,..xn],[z0,z1,..zn]]
        :param z_span: If None, span from VNA is used. If specified, vna span will be updated.
        :param p0: intial fit parameters
        :return:
        """
        if not qkit.module_available("scipy"):
            raise ImportError('scipy not available.')
        
        if curve_p[1][-1] > 1e6:  # test if z_values are given in Hz or GHz
            multiplier = 1e9
        else:
            multiplier = 1
        if z_span is not None:
            self.z_span = z_span
            self.vna.set_span(z_span)
        else:
            self.z_span = self.vna.get_span()
        x_fit = np.array(curve_p[0])
        z_fit = np.array(curve_p[1])
        try:
            if curve_f == 'lin_spline':
                self.xzlandscape_func = interp1d(x_fit, z_fit)
            elif curve_f == 'spline':
                self.xzlandscape_func = UnivariateSpline(x_fit, z_fit)
            else:  # curve_fit procedure differs from splines
                if curve_f == 'parab':
                    fit_fct = self.f_parab
                elif curve_f == 'hyp':
                    fit_fct = self.f_hyp
                elif curve_f == 'lin':
                    fit_fct = self.f_lin
                    p0 = p0[:2]
                else:
                    raise ValueError('function type not known...aborting')
                popt, pcov = curve_fit(fit_fct, x_fit, z_fit/multiplier, p0=p0)
                self.xzlandscape_func = lambda x: multiplier * fit_fct(x, *popt)

            self.xz_freqpoints = np.arange(np.min(self.xzlandscape_func(self.spec.x_vec)) - self.z_span / 2,
                                           np.max(self.xzlandscape_func(self.spec.x_vec)) + self.z_span / 2,
                                           self.vna.get_span() / self.vna.get_nop())
        except Exception as message:
            print('fit not successful:', message)

    def delete_landscape_function_xy(self, n=None):
        """
        delete single xy landscape function n (with 0 being the first one generated)
        or the complete landscape for n not specified
        """
        if n is not None:
            del self.xylandscapes[n]
        else:
            self.xylandscapes = []


    def delete_landscape_function_xz(self):
        """
        delets the xz_landscape_function incl. the xz_freqpoints
        :return: None
        """
        self.xzlandscape_func = None
        self.xz_freqpoints = None
        print('xz_landscape deleted')

    def plot_xy_landscape(self):
        """
        Plots the xy landscape(s) (for 3D scan, z-axis (vna) is not plotted
        :return:
        """
        if not qkit.module_available("matplotlib"):
            raise ImportError("matplotlib not found.")

        if self.xylandscapes:
            for i in self.xylandscapes:
                try:
                    arg = np.where((i['x_range'][0] <= self.spec.x_vec) & (self.spec.x_vec <= i['x_range'][1]))
                    x = self.spec.x_vec[arg]
                    t = i['center_points'][arg]
                    plt.plot(x, t, color='C1')
                    if i['blacklist']:
                        plt.fill_between(x, t + i['y_span'] / 2., t - i['y_span'] / 2., color='C3', alpha=0.5)
                    else:
                        plt.fill_between(x, t + i['y_span'] / 2., t - i['y_span'] / 2., color='C0', alpha=0.5)
                except Exception as e:
                    print(e)
                    print('invalid trace...skip')
            plt.axhspan(np.min(self.spec.y_vec), np.max(self.spec.y_vec), facecolor='0.5', alpha=0.5)
            plt.xlim(np.min(self.spec.x_vec), np.max(self.spec.x_vec))
            plt.show()
        else:
            print('No trace generated. Use landscape.generate_xy_function')

    def plot_xz_landscape(self):
        """
        plots the xz landscape, i.e., how your vna frequency span changes with respect to the x vector
        :return: None
        """
        if not qkit.module_available("matplotlib"):
            raise ImportError("matplotlib not found.")

        if self.xzlandscape_func:
            y_values = self.xzlandscape_func(self.spec.x_vec)
            plt.plot(self.spec.x_vec, y_values, 'C1')
            plt.fill_between(self.spec.x_vec, y_values+self.z_span/2., y_values-self.z_span/2., color='C0', alpha=0.5)
            plt.xlim((self.spec.x_vec[0], self.spec.x_vec[-1]))
            plt.ylim((self.xz_freqpoints[0], self.xz_freqpoints[-1]))
            plt.show()
        else:
            print('No xz funcion generated. Use landscape.generate_xz_function')

    def set_y_span(self, y_span, n=None):
        if not self.xylandscapes:
            self.y_span_default = y_span
        else:
            if n is not None:
                self.xylandscapes[n]['y_span'] = y_span
            else:
                for e in self.xylandscapes:
                    e['y_span'] = y_span

    def get_y_span(self):
        return self.y_span_default

    def get_y_span_list(self):
        return [e['y_span'] for e in self.xylandscapes]

    def vna_frequency_wrapper(self, x_set_obj):
        """
        Function wraps the x_set_obj function for a landscape_xy scan such that the vna frequencies are automatically
        adjusted
        :param x_set_obj: as given by the user
        :return: the wrapped function
        """
        def vna_wrapper(x):
            start_freq = self.xz_freqpoints[np.argmin(np.abs(self.xz_freqpoints -
                                                             (self.xzlandscape_func(x)-self.z_span/2)))]
            self.vna.set_startfreq(start_freq)
            self.vna.set_stopfreq(start_freq + self.z_span)
            x_set_obj(x)
        return vna_wrapper

    def perform_measurement_at_point(self, x, y, ix):
        """
        Looks if the point is of interest and returns True or False
        :param x: point in the x-vector
        :param y: point in the y-vector
        :param ix: index of x-vector
        :return: measure_bool, whether or not the point should be measured
        """
        # looks strange but works
        measure = False
        for e in self.xylandscapes:
            if np.abs(e['center_points'][ix] - y) <= e['y_span'] / 2 \
            and e['x_range'][0] <= x <= e['x_range'][1]:  # The point is covered by this span
                if e['blacklist']:
                    return False  # if the point is blacklisted anywhere, we don't need to look further
                else:
                    measure = True
        return measure

    def get_tracedata_xz(self, x):
        """
        Function to fill the tracedata with NaNs outside the scan region
        :param x: x_value where we perform the scan
        :return:
        """
        amp = np.full_like(self.xz_freqpoints, np.NaN, dtype=np.float16)
        pha = np.full_like(self.xz_freqpoints, np.NaN, dtype=np.float16)
        startarg = np.argmin(np.abs(self.xz_freqpoints-(self.xzlandscape_func(x)-self.z_span/2)))
        stoparg = startarg+ self.vna.get_nop()
        a, p = self.vna.get_tracedata()
        amp[startarg:stoparg] = a
        pha[startarg:stoparg] = p
        return amp, pha

    def get_freqpoints_xz(self):
        return self.xz_freqpoints

    def f_parab(self, x, a, b, c):
        return a * (x - b) ** 2 + c

    def f_hyp(self, x, a, b, c):
        "hyperbolic function with the form y = sqrt[ a*(x-b)**2 + c ]"
        return np.sqrt(a * (x - b) ** 2 + c)

    def f_lin(self, x, a, b):
        return a * x + b

    def f_transmon(self, x, w_max, L, I_ext, djj):
        """
        Dispersion of a tunable transmon qubit with junction asymmetry.

        Args:
            x:     x-value
            w_max:    Maximum qubit frequency without detuning.
            L:     Oscillation period in current/x-value.
            I_ext: Offset current/x offset.
            djj:   Josephson junction asymmetry (Ic1 - Ic2)/(Ic1 + Ic2)

        Returns:
            Primal transition frequency of a transmon qubit.
        """
        return w_max * (np.abs(np.cos(np.pi / L * (x - I_ext))) * (
                1 + djj ** 2 * np.tan(np.pi / L * (x - I_ext)) ** 2) ** .5) ** 0.5
