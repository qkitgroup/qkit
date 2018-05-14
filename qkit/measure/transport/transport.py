# transport.py  measurement class for IV like transport measurements
# MMW/HR@KIT 11/2017

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
#import matplotlib.pylab as plt
#from scipy.optimize import curve_fit
from time import sleep
import sys
import qt
import threading

import qkit
from qkit.storage import store as hdf
#from qkit.analysis.IV_curve import IV_curve
from qkit.gui.plot import plot as qviewkit
from qkit.gui.notebook.Progress_Bar import Progress_Bar
from qkit.measure.measurement_class import Measurement 
import qkit.measure.write_additional_files as waf

##################################################################

class transport(object):
    '''
    usage:
        tr = transport.transport(IV_Device = IVD)
        tr.set_dVdI(<bool>)
        tr.sweep.reset_sweeps()
        tr.add_sweep_4quadrants(start=<start>, stop=<stop>, step=<step>, offset=<offset>)
        tr.measure_XD()
    '''
    
    def __init__(self, IV_Device, exp_name = '', sample = None):
        '''
        Initializes the class for transport measurement such as IV characteristics.
        
        Input:
            IV_Device (str)
            exp_name (str): Experiment name used as suffix of <file_name>
            sample (...): ... used for measurement object
        Output:
            None
        '''
        ## Input variables
        self.IVD = IV_Device
        self.exp_name = exp_name
        self._sample = sample
        ## data file setting default values
        self.comment = ''
        self.dirname = None
        self._measurement_object = Measurement()
        self._measurement_object.measurement_type = 'transport'
        self._measurement_object.sample = self._sample
        self._web_visible = True
        ## measurement services
        self.progress_bar = True
        self.open_qviewkit = True
        self._qvk_process = False  # qviewkit process
        self._plot_comment = ''
        ## measurement setting default values
        self.sweep = self.sweeps()  # calls sweep subclass
        self._dVdI = False  # adds dV/dI data series, views, ...
        self.set_log_function()
        # 2D & 3D scan variables
        self.x_set_obj = None
        self.y_set_obj = None
        self._tdx = 2e-3  # (s)
        self._tdy = 2e-3  # (s)
        self.set_log_function()
        
        
    def add_sweep_4quadrants(self, start, stop, step, offset=0):
        '''
        Adds a four quadrants sweep series with the pattern
            0th: +start -> +stop,  step
            1st: +stop  -> +start, step
            2nd: +start -> -stop,  step
            3rd: -stop  -> +start, step
        
        Input:
            start (float): Start value of sweep
            stop  (float): Stop value of sweep
            step  (float): Step value of sweep
        Output:
            None
        '''
        self.sweep.add_sweep(start+offset, +stop+offset, step)
        self.sweep.add_sweep(+stop+offset, start+offset, step)
        self.sweep.add_sweep(start+offset, -stop+offset, step)
        self.sweep.add_sweep(-stop+offset, start+offset, step)
    
    
    def set_dVdI(self, status=True):
        '''
        Sets the dVdI parameter for the transport class, meaning weather differential resistance is calculated or not
        
        Input:
            status (bool)
        Output:
            None
        '''
        self._dVdI = status
        return
    
    
    def get_dVdI(self):
        '''
        Gets the dVdI parameter for the transport class, meaning weather differential resistance is calculated or not
        
        Input:
            None
        Output:
            status (bool)
        '''
        return self._dVdI
    
    
    def set_x_parameters(self, x_vec, x_coordname, x_set_obj, x_unit=""):
        '''
        Sets x-parameters for 2D and 3D scan.
        In a 3D measurement, the x-parameters will be the "outer" sweep meaning for every x value all y values are swept and for each (x,y) value the bias is swept according to the set sweep parameters.
        
        Input:
            x_vec (array): contains the sweeping values
            x_coordname (string)
            x_instrument (obj): callable object to execute with x_vec-values
            x_unit (string): optional
        Output:
            None
        '''
        self.x_vec = x_vec
        self.x_coordname = x_coordname
        self.x_set_obj = x_set_obj
        # self.delete_fit_function()
        self.x_unit = x_unit
        return
    
    
    def set_tdx(self, val):
        '''
        Sets sleep time between x-iterations in 2D and 3D scans.
        
        Input:
            val (float)
        Output:
            None
        '''
        self._tdx = val
        return
    
    
    def get_tdx(self):
        '''
        Gets sleep time between x-iterations in 2D and 3D scans.
        
        Input:
            None
        Output:
            val (float)
        '''
        return self._tdx
    
    
    def set_y_parameters(self, y_vec, y_coordname, y_set_obj, y_unit=""):
        '''
        Sets x-parameters for 3D scan, where y-parameters will be the "inner" sweep meaning for every x value all y values are swept and for each (x,y) value the bias is swept according to the set sweep parameters.
        
        Input:
            y_vec (array): contains the sweeping values
            y_coordname (string)
            y_instrument (obj): callable object to execute with x_vec-values
            y_unit (string): optional
        Output:
            None
        '''
        self.y_vec = y_vec
        self.y_coordname = y_coordname
        self.y_set_obj = y_set_obj
        # self.delete_fit_function()
        self.y_unit = y_unit
        return
    
    
    def set_tdy(self, val):
        '''
        Sets sleep time between y-iterations in 3D scans.
        
        Input:
            val (float)
        Output:
            None
        '''
        self._tdy = val
        return
    
    
    def get_tdy(self):
        '''
        Gets sleep time between y-iterations in 3D scans.
        
        Input:
            None
        Output:
            val (float)
        '''
        return self._tdy
    
    
    def set_log_function(self, func=None, name=None, unit=None, log_dtype=None):
        '''
        Saves desired values obtained by a function <func> in the .h5-file as a value vector with name <name>, unit <unit> and in data format <f>.
        The function (object) can be passed to the measurement loop which is executed before every x iteration
        but after executing the x_object setter in 2D measurements and before every line (but after setting 
        the x value) in 3D measurements.
        The return value of the function of type float or similar is stored in a value vector in the h5 file.
        
        Input:
            func list(function): function that returns the value to be saved
            name (str): name of logging parameter appearing in h5 file, default: 'log_param'
            unit (str): unit of logging parameter, default: ''
            log_dtype (f): h5 data type, default: 'f' (float32)
        Output:
            None
        '''
        if name is None:
            try:
                name = ['log_param']*len(func)
            except Exception:
                name = None
        if unit is None:
            try:
                unit = ['']*len(func)
            except Exception:
                unit = None
        if log_dtype is None:
            try:
                log_dtype = ['f']*len(func)
            except Exception:
                log_dtype = None
        
        self.log_function = []
        self.log_name = []
        self.log_unit = []
        self.log_dtype = []
        
        if func is not None:
            for i, f in enumerate(func):
                self.log_function.append(f)
                self.log_name.append(name[i])
                self.log_unit.append(unit[i])
                self.log_dtype.append(log_dtype[i])
        return
    
    
    def get_log_function(self):
        '''
        Gets the current log_function settings.
        
        Input:
            None
        Output:
            log_function (dict): {'func': function names
                                  'name': parameter names
                                  'unit': units
                                  'log_dtype': datatypes}
        '''
        return {'func': [f.__name__ for f in self.log_function],
                'name': self.log_name,
                'unit': self.log_unit,
                'log_dtype': self.log_dtype}
    
    
    def reset_log_function(self):
        '''
        Resets all log_function settings.
        
        Input:
            None
        Output:
            None
            '''
        self.log_function = []
        self.log_name = []
        self.log_unit = []
        self.log_dtype = []
        return
    
    
    def _prepare_measurement_IVD(self):
        '''
        All the relevant settings from the IVD are updated and called
        
        Input:
            None
        Output:
            None
        '''
        self._sweep_mode = self.IVD.get_sweep_mode()                            # 0 (VV-mode) | 1 (IV-mode) | 2 (VI-mode)
        self._pseudo_bias_mode = self.IVD.get_pseudo_bias_mode()                # 0 (current bias) | 1 (voltage bias)
        self._bias = self.IVD.get_bias()                                        # 0 (current bias) | 1 (voltage bias)
        self._IV_modes = {0: 'I', 1: 'V'}
        self._IV_units = {0: 'A', 1: 'V'}
        return
    
    
    def _prepare_measurement_file(self):
        '''
        Creates the output .h5-file with distinct dataset structures for each measurement type.
        At this point all measurement parameters are known and put in the output file
        
        Input:
            None
        Output:
            None
        '''
        print ('filename '+self._file_name)
        self._data_file                      = hdf.Data(name=self._file_name, mode='a')
        self._measurement_object.uuid        = self._data_file._uuid
        self._measurement_object.hdf_relpath = self._data_file._relpath
        self._measurement_object.instruments = qt.instruments.get_instruments()
        self._measurement_object.save()
        self._mo = self._data_file.add_textlist('measurement')
        self._mo.append(self._measurement_object.get_JSON())

        # write logfile and instrument settings
        ### FIXME: log_file???
        self._write_settings_dataset()
        #self._log = waf.open_log_file(self._data_file.get_filepath())

        # data variables
        self._data_bias = []
        self._data_I = []
        self._data_V = []
        if self._dVdI:
            self._data_dVdI = []
        
        ### 1D scan 
        if self._scan_1D:
            ## add data variables
            self.sweep._create_iterator()
            for i in range(self.sweep.get_nos()):
                self._data_bias.append(self._data_file.add_coordinate('{:s}_b_{!s}'.format(self._IV_modes[self._bias], i), unit=self._IV_units[self._bias]))
                self._data_bias[i].add(self._get_bias_values(sweep=self.sweep.get_sweep()))
                self._data_I.append(self._data_file.add_value_vector('I_{!s}'.format(i), x=self._data_bias[i], unit='A', save_timestamp=False))
                self._data_V.append(self._data_file.add_value_vector('V_{!s}'.format(i), x=self._data_bias[i], unit='V', save_timestamp=False))
                if self._dVdI:
                    self._data_dVdI.append(self._data_file.add_value_vector('dVdI_{!s}'.format(i), x=self._data_bias[i], unit='V/A', save_timestamp=False))
            ## add views
            self._add_views()
        
        ### 2D scan
        if self._scan_2D:
            self._data_x = self._data_file.add_coordinate(self.x_coordname, unit=self.x_unit)
            self._data_x.add(self.x_vec)
            ## add data variables
            self.sweep._create_iterator()
            for i in range(self.sweep.get_nos()):
                self._data_bias.append(self._data_file.add_coordinate('{:s}_b_{!s}'.format(self._IV_modes[self._bias], i), unit=self._IV_units[self._bias]))
                self._data_bias[i].add(self._get_bias_values(sweep=self.sweep.get_sweep()))
                self._data_I.append(self._data_file.add_value_matrix('I_{!s}'.format(i), x=self._data_x, y=self._data_bias[i], unit='A', save_timestamp=False))
                self._data_V.append(self._data_file.add_value_matrix('V_{!s}'.format(i), x=self._data_x, y=self._data_bias[i], unit='V', save_timestamp=False))
                if self._dVdI:
                    self._data_dVdI.append(self._data_file.add_value_matrix('dVdI_{!s}'.format(i), x=self._data_x, y=self._data_bias[i], unit='V/A', save_timestamp=False))
            ## Logfunction
            self._add_log_value_vector()
            ## add views
            self._add_views()
        
        ### 3D scan
        if self._scan_3D:
            self._data_x = self._data_file.add_coordinate(self.x_coordname, unit=self.x_unit)
            self._data_x.add(self.x_vec)
            self._data_y = self._data_file.add_coordinate(self.y_coordname, unit=self.y_unit)
            self._data_y.add(self.y_vec)
            ## add data variables
            self.sweep._create_iterator()
            for i in range(self.sweep.get_nos()):
                self._data_bias.append(self._data_file.add_coordinate('{:s}_b_{!s}'.format(self._IV_modes[self._bias], i), unit=self._IV_units[self._bias]))
                self._data_bias[i].add(self._get_bias_values(sweep=self.sweep.get_sweep()))
                self._data_I.append(self._data_file.add_value_box('I_{!s}'.format(i), x=self._data_x, y=self._data_y, z=self._data_bias[i], unit='A', save_timestamp=False))
                self._data_V.append(self._data_file.add_value_box('V_{!s}'.format(i), x=self._data_x, y=self._data_y, z=self._data_bias[i], unit='V', save_timestamp=False))
                if self._dVdI:
                    self._data_dVdI.append(self._data_file.add_value_box('dVdI_{!s}'.format(i), x=self._data_x, y=self._data_y, z=self._data_bias[i], unit='V/A', save_timestamp=False))
            ## Logfunction
            self._add_log_value_vector()
            ## add views
            self._add_views()
        ### add comment
        if self.comment:
            self._data_file.add_comment(self.comment)
        return
    
    
    def _get_bias_values(self, sweep):
        '''
        Gets a linear distributed numpy-array of set bias values
        
        Input:
            sweep obj(float) : start, stop, step
        Output
            bias_values (numpy.array)
        '''
        start = float(sweep[0])
        stop = float(sweep[1])
        step = float(sweep[2])
        step_signed = np.sign(stop-start)*np.abs(step)
        return np.arange(start, stop+step_signed/2., step_signed)
    
    
    def _add_log_value_vector(self):
        '''
        Adds all value vectors for log-function parameter.
        
        Input:
            None
        Output:
            None
        '''
        if self.log_function is not None:
            self._log_values = []
            for i in range(len(self.log_function)):
                self._log_values.append(self._data_file.add_value_vector(self.log_name[i], x=self._data_x, unit=self.log_unit[i], dtype=self.log_dtype[i]))
        return
    
    
    def _add_views(self):
        '''
        Adds views to the .h5-file.
        The view "IV" plots I(V) and contains the whole set of sweeps that are set.
        If <dVdI> is true, the view "dVdI" plots the differential gradient dV/dI(V) and contains the whole set of sweeps that are set.
        
        Input:
            None
        Output:
            None
        '''
        IV = self._data_file.add_view('IV', x=self._data_V[0], y=self._data_I[0])
        for i in range(1, self.sweep.get_nos()):
            IV.add(x=self._data_V[i], y=self._data_I[i])
        if self._dVdI:
            dVdI = self._data_file.add_view('dVdI', x=self._data_I[0], y=self._data_dVdI[0])
            for i in range(1, self.sweep.get_nos()):
                dVdI.add(x=eval('self._data_{:s}'.format(self._IV_modes[self._bias]))[i], y=self._data_dVdI[i])
        return
    
    
    def _write_settings_dataset(self):
        '''
        Writes settings both in extra .set-file and in "settings" entry in data
        
        Input:
            None
        Output:
            None
        '''
        self._settings = self._data_file.add_textlist('settings')
        settings = waf.get_instrument_settings(self._data_file.get_filepath())
        self._settings.append(settings)
        return
    
    
    def measure_1D(self, web_visible=True, **kwargs):
        '''
        Measure method to record a 1 dimensional set of IV curves while sweeping bias according to the set sweep parameters. 
        Every single data point is taken with the current IV Device settings.
        
        Input:
            web_visible (bool)
            **kwargs          : channel_bias (int)  : 1 (default) | 2 for VV-mode
                                channel_sense (int) : 1 | 2 (default) for VV-mode
                                channel (int)       : 1 (default) | 2 for IV-mode or VI-mode
                                iReadingBuffer (str): for Keithley 2636A only
                                vReadingBuffer (str): for Keithley 2636A only
        Output:
            None
        '''
        self._scan_1D = True
        self._scan_2D = False
        self._scan_3D = False
        
        ## measurement object
        self._measurement_object.measurement_func = sys._getframe().f_code.co_name
        self._measurement_object.x_axis = 'voltage'
        self._measurement_object.y_axis = ''
        self._measurement_object.z_axis = ''
        self._measurement_object.web_visible = web_visible
        
        if not self.dirname:
            self.dirname = 'IVD_tracedata'
        self._file_name = self.dirname.replace(' ', '').replace(',','_')
        if self.exp_name:
            self._file_name += '_' + self.exp_name
        
        ## progress bar
        if self.progress_bar:
            self._pb = Progress_Bar(max_it=self.sweep.get_nos(), name='1D IVD sweep ' + self.dirname)

        ## prepare storage
        self._prepare_measurement_IVD()
        self._prepare_measurement_file()
        
        '''opens qviewkit to plot measurement, sense values are opened by default'''
        if self.open_qviewkit:
            self._qvk_process = qviewkit.plot(self._data_file.get_filepath())#, datasets=['{:s}_{:d}'.format(self._IV_modes[not(self._bias)].lower(), i) for i in range(self.sweep.get_nos())])
        print('recording trace...')

        ## measurement
        sys.stdout.flush()
        qt.mstart()
        
        # turn on IVD
        if self.IVD.get_sweep_mode() == 0:
            self._channel_bias  = kwargs.get('channel_bias', 1)
            self._channel_sense = kwargs.get('channel_sense', 2)
            self.IVD.set_stati(status=True)
        elif self.IVD.get_sweep_mode() in [1, 2]:
            self._channel  = kwargs.get('channel', 1)
            self.IVD.set_status(status=True, channel=self._channel)
        # interate sweeps
        self.sweep._create_iterator()
        for i in range(self.sweep.get_nos()):
            # take data
            I_values, V_values = self.IVD.take_IV(sweep=self.sweep.get_sweep(), **kwargs)
            self._data_I[i].append(I_values)
            self._data_V[i].append(V_values)
            if self._dVdI:
                self._data_dVdI[i].append(np.array(np.gradient(V_values))/np.array(np.gradient(I_values)))
            # progress bar
            if self.progress_bar:
                self._pb.iterate()
            qt.msleep()
        # turn off IVD
        if self.IVD.get_sweep_mode() == 0:
            self.IVD.set_stati(status=False)
        elif self.IVD.get_sweep_mode() in [1, 2]:
            self.IVD.set_status(status=False, channel=self._channel)
        # end measurement
        qt.mend()
        self._end_measurement()
    
    
    def measure_2D(self, web_visible=True, **kwargs):
        '''
        Measure method to record a 2 dimensional set of IV curves while sweeping
        bias according to the set sweep parameters and all parameters x_vec in x_obj.
        Every single data point is taken with the current IV Device settings.
        
        Input:
            web_visible (bool):
            **kwargs          : channel_bias (int)  : 1 (default) | 2 for VV-mode
                                channel_sense (int) : 1 | 2 (default) for VV-mode
                                channel (int)       : 1 (default) | 2 for IV-mode or VI-mode
                                iReadingBuffer (str): for Keithley 2636A only
                                vReadingBuffer (str): for Keithley 2636A only
        Output:
            None
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

        ## progress bar
        if self.progress_bar:
            self._pb = Progress_Bar(max_it=len(self.x_vec)*self.sweep.get_nos(), name='2D IVD sweep ' + self.dirname)

        ## prepare storage
        self._prepare_measurement_IVD()
        self._prepare_measurement_file()
        
        ## measurement object
        self._measurement_object.measurement_func = sys._getframe().f_code.co_name
        self._measurement_object.x_axis = self.x_coordname
        self._measurement_object.y_axis = 'current' # or self._IV_modes[self._bias]
        self._measurement_object.z_axis = ''
        self._measurement_object.web_visible = self._web_visible

        ## open qviewkit to plot measurement, sense values are opened by default
        if self.open_qviewkit:
            self._qvk_process = qviewkit.plot(self._data_file.get_filepath())#, datasets=['{:s}_{:d}'.format(self._IV_modes[not self._bias].lower(), i) for i in range(self.sweep.get_nos())])

        ## measurement
        self._measure(**kwargs)
        return
    
    
    def measure_3D(self, web_visible=True, **kwargs):
        '''
        Measure method to record a 3 dimensional set of IV curves while sweeping bias according to the set sweep parameters, all parameters x_vec in x_obj and all parameters y_vec in y_obj.
        The sweep over y_obj is the inner loop, for every value x_vec[i] all values y_vec are measured.
        Every single data point is taken with the current IV Device settings.
        
        Input:
            web_visible (bool):
            **kwargs          : channel_bias (int)  : 1 (default) | 2 for VV-mode
                                channel_sense (int) : 1 | 2 (default) for VV-mode
                                channel (int)       : 1 (default) | 2 for IV-mode or VI-mode
                                iReadingBuffer (str): for Keithley 2636A only
                                vReadingBuffer (str): for Keithley 2636A only
        Output:
            None
        '''
        ### TODO: landscape scan
        if not self.x_set_obj or not self.y_set_obj:
            logging.error('axes parameters not properly set...aborting')
            return
        self._scan_1D = False
        self._scan_2D = False
        self._scan_3D = True

        self._measurement_object.measurement_func = sys._getframe().f_code.co_name
        self._measurement_object.x_axis = self.x_coordname.replace(' ', '_')
        self._measurement_object.y_axis = self.y_coordname.replace(' ', '_')
        self._measurement_object.z_axis = 'current' # or self._IV_modes[self._bias]
        self._measurement_object.web_visible = web_visible

        if not self.dirname:
            self.dirname = self.x_coordname + ', ' + self.y_coordname
        self._file_name = '3D_' + self.dirname.replace(' ', '').replace(',', '_')
        if self.exp_name:
            self._file_name += '_' + self.exp_name

        ## progress bar
        if self.progress_bar:
            self._pb = Progress_Bar(max_it=len(self.x_vec)*len(self.y_vec)*self.sweep.get_nos(), name='3D IVD sweep ' + self.dirname)
        
        ## prepare storage
        self._prepare_measurement_IVD()
        self._prepare_measurement_file()
        
        ## opens qviewkit to plot measurement, sense values are opened by default
        if self.open_qviewkit:
            self._qvk_process = qviewkit.plot(self._data_file.get_filepath())#, datasets=['{:s}_{:d}'.format(self._IV_modes[not self._bias].lower(), i) for i in range(self.sweep.get_nos())])

        ## measurement
        self._measure(**kwargs)
        return
    
    
    def _measure(self, **kwargs):
        '''
        measures and plots the data depending on the measurement type.
        the measurement loops feature the setting of the objects and saving the data in the .h5 file.
        
        Input:
            **kwargs: channel_bias (int)  : 1 (default) | 2 for VV-mode
                      channel_sense (int) : 1 | 2 (default) for VV-mode
                      channel (int)       : 1 (default) | 2 for IV-mode or VI-mode
                      iReadingBuffer (str): for Keithley 2636A only
                      vReadingBuffer (str): for Keithley 2636A only
        '''
        qt.mstart()
        try:
            # turn on IVD
            if self.IVD.get_sweep_mode() == 0:
                self._channel_bias  = kwargs.get('channel_bias', 1)
                self._channel_sense = kwargs.get('channel_sense', 2)
                self.IVD.set_stati(status=True)
            elif self.IVD.get_sweep_mode() in [1, 2]:
                self._channel  = kwargs.get('channel', 1)
                self.IVD.set_status(status=True, channel=self._channel)
            
            ## loop: x_obj with parameters from x_vec
            for ix, x in enumerate(self.x_vec):
                self.x_set_obj(x)
                sleep(self._tdx)
                
                ## log function
                if self.log_function is not None:
                    for i, f in enumerate(self.log_function):
                        self._log_values[i].append(float(f()))
                
                ## 3D scan
                if self._scan_3D:
                    ## loop: y_obj with parameters from y_vec (only 3D measurement)
                    for y in self.y_vec:
                        self.y_set_obj(y)
                        sleep(self._tdy)
                        ## measurement
                        self.sweep._create_iterator()
                        for i in range(self.sweep.get_nos()):
                            I_values, V_values = self.IVD.take_IV(sweep=self.sweep.get_sweep(), **kwargs)
                            self._data_I[i].append(I_values)
                            self._data_V[i].append(V_values)
                            if self._dVdI:
                                self._data_dVdI[i].append(np.array(np.gradient(V_values))/np.array(np.gradient(I_values)))
                            # progress bar
                            if self.progress_bar:
                                self._pb.iterate()
                            qt.msleep()
                    ## filling of value-box by storing data in the next 2d structure after every y-loop
                    for i in range(self.sweep.get_nos()):
                        self._data_I[i].next_matrix()
                        self._data_V[i].next_matrix()
                        if self._dVdI:
                            self._data_dVdI[i].next_matrix()
                
                # 2D scan
                if self._scan_2D:
                    ##  measurement
                    self.sweep._create_iterator()
                    for i in range(self.sweep.get_nos()):
                        I_values, V_values = self.IVD.take_IV(sweep=self.sweep.get_sweep(), **kwargs)
                        self._data_I[i].append(I_values)
                        self._data_V[i].append(V_values)
                        if self._dVdI:
                            self._data_dVdI[i].append(np.array(np.gradient(V_values))/np.array(np.gradient(I_values)))
                        # progress bar
                        if self.progress_bar:
                            self._pb.iterate()
                        qt.msleep()

        except Exception as e:
            print e.__doc__
            print e.message
        finally:
            self._end_measurement()
            # turn off IVD
            if self.IVD.get_sweep_mode() == 0:
                self.IVD.set_stati(status=False)
            elif self.IVD.get_sweep_mode() in [1, 2]:
                self.IVD.set_status(status=False, channel=self._channel)
            qt.mend()
        return
    
    
    def _end_measurement(self):
        '''
        the data file is closed and filepath is printed
        '''
        print self._data_file.get_filepath()
        t = threading.Thread(target=qviewkit.save_plots, args=[self._data_file.get_filepath(), self._plot_comment])
        t.start()
        self._data_file.close_file()
        qkit.store_db.add(self._data_file.get_filepath())
        # waf.close_log_file(self._log)
        self.dirname = None
        return
    
    
    def get_bias_values(self, sweep):
        '''
        Gets a linear distributed numpy-array of set bias values
        
        Input:
            sweep obj(float) : start, stop, step
        Output
            bias_values (numpy.array)
        '''
        start       = float(sweep[0])
        stop        = float(sweep[1])
        step        = float(sweep[2])
        step_signed = np.sign(stop-start)*np.abs(step)
        return np.arange(start, stop+step_signed/2., step_signed)
    
    
    def set_plot_comment(self, comment):
        '''
        Small comment to add at the end of plot pics for more information i.e. good for wiki entries.
        '''
        self._plot_comment=comment
    
    
    class sweeps(object):
        '''
        This is a subclass of <transport> that provides the customized usage of many sweeps in one measurement.
        
        Usage:
            tr.sweep.reset_sweeps()
        '''
        
        
        def __init__(self):
            '''
            Initializes the sweep parameters as empty.
            
            Input:
                None
            Output:
                None
            '''
            self._starts = []
            self._stops = []
            self._steps = []
            self._create_iterator()
            return
        
        
        def _create_iterator(self):
            '''
            Creates iterator of start, stop and step arrays.
            
            Input:
                None
            Output:
                None
            '''
            self._start_iter = iter(self._starts)
            self._stop_iter = iter(self._stops)
            self._step_iter = iter(self._steps)
            return
        
        
        def add_sweep(self, start, stop, step):
            '''
            Adds a sweep object with given parameters.
            
            Input:
                start (float): Start value of sweep
                stop  (float): Stop value of sweep
                step  (float): Step value of sweep
            '''
            self._starts.append(start)
            self._stops.append(stop)
            self._steps.append(step)
            return
        
        
        def reset_sweeps(self):
            '''
            Resets sweeps.
            
            Input:
                None
            Output:
                None
            '''
            self._starts = []
            self._stops = []
            self._steps = []
            return
        
        
        def get_sweep(self):
            '''
            Gets sweep parameter.
            
            Input:
                None
            Output:
                sweep obj(float) : start, stop, step
            '''
            return (self._start_iter.next(),
                    self._stop_iter.next(),
                    self._step_iter.next())
            
            
        def get_nos(self):
            '''
            Gets number of sweeps.
            
            Input:
                None
            Output:
                nos (int)
            '''
            return len(self._starts)