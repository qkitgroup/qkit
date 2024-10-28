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
from scipy import signal
import logging
import time
import sys
import threading

import qkit
from qkit.storage import store as hdf
from qkit.gui.plot import plot as qviewkit
from qkit.gui.notebook.Progress_Bar import Progress_Bar
from qkit.measure.measurement_class import Measurement 
import qkit.measure.write_additional_files as waf


class transport(object):
    """
    This is a measurement class to perform transport measurements such as IV-characteristics by means of a current-voltage source meter.
    """
    
    def __init__(self, IV_Device):
        """
        Initializes the class for transport measurement such as IV characteristics.
        
        Parameters
        ----------
        IV_Device: qkit-instrument
            Current-voltage device that provides biasing and sensing.
        
        Returns
        -------
        None
        
        Examples
        --------
        >>> import qkit
        QKIT configuration initialized -> available as qkit.cfg[...]
        >>> qkit.cfg['run_id']='run_number'
        >>> qkit.cfg['user']='User'
        >>> qkit.start()
        Starting QKIT framework ... -> qkit.core.startup
        Loading module ... S10_logging.py
        Loading module ... S12_lockfile.py
        Loading module ... S14_setup_directories.py
        Loading module ... S20_check_for_updates.py
        Loading module ... S25_info_service.py
        Loading module ... S30_qkit_start.py
        Loading module ... S65_load_RI_service.py
        Loading module ... S70_load_visa.py
        Loading module ... S80_load_file_service.py
        Loading module ... S85_init_measurement.py
        Loading module ... S98_started.py
        Loading module ... S99_init_user.py
        Initialized the file info database (qkit.fid) in 0.000 seconds.
        
        >>> IVD = qkit.instruments.create('IVD', 'Keithley', address='TCPIP0::00.00.000.00::INSTR', reset=True)  # Keithley_2636A
        >>> from qkit.measure.transport import transport
        >>> tr = transport.transport(IV_Device=IVD)
        
        >>> import qkit.measure.samples_class as sc
        >>> sample = sc.Sample()
        >>> sample.name = 'sample_name'
        
        >>> tr.set_filename(filename='filename')
        >>> tr.set_expname(expname='expname')
        >>> tr.set_comment(comment='comment')
        >>> tr.set_sample(sample)
        >>> tr.set_dVdI(True)
        >>> tr.sweep.reset_sweeps()
        >>> tr.add_sweep_4quadrants(start=0e-9, stop=100e-9, step=100e-12, offset=0e-12)
        
        >>> tr.measure_XD()
        Measurement complete: d:\\data\XXXXXX_XD_sample_name\XXXXXX_XD_sample_name.h5
        Plots saved in d:\\data\XXXXXX_XD_sample_name\images
        """
        self._IVD = IV_Device
        # measurement object
        self._measurement_object = Measurement()
        self._measurement_object.measurement_type = 'transport'
        self._web_visible = True
        self._filename = None
        self._expname = None
        self._comment = None
        # measurement services
        self.progress_bar = True
        self.open_qviewkit = True
        self._qvk_process = False  # qviewkit process
        self._plot_comment = ''
        # measurement setting default values
        self.sweeps = self.sweep()  # calls sweep subclass
        # numerical derivation dV/dI (differential resistance)
        self._dVdI = False  # adds numerical derivation dV/dI as data series, views, ...
        self._numder_func = signal.savgol_filter  # function to calculate numerical derivative (default: Savitzky-Golay filter)
        self._numder_args = ()  # arguments for derivation function
        self._numder_kwargs = {'window_length': 15, 'polyorder': 3, 'deriv': 1}  # keyword arguments for derivation function
        self._average = None  # trace averaging
        self._view_xy = False
        # x and y data
        self._hdf_x = None
        self._hdf_y = None
        # xy, 2D & 3D scan variables
        self.set_log_function()
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
        self._landscape = False
        self._fit_func = None
        self._fit_name = None
        self._fit_unit = None
        self._fit_kwargs = None
    
    def set_sample(self, sample):
        """
        Adds sample object (e.g. with sample properties, measurement comments) to measurement object.
        
        Parameters
        ----------
        sample: qkit.measure.sample_class.Sample()
            Sample object to store information about the sample.
        
        Returns
        -------
        None
        
        Examples
        --------
        >>> import qkit.measure.samples_class as sc
        >>> sample = sc.Sample()
        >>> sample.name = 'sample_name'
        >>> tr.set_sample(sample)
        """
        self._measurement_object.sample = sample
        return
    
    def add_sweep_4quadrants(self, start, stop, step, offset=0, sleep=0):
        """
        Adds a four quadrants sweep series with the pattern 
            0th: (+<start> --> +<stop>,  <step>) + <offset>
            1st: (+<stop>  --> +<start>, <step>) + <offset>
            2nd: (+<start> --> -<stop>,  <step>) + <offset>
            3rd: (-<stop>  --> +<start>, <step>) + <offset>
            time.sleep(<sleep>)
        
        Parameters
        ----------
        start: float
            Start value of sweep.
        stop: float
            Stop value of sweep.
        step: float
            Step value of sweep.
        offset: float, optional
            Offset value by which <start> and <stop> are shifted. Default is 0.
        sleep: float
            Sleep time after whole sweep. Default is 0.
        
        Returns
        -------
        None
        """
        self.sweeps.add_sweep(start=start+offset, stop=+stop+offset, step=step, sleep=sleep)
        self.sweeps.add_sweep(start=+stop+offset, stop=start+offset, step=step, sleep=sleep)
        self.sweeps.add_sweep(start=start+offset, stop=-stop+offset, step=step, sleep=sleep)
        self.sweeps.add_sweep(start=-stop+offset, stop=start+offset, step=step, sleep=sleep)
        return
    
    def add_sweep_halfswing(self, amplitude, step, offset=0, sleep=0):
        """
        Adds a halfswing sweep series with the pattern 
            0th: (+<amplitude> --> -<amplitude, <step>) + <offset>
            1st: (-<amplitude> --> +<amplitude, <step>) + <offset>
            time.sleep(<sleep>)
        
        Parameters
        ----------
        amplitude: float
            Amplitude value of sweep.
        step: float
            Step value of sweep.
        offset: float
            Offset value by which <start> and <stop> are shifted. Default is 0.
        sleep: float
            Sleep time after whole sweep. Default is 0.
        
        Returns
        -------
        None
        """
        self.sweeps.add_sweep(start=+amplitude+offset, stop=-amplitude+offset, step=step, sleep=sleep)
        self.sweeps.add_sweep(start=-amplitude+offset, stop=+amplitude+offset, step=step, sleep=sleep)
        return
    
    def set_dVdI(self, status, func=None, *args, **kwargs):
        """
        Sets the internal dVdI parameter, to decide weather the differential resistance (dV/dI) is calculated or not.
        
        Parameters
        ----------
        status: bool
            Status if numerical derivative is calculated.
        func: function
            Function to calculate numerical derivative, e.g. scipy.signal.savgol_filter (default), numpy.gradient, ...
        *args: array_likes, optional
            Arguments for derivation function.
        **kwargs: dictionary_likes, optional
            Keyword arguments for derivation function.
        
        Returns
        -------
        None
        
        Examples
        --------
        Savitzky-Golay filter
        >>> tr.set_dVdI(True, func=signal.savgol_filter, window_length=15, polyorder=3, deriv=1)
        
        Gradient as difference quotient
        >>> tr.set_dVdI(True, func=np.gradient)
        """
        self._dVdI = status
        if func is not None:
            self._numder_func = func
            self._numder_args = args
            self._numder_kwargs = kwargs
        return
    
    def get_dVdI(self):
        """
        Gets the internal dVdI parameter, to decide weather the differential resistance (dV/dI) is calculated or not.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        status: bool
            Status if numerical derivative is calculated.
        func: function
            Function to calculate numerical derivative, e.g. scipy.signal.savgol_filter (default), numpy.gradient, ...
        *args: array_likes
            Arguments for derivation function.
        **kwargs: dictionary_likes
            Keyword arguments for derivation function.
        """
        return self._dVdI, self._numder_func, self._numder_args, self._numder_kwargs
    
    def _numerical_derivative(self, x, y):
        """
        Calculates numerical derivative dy/dx by means of set function <self._numder_func>, arguments <self._numder_args> and keyword arguments <self._numder_kwargs>.
    
        Parameters
        ----------
        x: array_likes
            An N-dimensional array containing x-values for numerical derivative.
        y: array_likes
            An N-dimensional array containing y-values for numerical derivative.
    
        Returns
        -------
        dydx: numpy.array
            An N-dimensional array containing numerical derivative dy/dx.
        """
        # TODO: catch error, if len(dataset) < window_length in case of SavGol filter
        try:
            return self._numder_func(y, *self._numder_args, **self._numder_kwargs)/self._numder_func(x, *self._numder_args, **self._numder_kwargs)
        except Exception as e:
            logging.warning("Can't calculate numerical derivative, possibly insufficient data points. %s", e)
            return np.zeros(len(y))*np.nan
    
    def set_x_dt(self, x_dt):
        """
        Sets sleep time between x-iterations in 2D and 3D scans.
        
        Parameters
        ----------
        x_dt: float
            The sleep time between x-iterations.
        
        Returns
        -------
        None
        """
        self._x_dt = x_dt
        return
    
    def get_x_dt(self):
        """
        Gets sleep time between x-iterations in 2D and 3D scans.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        x_dt: float
            The sleep time between x-iterations
        """
        return self._x_dt
    
    def set_x_parameters(self, x_vec, x_coordname, x_set_obj, x_unit='', x_dt=None):
        """
        Sets x-parameters for 2D and 3D scan.
        In a 3D measurement, the x-parameters will be the "outer" sweep meaning for every x value all y values are swept and for each (x,y) value the bias is swept according to the set sweep parameters.
        
        Parameters
        ----------
        x_vec: array_likes
            An N-dimensional array that contains the sweep values.
        x_coordname: string
            The coordinate name to be created as data series in the .h5 file.
        x_set_obj: obj
            An callable object to execute with x_vec-values.
        x_unit: string, optional
            The unit name to be used in data series in the .h5 file.
        x_dt: float, optional
            The sleep time between x-iterations.
        
        Returns
        -------
        None
        """
        # x-vec
        if np.iterable(x_vec):
            try:
                self._x_vec = np.array(x_vec, dtype=float)
            except Exception as e:
                raise type(e)('{!s}: Cannot set {!s} as x-vector'.format(__name__, x_vec, e))
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
        if x_dt is not None:
            self._x_dt = x_dt
        if self._landscape:
            self._lsc_vec = self._lsc_func(np.array(self._x_vec), *self._lsc_args)
        return
    
    def set_tdy(self, x_dt):
        """
        Sets sleep time between y-iterations in 3D scans.
        
        Parameters
        ----------
        x_dt: float
            The sleep time between y-iterations.
        
        Returns
        -------
        None
        """
        self._tdy = x_dt
        return
    
    def get_tdy(self):
        """
        Gets sleep time between y-iterations in 3D scans.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        x_dt: float
            The sleep time between y-iterations.
        """
        return self._tdy
    
    def set_y_parameters(self, y_vec, y_coordname, y_set_obj, y_unit='', y_dt=None):
        """
        Sets x-parameters for 3D scan, where y-parameters will be the "inner" sweep meaning for every x value all y values are swept and for each (x,y) value the bias is swept according to the set sweep parameters.
        
        Parameters
        ----------
        y_vec: array_likes
            An N-dimensional array that contains the sweep values.
        y_coordname: string
            The coordinate name to be created as data series in the .h5 file.
        y_set_obj: obj
            An callable object to execute with y_vec-values.
        y_unit: string, optional
            The unit name to be used in data series in the .h5 file.
        y_dt: float, optional
            The sleep time between y-iterations.
        
        Returns
        -------
        None
        """
        # y-vec
        if np.iterable(y_vec):
            try:
                self._y_vec = np.array(y_vec, dtype=float)
            except Exception as e:
                raise type(e)('{!s}: Cannot set {!s} as y-vector'.format(__name__, y_vec, e))
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
        if y_dt is not None:
            self._y_dt = y_dt
        return
    
    def set_landscape(self, func, args, mirror=True):
        """
        Sets parameters for landscapes scans in case of 2D and 3D scans to fasten up the measurement.
        The values of the given envelop function limit the sweep bounds for each x-value of 2D or 3D scans. The overall sweep bounds can merely be decreased, so that only envelop values <= sweep bounds affect them.
        
        Parameters
        ----------
        func: function
            An envelop function that limits bias values.
        args: tuple
            The arguments for the envelop function.
        mirror: bool, optional
            This determines if the envelop function is mirrored at the x-axis. Default is True
        
        Returns
        -------
        None

        Examples
        --------
        >>> tr.add_sweep_halfswing(1e-6, 10e-9)
        >>> def x_function(i):
                set_x_value(i)
                return
        >>> tr.set_x_parameters(x_vec = np.linspace(-10, 10, 21),
                                x_coordname = 'x_name',
                                x_set_obj = x_function,
                                x_unit = 'x_unit')
        >>> def lsc_func(x, a0, a1, x0):
                y = np.ones(shape = len(x)) * a1
                y[np.abs(x) > x0] = a0
                return y
        >>> tr.set_landscape(lsc_func, (500e-9, 1e-6, 5))
        """
        # TODO: possibility for landscape scans in both x and y direction
        self._landscape = True
        self._lsc_func = func
        self._lsc_args = args
        self._lsc_vec = func(np.array(self._x_vec), *args)
        self._lsc_mirror = mirror
        return
    
    def reset_landscape(self):
        self._landscape = False
        self._lsc_vec = None
        self._lsc_mirror = False
        return
    
    def set_xy_parameters(self, x_name, x_func, x_vec, x_unit, y_name, y_func, y_unit, x_kwargs={}, y_kwargs={}, x_dt=1e-3):
        """
        Set x- and y-parameters for measure_xy(), where y-parameters can be a list in order to record various quantities.
        
        Parameters
        ----------
        x_name: str
            The name of the x-parameter to be created as data series in the .h5 file.
        x_func: function
            A function that returns x-values.
        x_vec: array_likes of floats
            An array of x-values at which data should be taken.
        x_unit: str
            The unit of the x-parameter to be used in data series in the .h5 file.
        x_kwargs: dict
            Keyword arguments forwarded to the x-function <x_func>.
        y_name: array_likes of strings
            Names of y-parameters to be created as data series in the .h5 file.
        y_func: function
            A function that returns y-values.
        y_unit: array_likes of strings
            Units of y-parameters to be used in data series in the .h5 file.
        y_kwargs: dict
            Keyword arguments forwarded to the y-function <y_func>.
        x_dt: float, optional
            The sleep time between queries of x-values. Default is 1e-3.
        
        Returns
        -------
        None
        """
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
        if np.iterable(x_vec):
            self._x_vec = x_vec
        else:
            raise ValueError('{:s}: Cannot set {!s} as x-vector: iterable object needed'.format(__name__, x_vec))
        # x-unit
        if type(x_unit) is str:
            self._x_unit = x_unit
        else:
            raise ValueError('{:s}: Cannot set {!s} as x-unit: string needed'.format(__name__, x_unit))
        # x-kwargs
        if type(x_kwargs) is dict:
            self._x_kwargs = x_kwargs
        else:
            raise ValueError('{:s}: Cannot set {!s} as x-kwargs: dict needed'.format(__name__, x_kwargs))
        # y-name
        if type(y_name) is str:
            self._y_name = [y_name]
        elif np.iterable(y_name):
            for name in y_name:
                if type(name) is not str:
                    raise ValueError('{:s}: Cannot set {!s} as y-name: string needed'.format(__name__, name))
            self._y_name = y_name
        else:
            raise ValueError('{:s}: Cannot set {!s} as y-name: string of iterable object of strings needed'.format(__name__, y_name))
        # y-func
        if callable(y_func):
            self._y_func = [y_func]
        elif np.iterable(y_func):
            for func in y_func:
                if not callable(func):
                    raise ValueError('{:s}: Cannot set {!s} as y-function: callable object needed'.format(__name__, func))
            self._y_func = y_func
        else:
            raise ValueError('{:s}: Cannot set {!s} as y-function: callable object of iterable object of callable objects needed'.format(__name__, y_func))
        # y-unit
        if type(y_unit) is str:
            self._y_unit = [y_unit]
        elif np.iterable(y_unit):
            for unit in y_unit:
                if type(unit) is not str:
                    raise ValueError('{:s}: Cannot set {!s} as y-unit: string needed'.format(__name__, unit))
            self._y_unit = y_unit
        else:
            raise ValueError('{:s}: Cannot set {!s} as y-unit: string of iterable object of strings needed'.format(__name__, y_unit))
        # y-kwargs
        if type(y_kwargs) is dict:
            self._y_kwargs = [y_kwargs]
        elif np.iterable(y_kwargs):
            for kwargs in y_kwargs:
                if type(kwargs) is not dict:
                    raise ValueError('{:s}: Cannot set {!s} as y-kwargs: dict needed'.format(__name__, kwargs))
            self._y_kwargs = y_kwargs
        else:
            raise ValueError('{:s}: Cannot set {!s} as y-kwargs: dict of iterable object of dicts needed'.format(__name__, y_kwargs))
        # x-dt
        self._x_dt = x_dt
        return
    
    def set_log_function(self, func=None, name=None, unit=None, dtype='f'):
        """
        Saves desired values obtained by a function <func> in the .h5-file as a value vector with name <name>, unit <unit> and in data format <f>.
        The function (object) can be passed to the measurement loop which is executed before every x iteration
        but after executing the x_object setter in 2D measurements and before every line (but after setting 
        the x value) in 3D measurements.
        The return value of the function of type float or similar is stored in a value vector in the h5 file.
        
        Parameters
        ----------
        func: array_likes of callable objects
            A callable object that returns the value to be saved.
        name: array_likes of strings
            Names of logging parameter appearing in h5 file. Default is 'log_param'.
        unit: array_likes of strings
            Units of logging parameter. Default is ''.
        dtype: array_likes of dtypes
            h5 data type to be used in the data file. Default is 'f' (float64).
        
        Returns
        -------
        None
        """
        # TODO: dtype = float instead of 'f'
        # log-function
        if callable(func):
            func = [func]
        elif func is None:
            func = [None]
        elif np.iterable(func):
            for fun in func:
                if not callable(fun):
                    raise ValueError('{:s}: Cannot set {!s} as y-function: callable object needed'.format(__name__, fun))
        else:
            raise ValueError('{:s}: Cannot set {!s} as log-function: callable object of iterable object of callable objects needed'.format(__name__, func))
        self.log_function = func
        # log-name
        if name is None:
            try:
                name = ['log_param']*len(func)
            except Exception:
                name = [None]
        elif type(name) is str:
            name = [name]*len(func)
        elif np.iterable(name):
            for _name in name:
                if type(_name) is not str:
                    raise ValueError('{:s}: Cannot set {!s} as log-name: string needed'.format(__name__, _name))
        else:
            raise ValueError('{:s}: Cannot set {!s} as log-name: string of iterable object of strings needed'.format(__name__, name))
        self.log_name = name
        # log-unit
        if unit is None:
            try:
                unit = ['log_unit']*len(func)
            except Exception:
                unit = [None]
        elif type(unit) is str:
            unit = [unit]*len(func)
        elif np.iterable(unit):
            for _unit in unit:
                if type(_unit) is not str:
                    raise ValueError('{:s}: Cannot set {!s} as log-unit: string needed'.format(__name__, _unit))
        else:
            raise ValueError('{:s}: Cannot set {!s} as log-unit: string of iterable object of strings needed'.format(__name__, unit))
        self.log_unit = unit
        # log-dtype
        if dtype is None:
            try:
                dtype = [float]*len(func)
            except Exception:
                dtype = [None]
        elif type(dtype) is type:
            dtype = [dtype]*len(func)
        elif np.iterable(dtype):
            for _dtype in dtype:
                if type(_dtype) is not str:
                    raise ValueError('{:s}: Cannot set {!s} as log-dtype: string needed'.format(__name__, _dtype))
        else:
            raise ValueError('{:s}: Cannot set {!s} as log-dtype: string of iterable object of strings needed'.format(__name__, dtype))
        self.log_dtype = dtype
        return
    
    def get_log_function(self):
        """
        Gets the current log_function settings.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        func: array_likes of callable objects
            A callable object that returns the value to be saved.
        name: array_likes of strings
            Names of logging parameter appearing in h5 file. Default is 'log_param'.
        unit: array_likes of strings
            Units of logging parameter. Default is ''.
        dtype: array_likes of dtypes
            h5 data type to be used in the data file. Default is float (float64).
        """
        return [f.__name__ for f in self.log_function], self.log_name, self.log_unit, self.log_dtype
    
    def reset_log_function(self):
        """
        Resets all log_function settings.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        """
        self.log_function = []
        self.log_name = []
        self.log_unit = []
        self.log_dtype = []
        self._hdf_log = []
        return

    def set_fit_IV(self, func, name, unit='', **kwargs):
        """
        Sets fit-parameters for an in situ IV fit.
        This function is called for each trace with ints kexword arguments

        Parameters
        ----------
        func: obj
            An callable object to execute for each trace.
        name: string
            The coordinate name to be created as data series in the .h5 file.
        unit: string, optional
            The unit name to be used in data series in the .h5 file.
        **kwargs: dictionary_likes, optional
            Keyword arguments for fit function.

        Returns
        -------
        None

        Examples
        --------
        >>> from qkit.analysis.IV_curve import IV_curve as IVC
        >>> ivc = IVC()

        Ic fit via threshold voltage
        >>> tr.set_fit_IV(func=ivc.get_Ic_threshold, name='I_c', unit='A', offset=0)

        Ic fit via peaks in the numerical derivative dV/dI
        >>> tr.set_fit_IV(func=ivc.get_Ic_deriv, name='I_c', unit='A', prominence=10)

        Ic fit via peaks in the smoothed derivation in the frequency domain
        >>> tr.set_fit_IV(func=ivc.get_Ic_dft, name='I_c', unit='A', prominence=1e-2)
        """
        self._fit_func = func
        self._fit_name = name
        self._fit_unit = unit
        self._fit_kwargs = kwargs

    def reset_fit_IV(self):
        """
        Resets all fit_function settings.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self._fit_func = None
        self._fit_name = None
        self._fit_unit = None
        self._fit_kwargs = None

    def set_filename(self, filename):
        """
        Sets filename of current measurement to <filename>.
        
        Parameters
        ----------
        filename: str
            The file name used as suffix of uuid.
        
        Returns
        -------
        None
        """
        self._filename = filename
        return
    
    def get_filename(self):
        """
        Gets filename of current measurement.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        filename: str
            The file name used as suffix of uuid.
        """
        return self._filename
    
    def reset_filename(self):
        """
        Resets filename of current measurement to None.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        """
        self._filename = None
        return
    
    def set_expname(self, expname):
        """
        Sets experiment name of current measurement to <expname>.
        
        Parameters
        ----------
        expname: str
            The experiment name used as suffix of uuid and <filename>.
        
        Returns
        -------
        None
        """
        self._expname = expname
        return
    
    def get_expname(self):
        """
        Gets experiment name of current measurement
        
        Parameters
        ----------
        None
        
        Returns
        -------
        expname: str
            The experiment name used as suffix of uuid and <filename>.
        """
        return self._expname
    
    def reset_expname(self):
        """
        Resets experiment name of current measurement to None.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        """
        self._expname = None
        return
    
    def set_comment(self, comment):
        """
        Sets comment that is added to the .h5 file to <comment>
        
        Parameters
        ----------
        comment: str
            The comment added to data in .h5 file.
        
        Returns
        -------
        None
        """
        self._comment = comment
        return
    
    def get_comment(self):
        """
        Gets comment that is added to the .h5 file
        
        Parameters
        ----------
        None
        
        Returns
        -------
        comment: str
            The comment added to data in .h5 file.
        """
        return self._comment
    
    def reset_comment(self):
        """
        Resets comment that is added to the .h5 file to None.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        """
        self._comment = None
        return
    
    def set_average(self, avg):
        """
        Sets trace average parameter.
        
        Parameters
        ----------
        avg: int
            Number of averages of whole traces. Must be None (off) or natural numbers.
        
        Returns
        -------
        None
        """
        self._average = avg
        return
    
    def get_average(self):
        """
        Sets trace average parameter.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        avg: int
            Number of averages of whole traces. Is None (off) or a natural number.
        """
        return self._average
    
    def set_view_xy(self, view):
        """
        Sets views that combine different data series of xy-measurement.
        
        Parameters
        ----------
        view: bool or array_likes of integers
            Parameter that determines if additional views of different y-parameters are added. Must be boolean or an array containing tuples of two natural numbers, where y1 is used x-axis and y2 as y-axis.
        
        Returns
        -------
        None
        """
        self._view_xy = view
        return
    
    def get_view_xy(self):
        """
        Gets views that combine different data series of xy-measurement.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        view: bool or array_likes of integers
            Parameter that determines if additional views of different y-parameters are added. Is boolean or an array containing tuples of two natural numbers, where y1 is used x-axis and y2 as y-axis.
        """
        return self._view_xy
    
    def measure_xy(self):
        """
        Measures single data points, e.g. current or voltage and iterating all parameters x_vec, e.g. time.
        Every single data point is taken with the current IV Device settings.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        """
        self._scan_dim = 0
        ''' measurement object '''
        self._measurement_object.measurement_func = sys._getframe().f_code.co_name
        ''' measurement '''
        self._measure()
        return
    
    def measure_1D(self):
        """
        Measures a 1 dimensional set of IV curves while sweeping the bias according to the set sweep parameters. 
        Every single data point is taken with the current IV Device settings.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        """
        self._scan_dim = 1
        ''' measurement object '''
        self._measurement_object.measurement_func = sys._getframe().f_code.co_name
        ''' measurement '''
        self._measure()
        return
    
    def measure_2D(self):
        """
        Measures a 2 dimensional set of IV curves while sweeping the bias according to the set sweep parameters and iterating all parameters x_vec in x_obj. 
        Every single data point is taken with the current IV Device settings.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        """
        if self._x_set_obj is None:
            logging.error('{:s}: axes parameters not properly set'.format(__name__))
            raise TypeError('{:s}: axes parameters not properly set'.format(__name__))
        
        self._scan_dim = 2        
        ''' measurement object '''
        self._measurement_object.measurement_func = sys._getframe().f_code.co_name
        ''' measurement '''
        self._measure()
        return
    
    def measure_3D(self):
        """
        Measures a 3 dimensional set of IV curves while sweeping the bias according to the set sweep parameters and iterating all parameters x_vec in x_obj and all parameters y_vec in y_obj. The sweep over y_obj is the inner loop, for every value x_vec[i] all values y_vec are measured.
        Every single data point is taken with the current IV Device settings.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        """
        if self._x_set_obj is None or self._y_set_obj is None:
            logging.error('{:s}: axes parameters not properly set'.format(__name__))
            raise TypeError('{:s}: axes parameters not properly set'.format(__name__))
        self._scan_dim = 3
        ''' measurement object '''
        self._measurement_object.measurement_func = sys._getframe().f_code.co_name
        ''' measurement '''
        self._measure()
        return
    
    def _measure(self):
        """
        Creates output files, measures according to IVD and sweep settings, stores data and shows them in the qviewkit
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        """
        def _pass(arg):
            """ dummy function that just passes, used for x, y iteration in case of 1D and 2D scan """
            pass
        
        ''' axis labels '''
        _axis = {0: (self._x_name, '', ''),
                 1: ('voltage', '', ''),
                 2: (self._x_coordname, 'current', ''),  # or self._IV_modes[self._bias] for y
                 3: (self._x_coordname, self._y_coordname, 'current')}
        self._measurement_object.x_axis, self._measurement_object.y_axis, self._measurement_object.z_axis = _axis[self._scan_dim]
        ''' prepare IV device '''
        self._prepare_measurement_IVD()
        ''' prepare data storage '''
        self._prepare_measurement_file()
        ''' prepare progress bar '''
        self._prepare_progress_bar()
        ''' opens qviewkit to plot measurement '''
        if self.open_qviewkit:
            if self._scan_dim == 0:
                datasets = []
            else:
                datasets = ['views/IV']
                if self._fit_name:
                    for i in range(self.sweeps.get_nos()):
                        datasets.append('analysis/{:s}_{:d}'.format(self._fit_name, i))
                elif self._scan_dim > 1:
                    for i in range(self.sweeps.get_nos()):
                        datasets.append('{:s}_{:d}'.format(self._IV_modes[not self._bias].lower(), i))
            self._qvk_process = qviewkit.plot(self._data_file.get_filepath(), datasets=datasets)  # opens IV-view by default
        ''' measurement '''
        sys.stdout.flush()
        qkit.flow.start()
        try:
            if self._scan_dim == 0:  # single data points
                for x_val in self._x_vec:
                    self._hdf_x.add(x_val)
                    self._x_func(x_val, **self._x_kwargs)
                    for func, kwargs, lst in zip(self._y_func, self._y_kwargs, self._hdf_y):
                        lst.add(func(**kwargs))
                    # iterate progress bar
                    if self.progress_bar:
                        self._pb.iterate()
                    time.sleep(self._x_dt)
            elif self._scan_dim in [1, 2, 3]:  # IV curve
                _rst_log_hdf_appnd = False  # variable to save points of log-function in 2D-matrix
                self._rst_fit_hdf_appnd = False
                for self.ix, (x, x_func) in enumerate([(None, _pass)] if self._scan_dim < 2 else [(x, self._x_set_obj) for x in self._x_vec]):  # loop: x_obj with parameters from x_vec if 2D or 3D else pass(None)
                    x_func(x)
                    time.sleep(self._x_dt)
                    for self.iy, (y, y_func) in enumerate([(None, _pass)] if self._scan_dim < 3 else [(y, self._y_set_obj) for y in self._y_vec]):  # loop: y_obj with parameters from y_vec if 3D else pass(None)
                        y_func(y)
                        time.sleep(self._tdy)
                        # log function
                        if self.log_function != [None]:
                            for j, f in enumerate(self.log_function):
                                if self._scan_dim == 1:
                                    self._data_log[j] = np.array([float(f())])  # np.asarray(f(), dtype=float)
                                    self._hdf_log[j].append(self._data_log[j])
                                elif self._scan_dim == 2:
                                    self._data_log[j][self.ix] = float(f())
                                    self._hdf_log[j].append(self._data_log[j], reset=True)
                                elif self._scan_dim == 3:
                                    self._data_log[j][self.ix, self.iy] = float(f())
                                    self._hdf_log[j].append(self._data_log[j][self.ix], reset=_rst_log_hdf_appnd)
                            if self._scan_dim == 3: # reset needs to be updated for all log-functions simultaneously and thus outside of the loop 
                                _rst_log_hdf_appnd = not bool(self.iy+1 == len(self._y_vec))
                        # iterate sweeps and take data
                        self._get_sweepdata()
                    # filling of value-box by storing data in the next 2d structure after every y-loop
                    if self._scan_dim is 3:
                        for lst in [val for k, val in enumerate([self._hdf_I, self._hdf_V, self._hdf_dVdI]) if k < 2+int(self._dVdI)]:
                            for val in range(self.sweeps.get_nos()):
                                lst[val].next_matrix()
        finally:
            ''' end measurement '''
            qkit.flow.end()
            t = threading.Thread(target=qviewkit.save_plots, args=[self._data_file.get_filepath(), self._plot_comment])
            t.start()
            self._data_file.close_file()
            waf.close_log_file(self._log_file)
            self._set_IVD_status(False)
            print('Measurement complete: {:s}'.format(self._data_file.get_filepath()))
        return
    
    def _prepare_measurement_IVD(self):
        """
        All the relevant settings from the IVD are updated and called.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        """
        self._sweep_mode = self._IVD.get_sweep_mode()  # 0 (VV-mode) | 1 (IV-mode) | 2 (VI-mode)
        self._bias = self._IVD.get_sweep_bias()  # 0 (current bias) | 1 (voltage bias)
        self._IV_modes = {0: 'I', 1: 'V'}
        self._IV_units = {0: 'A', 1: 'V'}
        self._set_IVD_status(True)
        return
    
    def _set_IVD_status(self, status):
        """
        Sets the output status of the used IVD (of channel <**kwargs>) to <status>.
        
        Parameters
        ----------
        status: bool
            Output status of used IV-device.
        
        Returns
        -------
        None
        """
        for channel in self._IVD.get_sweep_channels():
            self._IVD.set_status(status=status, channel=channel)
        return
    
    def _prepare_measurement_file(self):
        """
        Creates one file each for data (.h5) with distinct dataset structures for each measurement dimension, settings (.set), logging (.log) and measurement (.measurement).
        At this point all measurement parameters are known and put in the output files.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        """
        ''' create files '''
        # data.h5 file
        self._data_file = hdf.Data(name='_'.join(list(filter(None, ('xy' if self._scan_dim is 0 else '{:d}D_IV_curve'.format(self._scan_dim), self._filename, self._expname)))), mode='a')
        # settings.set file
        self._hdf_settings = self._data_file.add_textlist('settings')
        self._hdf_settings.append(waf.get_instrument_settings(self._data_file.get_filepath()))
        # logging.log file
        self._log_file = waf.open_log_file(self._data_file.get_filepath())
        ''' measurement object, sample object '''
        self._measurement_object.uuid = self._data_file._uuid
        self._measurement_object.hdf_relpath = self._data_file._relpath
        self._measurement_object.instruments = qkit.instruments.get_instrument_names()  # qkit.instruments.get_instruments() #
        if self._measurement_object.sample is not None:
            self._measurement_object.sample.sweeps = self.sweeps.get_sweeps()
            self._measurement_object.sample.average = self._average
        if self._average is not None:
            self._measurement_object.average = self._average
        self._measurement_object.save()
        self._hdf_mo = self._data_file.add_textlist('measurement')
        self._hdf_mo.append(self._measurement_object.get_JSON())
        ''' data variables '''
        self._hdf_bias = []
        self._hdf_I = []
        self._hdf_V = []
        self._hdf_dVdI = []
        self._hdf_fit = []
        self._data_fit = []
        if self._scan_dim == 0:
            ''' xy '''
            # add data variables
            self._hdf_x = self._data_file.add_coordinate(self._x_name,
                                                         unit=self._x_unit)
            self._hdf_y = [self._data_file.add_value_vector(self._y_name[i],
                                                            x=self._hdf_x,
                                                            unit=self._y_unit[i],
                                                            save_timestamp=False)
                           for i,_ in enumerate(self._y_func)]
            # add views
            if self._view_xy:
                if self._view_xy is True:
                    self._view_xy = [(x, y) for i, x in enumerate(range(len(self._hdf_y)))
                                     for y, _ in enumerate(self._hdf_y)[i+1::]]
                for view in self._view_xy:
                    self._data_file.add_view('{:s}_vs_{:s}'.format(*np.array(self._y_name)[np.array(view[::-1])]),
                                             x=self._hdf_y[view[0]],
                                             y=self._hdf_y[view[1]])
        elif self._scan_dim == 1:
            ''' 1D scan '''
            # add data variables
            self.sweeps.create_iterator()
            for i in range(self.sweeps.get_nos()):
                self._hdf_bias.append(self._data_file.add_coordinate('{:s}_b_{!s}'.format(self._IV_modes[self._bias], i),
                                                                     unit=self._IV_units[self._bias]))
                self._hdf_bias[i].add(self._get_bias_values(sweep=self.sweeps.get_sweep()))
                self._hdf_I.append(self._data_file.add_value_vector('I_{!s}'.format(i),
                                                                    x=self._hdf_bias[i],
                                                                    unit='A',
                                                                    save_timestamp=False))
                self._hdf_V.append(self._data_file.add_value_vector('V_{!s}'.format(i),
                                                                    x=self._hdf_bias[i],
                                                                    unit='V',
                                                                    save_timestamp=False))
                if self._dVdI:
                    self._hdf_dVdI.append(self._data_file.add_value_vector('dVdI_{!s}'.format(i),
                                                                           x=self._hdf_bias[i],
                                                                           unit='V/A',
                                                                           save_timestamp=False,
                                                                           folder='analysis',
                                                                           comment=self._get_numder_comment(self._hdf_V[i].name)+
                                                                                   '/'+self._get_numder_comment(self._hdf_I[i].name)))
                if self._fit_func:
                    self._hdf_fit.append(self._data_file.add_value_vector('{:s}_{:d}'.format(self._fit_name, i),
                                                                          x=np.zeros(1),
                                                                          unit=self._fit_unit,
                                                                          save_timestamp=False,
                                                                          folder='analysis',
                                                                          comment=self._get_fit_comment(i)))
                    self._data_fit.append(np.nan)
            # log-function
            self._add_log_value_vector()
            # add views
            self._add_views()
        elif self._scan_dim == 2:
            ''' 2D scan '''
            self._hdf_x = self._data_file.add_coordinate(self._x_coordname, unit=self._x_unit)
            self._hdf_x.add(self._x_vec)
            # add data variables
            self.sweeps.create_iterator()
            for i in range(self.sweeps.get_nos()):
                self._hdf_bias.append(self._data_file.add_coordinate('{:s}_b_{!s}'.format(self._IV_modes[self._bias], i),
                                                                     unit=self._IV_units[self._bias]))
                self._hdf_bias[i].add(self._get_bias_values(sweep=self.sweeps.get_sweep()))
                self._hdf_I.append(self._data_file.add_value_matrix('I_{!s}'.format(i),
                                                                    x=self._hdf_x,
                                                                    y=self._hdf_bias[i],
                                                                    unit='A',
                                                                    save_timestamp=False))
                self._hdf_V.append(self._data_file.add_value_matrix('V_{!s}'.format(i),
                                                                    x=self._hdf_x,
                                                                    y=self._hdf_bias[i],
                                                                    unit='V',
                                                                    save_timestamp=False))
                if self._dVdI:
                    self._hdf_dVdI.append(self._data_file.add_value_matrix('dVdI_{!s}'.format(i),
                                                                           x=self._hdf_x,
                                                                           y=self._hdf_bias[i],
                                                                           unit='V/A',
                                                                           save_timestamp=False,
                                                                           folder='analysis',
                                                                           comment=self._get_numder_comment(self._hdf_V[i].name)+
                                                                                   '/'+self._get_numder_comment(self._hdf_I[i].name)))
                if self._fit_func:
                    self._hdf_fit.append(self._data_file.add_value_vector('{:s}_{:d}'.format(self._fit_name, i),
                                                                          x=self._hdf_x,
                                                                          unit=self._fit_unit,
                                                                          save_timestamp=False,
                                                                          folder='analysis',
                                                                          comment=self._get_fit_comment(i)))
                    self._data_fit.append(np.ones(len(self._x_vec)) * np.nan)
            # log-function
            self._add_log_value_vector()
            # add views
            self._add_views()
        elif self._scan_dim == 3:
            ''' 3D scan '''
            self._hdf_x = self._data_file.add_coordinate(self._x_coordname,
                                                         unit=self._x_unit)
            self._hdf_x.add(self._x_vec)
            self._hdf_y = self._data_file.add_coordinate(self._y_coordname,
                                                         unit=self._y_unit)
            self._hdf_y.add(self._y_vec)
            # add data variables
            self.sweeps.create_iterator()
            for i in range(self.sweeps.get_nos()):
                self._hdf_bias.append(self._data_file.add_coordinate('{:s}_b_{!s}'.format(self._IV_modes[self._bias], i),
                                                                     unit=self._IV_units[self._bias]))
                self._hdf_bias[i].add(self._get_bias_values(sweep=self.sweeps.get_sweep()))
                self._hdf_I.append(self._data_file.add_value_box('I_{!s}'.format(i),
                                                                 x=self._hdf_x,
                                                                 y=self._hdf_y,
                                                                 z=self._hdf_bias[i],
                                                                 unit='A',
                                                                 save_timestamp=False))
                self._hdf_V.append(self._data_file.add_value_box('V_{!s}'.format(i),
                                                                 x=self._hdf_x,
                                                                 y=self._hdf_y,
                                                                 z=self._hdf_bias[i],
                                                                 unit='V',
                                                                 save_timestamp=False))
                if self._dVdI:
                    self._hdf_dVdI.append(self._data_file.add_value_box('dVdI_{!s}'.format(i),
                                                                        x=self._hdf_x,
                                                                        y=self._hdf_y,
                                                                        z=self._hdf_bias[i],
                                                                        unit='V/A',
                                                                        save_timestamp=False,
                                                                        folder='analysis',
                                                                        comment=self._get_numder_comment(self._hdf_V[i].name)+
                                                                                '/'+self._get_numder_comment(self._hdf_I[i].name)))
                if self._fit_func:
                    self._hdf_fit.append(self._data_file.add_value_matrix('{:s}_{:d}'.format(self._fit_name, i),
                                                                          x=self._hdf_x,
                                                                          y=self._hdf_y,
                                                                          unit=self._fit_unit,
                                                                          save_timestamp=False,
                                                                          folder='analysis',
                                                                          comment=self._get_fit_comment(i)))
                    self._data_fit.append(np.ones((len(self._x_vec), len(self._y_vec))) * np.nan)
            # log-function
            self._add_log_value_vector()
            # add views
            self._add_views()
        ''' add comment '''
        if self._comment:
            self._data_file.add_comment(self._comment)
        return

    def _prepare_progress_bar(self):
        """
        Creates a progress bar using ipywidgets to show the measurement progress.
        Usually the number of performed sweeps, but in case of landscape scans entire number of bias points, is used as number of iterations.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        if self.progress_bar:
            # number of iterations as number of performed sweeps
            num_its = {0: len(self._x_vec),
                       1: self.sweeps.get_nos()*[1 if self._average is None else self._average][0],
                       2: len(self._x_vec)*self.sweeps.get_nos()*[1 if self._average is None else self._average][0],
                       3: len(self._x_vec)*len(self._y_vec)*self.sweeps.get_nos()*[1 if self._average is None else self._average][0]}
            if self._landscape and self._scan_dim in [2, 3]:
                # use entire number of bias points as number of iterations to estimate measurement time better
                bias_values = np.array([np.meshgrid(self._get_bias_values(sweep),
                                                    np.ones(len(self._x_vec)))[0]
                                        for sweep in self.sweeps.get_sweeps()])
                lsc_limits = np.array([self._lsc_vec,
                                        -self._lsc_vec if self._lsc_mirror
                                        else np.ones(shape=self._x_vec.shape)*np.array(self.sweeps.get_sweeps())[:,:2]])
                lsc_mask = np.logical_and(bias_values <= np.dot(np.ones((bias_values.shape[2], 1)), [np.max(lsc_limits, axis=0)]).T,
                                          bias_values >= np.dot(np.ones((bias_values.shape[2], 1)), [np.min(lsc_limits, axis=0)]).T)
                num_its[self._scan_dim] = np.sum(lsc_mask)*len(self._y_vec)*[1 if self._average is None else self._average][0]
                self._pb_addend = np.concatenate(list(zip(*np.sum(lsc_mask, axis=2))))  # value that counter has to be increased after each sweep
            self._pb = Progress_Bar(max_it=num_its[self._scan_dim],
                                    name='_'.join(list(filter(None, ('xy' if self._scan_dim is 0 else '{:d}D_IV_curve'.format(self._scan_dim), self._filename, self._expname)))))
        else:
            print('recording trace...')
    
    def _get_bias_values(self, sweep):
        """
        Gets a linearly distributed numpy-array of set bias values according to the sweep <sweep>.
        
        Parameters
        ----------
        sweep: array_likes of floats
            Sweep object containing start, stop, step and sleep values.
        
        Returns
        -------
        bias_values: numpy.array
            A linearly distributed numpy-array of given sweep parameters.
        """
        start = float(sweep[0])
        stop = float(sweep[1])
        step = float(sweep[2])
        ndigits = -int(np.floor(np.log10(np.abs(step)))) + 1
        nop = int(abs((stop - start) / step + np.sign(stop - start) * step / 100)) + 1
        return np.round(np.linspace(start, np.sign(stop - start) * (nop - 1) * step + start, nop), # stop is rounded down to multiples of step
                        decimals=ndigits)  # every element is rounded to overcome missing precision of numpy linspace
    
    def _get_numder_comment(self, name):
        """
        Save numerical derivative method (function, arguments, keyword arguments) to analysis comment in the .h5 file.
        
        Parameters
        ----------
        name: str
            Name of dataseries.
        
        Returns
        -------
        None
        """
        return '{!s}.{!s}('.format(self._numder_func.__module__, self._numder_func.__name__)+\
               ', '.join(np.concatenate([[name],
                                         np.array(self._numder_args, dtype=str) if self._numder_args else [],
                                         ['{:s}={!s}'.format(key, val) for key, val in self._numder_kwargs.items()] if self._numder_kwargs else []]))+\
               ')'

    def _get_fit_comment(self, i):
        """
        Save fit method (function, arguments, keyword arguments) to analysis comment in the .h5 file.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        return '{!s}.{!s}('.format(self._fit_func.__module__, self._fit_func.__name__)+\
               ', '.join(np.concatenate([['I={:s}'.format(self._hdf_I[i].name),
                                         'V={:s}'.format(self._hdf_V[i].name),
                                         'dVdI={:s}'.format(self._hdf_dVdI[i].name)],
                                        ['{:s}={!s}'.format(key, val) for key, val in self._fit_kwargs.items()] if self._fit_kwargs else []]))+\
               ')'

    def _add_log_value_vector(self):
        """
        Adds all value vectors for log-function parameter.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        """
        if self.log_function != [None]:
            self._hdf_log = []
            self._data_log = []
            for i, _ in enumerate(self.log_function):
                if self._scan_dim == 1:
                    self._hdf_log.append(self._data_file.add_coordinate(self.log_name[i],
                                                                        unit=self.log_unit[i]))
                    self._data_log.append(np.nan)
                elif self._scan_dim == 2:
                    self._hdf_log.append(self._data_file.add_value_vector(self.log_name[i],
                                                                          x=self._hdf_x,
                                                                          unit=self.log_unit[i],
                                                                          dtype=self.log_dtype[i]))
                    self._data_log.append(np.ones(len(self._x_vec))*np.nan)
                elif self._scan_dim == 3:
                    self._hdf_log.append(self._data_file.add_value_matrix(self.log_name[i],
                                                                          x=self._hdf_x,
                                                                          y=self._hdf_y,
                                                                          unit=self.log_unit[i],
                                                                          dtype=self.log_dtype[i]))
                    self._data_log.append(np.ones((len(self._x_vec), len(self._y_vec)))*np.nan)
        return
    
    def _add_views(self):
        """
        Adds views to the .h5-file. The view "IV" plots I(V) and contains the whole set of sweeps that are set.
        If <dVdI> is true, the view "dVdI" plots the differential gradient dV/dI(V) and contains the whole set of sweeps that are set.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        """
        self._hdf_view_IV = self._data_file.add_view('IV',
                                                     x=self._hdf_V[0],
                                                     y=self._hdf_I[0],
                                                     view_params={"labels": ('V', 'I'),
                                                                  'plot_style': 1,
                                                                  'markersize': 5})
        for i in range(1, self.sweeps.get_nos()):
            self._hdf_view_IV.add(x=self._hdf_V[i], y=self._hdf_I[i])
        if self._dVdI:
            self._hdf_view_dVdI = self._data_file.add_view('dVdI',
                                                           x=self._hdf_I[0],
                                                           y=self._hdf_dVdI[0],
                                                           view_params={"labels": ('I', 'dVdI'),
                                                                        'plot_style': 1,
                                                                        'markersize': 5})
            for i in range(1, self.sweeps.get_nos()):
                self._hdf_view_dVdI.add(x=[self._hdf_I, self._hdf_V][self._bias][i],
                                        y=self._hdf_dVdI[i])
        return
    
    def _get_sweepdata(self):
        """
        Iterates sweeps of sweep class and takes data for each sweep.
        If average is set, traces are taken <average>-fold to average and saved after each iteration
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        """
        if self._average is None:
            self.sweeps.create_iterator()
            for j in range(self.sweeps.get_nos()):
                # take data
                I_values, V_values = self.take_IV(sweep=self.sweeps.get_sweep())
                data = {self._hdf_I[j]:(I_values,),
                        self._hdf_V[j]:(V_values,)} # tuple in oder to use *args later
                if self._dVdI:
                    data[self._hdf_dVdI[j]] = (self._numerical_derivative(I_values, V_values),)
                if self._fit_func:
                    #data[self._hdf_fit[j]] = self._fit_func(data[self._hdf_I[j]],
                    #                                        data[self._hdf_V[j]],
                    #                                        data[self._hdf_dVdI[j]],
                    #                                        **self._fit_kwargs)
                    if self._scan_dim == 1:
                        self._data_fit[j] = float(self._fit_func(data[self._hdf_I[j]][0],
                                                                           data[self._hdf_V[j]][0],
                                                                           data[self._hdf_dVdI[j]][0],
                                                                           **self._fit_kwargs))
                        data[self._hdf_fit[j]] = (self._data_fit[j],)
                    elif self._scan_dim == 2:
                        self._data_fit[j][self.ix] = float(self._fit_func(data[self._hdf_I[j]][0],
                                                                          data[self._hdf_V[j]][0],
                                                                          data[self._hdf_dVdI[j]][0],
                                                                          **self._fit_kwargs))
                        data[self._hdf_fit[j]] = (self._data_fit[j], True)
                    elif self._scan_dim == 3:
                        self._data_fit[j][self.ix, self.iy] = float(self._fit_func(data[self._hdf_I[j]][0],
                                                                                   data[self._hdf_V[j]][0],
                                                                                   data[self._hdf_dVdI[j]][0],
                                                                                   **self._fit_kwargs))
                        data[self._hdf_fit[j]] = (self._data_fit[j][self.ix], self._rst_fit_hdf_appnd)
                        self._rst_fit_hdf_appnd = not bool(self.iy + 1 == len(self._y_vec))
                # save data
                for key, val in data.items():
                    key.append(*val)
                # iterate progress bar
                if self.progress_bar:
                    self._pb.iterate(addend=self._pb_addend[self.ix] if self._landscape else 1)
                qkit.flow.sleep()
        else:
            I_values, V_values = [], []
            for i in range(self._average):
                I_values.append([])
                V_values.append([])
                self.sweeps.create_iterator()
                for j in range(self.sweeps.get_nos()):
                    # take data
                    for val, lst in zip(self.take_IV(sweep=self.sweeps.get_sweep()), [I_values, V_values]):
                        lst[i].append(list(val))  # append as list in order to later use zip
                    I_values_avg, V_values_avg = np.mean(list(zip(*I_values))[j], axis=0), np.mean(list(zip(*V_values))[j], axis=0)  # use zip since np.mean cannot handle different shapes
                    data = {self._hdf_I[j]:I_values_avg,
                            self._hdf_V[j]:V_values_avg}
                    if self._dVdI:
                        data[self._hdf_dVdI[j]] = self._numerical_derivative(I_values_avg, V_values_avg)
                    if self._fit_func:
                        data[self._hdf_fit[j]] = self._fit_func(data[self._hdf_I[j]],
                                                                data[self._hdf_V[j]],
                                                                data[self._hdf_dVdI[j]],
                                                                **self._fit_kwargs)
                    # save data
                    for key, val in data.items():
                        key.append(val, reset=bool(i))  # append data series or overwrite last iteration by new averaged data
                        key.ds.attrs['average'] = '({:d}/{:d})'.format(i+1, self._average)  # add (iteration/average) as attribute
                        self._data_file.flush()
                    # iterate progress bar
                    if self.progress_bar:
                        self._pb.iterate(addend=self._pb_addend[self.ix] if self._landscape else 1)
            # set average attribute to number of averages
            for j in range(self.sweeps.get_nos()):
                for lst in [val for k, val in enumerate([self._hdf_I, self._hdf_V, self._hdf_dVdI]) if k < 2+int(self._dVdI)]:
                    lst[j].ds.attrs['average'] = self._average
            self._data_file.flush()
            qkit.flow.sleep()
        return
    
    def take_IV(self, sweep):
        """
        Takes IV and considers if landscape is set.
        
        Parameters
        ----------
        sweep: array_likes of floats
            Sweep object containing start, stop, step and sleep values.
        
        Returns
        -------
        I_values: numpy.array(float)
            Measured current values.
        V_values: numpy.array(float)
            Measured voltage values.
        """
        # take data
        if self._landscape:
            # modify sweep by envelop of landscape function
            bias_lim = self._lsc_vec[self.ix]
            if self._lsc_mirror:
                sweep_lsc = np.nanmin([np.abs(sweep), [bias_lim, bias_lim, np.nan, np.nan]], axis=0)*np.sign(sweep)
            else:
                sweep_lsc = np.nanmin([sweep, [bias_lim, bias_lim, np.nan, np.nan]], axis=0)
            # find landscape bounds in full bias values
            bias_data = self._get_bias_values(sweep)
            mask = np.logical_and(bias_data >= np.min(sweep_lsc[:2]), bias_data <= np.max(sweep_lsc[:2]))
            sweep_lsc[:2] = bias_data[np.where(mask)[0]][0], bias_data[np.where(mask)[0]][-1]
            # take data
            data = self._IVD.take_IV(sweep=sweep_lsc)
            # fill skipped bias values with np.nan to keep shape constant
            I_values, V_values = np.array([np.nan] * len(mask)), np.array([np.nan] * len(mask))
            np.place(arr=I_values, mask=mask, vals=data[0])
            np.place(arr=V_values, mask=mask, vals=data[1])
        else:
            I_values, V_values = self._IVD.take_IV(sweep=sweep)
        time.sleep(sweep[3])
        return I_values, V_values
    
    def set_plot_comment(self, comment):
        """
        Set small comment to add at the end of plot pics for more information i.e. good for wiki entries.
        
        Parameters
        ----------
        comment: str
            A comment that is added in the plot images.
        
        Returns
        -------
        None
        """
        self._plot_comment = comment
        return
    
    class sweep(object):
        """
        This is a subclass of <transport> that provides the customized usage of many sweeps in one measurement.
        """
        def __init__(self):
            """
            Initializes the sweep parameters as empty.
        
            Parameters
            ----------
            None
        
            Returns
            -------
            None
            """
            self._starts = []
            self._stops = []
            self._steps = []
            self._sleeps = []
            self.create_iterator()
            return
        
        def create_iterator(self):
            """
            Creates iterator of start, stop, step and sleep arrays.
        
            Parameters
            ----------
            None
        
            Returns
            -------
            None
            """
            self._start_iter = iter(self._starts)
            self._stop_iter = iter(self._stops)
            self._step_iter = iter(self._steps)
            self._sleep_iter = iter(self._sleeps)
            return
        
        def add_sweep(self, start, stop, step, sleep=0):
            """
            Adds a sweep object with given parameters.
        
            Parameters
            ----------
            start: float
                Start value of the sweep.
            stop: float
                Stop value of the sweep.
            step: float
                Step value of the sweep.
            sleep: float
                Sleep time after whole sweep. Default is 0.
        
            Returns
            -------
            None
            """
            self._starts.append(start)
            self._stops.append(stop)
            self._steps.append(step)
            self._sleeps.append(sleep)
            return
        
        def reset_sweeps(self):
            """
            Resets sweeps.
        
            Parameters
            ----------
            None
        
            Returns
            -------
            None
            """
            self._starts = []
            self._stops = []
            self._steps = []
            self._sleeps = []
            return
        
        def get_sweep(self):
            """
            Gets sweep parameter.
        
            Parameters
            ----------
            None
        
            Returns
            -------
            sweep: tuple of floats
                Sweep object containing start, stop, step and sleep values.
            """
            return (next(self._start_iter),
                    next(self._stop_iter),
                    next(self._step_iter),
                    next(self._sleep_iter))
        
        def get_sweeps(self):
            """
            Gets parameters of all sweep.
        
            Parameters
            ----------
            None
        
            Returns
            -------
            sweep: list of floats
                Sweep object containing start, stop, step and sleep values.
            """
            return list(zip(*[self._starts, self._stops, self._steps, self._sleeps]))
        
        def get_nos(self):
            """
            Gets number of sweeps.
        
            Parameters
            ----------
            None
        
            Returns
            -------
            nos: int
                Number of sweeps stored in this sweep-class.
            """
            return len(self._starts)
