# spin_tune.py intented for use with a voltage source and an arbitrary I-V-device or lockin
# JF@KIT 04/2021

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

import qkit
import qkit.measure.measurement_base as mb
from qkit.gui.notebook.Progress_Bar import Progress_Bar
from qkit.measure.write_additional_files import get_instrument_settings

import numpy as np

from numpy.random import rand

class Exciting(mb.MeasureBase):
    """
    A class containing measurement routines for spin qubit tuning.
    
    Parents
    -------
    Measurement_base
    
    Attributes
    ----------
    reverse2D : bool
        Zig-zag sweeping during 2D Measurements
    
    report_static_voltages: bool
        Create an extra entry in the .h5 file which reports the active (non-zero) gate voltages
    
    measurand : dict
        Contains the name and the unit of the measurand
    
    Methods
    -------
    set_z_parameters(self, vec, coordname, set_obj, unit, dt=None): 
        sets the z-axis for 3D Measurements.
    
    set_get_value_func(self, get_func, *args, **kwargs):
        Sets the measurement function.
    
    measure1D() :
        Starts a 1D measurement
    
    measure2D() :
        Starts a 2D measurement
        
    measure3D() :
        Starts a 3D measurement
    """
    def __init__(self, exp_name = "", sample = None):
        """
        Parameters
        ----------
        exp_name : str, optional
            Name of the current experiment
        sample : qkit.measure.samples_class.Sample, optional
            Sample used in the current experiment
        
        """
        mb.MeasureBase.__init__(self, sample)
        
        self._z_parameter = None
        
        self._get_value_func = None
        self._get_tracedata_func = None
        self.reverse2D = True
        self.report_static_voltages = True
        
        self.gate_lib = {}
        self.measurand = {"name" : "current", "unit" : "A"}
        
    
    def set_z_parameters(self, vec, coordname, set_obj, unit, dt=None):
        """
        Sets z-parameters for 2D and 3D scan.
        In a 3D measurement, the x-parameters will be the "outer" sweep meaning for every x value all y values are swept and for each (x,y) value the bias is swept according to the set sweep parameters.

        Parameters
        ----------
        vec : array_like
            An N-dimensional array that contains the sweep values.
        coordname : string
            The coordinate name to be created as data series in the .h5 file.
        set_obj : obj
            An callable object to execute with vec-values.
        unit : string
            The unit name to be used in data series in the .h5 file.
        dt : float, optional
            The sleep time between z-iterations.

        Returns
        -------
        None
        
        Raises
        ------
        Exception
            If the creation of the coordinate fails.
        """
        try:
            self._z_parameter = self.Coordinate(coordname, unit, np.array(vec, dtype=float), set_obj, dt)
            self._z_parameter.validate_parameters()
        except Exception as e:
            self._z_parameter = None
            raise e
           
    def set_get_value_func(self, get_func, *args, **kwargs):
        """
        Sets the measurement function.
        
        Parameters
        ----------
        get_func: function
            the get_func must return an int or float datatype. Arrays are not allowed.
        *args, **kwargs:
            Additional arguments to be passed to the get_func each time the measurement function is called.
        
        Returns
        -------
        None
        
        Raises
        ------
        TypeError
            If the passed object is not callable.
        """
        if not callable(get_func):
            raise TypeError("%s: Cannot set %s as get_value_func. Callable object needed." % (__name__, get_func))
        self._get_value_func = lambda: get_func(*args, **kwargs)
        self._get_tracedata_func = None
        
    def set_get_tracedata_func(self, get_func, *args, **kwargs):
        if not callable(get_func):
            raise TypeError("%s: Cannot set %s as get_tracedata_func. Callable object needed." % (__name__, get_func))
        self._get_tracedata_func = lambda: get_func(*args, **kwargs)
        self._get_value_func = None
    
    def _prepare_measurement_file(self, data, coords=()):
        mb.MeasureBase._prepare_measurement_file(self, data, coords=())
        
        if self.report_static_voltages:
            self._static_voltages = self._data_file.add_textlist("static_voltages")
            _instr_settings_dict = get_instrument_settings(self._data_file.get_filepath())
           
            string1 = "gate"
            string2 = "_output_voltage_in_V"
            active_gates = {}
            
            for parameters in _instr_settings_dict.values():
                for (key, value) in parameters.items():
                    if string1 in key and string2 in key and abs(value) > 0.0004:
                        active_gates.update({key:value})
            self._static_voltages.append(active_gates)
        
        
    #testfuncs to be removed later
    def _my_gauss(self, x_val, y_val, z_val = 0):
        
        def gauss(x, mu, sigma):
            return np.exp(-(x - mu)**2 / (2 * sigma **2)) / (sigma * np.sqrt(2 * np.pi))
        
        mu_x = 2 - z_val/10
        mu_y = 2           
        sigma = 1
        
        result = gauss(x_val, mu_x, sigma) * gauss(y_val, mu_y, sigma)
        
        return result
    
    def _test_logfunc(self):
        a = float(rand(1))
        print(a)
        return a
    
    def measure1D(self, iterations = 10):
        self._measurement_object.measurement_func = "%s: measure1D" % __name__
        
        pb = Progress_Bar(iterations)
        avg_data = [self.Data(name = self.measurand["name"], coords = [self._x_parameter], unit = self.measurand["unit"], save_timestamp = False)]
        self._prepare_measurement_file(avg_data)
        self._open_qviewkit()
        try:
# =============================================================================
#             for x_val in self._x_parameter.values:
#                 self._x_parameter.set_function(x_val)
#                 qkit.flow.sleep(self._x_parameter.wait_time)
#                 self._datasets[self.measurand["name"]].append(float(self._get_value_func()))
#                 pb.iterate()
# =============================================================================
            self._datasets[self.measurand["name"]].append(self._get_tracedata_func())
            for it in range(iterations):
                qkit.flow.sleep(self._x_parameter.wait_time)
                avg = 0
                if iterations == 0:
                    avg = self._get_tracedata_func()
                    self._datasets[self.measurand["name"]].append(avg)
                else:
                    avg += self._get_tracedata_func()
                    avg = avg / (it + 1)
                    arr = np.zeros(len(self._get_tracedata_func()))
                    self._datasets[self.measurand["name"]].ds.read_direct(arr)
                    print(arr)
                    self._datasets[self.measurand["name"]].ds.write_direct(np.ascontiguousarray(np.atleast_1d(avg)))
                    self._datasets[self.measurand["name"]].ds.attrs['iteration'] = it + 1
                    self._data_file.flush()
                pb.iterate()
        finally:
            self._end_measurement()
            
    def measure2D(self):        
        self._measurement_object.measurement_func = "%s: measure2D" % __name__
        
        pb = Progress_Bar(len(self._x_parameter.values) * len(self._y_parameter.values))        
        self._prepare_measurement_file([self.Data(name = self.measurand["name"], coords = [self._x_parameter, self._y_parameter], 
                                                  unit = self.measurand["unit"], save_timestamp = False)])
        self._open_qviewkit()
        try:
            direction = 1
            for x_val in self._x_parameter.values:
                sweepy = []
                self._x_parameter.set_function(x_val)
                self._acquire_log_functions()
                qkit.flow.sleep(self._x_parameter.wait_time)
                
                for y_val in self._y_parameter.values[::direction]:                    
                    self._y_parameter.set_function(y_val)
                    qkit.flow.sleep(self._y_parameter.wait_time)
                    sweepy.append(float(self._get_value_func()))
                    #sweepy.append(self._my_gauss(x_val, y_val))
                    pb.iterate()
                    
                self._datasets[self.measurand["name"]].append(sweepy[::direction])
                if self.reverse2D: direction *= -1
        finally:
            self._end_measurement()
    
    def measure3D(self):        
        self._measurement_object.measurement_func = "%s: measure3D" % __name__
        
        pb = Progress_Bar(len(self._x_parameter.values) * len(self._y_parameter.values) * len(self._z_parameter.values))        
        self._prepare_measurement_file([self.Data(name = self.measurand["name"], coords = [self._x_parameter, self._y_parameter, self._z_parameter], 
                                                  unit = self.measurand["unit"], save_timestamp = False)])
        self._open_qviewkit()
        try:            
            for x_val in self._x_parameter.values:
                self._x_parameter.set_function(x_val)
                self._acquire_log_functions()
                qkit.flow.sleep(self._x_parameter.wait_time)
                
                direction = 1
                for y_val in self._y_parameter.values:
                    sweepy = []
                    self._y_parameter.set_function(y_val)
                    qkit.flow.sleep(self._y_parameter.wait_time)
                    
                    for z_val in self._z_parameter.values[::direction]:                    
                        self._z_parameter.set_function(z_val)
                        qkit.flow.sleep(self._z_parameter.wait_time)
                        sweepy.append(float(self._get_value_func()))
                        #sweepy.append(self._my_gauss(x_val, y_val, z_val))
                        pb.iterate()
                        
                    self._datasets[self.measurand["name"]].append(sweepy[::direction])
                    if self.reverse2D: direction *= -1
                
                self._datasets[self.measurand["name"]].next_matrix()
        finally:
            self._end_measurement()