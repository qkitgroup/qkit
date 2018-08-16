# transport.py  measurement class for IV like transport measurements
# Hannes Rotzinger, hannes.rotzinger@kit.edu 2010
# Micha Wildermuth, micha.wildermuth@kit.edu 2017

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
from time import sleep
import sys
import qt
import threading

import qkit
from qkit.storage import store as hdf
from qkit.gui.plot import plot as qviewkit
from qkit.gui.notebook.Progress_Bar import Progress_Bar
from qkit.measure.measurement_class import Measurement 
import qkit.measure.write_additional_files as waf


class transport(object):
    '''
    usage:
        tr = transport.transport(IV_Device = IVD)
        tr.set_dVdI(<bool>)
        tr.sweep.reset_sweeps()
        tr.add_sweep_4quadrants(start=<start>, stop=<stop>, step=<step>, offset=<offset>)
        tr.measure_XD()
    '''
    
    def __init__(self, IV_Device, sample=None, **kwargs):
        '''
        Initializes the class for transport measurement such as IV characteristics.
        
        Input:
            IV_Device (str): Source measure unit that takes IV data
            sample (object): sample object of measurement_class used for measurement object
            **kwargs: filename (str): file name used as suffix of uuid
                      expname (str): experiment name used as suffix of uuid and <filename>
                      comment (str): comment added to data in .h5 file
        Output:
            None
        '''
        # Input variables
        self._IVD = IV_Device
        self._sample = sample
        # data file setting default values
        self._filename = kwargs.get('filename', None)
        self._expname = kwargs.get('expname', None)
        self._comment = kwargs.get('comment', None)
        self._measurement_object = Measurement()
        self._measurement_object.measurement_type = 'transport'
        self._measurement_object.sample = self._sample
        self._web_visible = True
        # measurement services
        self.progress_bar = True
        self.open_qviewkit = True
        self._qvk_process = False  # qviewkit process
        self._plot_comment = ''
        # measurement setting default values
        self.sweeps = self.sweep()  # calls sweep subclass
        self._dVdI = False  # adds dV/dI data series, views, ...
        self._average = None
        self.set_log_function()
        # xy, 2D & 3D scan variables
        self._x_name = ''
        self._y_name = ''
        self._scan_dim = None
        self._x_dt = 2e-3  # in s
        self._x_vec = [None]
        self._x_coordname = None
        self._x_set_obj = None
        self._x_unit = None
        self._tdy = 2e-3  # in s
        self._y_vec = [None]
        self._y_coordname = None
        self._y_set_obj = None
        self._y_unit = None

    def add_sweep_4quadrants(self, start, stop, step, offset=0):
        '''
        Adds a four quadrants sweep series with the pattern 
            0th: (+start -> +stop,  step)+offset
            1st: (+stop  -> +start, step)+offset
            2nd: (+start -> -stop,  step)+offset
            3rd: (-stop  -> +start, step)+offset
        
        Input:
            start (float): Start value of sweep
            stop (float): Stop value of sweep
            step (float): Step value of sweep
            offset (float): Offset value by which <start> and <stop> are shifted
        Output:
            None
        '''
        self.sweeps.add_sweep(start+offset, +stop+offset, step)
        self.sweeps.add_sweep(+stop+offset, start+offset, step)
        self.sweeps.add_sweep(start+offset, -stop+offset, step)
        self.sweeps.add_sweep(-stop+offset, start+offset, step)

    def set_dVdI(self, status=True):
        '''
        Sets the internal dVdI parameter, to decide weather the differential resistance (dV/dI) is calculated or not
        
        Input:
            status (bool): determines if numerical gradient is calculated and stored in an own data_vector
        Output:
            None
        '''
        self._dVdI = status
        return

    def get_dVdI(self):
        '''
        Gets the internal dVdI parameter, to decide weather the differential resistance (dV/dI) is calculated or not
        
        Input:
            None
        Output:
            status (bool): determines if numerical gradient is calculated and stored in an own data_vector
        '''
        return self._dVdI

    def set_x_dt(self, val):
        '''
        Sets sleep time between x-iterations in 2D and 3D scans.
        
        Input:
            val (float): sleep time between x-iterations
        Output:
            None
        '''
        self._x_dt = val
        return

    def get_x_dt(self):
        '''
        Gets sleep time between x-iterations in 2D and 3D scans.
        
        Input:
            None
        Output:
            val (float): sleep time between x-iterations
        '''
        return self._x_dt

    def set_x_parameters(self, x_vec, x_coordname, x_set_obj, x_unit='', x_dt=None):
        '''
        Sets x-parameters for 2D and 3D scan.
        In a 3D measurement, the x-parameters will be the "outer" sweep meaning for every x value all y values are swept and for each (x,y) value the bias is swept according to the set sweep parameters.
        
        Input:
            x_vec (array): contains the sweeping values
            x_coordname (string)
            x_set_obj (obj): callable object to execute with x_vec-values
            x_unit (string): optional
            x_dt (float): sleep time between x-iterations
        Output:
            None
        '''
        # x-vec
        if hasattr(x_vec, '__len__'):
            for val in x_vec:
                if not str(val).isdigit():
                    raise TypeError('{:s}: Cannot set {!s} as x-vector: {!s} is no number'.format(__name__, x_vec, val))
            self._x_vec = x_vec
        else:
            raise TypeError('{:s}: Cannot set {!s} as x-vector: iterable object needed'.format(__name__, x_vec))
        # x-coordname
        if type(x_coordname) is str:
            self._x_coordname = x_coordname
        else:
            raise ValueError('{:s}: Cannot set {!s} as x-coordname: string needed'.format(__name__, x_coordname))
        # x-set-object
        if callable(x_set_obj):
            self._x_set_obj = x_set_obj
        else:
            raise ValueError('{:s}: Cannot set {!s} as x-set-object: callable object needed'.format(__name__, x_set_obj))
        # x-unit
        if type(x_unit) is str:
            self._x_unit = x_unit
        else:
            raise ValueError('{:s}: Cannot set {!s} as x-unit: string needed'.format(__name__, x_unit))
        # x dt
        if x_dt is not None: self._x_dt = x_dt
        return

    def set_tdy(self, val):
        '''
        Sets sleep time between y-iterations in 3D scans.
        
        Input:
            val (float): sleep time between y-iterations
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
            val (float): sleep time between y-iterations
        '''
        return self._tdy

    def set_y_parameters(self, y_vec, y_coordname, y_set_obj, y_unit='', y_dt=None):
        '''
        Sets x-parameters for 3D scan, where y-parameters will be the "inner" sweep meaning for every x value all y values are swept and for each (x,y) value the bias is swept according to the set sweep parameters.
        
        Input:
            y_vec (array): contains the sweeping values
            y_coordname (string)
            y_instrument (obj): callable object to execute with x_vec-values
            y_unit (string): optional
            y_dt (float): sleep time between y-iterations
        Output:
            None
        '''
        # y-vec
        if hasattr(y_vec, '__len__'):
            for val in y_vec:
                if not str(val).isdigit():
                    raise TypeError('{:s}: Cannot set {!s} as y-vector: {!s} is no number'.format(__name__, y_vec, val))
            self._y_vec = y_vec
        else:
            raise TypeError('{:s}: Cannot set {!s} as y-vector: iterable object needed'.format(__name__, y_vec))
        # y-coordname
        if type(y_coordname) is str:
            self._y_coordname = y_coordname
        else:
            raise ValueError('{:s}: Cannot set {!s} as y-coordname: string needed'.format(__name__, y_coordname))
        # y-set-object
        if callable(y_set_obj):
            self._y_set_obj = y_set_obj
        else:
            raise ValueError('{:s}: Cannot set {!s} as y-set-object: callable object needed'.format(__name__, y_set_obj))
        # y-unit
        if type(y_unit) is str:
            self._y_unit = y_unit
        else:
            raise ValueError('{:s}: Cannot set {!s} as y-unit: string needed'.format(__name__, y_unit))
        # y dt
        if y_dt is not None: self._y_dt = y_dt
        return

    def set_xy_parameters(self, x_name, x_func, x_vec, x_unit, y_name, y_func, y_unit, x_dt=1e-3):
        '''
        Set x- and y-parameters for measure_xy(), where y-parameters can be a list in order to record various quantities.
        
        Input:
            x_name (str): name of x-parameter
            x_func (function): function that returns x-values
            x_vec (list(float)): array of x-values at which data should be taken
            x_unit (str): unit of x-parameter
            y_name (list(str)): name of y-parameter
            y_func (function): function that returns y-values
            y_unit (str): unit of x-parameter
            x_dt (float): sleep time between queries of x-values: 1e-3 (default)
        Output:
            None
        '''
        # x-name
        if type(x_name) is str:
            self._x_name = x_name
        else:
            raise ValueError('{:s}: Cannot set {!s} as x-name: string needed'.format(__name__, x_name))
        # x-func
        if callable(x_func):
            self._x_func = x_func
        else:
            raise ValueError('{:s}: Cannot set {!s} as x-function: callable object needed'.format(__name__, x_func))
        # x-vec
        if hasattr(x_vec, '__len__'):
            self._x_vec = x_vec
        else:
            raise ValueError('{:s}: Cannot set {!s} as x-vector: iterable object needed'.format(__name__, x_vec))
        # x-unit
        if type(x_unit) is str:
            self._x_unit = x_unit
        else:
            raise ValueError('{:s}: Cannot set {!s} as x-unit: string needed'.format(__name__, x_unit))
        # y-name
        if type(y_name) is str:
            self._y_name = [y_name]
        elif hasattr(y_name, '__len__'):
            for name in y_name:
                if type(name) is not str:
                    raise ValueError('{:s}: Cannot set {!s} as y-name: string needed'.format(__name__, name))
            self._y_name = y_name
        else:
            raise ValueError('{:s}: Cannot set {!s} as y-name: string of iterable object of strings needed'.format(__name__, y_name))
        # y-func
        if callable(y_func):
            self._y_func = [y_func]
        elif hasattr(y_func, '__len__'):
            for func in y_func:
                if not callable(func):
                    raise ValueError('{:s}: Cannot set {!s} as y-function: callable object needed'.format(__name__, func))
            self._y_func = y_func
        else:
            raise ValueError('{:s}: Cannot set {!s} as y-function: callable object of iterable object of callable objects needed'.format(__name__, y_func))
        # y-unit
        if type(y_unit) is str:
            self._y_unit = [y_unit]
        elif hasattr(y_unit, '__len__'):
            for unit in y_unit:
                if type(unit) is not str:
                    raise ValueError('{:s}: Cannot set {!s} as y-unit: string needed'.format(__name__, unit))
            self._y_unit = y_unit
        else:
            raise ValueError('{:s}: Cannot set {!s} as y-unit: string of iterable object of strings needed'.format(__name__, y_unit))
        # x-dt
        self._x_dt = x_dt
        return

    def set_log_function(self, func=None, name=None, unit=None, dtype=float):
        '''
        Saves desired values obtained by a function <func> in the .h5-file as a value vector with name <name>, unit <unit> and in data format <f>.
        The function (object) can be passed to the measurement loop which is executed before every x iteration
        but after executing the x_object setter in 2D measurements and before every line (but after setting 
        the x value) in 3D measurements.
        The return value of the function of type float or similar is stored in a value vector in the h5 file.
        
        Input:
            func (list(function)): function that returns the value to be saved
            name (list(str)): name of logging parameter appearing in h5 file, default: 'log_param'
            unit (list(str)): unit of logging parameter, default: ''
            dtype (list(dtype) or list(float)): h5 data type, default: float (float64)
        Output:
            None
        '''
        # log-function
        if callable(func):
            func = [func]
        elif func is None:
            func = [None]
        elif hasattr(func, '__len__'):
            for fun in func:
                if not callable(fun):
                    raise ValueError('{:s}: Cannot set {!s} as y-function: callable object needed'.format(__name__, fun))
        else:
            raise ValueError('{:s}: Cannot set {!s} as log-function: callable object of iterable object of callable objects needed'.format(__name__, func))
        self.log_function = [val for val in func]
        # log-name
        if name is None:
            try:
                name = ['log_param']*len(func)
            except Exception:
                name = [None]
        elif type(name) is str:
            name = [name]*len(func)
        elif hasattr(name, '__len__'):
            for name in name:
                if type(name) is not str:
                    raise ValueError('{:s}: Cannot set {!s} as log-name: string needed'.format(__name__, name))
        else:
            raise ValueError('{:s}: Cannot set {!s} as log-name: string of iterable object of strings needed'.format(__name__, name))
        self.log_name = [val for val in name]
        # log-unit
        if unit is None:
            try:
                unit = ['log_unit']*len(func)
            except Exception:
                unit = [None]
        elif type(unit) is str:
            unit = [unit]*len(func)
        elif hasattr(unit, '__len__'):
            for unit in unit:
                if type(unit) is not str:
                    raise ValueError('{:s}: Cannot set {!s} as log-unit: string needed'.format(__name__, unit))
        else:
            raise ValueError('{:s}: Cannot set {!s} as log-unit: string of iterable object of strings needed'.format(__name__, unit))
        self.log_unit = [val for val in unit]
        # log-dtype
        if dtype is None:
            try:
                dtype = [float]*len(func)
            except Exception:
                dtype = [None]
        elif type(dtype) is type:
            dtype = [dtype]*len(func)
        elif hasattr(dtype, '__len__'):
            for _dtype in dtype:
                if type(_dtype) is not type:
                    raise ValueError('{:s}: Cannot set {!s} as log-dtype: string needed'.format(__name__, _dtype))
        else:
            raise ValueError('{:s}: Cannot set {!s} as log-dtype: string of iterable object of strings needed'.format(__name__, dtype))
        self.log_dtype = [val for val in dtype]
        return

    def get_log_function(self):
        '''
        Gets the current log_function settings.
        
        Input:
            None
        Output:
            log_function (dict): {'func': list(function names)
                                  'name': list(parameter names)
                                  'unit': list(units)
                                  'log_dtype': list(datatypes)}
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

    def set_filename(self, filename):
        '''
        Sets filename of current measurement to <filename>
        
        Input:
            filename (str): file name used as suffix of uuid
        Output:
            None
        '''
        self._filename = filename
        return

    def get_filename(self):
        '''
        Gets filename of current measurement
        
        Input:
            None
        Output:
            filename (str): file name used as suffix of uuid
        '''
        return self._filename

    def set_expname(self, expname):
        '''
        Sets experiment name of current measurement to <expname>
        
        Input:
            expname (str): experiment name used as suffix of uuid and <filename>
        Output:
            None
        '''
        self._expname = expname
        return

    def get_expname(self):
        '''
        Gets experiment name of current measurement
        
        Input:
            None
        Output:
            expname (str): experiment name used as suffix of uuid and <filename>
        '''
        return self._expname

    def set_comment(self, comment):
        '''
        Sets comment that is added to the .h5 file to <comment>
        
        Input:
            comment (str): comment added to data in .h5 file
        Output:
            None
        '''
        self._comment = comment
        return

    def get_comment(self):
        '''
        Gets comment that is added to the .h5 file
        
        Input:
            None
        Output:
            comment (str): comment added to data in .h5 file
        '''
        return self._comment

    def measure_xy(self, web_visible=True, **kwargs):
        '''
        Input:
            web_visible (bool): variable used for data base
            **kwargs: view: True | False (default) | list(tuple(y1 as x-axis, y2 as y-axis))
        Output:
            None
        '''
        self._scan_dim = 0
        
        ''' measurement object '''
        self._measurement_object.measurement_func = sys._getframe().f_code.co_name
        self._measurement_object.web_visible = web_visible
        
        ''' measurement '''
        self._measure(**kwargs)
        return
    
    def measure_1D(self, web_visible=True, average=None, **kwargs):
        '''
        Measures a 1 dimensional set of IV curves while sweeping the bias according to the set sweep parameters. 
        Every single data point is taken with the current IV Device settings.
        
        Input:
            web_visible (bool): variable used for data base
            average (int): averages whole traces: natural number | None (default)
            **kwargs: filename (str): file name used as suffix of uuid
                      expname (str): experiment name used as suffix of uuid and <filename>
                      comment (str): comment added to data in .h5 file
                      channel_bias (int): 1 (default) | 2 for VV-mode
                      channel_sense (int): 1 | 2 (default) for VV-mode
                      channel (int): 1 (default) | 2 for IV-mode or VI-mode
                      iReadingBuffer (str): only, if IVD supports (Keithley 2636A)
                      vReadingBuffer (str): only, if IVD supports (Keithley 2636A)
        Output:
            None
        '''
        self._scan_dim = 1
        self._average = average
        
        ''' measurement object '''
        self._measurement_object.measurement_func = sys._getframe().f_code.co_name
        self._measurement_object.web_visible = web_visible
        
        ''' measurement '''
        self._measure(**kwargs)
        return

    def measure_2D(self, web_visible=True, average=None, **kwargs):
        '''
        Measures a 2 dimensional set of IV curves while sweeping the bias according to the set sweep parameters and iterating all parameters x_vec in x_obj. 
        Every single data point is taken with the current IV Device settings.
        
        Input:
            web_visible (bool): variable used for data base
            average (int): averages whole traces: natural number | None (default)
            **kwargs: filename (str): file name used as suffix of uuid
                      expname (str): experiment name used as suffix of uuid and <filename>
                      comment (str): comment added to data in .h5 file
                      channel_bias (int): 1 (default) | 2 for VV-mode
                      channel_sense (int): 1 | 2 (default) for VV-mode
                      channel (int): 1 (default) | 2 for IV-mode or VI-mode
                      iReadingBuffer (str): only, if IVD supports (Keithley 2636A)
                      vReadingBuffer (str): only, if IVD supports (Keithley 2636A)
        Output:
            None
        '''
        if self._x_set_obj is None:
            logging.error('{:s}: axes parameters not properly set'.format(__name__))
            raise TypeError('{:s}: axes parameters not properly set'.format(__name__))
        
        self._scan_dim = 2
        self._average = average
        
        ''' measurement object '''
        self._measurement_object.measurement_func = sys._getframe().f_code.co_name
        self._measurement_object.web_visible = web_visible
        
        ''' measurement '''
        self._measure(**kwargs)
        return

    def measure_3D(self, web_visible=True, average=None, **kwargs):
        '''
        Measures a 3 dimensional set of IV curves while sweeping the bias according to the set sweep parameters and iterating all parameters x_vec in x_obj and all parameters y_vec in y_obj. The sweep over y_obj is the inner loop, for every value x_vec[i] all values y_vec are measured.
        Every single data point is taken with the current IV Device settings.
        
        Input:
            web_visible (bool): variable used for data base
            average (int): averages whole traces: natural number | None (default)
            **kwargs: filename (str): file name used as suffix of uuid
                      expname (str): experiment name used as suffix of uuid and <filename>
                      comment (str): comment added to data in .h5 file
                      channel_bias (int): 1 (default) | 2 for VV-mode
                      channel_sense (int): 1 | 2 (default) for VV-mode
                      channel (int): 1 (default) | 2 for IV-mode or VI-mode
                      iReadingBuffer (str): only, if IVD supports (Keithley 2636A)
                      vReadingBuffer (str): only, if IVD supports (Keithley 2636A)
        Output:
            None
        '''
        ### TODO: add landscape scan
        if self._x_set_obj is None or self._y_set_obj is None:
            logging.error('{:s}: axes parameters not properly set'.format(__name__))
            raise TypeError('{:s}: axes parameters not properly set'.format(__name__))
        
        self._scan_dim = 3
        self._average = average
        
        ''' measurement object '''
        self._measurement_object.measurement_func = sys._getframe().f_code.co_name
        self._measurement_object.web_visible = web_visible
        
        ''' measurement '''
        self._measure(**kwargs)
        return

    def _measure(self, **kwargs):
        '''
        Creates output files, measures according to IVD and sweep settings, stores data and shows them in the qviewkit
        
        Input:
            **kwargs: filename (str): file name used as suffix of uuid
                      expname (str): experiment name used as suffix of uuid and <filename>
                      comment (str): comment added to data in .h5 file
                      channel_bias (int): 1 (default) | 2 for VV-mode
                      channel_sense (int): 1 | 2 (default) for VV-mode
                      channel (int): 1 (default) | 2 for IV-mode or VI-mode
                      iReadingBuffer (str): only, if IVD supports (Keithley 2636A)
                      vReadingBuffer (str): only, if IVD supports (Keithley 2636A)
        '''
        ''' axis labels '''
        _axis = {0: (self._x_name, '', ''),
                 1: ('voltage', '', ''),
                 2: (self._x_coordname, 'current', ''), # or self._IV_modes[self._bias] for y
                 3: (self._x_coordname, self._y_coordname, 'current')}
        self._measurement_object.x_axis, self._measurement_object.y_axis, self._measurement_object.z_axis = _axis[self._scan_dim]
        ''' prepare IV device '''
        self._prepare_measurement_IVD()
        ''' prepare data storage '''
        self._prepare_measurement_file(**kwargs)
        ''' opens qviewkit to plot measurement '''
        if self.open_qviewkit:
            self._qvk_process = qviewkit.plot(self._data_file.get_filepath())  # , datasets=['{:s}_{:d}'.format(self._IV_modes[not(self._bias)].lower(), i) for i in range(self.sweeps.get_nos())])
        ''' progress bar '''
        if self._average is None:
            average=1
        else:
            average = self._average
        if self.progress_bar:
            num_its = {0: len(self._x_vec),
                       1: self.sweeps.get_nos(),
                       2: len(self._x_vec)*self.sweeps.get_nos(),
                       3: len(self._x_vec)*len(self._y_vec)*self.sweeps.get_nos()}
            self._pb = Progress_Bar(max_it=num_its[self._scan_dim]*average, 
                                    name='{:d}D IV-curve: {:s}'.format(self._scan_dim, self._filename))
        else:
            print('recording trace...')
        ''' measurement '''
        sys.stdout.flush()
        qt.mstart()
        #qkit.flow.start()
        try:
            if self._scan_dim == 0:  # single data points
                x_vec = list(self._x_vec)
                # add +/-inf as last element to x_vec
                if all(x<y for x, y in zip(x_vec, x_vec[1:])):  # x_vec is increasing
                    x_vec.append(np.inf)
                elif all(x>y for x, y in zip(x_vec, x_vec[1:])):  # x_vec is decreasing
                    x_vec.append(-np.inf)
                # iterate x_vec
                i = 0
                while i < len(x_vec)-1:
                    x_val = self._x_func()
                    if min(x_vec[i:i+2]) <= x_val <= max(x_vec[i:i+2]):
                        for func, lst in zip(self._y_func, self._data_y):
                            lst.add(func())
                        self._data_x.add(x_val)
                        # iterate progress bar
                        if self.progress_bar:
                            self._pb.iterate()
                        i += 1
                    sleep(self._x_dt)
            elif self._scan_dim in [1, 2, 3]:  # IV curve
                for x, x_func in [(None, self._pass)] if self._scan_dim < 2 else [(x, self._x_set_obj) for x in self._x_vec]:  # loop: x_obj with parameters from x_vec if 2D or 3D else pass(None)
                    x_func(x)
                    sleep(self._x_dt)
                    # log function
                    if self.log_function != [None]:
                        for i, f in enumerate(self.log_function):
                            self._log_values[i].append(float(f()))
                    for y, y_func in [(None, self._pass)] if self._scan_dim < 3 else [(y, self._y_set_obj) for y in self._y_vec]:  # loop: y_obj with parameters from y_vec if 3D else pass(None)
                        y_func(y)
                        sleep(self._tdy)
                        # iterate sweeps and take data
                        self._get_sweepdata(**kwargs)
                    # filling of value-box by storing data in the next 2d structure after every y-loop
                    if self._scan_dim is 3:
                        for val, lst in zip(range(self.sweeps.get_nos()), [val for k, val in enumerate([self._data_I, self._data_V, self._data_dVdI]) if k < 2+int(self._dVdI)]):
                            lst[val].next_matrix()
        finally:
            ''' end measurement '''
            qt.mend()
            #qkit.flow.end()
            t = threading.Thread(target=qviewkit.save_plots, args=[self._data_file.get_filepath(), self._plot_comment])
            t.start()
            self._data_file.close_file()
            waf.close_log_file(self._log)
            self._set_IVD_status(False)
            print('Measurement complete: {:s}'.format(self._data_file.get_filepath()))
        return

    def _prepare_measurement_IVD(self, **kwargs):
        '''
        All the relevant settings from the IVD are updated and called
        
        Input:
            **kwargs: channel_bias (int): 1 (default) | 2 for VV-mode
                      channel_sense (int): 1 | 2 (default) for VV-mode
                      channel (int): 1 (default) | 2 for IV-mode or VI-mode
        Output:
            None
        '''
        self._sweep_mode = self._IVD.get_sweep_mode()  # 0 (VV-mode) | 1 (IV-mode) | 2 (VI-mode)
        self._bias = self._IVD.get_bias(**kwargs)  # 0 (current bias) | 1 (voltage bias)
        self._IV_modes = {0: 'I', 1: 'V'}
        self._IV_units = {0: 'A', 1: 'V'}
        self._set_IVD_status(True, **kwargs)
        return
    
    def _set_IVD_status(self, status, **kwargs):
        '''
        Sets the output status of the used IVD (of channel <**kwargs>) to <status>
        
        Input:
            **kwargs: channel_bias (int): 1 (default) | 2 for VV-mode
                      channel_sense (int): 1 | 2 (default) for VV-mode
                      channel (int): 1 (default) | 2 for IV-mode or VI-mode
        Output:
            None
        '''
        if self._IVD.get_sweep_mode() == 0:
            self._channel_bias = kwargs.get('channel_bias', 1)
            self._channel_sense = kwargs.get('channel_sense', 2)
            for channel in [self._channel_bias, self._channel_sense]:
                self._IVD.set_status(status=status, channel=channel)
        elif self._IVD.get_sweep_mode() in [1, 2]:
            self._channel = kwargs.get('channel', 1)
            self._IVD.set_status(status=status, channel=self._channel)

    def _prepare_measurement_file(self, **kwargs):
        '''
        Creates one file each for data (.h5) with distinct dataset structures for each measurement dimentsion, settings (.set), logging (.log) and measurement (.measurement)
        At this point all measurement parameters are known and put in the output files
        
        Input:
            **kwargs: filename (str): file name used as suffix of uuid
                      expname (str): experiment name used as suffix of uuid and <filename>
                      comment (str): comment added to data in .h5 file
        Output:
            None
        '''
        ''' create files '''
        # default filename if not already set
        dirnames = {0: '{:s}_vs_{:s}'.format('_'.join(self._y_name), self._x_name),
                    1: 'IV_curve',
                    2: 'IV_curve_{:s}'.format(self._x_coordname),
                    3: 'IV_curve_{:s}_{:s}'.format(self._x_coordname, self._y_coordname)}
        if self._filename is None:
            self._filename = kwargs.get('filename', dirnames[self._scan_dim]).replace(' ', '_').replace(',', '_')
        if self._expname is None:
            self._expname = kwargs.get('expname', None)
        else:
            self._filename = '{:s}_{:s}'.format(self._filename, self._expname)
        self._filename = '{:d}D_{:s}'.format(self._scan_dim, self._filename)
        self._comment = kwargs.get('comment', None)
        # data.h5 file
        self._data_file = hdf.Data(name=self._filename, mode='a')
        # settings.set file
        self._settings = self._data_file.add_textlist('settings')
        self._settings.append(waf.get_instrument_settings(self._data_file.get_filepath()))
        # logging.log file
        self._log = waf.open_log_file(self._data_file.get_filepath())
        ''' measurement object, sample object '''
        self._measurement_object.uuid = self._data_file._uuid
        self._measurement_object.hdf_relpath = self._data_file._relpath
        self._measurement_object.instruments = qkit.instruments.get_instrument_names() # qkit.instruments.get_instruments() # 
        if self._measurement_object.sample is not None:
            self._measurement_object.sample.sweeps = self.sweeps.get_sweeps()
            self._measurement_object.sample.average = self._average
        if self._average is not None:
            self._measurement_object.average = self._average
        self._measurement_object.save()
        self._mo = self._data_file.add_textlist('measurement')
        self._mo.append(self._measurement_object.get_JSON())
        ''' data variables '''
        self._data_bias = []
        self._data_I = []
        self._data_V = []
        self._data_dVdI = []
        if self._scan_dim == 0:
            ''' xy '''
            # add data variables
            self._data_x = self._data_file.add_coordinate(self._x_name, unit=self._x_unit)
            self._data_y = [self._data_file.add_value_vector(self._y_name[i], x=self._data_x, unit=self._y_unit[i], save_timestamp=False) for i in range(len(self._y_func))]
            # add views
            views = kwargs.get('view', False)
            if views:
                if views is True:
                    views = [(x, y) for i, x in enumerate(range(len(self._data_y))) for y in range(len(self._data_y))[i+1::]]
                for view in views:
                    self._data_file.add_view('{:s}_vs_{:s}'.format(*np.array(self._y_name)[np.array(view[::-1])]), x=self._data_y[view[0]], y=self._data_y[view[1]])
        elif self._scan_dim == 1:
            ''' 1D scan '''
            # add data variables
            self.sweeps.create_iterator()
            for i in range(self.sweeps.get_nos()):
                self._data_bias.append(self._data_file.add_coordinate('{:s}_b_{!s}'.format(self._IV_modes[self._bias], i), unit=self._IV_units[self._bias]))
                self._data_bias[i].add(self._get_bias_values(sweep=self.sweeps.get_sweep()))
                self._data_I.append(self._data_file.add_value_vector('I_{!s}'.format(i), x=self._data_bias[i], unit='A', save_timestamp=False))
                self._data_V.append(self._data_file.add_value_vector('V_{!s}'.format(i), x=self._data_bias[i], unit='V', save_timestamp=False))
                if self._dVdI:
                    self._data_dVdI.append(self._data_file.add_value_vector('dVdI_{!s}'.format(i), x=self._data_bias[i], unit='V/A', save_timestamp=False))
            # add views
            self._add_views()
        elif self._scan_dim == 2:
            ''' 2D scan '''
            self._data_x = self._data_file.add_coordinate(self._x_coordname, unit=self._x_unit)
            self._data_x.add(self._x_vec)
            # add data variables
            self.sweeps.create_iterator()
            for i in range(self.sweeps.get_nos()):
                self._data_bias.append(self._data_file.add_coordinate('{:s}_b_{!s}'.format(self._IV_modes[self._bias], i), unit=self._IV_units[self._bias]))
                self._data_bias[i].add(self._get_bias_values(sweep=self.sweeps.get_sweep()))
                self._data_I.append(self._data_file.add_value_matrix('I_{!s}'.format(i), x=self._data_x, y=self._data_bias[i], unit='A', save_timestamp=False))
                self._data_V.append(self._data_file.add_value_matrix('V_{!s}'.format(i), x=self._data_x, y=self._data_bias[i], unit='V', save_timestamp=False))
                if self._dVdI:
                    self._data_dVdI.append(self._data_file.add_value_matrix('dVdI_{!s}'.format(i), x=self._data_x, y=self._data_bias[i], unit='V/A', save_timestamp=False))
            # log-function
            self._add_log_value_vector()
            # add views
            self._add_views()
        elif self._scan_dim == 3:
            ''' 3D scan '''
            self._data_x = self._data_file.add_coordinate(self._x_coordname, unit=self._x_unit)
            self._data_x.add(self._x_vec)
            self._data_y = self._data_file.add_coordinate(self._y_coordname, unit=self._y_unit)
            self._data_y.add(self._y_vec)
            # add data variables
            self.sweeps.create_iterator()
            for i in range(self.sweeps.get_nos()):
                self._data_bias.append(self._data_file.add_coordinate('{:s}_b_{!s}'.format(self._IV_modes[self._bias], i), unit=self._IV_units[self._bias]))
                self._data_bias[i].add(self._get_bias_values(sweep=self.sweeps.get_sweep()))
                self._data_I.append(self._data_file.add_value_box('I_{!s}'.format(i), x=self._data_x, y=self._data_y, z=self._data_bias[i], unit='A', save_timestamp=False))
                self._data_V.append(self._data_file.add_value_box('V_{!s}'.format(i), x=self._data_x, y=self._data_y, z=self._data_bias[i], unit='V', save_timestamp=False))
                if self._dVdI:
                    self._data_dVdI.append(self._data_file.add_value_box('dVdI_{!s}'.format(i), x=self._data_x, y=self._data_y, z=self._data_bias[i], unit='V/A', save_timestamp=False))
            # log-function
            self._add_log_value_vector()
            # add views
            self._add_views()
        ''' add comment '''
        if self._comment:
            self._data_file.add_comment(self._comment)
        return

    def _get_bias_values(self, sweep):
        '''
        Gets a linear distributed numpy-array of set bias values according to the sweep <sweep>
        
        Input:
            sweep (list(float)): start, stop, step
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
        Adds views to the .h5-file. The view "IV" plots I(V) and contains the whole set of sweeps that are set.
        If <dVdI> is true, the view "dVdI" plots the differential gradient dV/dI(V) and contains the whole set of sweeps that are set.
        
        Input:
            None
        Output:
            None
        '''
        self._view_IV = self._data_file.add_view('IV', x=self._data_V[0], y=self._data_I[0])
        for i in range(1, self.sweeps.get_nos()):
            self._view_IV.add(x=self._data_V[i], y=self._data_I[i])
        if self._dVdI:
            self._view_dVdI = self._data_file.add_view('dVdI', x=self._data_I[0], y=self._data_dVdI[0])
            for i in range(1, self.sweeps.get_nos()):
                self._view_dVdI.add(x=eval('self._data_{:s}'.format(self._IV_modes[self._bias]))[i], y=self._data_dVdI[i])
        return
    
    def _get_sweepdata(self, **kwargs):
        '''
        Iterates sweeps of sweep class and takes data for each sweep.
        If average is set, traces are taken <average>-fold to average and saved after each iteration
        
        Input:
            **kwargs: channel_bias (int): 1 (default) | 2 for VV-mode
                      channel_sense (int): 1 | 2 (default) for VV-mode
                      channel (int): 1 (default) | 2 for IV-mode or VI-mode
                      iReadingBuffer (str): only, if IVD supports (Keithley 2636A)
                      vReadingBuffer (str): only, if IVD supports (Keithley 2636A)
        Output:
            bias_values (numpy.array(float))
            sense_values (numpy.array(float))
        '''
        if self._average is not None:
            I_values, V_values = [], []
            for i in range(self._average):
                I_values.append([])
                V_values.append([])
                self.sweeps.create_iterator()
                for j in range(self.sweeps.get_nos()):
                    # take data
                    for val, lst in zip(self._IVD.take_IV(sweep=self.sweeps.get_sweep(), **kwargs), [I_values, V_values]):
                        lst[i].append(list(val))  # append as list in order to use zip
                    I_values_avg, V_values_avg = np.mean(zip(*I_values)[j], axis=0), np.mean(zip(*V_values)[j], axis=0)  # use zip since np.mean cannot handle different shapes
                    # save data
                    for val, lst in zip([I_values_avg, V_values_avg, np.gradient(V_values_avg)/np.gradient(I_values_avg)],
                                        [val for k, val in enumerate([self._data_I, self._data_V, self._data_dVdI]) if k < 2+int(self._dVdI)]):
                        if i == 0:
                            lst[j].append(val)  # append data series
                        else:
                            lst[j].ds.write_direct(val)  # overwrite last iteration by new averaged data
                        lst[j].ds.attrs['average'] = '({:d}/{:d})'.format(i+1, self._average)  # add (iteration/average) as attribute
                        self._data_file.flush()
                    # iterate progress bar
                    if self.progress_bar:
                        self._pb.iterate()
            # set average attribute to number of averages
            for j in range(self.sweeps.get_nos()):
                for lst in [val for k, val in enumerate([self._data_I, self._data_V, self._data_dVdI]) if k < 2+int(self._dVdI)]:
                    lst[j].ds.attrs['average'] = self._average
            self._data_file.flush()
            #qkit.flow.sleep()
        else:
            self.sweeps.create_iterator()
            for j in range(self.sweeps.get_nos()):
                I_values, V_values = self._IVD.take_IV(sweep=self.sweeps.get_sweep(), **kwargs)
                for val, lst in zip([I_values, V_values, np.gradient(V_values)/np.gradient(I_values) if self._dVdI else None],
                                    [self._data_I[j], self._data_V[j], self._data_dVdI[j] if self._dVdI else [None]]):
                    lst.append(val)
                # iterate progress bar
                if self.progress_bar:
                    self._pb.iterate()
                #qkit.flow.sleep()
        return

    def set_plot_comment(self, comment):
        '''
        Set small comment to add at the end of plot pics for more information i.e. good for wiki entries.
        
        Input:
            comment (str)
        Output:
            None
        '''
        self._plot_comment = comment
    
    def _pass(self, arg):
        pass

    class sweep(object):
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
            self.create_iterator()
            return

        def create_iterator(self):
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
                stop (float): Stop value of sweep
                step (float): Step value of sweep
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
                sweep tuple(float): start, stop, step
            '''
            return (self._start_iter.next(),
                    self._stop_iter.next(),
                    self._step_iter.next())

        def get_sweeps(self):
            '''
            Gets parameters of all sweep.
            
            Input:
                None
            Output:
                sweep (list(list(float))): [[start, stop, step]]
            '''
            return zip(*[self._starts, self._stops, self._steps])

        def get_nos(self):
            '''
            Gets number of sweeps.
            
            Input:
                None
            Output:
                nos (int)
            '''
            return len(self._starts)
