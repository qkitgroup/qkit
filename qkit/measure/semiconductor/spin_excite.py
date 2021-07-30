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

from copy import deepcopy

import qupulse

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
    def __init__(self, readout_backend, exp_name = "", manipulation_backend = None, sample = None):
        """
        Parameters
        ----------
        exp_name : str, optional
            Name of the current experiment
        sample : qkit.measure.samples_class.Sample, optional
            Sample used in the current experiment
        
        """
        mb.MeasureBase.__init__(self, sample)
        
        self._ro_backend = readout_backend
        self._manip_backend = manipulation_backend
        self._pulse_seq = None
        
        self._z_parameter = None
        
        self.qupulse_obj = None
        self.qupulse_params = None
        
        self.reverse2D = True
        self.report_static_voltages = True
        
        self.gate_lib = {}
        self.measurand = {"name" : "current", "unit" : "A"}

        
    @property
    def qupulse_prog(self):
        return self._qupulse_prog
    @qupulse_prog.setter
    def qupulse_prog(self, prog):
        if not isinstance(prog, qupulse._program._loop.Loop):
            raise TypeError("Object must be a qupulse._program._loop.Loop")
        self._setup_ro(prog)
        self._qupulse_prog = prog
    
    def _setup_ro(self, prog):
        meas_dict = prog.get_measurement_windows()
        for measurement, parameters in meas_dict.items():
            measurement_durations = parameters[1]
            
            if measurement_durations[measurement_durations != measurement_durations[0]].size > 0: # check whether all elements are the same
                raise Exception ("%s: All measurement windows for one measurement have to be of the same length" % __name__)           
            
            try:
                if self._ro_backend.measurement_settings[measurement]["active"]:
                    self._ro_backend.measurement_settings[measurement]["measurement_count"] = len(measurement_durations)
                    self._ro_backend.measurement_settings[measurement]["sample_count"] = np.int32(np.ceil(measurement_durations[0] * self._ro_backend.measurement_settings[measurement]["sampling_rate"] * 1e-9))
            except KeyError:
                raise Exception("%s: Defined measurement windows do not fit you readout backend. The requested measurement %s is not available in the loaded backend." % (__name__, measurement))
                
        
    def _setup_manip(self):
        #Load the waveforms of the qupulse object onto the AWG
        pass
    
    def _active_measurements(self, func):
        for measurement in self._ro_backend.measurement_settings.keys():
            if self._ro_backend.measurement_settings[measurement]["active"]:
                func(measurement)
                
    def _active_measurement_nodes(self, func):
        for measurement in self._ro_backend.measurement_settings.keys():
            if self._ro_backend.measurement_settings[measurement]["active"]:
                for node in self._ro_backend.measurement_settings[measurement]["data_nodes"]:
                    func(measurement, node)
    
    def _active_measurements_wrapper(self, func):
        def wrapped_func(func):
            for measurement in self._ro_backend.measurement_settings.keys():
                if self._ro_backend.measurement_settings[measurement]["active"]:
                    func(measurement)
        return wrapped_func
    
    def _active_measurement_nodes_wrapper(self, func):
        def wrapped_func(func):
            for measurement in self._ro_backend.measurement_settings.keys():
                if self._ro_backend.measurement_settings[measurement]["active"]:
                    for node in self._ro_backend.measurement_settings[measurement]["data_nodes"]:
                        func(measurement, node)
        return wrapped_func          
    
    def _copy_file_structure(self, file):
        b = {}
        for key in file.keys():
            b.update({key : {}})
            for sub_key in file[key].keys():
                b[key].update({sub_key : np.NaN})
        return b
            
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
    
    def measure1D(self):
        self._measurement_object.measurement_func = "%s: measure1D" % __name__
        
        total_iterations = 0 #setup the progress bar
        datasets = []
        for measurement in self._ro_backend.measurement_settings.keys():
            
            if self._ro_backend.measurement_settings[measurement]["active"]:
                #Count the number of total iterations which have to be made during the measurement
                total_iterations += self._ro_backend.measurement_settings[measurement]["averages"]
                
                for node in self._ro_backend.measurement_settings[measurement]["data_nodes"]:
                    #Create one dataset for each Measurement node
                    datasets.append(self.Data(name = "%s.%s" % (measurement, node), coords = [self._x_parameter],
                                          unit = self._ro_backend.measurement_settings[measurement]["unit"], 
                                          save_timestamp = False))
        pb = Progress_Bar(total_iterations)
        self._prepare_measurement_file(datasets)
        self._open_qviewkit()
        try:
            self._ro_backend.arm()
            #self._manip_backend.run()            
            
            latest_data = self._ro_backend.read()
            total_sum = {}
            iterations = 0            
            for measurement in self._ro_backend.measurement_settings.keys():                
                
                if self._ro_backend.measurement_settings[measurement]["active"]:
                    #Count the number of iterations collected by the most recent call of read
                    first_node = list(latest_data[measurement].keys())[0]
                    iterations += len(latest_data[measurement][first_node])
                    #Create the datastructure of the averagesum over all measurements
                    total_sum[measurement] = {}
                    #total_sum.update({measurement : {}})
                    
                    for node in self._ro_backend.measurement_settings[measurement]["data_nodes"]:
                        #Check whether the arrays have the correct dimensions:
                        if latest_data[measurement][node].ndim != 3:
                            raise IndexError("Invalid readout dimensions. The readout backend must return arrays with 3 dimensions.")
                        #Calculate the average over all measurements (axis 0), and integrate the samples (axis 2)
                        total_sum[measurement][node] = np.average(latest_data[measurement][node], axis = (0, 2))
                        #Pass the data to the h5 file
                        self._datasets["%s.%s" % (measurement, node)].append(total_sum[measurement][node])

            pb.iterate(addend = iterations)
            
            divider = 2
            while not self._ro_backend.finished():
                old_iterations = iterations
                latest_data = self._ro_backend.read()
                for measurement in self._ro_backend.measurement_settings.keys():                
                    
                    if self._ro_backend.measurement_settings[measurement]["active"]:
                        #Count the number of iterations collected by the most recent call of read
                        first_node = list(latest_data[measurement].keys())[0]
                        iterations += len(latest_data[measurement][first_node])
                        
                        for node in self._ro_backend.measurement_settings[measurement]["data_nodes"]:
                            #Calculate the average over all measurements (axis 0), and integrate the samples (axis 2)
                            total_sum[measurement][node] += np.average(latest_data[measurement][node], axis = (0, 2))
                            #Divide through the number of finished iterations
                            self._datasets["%s.%s" % (measurement, node)].ds.write_direct(total_sum[measurement][node] / divider)
                divider += 1
                self._data_file.flush()
                pb.iterate(addend = iterations - old_iterations)
            
        finally:
            self._ro_backend.stop()
            #self._manip_backend.stop()
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
            
    def measure2D_ST(self):        
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
if __name__ == "__main__":
    import qkit
    from datetime import date
    qkit.cfg['run_id'] = 'Testing %s' % date.today()
    qkit.cfg['user'] = 'Julian'
    qkit.start()
    import qkit.measure.samples_class as sc
    
    import numpy as np
    from numpy.random import rand
    from qkit.measure.semiconductor.spin_excite import Exciting
    from qkit.measure.semiconductor.readout_backends import RO_test_backend
    import numpy as np
    import matplotlib.pyplot as plt
    import logging
    
    readout = RO_test_backend.RO_backend()
    excitation = Exciting(readout_backend = readout)
    excitation.qviewkit_singleInstance = True
    excitation.set_x_parameters(np.arange(1, 257), "la banane", lambda val: True, "V")
    
    v_source = qkit.instruments.create("bill_virtual", "virtual_voltage_source")
    #%%
    excitation._ro_backend.measurement_settings["M1"]["measurement_count"] = 256
    excitation._ro_backend.measurement_settings["M1"]["sample_count"] = 10
    excitation._ro_backend.measurement_settings["M1"]["averages"] = 400
    excitation.measure1D()