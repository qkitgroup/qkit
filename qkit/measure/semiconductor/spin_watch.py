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
import qkit.measure.semiconductor.utils.utility_objects as uo
from qkit.gui.notebook.Progress_Bar import Progress_Bar
from qkit.measure.write_additional_files import get_instrument_settings

import numpy as np

from warnings import warn

class Watchdog:
    def __init__(self):
        self.stop = False
        self.message = ""
        self.max_length = 0
        self.node_bounds = {}
        self._node_lengths = {}  
    
    def register_node(self, node, bound_lower, bound_upper):
        if type(node) != str:
            raise TypeError(f"{__name__}: {node} is not a valid measurement node. The measurement node must be a string.")
        try:
            bound_lower = float(bound_lower)
        except Exception as e:
            raise type(e)(f"{__name__}: Cannot set {bound_lower} as lower measurement bound for node {node}. Conversion to float failed.")
        try:
            bound_upper = float(bound_upper)
        except Exception as e:
            raise type(e)(f"{__name__}: Cannot set {bound_lower} as lower measurement bound for node {node}. Conversion to float failed.")
        
        if bound_lower >= bound_upper:
            raise ValueError(f"{__name__}: Invalid bounds. {bound_lower} is larger or equal to {bound_upper}.")
        
        self.node_bounds[node] = [bound_lower, bound_upper]
        self._node_lengths[node] = 0
        
    def reset(self):
        self.stop = False
        self.global_message = ""        
        for node in self._node_lengths.keys():
            self._node_lengths[node] = 0
    
    def limits_check(self, node, values):
        if node not in self.node_bounds.keys():
            raise KeyError(f"{__name__}: No bounds are defined for node {node}")
        for value in values:
            if value < self.node_bounds[node][0]:
                self.stop = True
                self.message = f"{__name__}: Lower measurement bound for node {node} reached. Stopping measurement."
            elif value > self.node_bounds[node][1]:
                self.stop = True
                self.message = f"{__name__}: Upper measurement bound for node {node} reached. Stopping measurement."
    
    def length_check(self, node, values):
        values_length = len(values)
        count = self._node_lengths[node] + values_length      
        
        if count >= self.max_length:
            values = values[:self.max_length - self._node_lengths[node]]
            self._node_lengths[node] = self.max_length
        else:
            self._node_lengths[node] = count
        return values
    
class Watching(mb.MeasureBase):
    """
    A class containing measurement routines for everything.
    
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
             
        self.meander_sweep = True
        self.report_static_voltages = True
        
        self.multiplexer = uo.Multiplexer()
        self.watchdog = uo.Watchdog()

        self._node_lengths = {}
    
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
    
    def register_measurement(self, name, unit, nodes, get_tracedata_func, *args, **kwargs):
        self.multiplexer.register_measurement(name, unit, nodes, get_tracedata_func, *args, **kwargs)
        for node in nodes:
            self.watchdog.register_node(f"{name}.{node}", -10, 10)
            self._node_lengths[f"{name}.{node}"] = 0
    
    def set_node_bounds(self, measurement, node, bound_lower, bound_upper):
        self.watchdog.register_node(f"{measurement}.{node}", bound_lower, bound_upper)
    
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
            
    def _finished(self):
        if all(length >= self.max_length for length in self._node_lengths.values()): return True
        else: return False
    
    def _length_check(self, node, values):
        values_length = len(values)
        count = self._node_lengths[node] + values_length      
        
        if count >= self.max_length:
            values = values[:self.max_length - self._node_lengths[node]]
            self._node_lengths[node] = self.max_length
        else:
            self._node_lengths[node] = count
        return values
    
    def multi_measure1D(self):
        self._measurement_object.measurement_func = "%s: multi_measure1D" % __name__
        dsets = self.multiplexer.prepare_measurement_datasets([self._x_parameter])
        self._prepare_measurement_file(dsets)
        self.max_length = len(self._x_parameter.values)
        pb = Progress_Bar(self.max_length * self.multiplexer.no_nodes)
        
        self._open_qviewkit()
        
        try:                
            while (not self._finished()):
                latest_data = self.multiplexer.measure()
                
                for data_node, values in latest_data.items():
                    values = np.atleast_1d(values)
                    self.watchdog.limits_check(data_node, values)                    
                    checked_data = self._length_check(data_node, values)
                    self._datasets[data_node].append(checked_data)                
                    pb.iterate(addend = len(checked_data))
                
                if self.watchdog.stop:
                    warn(f"{__name__}: {self.watchdog.message}")
                    break
        finally:
            for data_node in self._node_lengths.keys():
                self._node_lengths[data_node] = 0
            self.watchdog.reset()
            self._end_measurement()
    
    def measure1D(self):
        """"Starts a 1D - measurement along the x-coordinate."""
        self._measurement_object.measurement_func = "%s: measure1D" % __name__
        
        pb = Progress_Bar(len(self._x_parameter.values))        
        self._prepare_measurement_file([self.Data(name = self.measurand["name"], coords = [self._x_parameter], 
                                                  unit = self.measurand["unit"], save_timestamp = False)])
        self._open_qviewkit()        
        try:
            total_length = len(self._x_parameter.values)
            measured_length = 0
            stop = False
            for x_val in self._x_parameter.values:
                self._x_parameter.set_function(x_val)
                qkit.flow.sleep(self._x_parameter.wait_time)
                measured = np.atleast_1d(self._get_value_func())
                measured_length += len(measured)
                
                if measured_length >= total_length:
                    measured = measured[:len(measured) - (measured_length - total_length)]
                    stop = True
                    
                for value in measured:
                    if abs(value) > self.measurement_limit:
                        warn(f"{__name__}: Measurement limit reached. Stopping measure1D.")
                        qkit.flow.sleep(0.2)
                        stop = True
                
                self._datasets[self.measurand["name"]].append(measured)                
                pb.iterate(addend = len(measured))
                
                if stop: break
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