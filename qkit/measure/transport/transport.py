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
        self.sweep = self.sweeps()  # calls sweep subclass
        self._dVdI = False  # adds dV/dI data series, views, ...
        self.set_log_function()
        # 2D & 3D scan variables
        self._scan_dim = None
        self.x_vec = [None]
        self.x_coordname = None
        self.x_set_obj = None
        self.x_unit = None
        self.y_vec = [None]
        self.y_coordname = None
        self.y_set_obj = None
        self.y_unit = None
        self._tdx = 2e-3  # in s
        self._tdy = 2e-3  # in s
        self.set_log_function()

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
        self.sweep.add_sweep(start+offset, +stop+offset, step)
        self.sweep.add_sweep(+stop+offset, start+offset, step)
        self.sweep.add_sweep(start+offset, -stop+offset, step)
        self.sweep.add_sweep(-stop+offset, start+offset, step)

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

    def set_x_parameters(self, x_vec, x_coordname, x_set_obj, x_unit=''):
        '''
        Sets x-parameters for 2D and 3D scan.
        In a 3D measurement, the x-parameters will be the "outer" sweep meaning for every x value all y values are swept and for each (x,y) value the bias is swept according to the set sweep parameters.
        
        Input:
            x_vec (array): contains the sweeping values
            x_coordname (string)
            x_set_obj (obj): callable object to execute with x_vec-values
            x_unit (string): optional
        Output:
            None
        '''
        try:
            for i in x_vec:
                if not str(i).isdigit():
                    raise TypeError('{:s}: elements of {!s} are no numbers'.format(__name__, x_vec))
            self.x_vec = x_vec
        except TypeError as e:
            raise TypeError('{:s}: {!s} is no valid x_vec\n{:s}'.format(__name__, x_vec, e))
        if type(x_coordname) is str:
            self.x_coordname = x_coordname
        else:
            raise TypeError('{:s}: {!s} is not a string'.format(__name__, x_coordname))
        if callable(x_set_obj):
            self.x_set_obj = x_set_obj
        else:
            raise TypeError('{:s}: {!s} is not callable'.format(__name__, x_set_obj))
        if type(x_unit) is str:
            self.x_unit = x_unit
        else:
            raise TypeError('{:s}: {!s} is not a string'.format(__name__, x_unit))
        return

    def set_tdx(self, val):
        '''
        Sets sleep time between x-iterations in 2D and 3D scans.
        
        Input:
            val (float): sleep time between x-iterations
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
            val (float): sleep time between x-iterations
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
        try:
            for i in y_vec:
                if not str(i).isdigit():
                    raise TypeError('{:s}: elements of {!s} are no numbers'.format(__name__, y_vec))
            self.y_vec = y_vec
        except TypeError as e:
            raise TypeError('{:s}: {!s} is no valid x_vec\n{:s}'.format(__name__, y_vec, e))
        if type(y_coordname) is str:
            self.y_coordname = y_coordname
        else:
            raise TypeError('{:s}: {!s} is not a string'.format(__name__, y_coordname))
        if callable(y_set_obj):
            self.y_set_obj = y_set_obj
        else:
            raise TypeError('{:s}: {!s} is not callable'.format(__name__, y_set_obj))
        if type(y_unit) is str:
            self.y_unit = y_unit
        else:
            raise TypeError('{:s}: {!s} is not a string'.format(__name__, y_unit))
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

    def set_log_function(self, func=None, name=None, unit=None, log_dtype=None):
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
            log_dtype (list(float)): h5 data type, default: 'f' (float32)
        Output:
            None
        '''
        if type(func) is not list:
            try:
                if callable(func):
                    func = [func]
                elif func is None:
                    pass
                else:
                    raise AttributeError('{:s}: Cannot set {!s} as log-function'.format(__name__, func))
            except Exception:
                raise AttributeError('{:s}: Cannot set {!s} as log-function'.format(__name__, func))
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
        if self.x_set_obj is None:
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
        if self.x_set_obj is None or self.y_set_obj is None:
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
        _axis = {1: ('voltage', '', ''),
                 2: (self.x_coordname, 'current', ''), # or self._IV_modes[self._bias] for y
                 3: (self.x_coordname, self.y_coordname, 'current')}
        self._measurement_object.x_axis, self._measurement_object.y_axis, self._measurement_object.z_axis = _axis[self._scan_dim]
        ''' prepare IV device '''
        self._prepare_measurement_IVD()
        ''' prepare data storage '''
        self._prepare_measurement_file(**kwargs)
        ''' opens qviewkit to plot measurement '''
        if self.open_qviewkit:
            self._qvk_process = qviewkit.plot(self._data_file.get_filepath())  # , datasets=['{:s}_{:d}'.format(self._IV_modes[not(self._bias)].lower(), i) for i in range(self.sweep.get_nos())])
        ''' progress bar '''
        if self._average is None:
            average=1
        else:
            average = self._average
        if self.progress_bar: 
            num_its = {1: self.sweep.get_nos(),
                       2: len(self.x_vec)*self.sweep.get_nos(),
                       3: len(self.x_vec)*len(self.y_vec)*self.sweep.get_nos()}
            self._pb = Progress_Bar(max_it=num_its[self._scan_dim]*average, 
                                    name='{:d}D IVD sweep: {:s}'.format(self._scan_dim, self._filename))
        else:
            print('recording trace...')
        ''' measurement '''
        sys.stdout.flush()
        qt.mstart()
        #qkit.flow.start()
        try:
            ''' 1D scan '''
            if self._scan_dim == 1:
                # iterate sweeps and take data
                self._get_sweepdata(**kwargs)
            else:
                for ix, x in enumerate(self.x_vec):  # loop: x_obj with parameters from x_vec
                    self.x_set_obj(x)
                    sleep(self._tdx)
                    # log function
                    if self.log_function is not None:
                        for i, f in enumerate(self.log_function):
                            self._log_values[i].append(float(f()))
                    ''' 2D scan '''
                    if self._scan_dim == 2:
                        # iterate sweeps and take data
                        self._get_sweepdata(**kwargs)
                    ''' 3D scan '''
                    if self._scan_dim == 3:
                        for y in self.y_vec:  # loop: y_obj with parameters from y_vec (only 3D measurement)
                            self.y_set_obj(y)
                            sleep(self._tdy)
                            # iterate sweeps and take data
                            self._get_sweepdata(**kwargs)
                        # filling of value-box by storing data in the next 2d structure after every y-loop
                        for i in range(self.sweep.get_nos()):
                            self._data_I[i].next_matrix()
                            self._data_V[i].next_matrix()
                            if self._dVdI:
                                self._data_dVdI[i].next_matrix()
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
        dirnames = {1: '1D_IV_curve',
                    2: '2D_IV_curve_{:s}'.format(self.x_coordname),
                    3: '3D_IV_curve_{:s}_{:s}'.format(self.x_coordname, self.y_coordname)}
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
        settings = waf.get_instrument_settings(self._data_file.get_filepath())
        self._settings.append(settings)
        # logging.log file
        self._log = waf.open_log_file(self._data_file.get_filepath())
        ''' measurement object, sample object '''
        self._measurement_object.uuid = self._data_file._uuid
        self._measurement_object.hdf_relpath = self._data_file._relpath
        self._measurement_object.instruments = qkit.instruments.get_instrument_names()
        if self._measurement_object.sample is not None:
            self._measurement_object.sample.sweeps = self.sweep.get_sweeps()
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
        if self._dVdI:
            self._data_dVdI = []
        if self._scan_dim == 1:
            ''' 1D scan '''
            # add data variables
            self.sweep.create_iterator()
            for i in range(self.sweep.get_nos()):
                self._data_bias.append(self._data_file.add_coordinate('{:s}_b_{!s}'.format(self._IV_modes[self._bias], i), unit=self._IV_units[self._bias]))
                self._data_bias[i].add(self._get_bias_values(sweep=self.sweep.get_sweep()))
                self._data_I.append(self._data_file.add_value_vector('I_{!s}'.format(i), x=self._data_bias[i], unit='A', save_timestamp=False))
                self._data_V.append(self._data_file.add_value_vector('V_{!s}'.format(i), x=self._data_bias[i], unit='V', save_timestamp=False))
                if self._dVdI:
                    self._data_dVdI.append(self._data_file.add_value_vector('dVdI_{!s}'.format(i), x=self._data_bias[i], unit='V/A', save_timestamp=False))
            # add views
            self._add_views()
        elif self._scan_dim == 2:
            ''' 2D scan '''
            self._data_x = self._data_file.add_coordinate(self.x_coordname, unit=self.x_unit)
            self._data_x.add(self.x_vec)
            # add data variables
            self.sweep.create_iterator()
            for i in range(self.sweep.get_nos()):
                self._data_bias.append(self._data_file.add_coordinate('{:s}_b_{!s}'.format(self._IV_modes[self._bias], i), unit=self._IV_units[self._bias]))
                self._data_bias[i].add(self._get_bias_values(sweep=self.sweep.get_sweep()))
                self._data_I.append(self._data_file.add_value_matrix('I_{!s}'.format(i), x=self._data_x, y=self._data_bias[i], unit='A', save_timestamp=False))
                self._data_V.append(self._data_file.add_value_matrix('V_{!s}'.format(i), x=self._data_x, y=self._data_bias[i], unit='V', save_timestamp=False))
                if self._dVdI:
                    self._data_dVdI.append(self._data_file.add_value_matrix('dVdI_{!s}'.format(i), x=self._data_x, y=self._data_bias[i], unit='V/A', save_timestamp=False))
            # Logfunction
            self._add_log_value_vector()
            # add views
            self._add_views()
        elif self._scan_dim == 3:
            ''' 3D scan '''
            self._data_x = self._data_file.add_coordinate(self.x_coordname, unit=self.x_unit)
            self._data_x.add(self.x_vec)
            self._data_y = self._data_file.add_coordinate(self.y_coordname, unit=self.y_unit)
            self._data_y.add(self.y_vec)
            # add data variables
            self.sweep.create_iterator()
            for i in range(self.sweep.get_nos()):
                self._data_bias.append(self._data_file.add_coordinate('{:s}_b_{!s}'.format(self._IV_modes[self._bias], i), unit=self._IV_units[self._bias]))
                self._data_bias[i].add(self._get_bias_values(sweep=self.sweep.get_sweep()))
                self._data_I.append(self._data_file.add_value_box('I_{!s}'.format(i), x=self._data_x, y=self._data_y, z=self._data_bias[i], unit='A', save_timestamp=False))
                self._data_V.append(self._data_file.add_value_box('V_{!s}'.format(i), x=self._data_x, y=self._data_y, z=self._data_bias[i], unit='V', save_timestamp=False))
                if self._dVdI:
                    self._data_dVdI.append(self._data_file.add_value_box('dVdI_{!s}'.format(i), x=self._data_x, y=self._data_y, z=self._data_bias[i], unit='V/A', save_timestamp=False))
            # Logfunction
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
        for i in range(1, self.sweep.get_nos()):
            self._view_IV.add(x=self._data_V[i], y=self._data_I[i])
        if self._dVdI:
            self._view_dVdI = self._data_file.add_view('dVdI', x=self._data_I[0], y=self._data_dVdI[0])
            for i in range(1, self.sweep.get_nos()):
                self._view_dVdI.add(x=eval('self._data_{:s}'.format(self._IV_modes[self._bias]))[i], y=self._data_dVdI[i])
        return
    
    def _get_sweepdata(self, **kwargs):
        '''
        Iterates sweeps of sweep class and takes data for each sweep
        
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
                self.sweep.create_iterator()
                for j in range(self.sweep.get_nos()):
                    for val, lst in zip(self._IVD.take_IV(sweep=self.sweep.get_sweep(), **kwargs), [I_values[i], V_values[i]]):
                        lst.append(list(val))
                    I_values_avg, V_values_avg = np.mean(zip(*I_values)[j], axis=0), np.mean(zip(*V_values)[j], axis=0)
                    if i == 0:
                        self._data_I[j].append(I_values_avg)
                        self._data_V[j].append(V_values_avg)
                        if self._dVdI:
                            self._data_dVdI[j].append(np.array(np.gradient(V_values_avg))/np.array(np.gradient(I_values_avg)))
                    else:
                        self._data_I[j].ds.write_direct(I_values_avg)
                        self._data_V[j].ds.write_direct(V_values_avg)
                        if self._dVdI:
                            self._data_dVdI[j].ds.write_direct(np.array(np.gradient(V_values_avg))/np.array(np.gradient(I_values_avg)))
                    ### TODO: attributes
                    self._data_I[j].ds.attrs['iteration'] = i+1
                    self._data_V[j].ds.attrs['iteration'] = i+1
                    if self._dVdI:
                        self._data_dVdI[j].ds.attrs['iteration'] = i+1
                    self._data_file.flush()
                    # progress bar
                    if self.progress_bar:
                        self._pb.iterate()
                #qkit.flow.sleep()
        else:
            self.sweep.create_iterator()
            for j in range(self.sweep.get_nos()):
                I_values, V_values = self._IVD.take_IV(sweep=self.sweep.get_sweep(), **kwargs)
                self._data_I[j].append(I_values)
                self._data_V[j].append(V_values)
                if self._dVdI:
                    self._data_dVdI[j].append(np.array(np.gradient(V_values))/np.array(np.gradient(I_values)))
                # progress bar
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
