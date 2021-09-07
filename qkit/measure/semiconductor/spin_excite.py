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
from qkit.measure.semiconductor.readout_backends.RO_backend_base import RO_backend_base
from qkit.measure.semiconductor.manipulation_backends.MA_backend_base import MA_backend_base

import qupulse

import numpy as np
import warnings
import inspect

from numpy.random import rand
from collections.abc import MutableMapping

class TransformedDict(MutableMapping):
    """A dictionary that applies an arbitrary key-altering
       function before accessing the keys"""

    def __init__(self, mapping, *args, **kwargs):
        self.mapping = mapping
        self.store = dict()
        self.update(dict(*args, **kwargs))  # use the free update to set keys

    def __getitem__(self, key):
        return self.store[key]

    def __setitem__(self, key, value):
        self.store[self._keytransform(key)] = value

    def __delitem__(self, key):
        del self.store[key]

    def __iter__(self):
        return iter(self.store)
    
    def __len__(self):
        return len(self.store)
    
    def __str__(self):
        return self.store.__str__()

    def _keytransform(self, key):
        return self.mapping[key]  

class Qupulse_decoder2:
    valid_pulses = np.array(inspect.getmembers(qupulse.pulses, inspect.isclass))[:, 1]
    _for_type = qupulse.pulses.loop_pulse_template.ForLoopPulseTemplate
    def __init__(self, *experiments):
        self.experiments = experiments          
        self.measurement_pars = {}
        
        self._validate_entries()
        self._extract_measurement_pars()
        self._extract_axis_pars()
        
    def _validate_entries(self):
        pt_channels = set()
        pt_measurements = set()
        pt_axis = set()
        
        for pt, pars in self.experiments:
            #check whether the pulse template and the parameters are of the correct types.
            if type(pt) not in self.valid_pulses:
                raise TypeError("Invalid pulse template. It must be a qupulse pulse template.")
            if type(pars) != dict:
                raise TypeError("Invalid pulse parameters. It must be a dictionary.")
            #check whether channel and measurement definitions do not overlap.
            for channel in pt.defined_channels:
                if channel in pt_channels:
                    raise ValueError("Channels of different experiments overlap. Experiments are not allowed to share channels.")
                pt_channels.add(channel)
            for measurement in pt.measurement_names:
                if measurement in pt_measurements:
                    raise ValueError("Measurements of different experiments overlap. Experiments are not allowed to share Measurements.")
                pt_measurements.add(measurement)
            #In case there are forloop pts, check whether they don't have overlapping measurement axis
            if isinstance(pt, self._for_type):
                a = pt.loop_range.step.original_expression
                if isinstance(a, str) and a in pt_axis:
                    raise ValueError("Different Experiments have the same step parameter name. Experiments must have different step parameter names.")
                pt_axis.add(a)

    def _extract_measurement_pars(self):
        for pt, pars in self.experiments:
            prog = pt.create_program(parameters = pars)
            for measurement, parameters in prog.get_measurement_windows().items():
                measurement_durations = parameters[1]
                if measurement_durations[measurement_durations != measurement_durations[0]].size > 0: # check whether all elements are the same
                    raise ValueError ("%s: All measurement windows for one measurement have to be of the same length" % __name__)
                self.measurement_pars[measurement] = {}
                self.measurement_pars[measurement]["measurement_count"] = len(measurement_durations)
                self.measurement_pars[measurement]["measurement_duration"] = measurement_durations[0] * 1e-9
    
    def _get_loop_start(self, pt, pars):
        key = pt.loop_range.start.original_expression
        if type(key) == str:
            loop_start_value = pars[key]
        elif type(key) == int:
            loop_start_value = key
        return loop_start_value
    
    def _get_loop_stop(self, pt, pars):
        key = pt.loop_range.stop.original_expression
        if type(key) == str:
            loop_stop_value = pars[key]
        elif type(key) == int:
            loop_stop_value = key
        return loop_stop_value 
    
    def _get_loop_step(self, pt, pars):
        key = pt.loop_range.step.original_expression
        if type(key) == str:
            loop_step_name = key
            loop_step_value = pars[key]
        elif type(key) == int:
            loop_step_name = "for_loop_step%d" % self._nameless_counter
            loop_step_value = key
            self._nameless_counter += 1
        return loop_step_value, loop_step_name
                
    def _extract_axis_pars(self):
        self._nameless_counter = 1
        for pt, pars in self.experiments:
            if isinstance(pt, self._for_type):
                loop_start = self._get_loop_start(pt, pars)
                loop_stop = self._get_loop_stop(pt, pars)
                loop_step, loop_step_name = self._get_loop_step(pt, pars)
                if not pt.measurement_names:
                    warnings.warn("%s does not contain any measurements. Measurement axis parameters cannot be extracted automatically." % pt.identifier)
                for measurement in pt.measurement_names:
                    self.measurement_pars[measurement]["loop_step_name"] = loop_step_name
                    self.measurement_pars[measurement]["loop_range"] = np.arange(loop_start, loop_stop, loop_step) * 1e-9
            else:
                warnings.warn("%s is not a ForLoopPulseTemplate. Measurement axis parameters cannot be extracted automatically." % pt.identifier) 
    
class Settings:
    def __init__(self, core, decoder_params, **add_pars):
        self.core = core
        
        self._assert_mapping(decoder_params, add_pars)
        self._assert_averages(decoder_params, add_pars)        
        self.measurement_settings = TransformedDict(self.mapping, decoder_params)        
        self._validate_entries()
        
        self._get_units()
        self._get_nodes()
        self._time_to_samples()
    
    def __iter__(self):
        return iter(self.measurement_settings)
    
    def __getitem__(self, key):
        return self.measurement_settings[key]
    
    def keys(self):
        return self.measurement_settings.keys()
    
    def values(self):
        return self.measurement_settings.values()
    
    def items(self):
        return self.measurement_settings.items()
        
    def _assert_mapping(self, decoder_params, add_pars):
        if "measurement_mapping" in add_pars:
            if type(add_pars["measurement_mapping"]) != dict:
                raise TypeError("Invalid data type for measurement_mapping. Must be a dictionary.")
            if not all(x in add_pars["measurement_mapping"].keys() for x in decoder_params.keys()):
                raise KeyError("Measurement mapping incomplete. Not all measurements are mapped.")
            self.mapping = add_pars["measurement_mapping"]
            self.inverse_mapping = {v : k for k, v in self.mapping.items()}
        else:
            self.mapping = self.inverse_mapping = {v : v for v in decoder_params.keys()}
    
    def _assert_averages(self, decoder_params, add_pars):        
        if "averages" in add_pars:
            if type(add_pars["averages"]) != dict:
                raise TypeError("Invalid data type for averages. Must be a dictionary.")
            for measurement, settings in decoder_params.items():
                if measurement not in add_pars["averages"]:
                    raise KeyError("Averages incomplete. Not all measurements have an assigned number of averages")
                else: settings["averages"] = add_pars["averages"][measurement]
        else:
            for settings in decoder_params.values():
                settings["averages"] = 1000
            warnings.warn("No averages given. Defaulting to 1000 for all measurements")
            
    def _validate_entries(self):
        for measurement in self.measurement_settings.keys():
            if measurement not in self.core._ro_backend._registered_measurements.keys():
                raise AttributeError(f"Your readout backend does not support measurement {measurement}")
                
    def _time_to_samples(self):        
        for measurement, settings in self.measurement_settings.items():
            settings["sample_count"] = np.int32(np.floor(settings["measurement_duration"] * \
                    getattr(self.core._ro_backend, f"{measurement}_get_sample_rate")()))
            
    def _get_units(self):
        for measurement, settings in self.measurement_settings.items():
            settings["unit"] = self.core._ro_backend._registered_measurements[measurement]["unit"]
    
    def _get_nodes(self):
        for measurement, settings in self.measurement_settings.items():
            settings["data_nodes"] = self.core._ro_backend._registered_measurements[measurement]["data_nodes"]
    
    def load(self):
        for measurement in self.core._ro_backend._registered_measurements:
            getattr(self.core._ro_backend, f"{measurement}_deactivate")()
        for measurement, settings in self.measurement_settings.store.items():
            getattr(self.core._ro_backend, f"{measurement}_set_measurement_count")(settings["measurement_count"])
            getattr(self.core._ro_backend, f"{measurement}_set_sample_count")(settings["sample_count"])
            getattr(self.core._ro_backend, f"{measurement}_set_averages")(settings["averages"])
            getattr(self.core._ro_backend, f"{measurement}_activate")()
        
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
    def __init__(self, readout_backend, #manipulation_backend,
                 *experiments, exp_name = "", manipulation_backend = None, sample = None, **add_pars):
        """
        Parameters
        ----------
        exp_name : str, optional
            Name of the current experiment
        sample : qkit.measure.samples_class.Sample, optional
            Sample used in the current experiment
        
        """
        mb.MeasureBase.__init__(self, sample)
        
        self._validate_RO_backend(readout_backend)
        self._ro_backend = readout_backend
        #self._validate_manip_backend(manipulation_backend)
        self._manip_backend = manipulation_backend   
        
        self._t_parameters = {}
        self.compile_qupulse(*experiments, **add_pars)
        
        self.meander_sweep = True
        self.report_static_voltages = True
        
    
    @property
    def meander_sweep(self):
        return self._meander_sweep
    
    @meander_sweep.setter
    def meander_sweep(self, yesno):
        if not isinstance(yesno, bool):
            raise TypeError("Invalid meander_sweep parameter. Must be a boolean value.")
        self._meander_sweep = yesno
    
    @property
    def report_static_voltages(self):
        return self._report_static_voltages
    
    @report_static_voltages.setter
    def report_static_voltages(self, yesno):
        if not isinstance(yesno, bool):
            raise TypeError("Invalid report_static_voltages parameter. Must be a boolean value.")
        self._report_static_voltages = yesno
    
    def _validate_RO_backend(self, RO_backend):
        if not issubclass(RO_backend.__class__, RO_backend_base):
            raise TypeError("Invalid readout backend. The backend must be a subclass of RO_backend_base")
            
    def _validate_MA_backend(self, MA_backend):
        if not issubclass(MA_backend.__class__, MA_backend_base):
            raise TypeError("Invalid manipulation backend. The backend must be a subclass of MA_backend_base")
            
    def update_t_parameters(self, vec, coordname, measurement):
            new_t_parameter = self.Coordinate(coordname, 
                                                unit = "s", 
                                                values = np.array(vec, dtype=float),
                                                set_function = lambda val: True,
                                                wait_time = 0)
            new_t_parameter.validate_parameters()
            self._t_parameters[measurement] = new_t_parameter
            
            #We have to do this because qkit is dumb...
            #Coordinate objects have no way of knowing that they're equal. So if you try to build a dataset out of two coordinates which are nominally the same,
            #but located at different points in the RAM this FUCKIN PIECE OF..., erm I mean qkit will think that you try to create the same dataset out of two
            #different coordinates and will throw errors at your face.
            for meas, coordinate in self._t_parameters.items():
                if coordinate.name == new_t_parameter.name:
                    self._t_parameters[measurement] = self._t_parameters[meas]           
    
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
    
    def _prepare_measurement(self, *coords):
        total_iterations = 0 #setup the progress bar
        datasets = []
        coords_list = list(coords)
        for measurement in self.settings:
            total_iterations += self.settings[measurement]["averages"]
            
            for node in self.settings[measurement]["data_nodes"]:
                #Create one dataset for each Measurement node
                datasets.append(self.Data(name = "%s.%s" % (self.settings.inverse_mapping[measurement], node), coords = coords_list + [self._t_parameters[measurement]],
                                      unit = self.settings[measurement]["unit"], 
                                      save_timestamp = False))
        self._total_iterations = total_iterations
        self._prepare_measurement_file(datasets)
        if self.open_qviewkit:
            self._open_qviewkit()
    
    def _measure_vs_time(self, dimension, progress_bar):
        self._ro_backend.arm()
        #self._manip_backend.run()       
        total_sum = {}
        iterations = 0
        divider = 1
        while not self._ro_backend.finished():
            old_iterations = iterations
            latest_data = self._ro_backend.read()
            for measurement in latest_data.keys():
                if divider == 1:                            
                    total_sum[measurement] = {}                 
                #Count the number of iterations collected by the most recent call of read
                first_node = list(latest_data[measurement].keys())[0]
                iterations += len(latest_data[measurement][first_node])
                
                for node in latest_data[measurement].keys():
                    if latest_data[measurement][node].ndim != 3:
                        raise IndexError("Invalid readout dimensions. The readout backend must return arrays with 3 dimensions.")
                    if False in np.any(latest_data[measurement][node], axis = (0, 2)):
                        raise ValueError("During the last read the readout returned an array with empty slices.")
                    #Calculate the average over all measurements (axis 0), and integrate the samples (axis 2)
                    if divider == 1:
                        total_sum[measurement][node] = np.average(latest_data[measurement][node], axis = (0, 2))
                        self._datasets["%s.%s" % (self.settings.inverse_mapping[measurement], node)].append(total_sum[measurement][node])
                    else:
                        total_sum[measurement][node] += np.average(latest_data[measurement][node], axis = (0, 2))
                        #Divide through the number of finished iterations, since you accumulate all the averages
                        if dimension == 1:
                            self._datasets["%s.%s" % (self.settings.inverse_mapping[measurement], node)].ds[:] =  total_sum[measurement][node] / divider
                        elif dimension == 2:
                            self._datasets["%s.%s" % (self.settings.inverse_mapping[measurement], node)].ds[-1] = total_sum[measurement][node] / divider
                        elif dimension == 3:
                            self._datasets["%s.%s" % (self.settings.inverse_mapping[measurement], node)].ds[-1][-1] = total_sum[measurement][node] / divider
            divider += 1
            self._data_file.flush()
            progress_bar.iterate(addend = iterations - old_iterations)
        self._ro_backend.stop()
        #self._manip_backend.stop()
    
    def compile_qupulse(self, *experiments, **add_pars):
        self.decoded = Qupulse_decoder2(*experiments)
        print(self.decoded.measurement_pars)
        self.settings = Settings(self, self.decoded.measurement_pars, **add_pars)
        for measurement in self.settings:
            self.update_t_parameters(self.settings[measurement]["loop_range"], 
                                     self.settings[measurement]["loop_step_name"],
                                     measurement)
        self.settings.load()
        
    def measure1D(self):
        self._measurement_object.measurement_func = "%s: measure1D" % __name__
        self._prepare_measurement()
        pb = Progress_Bar(self._total_iterations)
        try:
            #self._acquire_log_functions()
            self._measure_vs_time(1, pb)
        finally:
            self._ro_backend.stop()
            #self._manip_backend.stop()
            self._end_measurement()
            
    def measure2D(self):        
        self._measurement_object.measurement_func = "%s: measure2D" % __name__        
        self._prepare_measurement(self._x_parameter)
        pb = Progress_Bar(len(self._x_parameter.values) * self._total_iterations)
        try:
            for x_val in self._x_parameter.values:
                self._x_parameter.set_function(x_val)
                self._acquire_log_functions()
                qkit.flow.sleep(self._x_parameter.wait_time)
                self._measure_vs_time(2, pb)
        finally:
            self._ro_backend.stop()
            #self._manip_backend.stop()
            self._end_measurement()
    
    def measure3D(self):        
        self._measurement_object.measurement_func = "%s: measure3D" % __name__
        self._prepare_measurement(self._x_parameter, self._y_parameter)
        pb = Progress_Bar(len(self._x_parameter.values) * len(self._y_parameter.values) * self._total_iterations)
        try:            
            direction = 1
            for x_val in self._x_parameter.values:
                self._x_parameter.set_function(x_val)
                self._acquire_log_functions()
                qkit.flow.sleep(self._x_parameter.wait_time)
                
                for y_val in self._y_parameter.values[::direction]:
                    self._y_parameter.set_function(y_val)
                    qkit.flow.sleep(self._y_parameter.wait_time)
                    self._measure_vs_time(3, pb)
                
                for dset in self._datasets.values():
                    dset.next_matrix()
                if self.meander_sweep: direction *= -1
        finally:
            self._ro_backend.stop()
            #self._manip_backend.stop()
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
    
# =============================================================================
# class Qupulse_decoder:
#     def __init__(self, qupulse_pt, qupulse_pars):
#         self.qupulse_pt = qupulse_pt
#         self.qupulse_pars = qupulse_pars
#         self.get_loop_start()
#         self.get_loop_stop()
#         self.get_loop_step()
#         self.get_measurement_parameters()
#         self.loop_range = np.arange(self.loop_start_value, self.loop_stop_value, self.loop_step_value) * 1e-9
#         self.loop_length = len(self.loop_range)
#         
#     @property
#     def qupulse_pt(self):
#         return self._qupulse_pt
#     @qupulse_pt.setter
#     def qupulse_pt(self, new_pt):
#         if not isinstance(new_pt, qupulse.pulses.loop_pulse_template.ForLoopPulseTemplate):
#             raise TypeError("Invalid pulse template. Must be a ForLoopPulseTemplate.")
#         self._qupulse_pt = new_pt
#     @property
#     def qupulse_pars(self):
#         return self._qupulse_pars
#     @qupulse_pars.setter
#     def qupulse_pars(self, new_pars):
#         if not isinstance(new_pars, dict):
#             raise TypeError("Invalid pulse parameters. Must be a dictionary.")
#         self._qupulse_pars = new_pars
#         
#     def get_loop_start(self):
#         key = self.qupulse_pt.loop_range.start.original_expression
#         if type(key) == str:
#             self.loop_start_name = key
#             self.loop_start_value = self.qupulse_pars[key]
#         elif type(key) == int:
#             self.loop_start_name = "for_loop_start"
#             self.loop_start_value = key
#         else:
#             raise TypeError("Data type of the original qupulse Expression is unknown")
# 
#     def get_loop_stop(self):
#         key = self.qupulse_pt.loop_range.stop.original_expression
#         if type(key) == str:
#             self.loop_stop_name = key
#             self.loop_stop_value = self.qupulse_pars[key]
#         elif type(key) == int:
#             self.loop_stop_name = "for_loop_stop"
#             self.loop_stop_value = key
#         else:
#             raise TypeError("Data type of the original qupulse Expression is unknown")
#     
#     def get_loop_step(self):
#         key = self.qupulse_pt.loop_range.step.original_expression
#         if type(key) == str:
#             self.loop_step_name = key
#             self.loop_step_value = self.qupulse_pars[key]
#         elif type(key) == int:
#             self.loop_step_name = "for_loop_step"
#             self.loop_step_value = key
#         else:
#             raise TypeError("Data type of the original qupulse Expression is unknown")
#     
#     def get_measurement_parameters(self):
#         try:
#             averages = self.qupulse_pars["n_rep"]
#         except KeyError:
#             warnings.warn("No repetitions per measurement defined. Defaulting to 1000.")
#             averages = 1000
#         
#         qupulse_prog = self.qupulse_pt.create_program(parameters = self.qupulse_pars)
#         self.measurement_pars = qupulse_prog.get_measurement_windows()
#         
#         for measurement in self.measurement_pars.keys():
#             if isinstance(averages, dict) and isinstance(averages[measurement], int):
#                 self.measurement_pars[measurement] = self.measurement_pars[measurement] + (averages[measurement],)
#             elif isinstance(averages, int):
#                 self.measurement_pars[measurement] = self.measurement_pars[measurement] + (averages,)
#             else:
#                 raise TypeError("Cannot set averages. Parameter entry must be an int or a dictionary containing ints.") 
# =============================================================================