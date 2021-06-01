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
import logging

from numpy.random import rand

class tuning(mb.MeasureBase):
    def __init__(self, exp_name = "", sample = None):
        mb.MeasureBase.__init__(self, sample)
        
        self._z_parameter = None
        
        self._get_value_func = None
        self._get_tracedata_func = None
        self.reverse2D = True
        self.report_static_votlages = True
        
        self.gate_lib = {}
        self.measurand = {"name" : "current", "unit" : "A"}
        
    
    def set_z_parameters(self, vec, coordname, set_obj, unit, dt=None): 
        try:
            self._z_parameter = self.Coordinate(coordname, unit, np.array(vec, dtype=float), set_obj, dt)
            self._z_parameter.validate_parameters()
        except Exception as e:
            self._z_parameter = None
            raise e
        
        
    def add_gates(self, gate_dict):
        if type(gate_dict) is not dict:
            raise TypeError("%s: Cannot append %s to the gate library. Dict needed." % (__name__, gate_dict))
        for gate_name, set_func in gate_dict.items():
            if type(gate_name) is not str:
                raise TypeError("%s: Cannot append %s to the gate library. Dict keys must be strings." % (__name__, gate_dict))
            if  not callable(set_func):
                raise TypeError("%s: Cannot append %s to the gate library. Dict values must be functions." % (__name__, gate_dict))
        self.gate_lib.update(gate_dict)
    
    def reset_gates(self):
        logging.warning("Gate library was reset and is empty.")
        self.gate_lib = {}
    
    def set_x_gate(self, gate, vrange, mV = False):
        if gate not in self.gate_lib.keys():
            raise KeyError("%s: Cannot set %s as x_gate.. It could not be found in the gate library." % (__name__, gate))
        if mV:
            vrange = vrange / 1000
       
        try:
            self._x_parameter = self.Coordinate(gate, "V", np.array(vrange, dtype=float), self.gate_lib[gate], 0)
            self._x_parameter.validate_parameters()
        except Exception as e:
            self._x_parameter = None
            raise e
            
    def set_y_gate(self, gate, vrange, mV = False):
        if gate not in self.gate_lib.keys():
            raise KeyError("%s: Cannot set %s as y_gate. It could not be found in the gate library." % (__name__, gate))
        if mV:
            vrange = vrange / 1000
        
        try:
            self._y_parameter = self.Coordinate(gate, "V", np.array(vrange, dtype=float), self.gate_lib[gate], 0)
            self._y_parameter.validate_parameters()
        except Exception as e:
            self._y_parameter = None
            raise e
            
    def set_z_gate(self, gate, vrange, mV = False):
        if gate not in self.gate_lib.keys():
            raise KeyError("%s: Cannot set %s as z_gate. It could not be found in the gate library." % (__name__, gate))
        if mV:
            vrange = vrange / 1000
       
        try:
            self._z_parameter = self.Coordinate(gate, "V", np.array(vrange, dtype=float), self.gate_lib[gate], 0)
            self._z_parameter.validate_parameters()
        except Exception as e:
            self._z_parameter = None
            raise e
            
    def set_get_value_func(self, get_func, *args, **kwargs):
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
    
    def measure1D(self):
        self._measurement_object.measurement_func = "%s: measure1D" % __name__
        
        pb = Progress_Bar(len(self._x_parameter.values))        
        self._prepare_measurement_file([self.Data(name = self.measurand["name"], coords = [self._x_parameter], 
                                                  unit = self.measurand["unit"], save_timestamp = False)])
        self._open_qviewkit()
        try:
            for x_val in self._x_parameter.values:
                self._x_parameter.set_function(x_val)
                qkit.flow.sleep(self._x_parameter.wait_time)
                self._datasets[self.measurand["name"]].append(self._get_value_func())
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
                    sweepy.append(self._get_value_func())
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
                        sweepy.append(self._get_value_func())
                        #sweepy.append(self._my_gauss(x_val, y_val, z_val))
                        pb.iterate()
                        
                    self._datasets[self.measurand["name"]].append(sweepy[::direction])
                    if self.reverse2D: direction *= -1
                
                self._datasets[self.measurand["name"]].next_matrix()
        finally:
            self._end_measurement()