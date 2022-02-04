# spin_tune.py intented for use with arbitrary measurement hardware.
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
from qkit.measure.semiconductor.utils.multiplexer import Sequential_multiplexer
from qkit.measure.semiconductor.utils.watchdog import Watchdog
from qkit.gui.notebook.Progress_Bar import Progress_Bar
from qkit.measure.write_additional_files import get_instrument_settings

import numpy as np

from warnings import warn
    
class Watching(mb.MeasureBase):
    """
    A class containing measurement routines for asynchronous data acquisition.
    
    Parents
    -------
    Measurement_base
    
    Attributes
    ----------
    report_static_voltages: bool
        Create an extra entry in the .h5 file which reports the active (non-zero) gate voltages
    
    Methods
    -------
    register_measurement(name, unit, nodes, get_tracedata_func, *args, **kwargs):
        Registers a measurement.

    activate_measurement(self, measurement):
        Activates the given measurement.

    deactivate_measurement(measurement):
        Deactivates the given measurement.

    set_node_bounds(measurement, node, bound_lower, bound_upper):
        Sets the upper and the lower bounds for a registered measurement node.

    set_z_parameters(vec, coordname, set_obj, unit, dt=None): 
        sets the z-axis for 3D Measurements.
    
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
        
        self.multiplexer = Sequential_multiplexer()
        self.watchdog = Watchdog()
        self._node_lengths = {}
        
    @property
    def report_static_voltages(self):
        return self._report_static_voltages
    
    @report_static_voltages.setter
    def report_static_voltages(self, yesno):
        if not isinstance(yesno, bool):
            raise TypeError(f"{__name__}: Cannot use {yesno} as report_static_voltages. Must be a boolean value.")        
        self._report_static_voltages = yesno
    
    def register_measurement(self, name, nodes, get_tracedata_func, *args, **kwargs):
        """
        Registers a measurement.

        Parameters
        ----------
        name : string
            Name of the measurement which is to be registered.
        unit : string
            Unit of the measurement.
        nodes : list(string)
            The data nodes of the measurement
        get_tracedata_func : callable
            Callable object which produces the data for the measurement which is to be registered.
        *args, **kwargs:
            Additional arguments which are passed to the get_tracedata_func during registration.

        Returns
        -------
        None
        """
        self.multiplexer.register_measurement(name, nodes, get_tracedata_func, *args, **kwargs)
        for node in nodes.keys():
            nodekey = f"{name}.{node}"
            self.watchdog.register_node(nodekey, -10, 10)            
    
    def activate_measurement(self, measurement):
        """
        Activates the given measurement.

        Parameters
        ----------
        measurement : string
            Name of the measurement the measurement which is to be activated.

        Returns
        -------
        None
        
        Raises
        ------
        KeyError
            If the given measurement doesn't exist.
        """
        self.multiplexer.activate_measurement(measurement)
        for node in self.multiplexer.registered_measurements[measurement]["nodes"]:
            nodekey = f"{measurement}.{node}"
            self._node_lengths[nodekey] = 0

    def deactivate_measurement(self, measurement):
        """
        Deactivates the given measurement.

        Parameters
        ----------
        measurement : string
            Name of the measurement the measurement which is to be deactivated.

        Returns
        -------
        None
        
        Raises
        ------
        KeyError
            If the given measurement doesn't exist.
        """
        self.multiplexer.deactivate_measurement(measurement)
        for node in self.multiplexer.registered_measurements[measurement]["nodes"]:
            nodekey = f"{measurement}.{node}"
            self._node_lengths.pop(nodekey, None)

    def set_node_bounds(self, measurement, node, bound_lower, bound_upper):
        """
        Sets the upper and the lower bounds for a registered measurement node.

        Parameters
        ----------
        measurement : string
            Name of the measurement the measurement node belongs to.
        node : string
            Name of the node whose limits are to be set.
        bound_lower : float
            Lower bound for the allowed measurement node values.
        bound_upper : float
            Upper bound for the allowed measurement node values.

        Returns
        -------
        None
        
        Raises
        ------
        KeyError
            If the given measurement doesn't exist.
        KeyError
            If the given node does not exist within the given measurement.
        """
        register = self.multiplexer.registered_measurements
        if measurement not in register.keys():
            raise KeyError(f"{__name__}: \"{measurement}\" is not a registered measurement.")
        if node not in register[measurement]["nodes"]:            
            raise KeyError(f"{__name__}: Measurement \"{measurement}\" does not contain node \"{node}\".")
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
        return all(length >= self.max_length for length in self._node_lengths.values())
    
    def _check_data(self, data_node, values):
        values = np.atleast_1d(values)
        self.watchdog.limits_check(data_node, values)
        
        values_length = len(values)
        count = self._node_lengths[data_node] + values_length
        
        if count >= self.max_length:
            values = values[:self.max_length - self._node_lengths[data_node]]
            self._node_lengths[data_node] = self.max_length
        else:
            self._node_lengths[data_node] = count
        return values    
        
    def _prepare_empty_container(self):
        sweepy = {}
        for name, measurement in self.multiplexer.registered_measurements.items():
            if measurement["active"]:
                for node in measurement["nodes"]:
                    sweepy[f"{name}.{node}"] = []
        return sweepy
                
    def measure1D(self, data_to_show = None):
        """
        Starts a 1D - measurement, along the x coordinate.
        
        Parameters
        ----------
        data_to_show : List of strings, optional
            Name of Datasets, which qviewkit opens at measurement start.
        """
        assert self._x_parameter, f"{__name__}: Cannot start measure1D. x_parameters required."
        self._measurement_object.measurement_func = "%s: measure1D" % __name__
        dsets = self.multiplexer.prepare_measurement_datasets([self._x_parameter])
        self._prepare_measurement_file(dsets)
        self.max_length = len(self._x_parameter.values)
        pb = Progress_Bar(self.max_length * self.multiplexer.no_active_nodes)
        
        self._open_qviewkit(datasets = data_to_show)
        
        try:                
            while (not self._finished()):
                latest_data = self.multiplexer.measure()
                
                for data_node, values in latest_data.items():       
                    checked_data = self._check_data(data_node, values)
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

    def measure2D(self, data_to_show = None):
        """
        Starts a 2D - measurement, with y being the inner and x the outer loop coordinate.
        
        Parameters
        ----------
        data_to_show : List of strings, optional
            Name of Datasets, which qviewkit opens at measurement start.
        """
        assert self._x_parameter, f"{__name__}: Cannot start measure2D. x_parameters required."
        assert self._y_parameter, f"{__name__}: Cannot start measure2D. y_parameters required."
        self._measurement_object.measurement_func = "%s: measure2D" % __name__
        dsets = self.multiplexer.prepare_measurement_datasets([self._x_parameter, self._y_parameter])
        self._prepare_measurement_file(dsets)
        self.max_length = len(self._y_parameter.values)
        pb = Progress_Bar(self.max_length * self.multiplexer.no_active_nodes * len(self._x_parameter.values))
        
        self._open_qviewkit(datasets = data_to_show)
        
        try:
            for x_val in self._x_parameter.values:
                sweepy = self._prepare_empty_container()
                self._x_parameter.set_function(x_val)
                self._acquire_log_functions()
                qkit.flow.sleep(self._x_parameter.wait_time)
                
                while (not self._finished()):
                    latest_data = self.multiplexer.measure()
                    
                    for data_node, values in latest_data.items():       
                        checked_data = self._check_data(data_node, values)
                        sweepy[data_node].extend(checked_data)
                        pb.iterate(addend = len(checked_data))
                    
                    if self.watchdog.stop:
                        warn(f"{__name__}: {self.watchdog.message}")
                        break
                
                for data_node, values in sweepy.items():          
                    self._datasets[data_node].append(values)
                    self._node_lengths[data_node] = 0
                
                if self.watchdog.stop: break                    
        finally:
            for data_node in self._node_lengths.keys():
                self._node_lengths[data_node] = 0
            self.watchdog.reset()
            self._end_measurement()
            
    def measure3D(self, data_to_show = None):
        """
        Starts a 3D - measurement, with z being the innermost, y the inner and x the outer loop coordinate.
        
        Parameters
        ----------
        data_to_show : List of strings, optional
            Name of Datasets, which qviewkit opens at measurement start.
        """
        assert self._x_parameter, f"{__name__}: Cannot start measure3D. x_parameters required."
        assert self._y_parameter, f"{__name__}: Cannot start measure3D. y_parameters required."
        assert self._z_parameter, f"{__name__}: Cannot start measure3D. z_parameters required."
        self._measurement_object.measurement_func = "%s: measure3D" % __name__
        dsets = self.multiplexer.prepare_measurement_datasets([self._x_parameter, self._y_parameter, self._z_parameter])
        self._prepare_measurement_file(dsets)
        self.max_length = len(self._z_parameter.values)
        pb = Progress_Bar(self.max_length * self.multiplexer.no_active_nodes * len(self._y_parameter.values) * len(self._x_parameter.values))
        
        self._open_qviewkit(datasets = data_to_show)
        try:            
            for x_val in self._x_parameter.values:
                self._x_parameter.set_function(x_val)
                self._acquire_log_functions()
                qkit.flow.sleep(self._x_parameter.wait_time)
                
                for y_val in self._y_parameter.values:
                    sweepy = self._prepare_empty_container()
                    self._y_parameter.set_function(y_val)
                    qkit.flow.sleep(self._y_parameter.wait_time)
                    
                    while (not self._finished()):
                        latest_data = self.multiplexer.measure()
                        
                        for data_node, values in latest_data.items():       
                            checked_data = self._check_data(data_node, values)
                            sweepy[data_node].extend(checked_data)
                            pb.iterate(addend = len(checked_data))
                        
                        if self.watchdog.stop:
                            warn(f"{__name__}: {self.watchdog.message}")
                            break
                    
                    for data_node, values in sweepy.items():
                        self._datasets[data_node].append(values)
                        self._node_lengths[data_node] = 0
                    
                    if self.watchdog.stop: break
                
                for dset in self._datasets.values():
                    dset.next_matrix()                    
                if self.watchdog.stop: break
        finally:
            for data_node in self._node_lengths.keys():
                self._node_lengths[data_node] = 0
            self.watchdog.reset()
            self._end_measurement()
            
if __name__ == "__main__":
    tuning = Watching()
    print(tuning.measurement_limit)
    print(tuning.report_static_voltages)