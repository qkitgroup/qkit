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

from warnings import warn

class Tuning(mb.MeasureBase):
    """
    A class containing measurement routines for spin qubit tuning.
    
    Parents
    -------
    Measurement_base
    
    Attributes
    ----------
    meander_sweep : bool
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
    def __init__(self, measurement_limit = 200e-12, exp_name = "", sample = None):
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
        
        self.measurement_limit = measurement_limit        
        self.meander_sweep = True
        self.report_static_voltages = True

        self.gate_lib = {}
        self.measurand = {"name" : "current", "unit" : "A"}
        
    @property
    def measurement_limit(self):       
        return self._measurement_limit
    
    @measurement_limit.setter
    def measurement_limit(self, newlim):
        try:
            self._measurement_limit = abs(float(newlim))
        except Exception as e:
            raise type(e)(f"{__name__}: Cannot set {newlim} as current limit. conversion to float failed: {e}")
    
    @property
    def meander_sweep(self):
        return self._meander_sweep
    
    @meander_sweep.setter
    def meander_sweep(self, yesno):
        if not isinstance(yesno, bool):
            raise TypeError(f"{__name__}: Cannot use {yesno} as meander_sweep. Must be a boolean value.")
        self._meander_sweep = yesno
        
    @property
    def report_static_voltages(self):
        return self._report_static_voltages
    
    @report_static_voltages.setter
    def report_static_voltages(self, yesno):
        if not isinstance(yesno, bool):
            raise TypeError(f"{__name__}: Cannot use {yesno} as report_static_voltages. Must be a boolean value.")        
        self._report_static_voltages = yesno

    @property
    def identifier(self):
        return self._identifier
    
    @identifier.setter
    def identifier(self, new_id):
        if not isinstance(new_id, str):
            raise TypeError(f"{__name__}: Cannot use {new_id} as identifier. Must be a boolean value.")
        self._identifier = new_id
    
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
            string2 = "_out"
            active_gates = {}
            
            for parameters in _instr_settings_dict.values():
                for (key, value) in parameters.items():
                    if string1 in key and key.endswith(string2) and abs(value) > 0.0004:
                        active_gates.update({key:value})
            self._static_voltages.append(active_gates)
    
    def measure1D(self):
        """"Starts a 1D - measurement along the x-coordinate."""
        self._measurement_object.measurement_func = "%s: measure1D" % __name__
        
        pb = Progress_Bar(len(self._x_parameter.values))        
        self._prepare_measurement_file([self.Data(name = self.measurand["name"], coords = [self._x_parameter], 
                                                  unit = self.measurand["unit"], save_timestamp = False)])
        self._open_qviewkit()
        try:
            for x_val in self._x_parameter.values:
                self._x_parameter.set_function(x_val)
                qkit.flow.sleep(self._x_parameter.wait_time)
                measured = float(self._get_value_func())
                self._datasets[self.measurand["name"]].append(measured)
                pb.iterate()
                if abs(measured) >= self.measurement_limit:
                    warn(f"{__name__}: Measurement limit reached. Stopping measure1D.")
                    qkit.flow.sleep(0.2)
                    break                
        finally:
            self._end_measurement()
            
    def measure2D(self):
        """Starts a 2D - measurement, with y being the inner and x the outer loop coordinate."""
        self._measurement_object.measurement_func = "%s: measure2D" % __name__
        
        pb = Progress_Bar(len(self._x_parameter.values) * len(self._y_parameter.values))        
        self._prepare_measurement_file([self.Data(name = self.measurand["name"], coords = [self._x_parameter, self._y_parameter], 
                                                  unit = self.measurand["unit"], save_timestamp = False)])
        self._open_qviewkit()
        try:
            y_direction = 1
            stop = False
            for x_val in self._x_parameter.values:
                sweepy = []
                self._x_parameter.set_function(x_val)
                self._acquire_log_functions()
                qkit.flow.sleep(self._x_parameter.wait_time)
                
                for y_val in self._y_parameter.values[::y_direction]:                    
                    self._y_parameter.set_function(y_val)
                    qkit.flow.sleep(self._y_parameter.wait_time)
                    measured = float(self._get_value_func())
                    sweepy.append(measured)
                    pb.iterate()
                    if abs(measured) >= self.measurement_limit:
                        stop = True
                        warn(f"{__name__}: Measurement limit reached. Stopping measure2D.")
                        qkit.flow.sleep(0.2)
                        break
                        
                self._datasets[self.measurand["name"]].append(sweepy[::y_direction])
                if self.meander_sweep: y_direction *= -1
                if stop: break                    
        finally:
            self._end_measurement()
    
    def measure3D(self):
        """Starts a 3D - measurement, with z being the innermost, y the inner and x the outer loop coordinate."""
        self._measurement_object.measurement_func = "%s: measure3D" % __name__
        
        pb = Progress_Bar(len(self._x_parameter.values) * len(self._y_parameter.values) * len(self._z_parameter.values))        
        self._prepare_measurement_file([self.Data(name = self.measurand["name"], coords = [self._x_parameter, self._y_parameter, self._z_parameter], 
                                                  unit = self.measurand["unit"], save_timestamp = False)])
        self._open_qviewkit()
        try:            
            stop = False
            for x_val in self._x_parameter.values:
                self._x_parameter.set_function(x_val)
                self._acquire_log_functions()
                qkit.flow.sleep(self._x_parameter.wait_time)
                
                z_direction = 1
                for y_val in self._y_parameter.values:
                    sweepy = []
                    self._y_parameter.set_function(y_val)
                    qkit.flow.sleep(self._y_parameter.wait_time)
                    
                    for z_val in self._z_parameter.values[::z_direction]:                    
                        self._z_parameter.set_function(z_val)
                        qkit.flow.sleep(self._z_parameter.wait_time)
                        measured = float(self._get_value_func())
                        sweepy.append(measured)
                        pb.iterate()
                        if abs(measured) >= self.measurement_limit:
                            stop = True
                            warn(f"{__name__}: Measurement limit reached. Stopping measure3D.")
                            qkit.flow.sleep(0.2)
                            break
                        
                    self._datasets[self.measurand["name"]].append(sweepy[::z_direction])
                    if self.meander_sweep: z_direction *= -1
                    if stop: break
                
                self._datasets[self.measurand["name"]].next_matrix()
                if stop: break
        finally:
            self._end_measurement()
            
if __name__ == "__main__":
    tuning = Tuning()
    print(tuning.measurement_limit)
    print(tuning.report_static_voltages)