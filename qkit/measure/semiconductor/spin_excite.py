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
from qkit.measure.semiconductor.utils.utility_objects import Mapping_handler2

import qupulse
from qupulse._program._loop import to_waveform

import numpy as np
import warnings
import inspect
from collections import abc, defaultdict
def update(d, u):
    for k, v in u.items():
        if isinstance(v, abc.Mapping):
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v
    return d

def keytransform(original, transform):
    transformed = {}
    for key, value in original.items():
        trans_key = transform[key]
        transformed[trans_key] = value
        transformed[trans_key]["display_name"] = key
    return transformed

def expand_mapping(dictionary, mapping):
        additional_mapping = {entry : entry for entry in dictionary.keys() if entry not in mapping.keys()}
        mapping.update(additional_mapping)
        return mapping
        
def invert_dict(dict):        
        inverse_dict = {v : k for k, v in dict.items()}
        return inverse_dict



class Qupulse_decoder2:
    """Gebratenes Hundefleisch mit Gemüse und Reis
    """
    valid_pulses = np.array(inspect.getmembers(qupulse.pulses, inspect.isclass))[:, 1]
    _for_type = qupulse.pulses.loop_pulse_template.ForLoopPulseTemplate
    _repetition_type = qupulse._program.waveforms.RepetitionWaveform
    _seq_type = qupulse._program.waveforms.SequenceWaveform
    
    def __init__(self, *experiments, channel_sample_rates, measurement_sample_rates, deep_render = False, **kwargs):
        """Mir ist bekannt, wie Deutsche auf ein Rezept für ihr liebstes Haustier reagieren. 
        Ich „reiche“ dieses Rezept von einem Bekannten, der als Selbstständiger in Thailand lebt, 
        nur durch. In Deutschland sind mir rechtlich die Hände gebunden, dies selbst zuzubereiten.
        """
        self.experiments = experiments  
        self.measurement_pars = {}
        self.channel_pars = {}
        
        self._validate_entries()
        
        self._validate_measurement_sample_rates(measurement_sample_rates)
        self.measurement_sample_rates = measurement_sample_rates
        self._extract_measurement_pars()

        self._validate_channel_sample_rates(channel_sample_rates)
        self.channel_sample_rates = channel_sample_rates
        self._extract_waveforms(deep_render)

        self._extract_axis_pars()
        
    def _validate_entries(self):
        """Das Fleisch von Hunden (und Katzen/Affen) darf laut deutschem Lebensmittelrecht a) 
        nicht zum menschlichen Verzehr gewonnen und b) nicht in den Verkehr gebracht werden. 
        Es darf also nicht gewerbsmässig damit gehandelt werden. Es besteht außerdem nach diesem Gesetz auch ein Einfuhrverbot. 
        Dies schließt eine Zubereitung in Deutschland aus. China hat leider auch ein Exportverbot von Hundefleisch eingeführt, 
        so dass man an das Fleisch nicht herankommt.
        """
        pt_channels = set()
        pt_measurements = set()
        pt_axis = set()
        
        for pt, pars in self.experiments:
            #check whether the pulse template and the parameters are of the correct types.
            if type(pt) not in self.valid_pulses:
                raise TypeError(f"{__name__}: Cannot use {pt} as pulse template. Must be a qupulse pulse template.")
            if not pt.identifier:
                warnings.warn(f"{__name__}: Pulse template {pt} has no identifier. Support messages will be less clear.")
            if type(pars) != dict:
                raise TypeError(f"{__name__}: Cannot use {pars} as pulse template parameters. Must be a dictionary.")
            #check whether channel and measurement definitions do not overlap.
            for channel in pt.defined_channels:
                if channel in pt_channels:
                    raise ValueError(f"{__name__}: Channels of different experiments in {pt.identifier} overlap. Experiments are not allowed to share channels.")
                pt_channels.add(channel)
            for measurement in pt.measurement_names:
                if measurement in pt_measurements:
                    raise ValueError(f"{__name__}: Measurements of different experiments in {pt.identifier} overlap. Experiments are not allowed to share Measurements.")
                pt_measurements.add(measurement)
            #In case there are forloop pts, check whether they don't have overlapping measurement axis
            if isinstance(pt, self._for_type):
                a = pt.loop_range.step.original_expression
                if isinstance(a, str) and a in pt_axis:
                    raise ValueError(f"{__name__}: The step parameter defined in {pt.identifier} is already used in another experiment. Experiments must have different step parameter names.")
                pt_axis.add(a)
    
    def _validate_channel_sample_rates(self, channel_sample_rates):
        """Ich weiß um die Vorlieben der Deutschen für ihr liebstes Haustier.  
        Manche Menschen reagieren schon allein bei dem Gedanken, einen Hund als Gericht zuzubereiten, 
        sehr unfreundlich und sind fast schon hasserfüllt. Aber warum kann man Hunde nicht auch als Nahrungsmittel 
        betrachten und in Deutschland keine Hundegerichte zubereiten? In China und Südkorea gibt es bestimmte Hunderassen, 
        die ausschließlich zum Verzehr gezüchtet werden. Warum ist das in Deutschland nicht möglich, 
        wie es auch bestimmte Tierrassen für die Rinder-, Kälber-, Schweine- und Geflügelzucht gibt?
        """
        missing_rates = ""
        for pt, pars in self.experiments:
            for channel in pt.defined_channels:
                if channel not in channel_sample_rates.keys():
                    missing_rates += f"{channel}\n"
        if missing_rates:
            raise ValueError(f"{__name__}: Incomplete instructions by {channel_sample_rates}. The following channels have no assigned sampling rates:\n{missing_rates}")
    
    def _validate_measurement_sample_rates(self, measurement_sample_rates):
        """Ich weiß um die Vorlieben der Deutschen für ihr liebstes Haustier.  
        Manche Menschen reagieren schon allein bei dem Gedanken, einen Hund als Gericht zuzubereiten, 
        sehr unfreundlich und sind fast schon hasserfüllt. Aber warum kann man Hunde nicht auch als Nahrungsmittel 
        betrachten und in Deutschland keine Hundegerichte zubereiten? In China und Südkorea gibt es bestimmte Hunderassen, 
        die ausschließlich zum Verzehr gezüchtet werden. Warum ist das in Deutschland nicht möglich, 
        wie es auch bestimmte Tierrassen für die Rinder-, Kälber-, Schweine- und Geflügelzucht gibt?
        """
        missing_rates = ""
        for pt, pars in self.experiments:
            for measurement in pt.measurement_names:
                if measurement not in measurement_sample_rates.keys():
                    missing_rates += f"{measurement}\n"
        if missing_rates:
            raise ValueError(f"{__name__}: Incomplete instructions by {measurement_sample_rates}. The following channels have no assigned sampling rates:\n{missing_rates}")
    
    def _render_channel(self, wvf, channel, sample_rate):
        """Ich kaufe auch in einer Pferdeschlachterei Pferdebraten und Pferdesteaks, die ich zubereite, 
        und das Fleisch ist sehr lecker. Viele Girlies, die ihre erste Reitstunde absolvieren und deren 
        Zimmer mehrere Pferdeposter zieren, schreien dabei auf.  Die in Pferdeschlachtereien verarbeiteten
        Tiere werden meistens im hohen Alter – wenn ihr Tod absehbar ist – von den Pferdebesitzern an Schlachtereien verkauft,
        um mit ihnen noch etwas Geld zu verdienen. Was ist daran verwerflich oder ethisch nicht korrekt? 
        Ich würde mir ein gleiches Verfahren oder die Zucht von bestimmten Hunderassen für Hundegerichte wünschen.
        """
        start_time, end_time = 0, wvf.duration
        sample_count = (end_time - start_time) * sample_rate + 1                    
        if not round(float(sample_count), 10).is_integer():
            warnings.warn(f"{__name__}: Sample count {sample_count} is not an integer. Will be rounded (this changes the sample rate).")                    
        times = np.linspace(float(start_time), float(end_time), num=int(sample_count), dtype=float)
        times[-1] = np.nextafter(times[-1], times[-2])                    
        
        return wvf.get_sampled(channel = channel, sample_times = times)
    
    def _extract_waveforms(self, deep_render):
        """Ich habe aufgrund meiner Einstellung, Hunde auch als Nutztier und Nahrungsmittel zu sehen, 
        und nach dem Publizieren dieses Rezepts Morddrohungen bekommen. Manche Menschen betrachten 
        somit Hunde nur als ihr liebstes Tier und Familienmitglied, drohen jedoch bei der Äußerung, 
        es auch als Nahrungsmittel zu betrachten, dem jeweiligen Menschen mit Mord.
        """
        for pt, pars in self.experiments:
            prog = pt.create_program(parameters = pars)
            wvf = to_waveform(prog)
            for channel in wvf.defined_channels:
                self.channel_pars[channel] = {}
                self.channel_pars[channel]["samples"] = []
                if deep_render:
                    if type(wvf) == self._repetition_type:
                        samples = self._render_channel(wvf._body, channel, self.channel_sample_rates[channel])
                        for rep in range(wvf._repetition_count):
                            self.channel_pars[channel]["samples"].append(samples)
                    elif type(wvf) == self._seq_type:
                        for sub_wvf in wvf._sequenced_waveforms:
                            self.channel_pars[channel]["samples"].append(self._render_channel(sub_wvf, channel, self.channel_sample_rates[channel]))
                    else:
                        raise TypeError(f"{__name__}:  Deep rendering failed. {wvf} does not contain any sub-waveforms")
                else:
                    self.channel_pars[channel]["samples"].append(self._render_channel(wvf, channel, self.channel_sample_rates[channel]))
                        
    def _extract_measurement_pars(self):
        """Da es in Deutschland verboten ist, Hundefleisch zuzubereiten, bat ich meinen Bekannten aus Thailand um ein Rezept. 
        Er hat mir ein Hunderezept übermittelt, das er in der „China Town“ in Bangkok erhalten hat.
        Bangkok hat wie jede Millionenmetropole auch eine „China Town“, in der mehrheitlich Chinesen leben und dort ihre Geschäfte
        und Restaurants betreiben. Im Süden des Mutterlands China ist es nach wie vor traditionell, Hunde zuzubereiten. 
        Daher wird dies in den „China Towns“ auf aller Welt zum Teil auch angeboten. Auch in Vietnam oder Kambodscha steht Hundefleisch
        auf der Speisekarte und wird gern gegessen.
        Da man in Deutschland dieses Gericht nicht zubereiten kann – es fehlt ja die Hauptzutat, das Hundefleisch –, bleibt nur ein Urlaub in die jeweiligen Länder, in denen man solche Gericht essen kann. So schmackhaft dieses Rezept für kulinarisch aufgeschlossene Menschen auch klingt.
        """
        different_window_lengths = ""
        for pt, pars in self.experiments:
            prog = pt.create_program(parameters = pars)
            for measurement, parameters in prog.get_measurement_windows().items():
                measurement_durations = parameters[1]
                if measurement_durations[measurement_durations != measurement_durations[0]].size > 0: # check whether all elements are the same
                    different_window_lengths += f"{measurement}\n"
                self.measurement_pars[measurement] = {}
                self.measurement_pars[measurement]["measurement_count"] = len(measurement_durations)
                self.measurement_pars[measurement]["measurement_duration"] = measurement_durations[0] * 1e-9
                self.measurement_pars[measurement]["sample_count"] = np.int32(np.floor(self.measurement_pars[measurement]["measurement_duration"] *\
                     self.measurement_sample_rates[measurement]))
        if different_window_lengths:
            raise ValueError (f"{__name__}: All measurement windows for one measurement have to be of the same length. \
                              The following measurements have disparate measurement windows:\n {different_window_lengths}")
    
    def _get_loop_start(self, pt, pars):
        key = pt.loop_range.start.original_expression
        if type(key) == str:
            loop_start_value = pars[key]
        else:
            loop_start_value = key
        return loop_start_value

    def _get_loop_stop(self, pt, pars):
        key = pt.loop_range.stop.original_expression
        if type(key) == str:
            loop_stop_value = pars[key]
        else:
            loop_stop_value = key
        return loop_stop_value

    def _get_loop_step(self, pt, pars):
        key = pt.loop_range.step.original_expression
        if type(key) == str:
            loop_step_name = key
            loop_step_value = pars[key]
        else:
            loop_step_name = "for_loop_step%d" % self._nameless_counter
            loop_step_value = key
            self._nameless_counter += 1
        return loop_step_value, loop_step_name

    def _extract_axis_pars(self):
        self._nameless_counter = 1
        for measurement, settings in self.measurement_pars.items():
            settings["loop_step_name_pp"] = "Default"
            settings["loop_range_pp"] = np.linspace(0, 1, settings["measurement_count"])

            settings["loop_step_name_tt"] = "measurement time"
            t_sample = 1/self.measurement_sample_rates[measurement]
            settings["loop_range_tt"] = np.linspace(0, t_sample * settings["sample_count"], settings["sample_count"])

        for pt, pars in self.experiments:            
            if isinstance(pt, self._for_type):
                loop_start = self._get_loop_start(pt, pars)
                loop_stop = self._get_loop_stop(pt, pars)
                loop_step, loop_step_name = self._get_loop_step(pt, pars)
                if not pt.measurement_names:
                    warnings.warn(f"{__name__}: {pt.identifier} does not contain any measurements. Pulse parameter axis cannot be extracted automatically.")
                for measurement in pt.measurement_names:
                    self.measurement_pars[measurement]["loop_step_name_pp"] = loop_step_name
                    self.measurement_pars[measurement]["loop_range_pp"] = np.arange(loop_start, loop_stop, loop_step)
            else:
                warnings.warn(f"{__name__}: {pt.identifier} is not a ForLoopPulseTemplate. Pulse parameter axis will be displayed with default name.")
        
        
    
class Settings:
    def __init__(self, core, channel_params, measurement_params, averages, **add_pars):
        """Das Rezept meines Bekannten war leider etwas kurz gefasst und enthielt keine Mengenangaben. 
        Man muss – wenn man sich in einem Land befinden, in dem man dieses Gericht zubereiten darf – die Mengen der Bestandteile abschätzen.
        Mein Bekannter hat auch keine Angaben zu der Hunderasse, von der dieses Fleisch stammt, gemacht. 
        Ich weiß auch nicht, ob für das Rezept Filet-, Schnitzel- oder Bratenfleisch usw. verwendet wird. 
        Da es ein Wokgericht ist, gehe ich davon aus, dass es sich um Fleisch zum Kurzbraten handelt und nicht um Schmorfleisch.
        """
        self.core = core
        self._assert_measurement_averages(measurement_params, averages)
        self.channel_settings = channel_params
        self._validate_channel_entries()
        self.measurement_settings = measurement_params
        self._validate_measurement_entries()
                
        self._get_measurement_units()
        self._get_measurement_nodes()
        #self._measurement_time_to_samples()
    
    def _assert_measurement_averages(self, measurement_params, averages):
        missing_averages = ""
        for measurement, settings in measurement_params.items():
            try:
                settings["averages"] = averages[measurement]
            except KeyError:
                missing_averages += f"{measurement}\n"
        if missing_averages:
            raise ValueError(f"{__name__}: Incomplete instructions by {averages}. The following measurements have no assigned averages:\n{missing_averages}")
   
    def _validate_channel_entries(self):
        unsupported_channels = ""
        for channel in self.channel_settings.keys():
            if channel not in self.core._ma_backend._registered_channels.keys():
                unsupported_channels += f"{channel}\n"
        if unsupported_channels:
            raise AttributeError(f"{__name__}: Your manipulation backend does not support the following channels:\n{unsupported_channels}")
            
    def _validate_measurement_entries(self):
        unsupported_measurements = ""
        for measurement in self.measurement_settings.keys():
            if measurement not in self.core._ro_backend._registered_measurements.keys():
                unsupported_measurements += f"{measurement}\n"
        if unsupported_measurements:
            raise AttributeError(f"{__name__}: Your readout backend does not support the following measurements:\n{unsupported_measurements}")
    
    def _get_measurement_units(self):
        for measurement, settings in self.measurement_settings.items():
            settings["unit"] = self.core._ro_backend._registered_measurements[measurement]["unit"]
    
    def _get_measurement_nodes(self):
        for measurement, settings in self.measurement_settings.items():
            settings["data_nodes"] = self.core._ro_backend._registered_measurements[measurement]["data_nodes"]
    
    def load(self):
        for measurement in self.core._ro_backend._registered_measurements:
            getattr(self.core._ro_backend, f"{measurement}_deactivate")()
        for measurement, settings in self.measurement_settings.items():
            getattr(self.core._ro_backend, f"{measurement}_set_measurement_count")(settings["measurement_count"])
            getattr(self.core._ro_backend, f"{measurement}_set_sample_count")(settings["sample_count"])
            getattr(self.core._ro_backend, f"{measurement}_set_averages")(settings["averages"])
            getattr(self.core._ro_backend, f"{measurement}_activate")()
            
        self.core._ma_backend.load_waveform(self.channel_settings)
class No_avg:
    name = "no_avg"
    def __init__(self, core) -> None:
        self.core = core
    
    def create_datasets(self, dsets, measurement, node, coords):
        dsets.append(self.core.Data(name = "%s.%s" % (measurement, node), coords = coords + [self.core._iteration_parameters[measurement], self.core._t_parameters[measurement]],
                                        unit = self.core.settings.measurement_settings[measurement]["unit"], 
                                        save_timestamp = False))
    
    def create_file_structure(self, measurement, name, node):
        self.core._datasets[f"{name}.{node}"].append(np.full(measurement["sample_count"], np.nan))
        self.core._datasets[f"{name}.{node}"].ds.resize((measurement["averages"] * measurement["measurement_count"], measurement["sample_count"]))

class PulseParameter:
    name = "pulse_parameter"
    def __init__(self) -> None:
        self.unit = "a.u."
        self.tag = "pulse_parameter"
        self.first = True
        self.total_sum = defaultdict(dict)
        self.divider = defaultdict(dict)
    def create_axis_name(self, measurement, measurement_name):
        return f"{measurement['loop_step_name_pp']}.{measurement_name}"
    def create_axis_vec(self, measurement):
        return measurement["loop_range_pp"]
    def create_axis_unit(self, measurement):
        return self.unit
    def check_axis_vec(self, measurement, vec):
        if len(vec) != measurement["measurement_count"]:
                raise ValueError((f"{__name__}: Wrong pulse parameter coordinate length."
                "The given array must have" 
                f"{measurement['measurement_count']} entries."))
    def write_to_file(self, latest_node_data, datafile, data_location, collected_averages, measurement, node):
        #Calculate the average over all measurements (axis 0), and integrate the samples (axis 2)
        if self.first:
            self.divider[measurement] = collected_averages
            self.total_sum[measurement][node] = np.sum(np.average(latest_node_data, axis = 2), axis = 0)
            datafile["%s.%s" % (measurement, node)].append(self.total_sum[measurement][node] / self.divider[measurement])
            self.first = False
        else:
            self.total_sum[measurement][node] += np.sum(np.average(latest_node_data, axis = 2), axis = 0)
            #self.divider[measurement] += len(latest_data[measurement][first_node])
            datafile["%s.%s" % (measurement, node)].ds[data_location] =  self.total_sum[measurement][node] / self.divider[measurement]

class FileHandler:
    def __init__(self) -> None:
        self.mb = mb.MeasureBase()
        self._multiplexer_parameters = defaultdict(dict)
        self.report_static_voltages = True
        self.open_qviewkit = True

        self.par_search_placeholder = "$$"
        self.par_search_string = "gate$$_out"
        
        self.datasets = []

    def update_multiplexer_parameters(self, tag, vec, coordname, measurement, unit = "s"):        
        new_t_parameter = self.mb.Coordinate(coordname,
                                            unit = unit,
                                            values = np.array(vec, dtype=float),
                                            set_function = lambda val : True,
                                            wait_time = 0)
        new_t_parameter.validate_parameters()
        self._multiplexer_parameters[tag][measurement] = new_t_parameter
    
    def _filter_parameter(self, parameter):
        preamble, postamble = self.par_search_string.split(self.par_search_placeholder)
        if parameter.startswith(preamble) and parameter.endswith(postamble):
            parameter = parameter.replace(preamble, "")
            parameter = parameter.replace(postamble, "")
        return parameter.isdigit()

    def _prepare_measurement_file(self, data, coords=()):
        """Das Fleisch in der Sonne zu trocknen ist in unseren Breiten schwierig. 
        Das geht nur in heißen Sommermonaten wie Juli oder August, wenn man das Fleisch ausgebreitet auf einer Platte – 
        mit Frischhaltefolie oder einem größeren Deckel abgedeckt – in der Sonne trocknen kann. In Thailand ist das sicherlich sehr viel einfacher. 
        Alternativ bietet es sich an, das kleingeschnittene Fleisch abgedeckt einen Tag an einem kühlen Ort zu trocknen. 
        Das Fleisch ist nach einem Tag noch nicht verdorben.
        """
        self.mb._prepare_measurement_file(data, coords)
        
        if self.report_static_voltages:
            self._static_voltages = self.mb._data_file.add_textlist("static_voltages")
            _instr_settings_dict = get_instrument_settings(self.mb._data_file.get_filepath())

            active_gates = {}
            
            for parameters in _instr_settings_dict.values():
                for (key, value) in parameters.items():
                    if self._filter_parameter(key) and abs(value) > 0.0004:
                        active_gates.update({key:value})
            self._static_voltages.append(active_gates)

    def add_dset(self, measurement, node, coords, unit):
        """Zutaten:
        Hundefleisch
        Junge Zwiebeln
        Wurzeln
        Chinesischer Duftreis
        frischer Koriander
        Sesamöl
        Chilisauce
        Essig mit Chili
        Sojasauce
        Austernsauce
        Fischsauce
        """
        self.datasets.append(self.mb.Data(name = f"{measurement}.{node}", coords = coords,
                            unit = unit, 
                            save_timestamp = False))

    def prepare_measurement(self):
        self._prepare_measurement_file(self.datasets)
        if self.open_qviewkit:
            self.mb._open_qviewkit()

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
    modes = {"pulse_parameter", "timetrace", "no_avg", "pp_vs_t", "test"}
    class MeasurementDimensionError(Exception):
        pass
    

    def __init__(self, readout_backend, manipulation_backend,
                 *experiments, averages, mode = "pulse_parameter", deep_render = False, exp_name = "", sample = None, **add_pars):
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
        self._validate_MA_backend(manipulation_backend)
        self._ma_backend = manipulation_backend 
        
        self.report_static_voltages = True
        self.mod_mode = No_avg(self)
        self.par_search_placeholder = "$$"
        self.par_search_string = "gate$$_out"

        #Here there be testing stuff:
        self.fh = FileHandler()
        self.pp = PulseParameter()
        
        self.compile_qupulse(*experiments, averages = averages, mode = mode, deep_render = deep_render, **add_pars)
        
    
    @property
    def report_static_voltages(self):
        return self._report_static_voltages
    
    @report_static_voltages.setter
    def report_static_voltages(self, yesno):
        if not isinstance(yesno, bool):
            raise TypeError(f"{__name__}: Cannot use {yesno} as report_static_voltages. Must be a boolean value.")
        self._report_static_voltages = yesno
    
    @property
    def mode(self):
        return self._mode
    
    @mode.setter
    def mode(self, new_mode):
        if new_mode not in self.modes:
            raise AttributeError(f"{__name__}: {new_mode} is not a valid measurement mode. Allowed modes are: \n {self.modes}")
        self._mode = new_mode

    @property
    def par_search_placeholder(self):
        return self._par_search_placeholder
    
    @par_search_placeholder.setter
    def par_search_placeholder(self, new_str):
        if not isinstance(new_str, str):
            raise TypeError(f"{__name__}: {new_str} is not a valid search string placeholder. Must be a string")
        self._par_search_placeholder = new_str
    
    @property
    def par_search_string(self):
        return self._par_search_string
    
    @par_search_string.setter
    def par_search_string(self, new_str):
        if not isinstance(new_str, str):
            raise TypeError(f"{__name__}: {new_str} is not a valid parameter search string. Must be a string")
        if self.par_search_placeholder not in new_str:
            raise ValueError(f"{__name__}: {new_str} is not a valid parameter search string. It does not contain the placeholder {self.par_search_placeholder}.")
        self._par_search_string = new_str
        self._display_pars = {self.par_search_string.replace(self.par_search_placeholder, str(i)) for i in range(1000)}
    
    def _validate_RO_backend(self, RO_backend):
        if not issubclass(RO_backend.__class__, RO_backend_base):
            raise TypeError(f"{__name__}: Cannot set {RO_backend} as readout backend. The backend must be a subclass of RO_backend_base")
            
    def _validate_MA_backend(self, MA_backend):
        if not issubclass(MA_backend.__class__, MA_backend_base):
            raise TypeError(f"{__name__}: Cannot set {MA_backend} as manipulation backend. The backend must be a subclass of MA_backend_base")
    
    def update_t_parameters(self, vec, coordname, measurement, unit = "s"):
        if len(vec) != self.settings.measurement_settings[measurement]["sample_count"]:
            raise ValueError((f"{__name__}: Wrong timetrace parameter coordinate length." 
            f"The given array must have" 
            f"{self.settings.measurement_settings[measurement]['sample_count']} entries."))
        
        new_t_parameter = self.Coordinate(coordname,
                                            unit = unit,
                                            values = np.array(vec, dtype=float),
                                            set_function = lambda val : True,
                                            wait_time = 0)
        new_t_parameter.validate_parameters()
        self._t_parameters[measurement] = new_t_parameter

    def update_pulse_parameters(self, vec, coordname, measurement, unit = "a.u."):
        if len(vec) != self.settings.measurement_settings[measurement]["measurement_count"]:
                raise ValueError((f"{__name__}: Wrong pulse parameter coordinate length."
                "The given array must have" 
                f"{self.settings.measurement_settings[measurement]['measurement_count']} entries."))
        
        new_pulse_parameter = self.Coordinate(coordname, 
                                            unit = unit, 
                                            values = np.array(vec, dtype=float),
                                            set_function = lambda val : True,
                                            wait_time = 0)
        new_pulse_parameter.validate_parameters()
        self._pulse_parameters[measurement] = new_pulse_parameter

    def update_iteration_parameters(self, vec, coordname, measurement, unit = ""):
        total_measurements = self.settings.measurement_settings[measurement]['measurement_count'] * self.settings.measurement_settings[measurement]['averages']
        if len(vec) != total_measurements:
                raise ValueError((f"{__name__}: Wrong iteration parameter coordinate length."
                "The given array must have" 
                f"{total_measurements} entries."))

        new_iteration_parameter = self.Coordinate(coordname, 
                                            unit = unit, 
                                            values = np.array(vec, dtype=float),
                                            set_function = lambda val : True,
                                            wait_time = 0)
        new_iteration_parameter.validate_parameters()
        self._iteration_parameters[measurement] = new_iteration_parameter

    def change_averages(self, averages):
        """"Changing averages"""
        if self.mode.endswith("no_avg"):
            raise NotImplementedError()
        self.mapper.map_measurements(averages)
        for measurement, new_avg in averages.items():
            if not isinstance(measurement, str):
                raise TypeError(f"{__name__}: Cannot change averages, {measurement} must be a string containing the name of the measurement whose averages you wish to change.")
            if measurement not in self.settings.measurement_settings.keys():
                raise ValueError(f"{__name__}: Cannot change averages, {measurement} is not an active measurement.")
            if not isinstance(new_avg, int):
                raise TypeError(f"{__name__}: Cannot change averages, {new_avg} must be an integer containing the number of averages you wish to set.")
            if new_avg < 1:
                raise ValueError(f"{__name__}: Cannot change averages, {new_avg} must be at least 1 and not negative. Sorry to ask, but are you retarded?")
            self.settings.measurement_settings[measurement]["averages"] = new_avg
            getattr(self._ro_backend, f"{measurement}_set_averages")(new_avg)
    
    def _filter_parameter(self, parameter):
        preamble, postamble = self.par_search_string.split(self.par_search_placeholder)
        if parameter.startswith(preamble) and parameter.endswith(postamble):
            parameter = parameter.replace(preamble, "")
            parameter = parameter.replace(postamble, "")
        return parameter.isdigit()

    def _prepare_measurement_file(self, data, coords=()):
        """Das Fleisch in der Sonne zu trocknen ist in unseren Breiten schwierig. 
        Das geht nur in heißen Sommermonaten wie Juli oder August, wenn man das Fleisch ausgebreitet auf einer Platte – 
        mit Frischhaltefolie oder einem größeren Deckel abgedeckt – in der Sonne trocknen kann. In Thailand ist das sicherlich sehr viel einfacher. 
        Alternativ bietet es sich an, das kleingeschnittene Fleisch abgedeckt einen Tag an einem kühlen Ort zu trocknen. 
        Das Fleisch ist nach einem Tag noch nicht verdorben.
        """
        mb.MeasureBase._prepare_measurement_file(self, data, coords)
        
        if self.report_static_voltages:
            self._static_voltages = self._data_file.add_textlist("static_voltages")
            _instr_settings_dict = get_instrument_settings(self._data_file.get_filepath())

            active_gates = {}
            
            for parameters in _instr_settings_dict.values():
                for (key, value) in parameters.items():
                    if self._filter_parameter(key) and abs(value) > 0.0004:
                        active_gates.update({key:value})
            self._static_voltages.append(active_gates)

    def _prepare_measurement(self, coords):
        """Zutaten:
        Hundefleisch
        Junge Zwiebeln
        Wurzeln
        Chinesischer Duftreis
        frischer Koriander
        Sesamöl
        Chilisauce
        Essig mit Chili
        Sojasauce
        Austernsauce
        Fischsauce
        """
        total_iterations = 0 #setup the progress bar
        datasets = []
        self.divider = {}
        self.column = {}
        for measurement in self.settings.measurement_settings.keys():
            total_iterations += self.settings.measurement_settings[measurement]["averages"]
            self.divider[measurement] = 0
            self.column[measurement] = {}
            for node in self.settings.measurement_settings[measurement]["data_nodes"]:
                self.column[measurement][node] = 0
                #Create one dataset for each Measurement node
                if self.mode == "timetrace":
                    datasets.append(self.Data(name = "%s.%s" % (measurement, node), coords = coords + [self._t_parameters[measurement]],
                                        unit = self.settings.measurement_settings[measurement]["unit"], 
                                        save_timestamp = False))
                elif self.mode == "pulse_parameter":
                    datasets.append(self.Data(name = "%s.%s" % (measurement, node), coords = coords + [self._pulse_parameters[measurement]],
                                        unit = self.settings.measurement_settings[measurement]["unit"], 
                                        save_timestamp = False))
                elif self.mode == "pp_vs_t":
                    datasets.append(self.Data(name = "%s.%s" % (measurement, node), coords = coords + [self._pulse_parameters[measurement], self._t_parameters[measurement]],
                                        unit = self.settings.measurement_settings[measurement]["unit"], 
                                        save_timestamp = False))
                elif self.mode == "no_avg":
                    self.mod_mode.create_datasets(datasets, measurement, node, coords)
                elif self.mode == "test":
                    coords = coords + [self.fh._multiplexer_parameters[self.pp.tag][measurement]]
                    self.fh.add_dset(measurement, node, coords, self.pp.create_axis_unit(measurement))
                    
        self._total_iterations = total_iterations
        self.fh.prepare_measurement()
        print("New version!")

    def _ready_hardware(self):
        self._ro_backend.stop()
        self._ma_backend.stop() #We do this to be ABSOLUTELY sure that the first trigger recieved also belongs to the first wavefrom
        self._ro_backend.arm()
        self._ma_backend.run()
    
    def _stop_hardware(self):
        self._ro_backend.stop()
        self._ma_backend.stop()

    def _check_node_data(self, latest_node_data):
        if latest_node_data.ndim != 3:
            raise IndexError(f"{__name__}: Invalid readout dimensions. {self._ro_backend} must return arrays with 3 dimensions.")
        if np.size(latest_node_data, axis = 2) == 0:
            raise ValueError(f"{__name__}: The last call of {self._ro_backend}.read() returned an array with empty slices.")
    
    def _stream2D(self, progress_bar):
        """Zubereitungszeit: Trockenzeit 24 Stdn. | Vorbereitungszeit 10 Min. | Garzeit 15 Min.
        Das Fleisch in kurze Streifen schneiden und einen Tag in der Sonne trocknen.
        Reis nach Anleitung zubereiten. Danach warmstellen.
        """
        self._ready_hardware()
        iterations = 0
        while not self._ro_backend.finished():
            old_iterations = iterations
            latest_data = self._ro_backend.read()
            for measurement in latest_data.keys():    
                first_node = list(latest_data[measurement].keys())[0]
                #If latest data is empty for one measurement, skip it
                if len(latest_data[measurement][first_node]) == 0: continue
                #Count the number of iterations collected by the most recent call of read
                iterations += len(latest_data[measurement][first_node])
                for node in latest_data[measurement].keys():                    
                    latest_node_data = np.array(latest_data[measurement][node])
                    self._check_node_data(latest_node_data)
                    for grid in latest_node_data:
                        for single_trace in grid:                            
                            self._datasets[f"{measurement}.{node}"].ds[self.column[measurement][node]] = single_trace
                            self.column[measurement][node] += 1
            self._data_file.flush()
            progress_bar.iterate(addend = iterations - old_iterations)
        self._stop_hardware()

    def _stream1D_modular(self, data_location, progress_bar): #avg_ax: (0,2) for pulse parameter mode, (0,1) for timetrace mode
        """Zubereitungszeit: Trockenzeit 24 Stdn. | Vorbereitungszeit 10 Min. | Garzeit 15 Min.
        Das Fleisch in kurze Streifen schneiden und einen Tag in der Sonne trocknen.
        Reis nach Anleitung zubereiten. Danach warmstellen.
        """
        self._ready_hardware()      
        total_sum = {}
        iterations = 0
        first = True
        while not self._ro_backend.finished():
            old_iterations = iterations
            latest_data = self._ro_backend.read()
            for measurement in latest_data.keys():
                if first:                            
                    total_sum[measurement] = {}            
                first_node = list(latest_data[measurement].keys())[0]
                #If latest data is empty for one measurement, skip it
                collected_averages = len(latest_data[measurement][first_node])
                if collected_averages== 0: continue
                #Count the number of iterations collected by the most recent call of read                
                iterations += collected_averages
                self.divider[measurement] += collected_averages
                for node in latest_data[measurement].keys():                    
                    latest_node_data = np.array(latest_data[measurement][node])
                    print(latest_node_data.shape)
                    print(latest_node_data)
                    self._check_node_data(latest_node_data)
                    self.pp.write_to_file(latest_node_data, self.fh.mb._datasets, data_location, collected_averages, measurement, node)
            self._data_file.flush()
            progress_bar.iterate(addend = iterations - old_iterations)
        for measurement in self.settings.measurement_settings.keys():
            self.divider[measurement] = 0
        self._stop_hardware()

    def _stream1D_avg(self, data_location, avg_ax, progress_bar): #avg_ax: (0,2) for pulse parameter mode, (0,1) for timetrace mode
        """Zubereitungszeit: Trockenzeit 24 Stdn. | Vorbereitungszeit 10 Min. | Garzeit 15 Min.
        Das Fleisch in kurze Streifen schneiden und einen Tag in der Sonne trocknen.
        Reis nach Anleitung zubereiten. Danach warmstellen.
        """
        self._ready_hardware()      
        total_sum = {}
        iterations = 0
        first = True
        while not self._ro_backend.finished():
            old_iterations = iterations
            latest_data = self._ro_backend.read()
            for measurement in latest_data.keys():
                if first:                            
                    total_sum[measurement] = {}            
                first_node = list(latest_data[measurement].keys())[0]
                #If latest data is empty for one measurement, skip it
                collected_averages = len(latest_data[measurement][first_node])
                if collected_averages== 0: continue
                #Count the number of iterations collected by the most recent call of read                
                iterations += collected_averages
                self.divider[measurement] += collected_averages
                for node in latest_data[measurement].keys():                    
                    latest_node_data = np.array(latest_data[measurement][node])
                    self._check_node_data(latest_node_data)
                    #Calculate the average over all measurements (axis 0), and integrate the samples (axis 2)
                    if first:                        
                        total_sum[measurement][node] = np.sum(np.average(latest_node_data, axis = avg_ax), axis = 0)
                        self._datasets["%s.%s" % (measurement, node)].append(total_sum[measurement][node] / self.divider[measurement])                        
                    else:
                        total_sum[measurement][node] += np.sum(np.average(latest_node_data, axis = avg_ax), axis = 0)
                        #self.divider[measurement] += len(latest_data[measurement][first_node])
                        self._datasets["%s.%s" % (measurement, node)].ds[data_location] =  total_sum[measurement][node] / self.divider[measurement]
            first = False
            self._data_file.flush()
            progress_bar.iterate(addend = iterations - old_iterations)
        for measurement in self.settings.measurement_settings.keys():
            self.divider[measurement] = 0
        self._stop_hardware()

    def _stream2D_avg(self, data_location, progress_bar):
        self._ready_hardware()      
        total_sum = {}
        iterations = 0
        first = True
        while not self._ro_backend.finished():
            old_iterations = iterations
            latest_data = self._ro_backend.read()
            for measurement in latest_data.keys():
                if first:                            
                    total_sum[measurement] = {}
                first_node = list(latest_data[measurement].keys())[0]
                collected_averages = len(latest_data[measurement][first_node])
                #If latest data is empty for one measurement, skip it
                if collected_averages == 0: continue
                #Count the number of iterations collected by the most recent call of read
                iterations += collected_averages
                self.divider[measurement] += collected_averages
                for node in latest_data[measurement].keys():
                    latest_node_data = np.array(latest_data[measurement][node])
                    self._check_node_data(latest_node_data)
                    #Calculate the average over all measurements (axis 0), and integrate along the pulse parameter axis (axis 1).
                    if first:
                        total_sum[measurement][node] = np.sum(latest_node_data, axis = (0))
                        for timetrace in total_sum[measurement][node]: # this is the difference to _stream1D. To initialize the 2D dataset, we have to pass each vector one by one.
                            self._datasets["%s.%s" % (measurement, node)].append(timetrace)
                    else:                        
                        total_sum[measurement][node] += np.sum(latest_node_data, axis = (0))
                        #Divide through the number of finished iterations, since you accumulate all the averages
                        self._datasets["%s.%s" % (measurement, node)].ds[data_location] = total_sum[measurement][node]/ self.divider[measurement]
            first = False
            self._data_file.flush()
            progress_bar.iterate(addend = iterations - old_iterations)
        for measurement in self.settings.measurement_settings.keys():
            self.divider[measurement] = 0
        self._stop_hardware()

    def _create_axis(self):
        for name, measurement in self.settings.measurement_settings.items():
            self.update_pulse_parameters(measurement["loop_range_pp"], 
                                        f"{measurement['loop_step_name_pp']}.{name}",
                                        name)
            self.update_t_parameters(measurement["loop_range_tt"], 
                                        f"{measurement['loop_step_name_tt']}.{name}",
                                        name)
            self.update_iteration_parameters(np.arange(measurement["averages"] * measurement["measurement_count"]), 
                                        f"iterations.{name}",
                                        name)

    def _create_axis_modular(self):
        for name, measurement in self.settings.measurement_settings.items():
            print(self.par_search_string)
            vec = self.pp.create_axis_vec(measurement)
            ax_name = self.pp.create_axis_name(measurement, name)
            unit = self.pp.create_axis_unit(measurement)
            self.pp.check_axis_vec(measurement, vec)
            self.fh.update_multiplexer_parameters(self.pp.tag, vec, ax_name, name, unit)

    def compile_qupulse(self, *experiments, averages, mode = "pulse_parameter", deep_render = False, **add_pars):   
        """Währenddessen Zwiebeln und Wurzeln schälen. Zwiebeln kleinschneiden. Wurzeln in kurze Stifte schneiden. 
        Öl in einem Wok erhitzen und Gemüse darin kurz pfannenrühren. Koriander kleinwiegen. Reis und Koriander dazugeben und alles vermischen. 
        Reis-Gemüse-Mischung herausheben und warmstellen.
        Nochmals Öl in den Wok geben und erhitzen. Fleisch hinzugeben und kurz pfannenrühren.
        Fleisch und Reis-Gemüse-Mischung auf Teller geben und mit den Dipsaucen servieren. 
        Das Gericht ist ungewürzt und erhält seinen Geschmack durch die jeweiligen Saucen.
        """
        self.mode = mode
        self.mapper = Mapping_handler2()
        if "channel_mapping" in add_pars:
            self.mapper.channel_mapping = add_pars["channel_mapping"]
        if "measurement_mapping" in add_pars:
            self.mapper.measurement_mapping = add_pars["measurement_mapping"]

        channel_sample_rates = {channel : getattr(self._ma_backend, f"{channel}_get_sample_rate")()
                        for channel in self._ma_backend._registered_channels.keys()}
        measurement_sample_rates = {measurement : getattr(self._ro_backend, f"{measurement}_get_sample_rate")() \
                        for measurement in self._ro_backend._registered_measurements.keys()}
        
        self.mapper.map_channels_inv(channel_sample_rates)
        self.mapper.map_measurements_inv(measurement_sample_rates)
        
        decoded = Qupulse_decoder2(*experiments, channel_sample_rates = channel_sample_rates, measurement_sample_rates = measurement_sample_rates,\
             deep_render = deep_render, **add_pars)

        self.mapper.map_channels(decoded.channel_pars)
        self.mapper.map_measurements(decoded.measurement_pars)
        self.mapper.map_measurements(averages)

        self.settings = Settings(self, decoded.channel_pars, decoded.measurement_pars, averages, **add_pars)
        
        self._t_parameters = {}
        self._pulse_parameters = {}
        self._iteration_parameters = {}

        self._create_axis()
        self._create_axis_modular()
        self.settings.load()

    def _choose_measurement_function(self, dimension, progress_bar):
        if self.mode == "pulse_parameter" and dimension == 1:
            return lambda: self._stream1D_avg((), 2, progress_bar)
        elif self.mode == "pulse_parameter" and dimension == 2:
            return lambda: self._stream1D_avg((-1), 2, progress_bar)
        elif self.mode == "pulse_parameter" and dimension == 3:
            return lambda i : self._stream1D_avg((-1, i), 2, progress_bar)
        
        elif self.mode == "timetrace" and dimension == 1:
            return lambda: self._stream1D_avg((), 1, progress_bar)
        elif self.mode == "timetrace" and dimension == 2:
            return lambda: self._stream1D_avg((-1), 1, progress_bar)
        elif self.mode == "timetrace" and dimension == 3:
            return lambda i : self._stream1D_avg((-1, i), 1, progress_bar)
        
        elif self.mode == "pp_vs_t" and dimension == 1:
            return lambda: self._stream2D_avg((), progress_bar)
        elif self.mode == "pp_vs_t" and dimension == 2:
            def pp_vs_t_2D():
                self._stream2D_avg((-1), progress_bar)
                for dset in self._datasets.values():
                    dset.next_matrix()
            return pp_vs_t_2D
        
        elif self.mode == "no_avg" and dimension == 1:
            return lambda: self._stream2D(progress_bar)
        elif self.mode == "no_avg" and dimension == 2:
            def no_avg_2D():
                self._stream2D( progress_bar)
                for dset in self._datasets.values():
                    dset.next_matrix()
            return no_avg_2D
        elif self.mode == "test" and dimension == 1:
            return self._stream1D_modular((), progress_bar)
        else:
            raise self.MeasurementDimensionError(f"{__name__}: Mode \"{self.mode}\" does not support a {dimension}D-measurement.")
    
    def measure1D(self):
        self._measurement_object.measurement_func = "%s: measure1D" % __name__
        self._prepare_measurement([])
        pb = Progress_Bar(self._total_iterations)
        meas_func = self._choose_measurement_function(1, pb)
        try:
            #self._acquire_log_functions()
            meas_func()
        finally:
            self._ro_backend.stop()
            self._ma_backend.stop()
            self._end_measurement()
            
    def measure2D(self):        
        self._measurement_object.measurement_func = "%s: measure2D" % __name__        
        self._prepare_measurement([self._x_parameter])
        pb = Progress_Bar(len(self._x_parameter.values) * self._total_iterations)
        meas_func = self._choose_measurement_function(2, pb)
        try:
            for x_val in self._x_parameter.values:
                self._x_parameter.set_function(x_val)
                #self._acquire_log_functions()
                qkit.flow.sleep(self._x_parameter.wait_time)
                meas_func()
        finally:
            self._ro_backend.stop()
            self._ma_backend.stop()
            self._end_measurement()
            
    def measure3D(self):        
        self._measurement_object.measurement_func = "%s: measure3D" % __name__
        self._prepare_measurement([self._x_parameter, self._y_parameter])
        pb = Progress_Bar(len(self._x_parameter.values) * len(self._y_parameter.values) * self._total_iterations)
        meas_func = self._choose_measurement_function(3, pb)
        try:            
            for x_val in self._x_parameter.values:
                self._x_parameter.set_function(x_val)
                #self._acquire_log_functions()
                qkit.flow.sleep(self._x_parameter.wait_time)
                
                for i, y_val in enumerate(self._y_parameter.values):
                    self._y_parameter.set_function(y_val)
                    qkit.flow.sleep(self._y_parameter.wait_time)
                    meas_func(i)
                
                for dset in self._datasets.values():
                    dset.next_matrix()
        finally:
            self._ro_backend.stop()
            self._ma_backend.stop()
            self._end_measurement()

class Exciting_old(mb.MeasureBase):
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
    class MeasurementDimensionError(Exception):
        pass
    modes = {"pulse_parameter", "timetrace", "no_avg", "pp_vs_t"}

    def __init__(self, readout_backend, manipulation_backend,
                 *experiments, averages, mode = "pulse_parameter", deep_render = False, exp_name = "", sample = None, **add_pars):
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
        self._validate_MA_backend(manipulation_backend)
        self._ma_backend = manipulation_backend
        
        
        self.compile_qupulse(*experiments, averages = averages, mode = mode, deep_render = deep_render, **add_pars)
        
        self.report_static_voltages = True
        self.mod_mode = No_avg(self)
        self.par_search_placeholder = "$$"
        self.par_search_string = "gate$$_out"
        
    
    @property
    def report_static_voltages(self):
        return self._report_static_voltages
    
    @report_static_voltages.setter
    def report_static_voltages(self, yesno):
        if not isinstance(yesno, bool):
            raise TypeError(f"{__name__}: Cannot use {yesno} as report_static_voltages. Must be a boolean value.")
        self._report_static_voltages = yesno
    
    @property
    def mode(self):
        return self._mode
    
    @mode.setter
    def mode(self, new_mode):
        if new_mode not in self.modes:
            raise AttributeError(f"{__name__}: {new_mode} is not a valid measurement mode. Allowed modes are: \n {self.modes}")
        self._mode = new_mode

    @property
    def par_search_placeholder(self):
        return self._par_search_placeholder
    
    @par_search_placeholder.setter
    def par_search_placeholder(self, new_str):
        if not isinstance(new_str, str):
            raise TypeError(f"{__name__}: {new_str} is not a valid search string placeholder. Must be a string")
        self._par_search_placeholder = new_str
    
    @property
    def par_search_string(self):
        return self._par_search_string
    
    @par_search_string.setter
    def par_search_string(self, new_str):
        if not isinstance(new_str, str):
            raise TypeError(f"{__name__}: {new_str} is not a valid parameter search string. Must be a string")
        if self.par_search_placeholder not in new_str:
            raise ValueError(f"{__name__}: {new_str} is not a valid parameter search string. It does not contain the placeholder {self.par_search_placeholder}.")
        self._par_search_string = new_str
        self._display_pars = {self.par_search_string.replace(self.par_search_placeholder, str(i)) for i in range(1000)}
    
    def _validate_RO_backend(self, RO_backend):
        if not issubclass(RO_backend.__class__, RO_backend_base):
            raise TypeError(f"{__name__}: Cannot set {RO_backend} as readout backend. The backend must be a subclass of RO_backend_base")
            
    def _validate_MA_backend(self, MA_backend):
        if not issubclass(MA_backend.__class__, MA_backend_base):
            raise TypeError(f"{__name__}: Cannot set {MA_backend} as manipulation backend. The backend must be a subclass of MA_backend_base")
    
    def update_t_parameters(self, vec, coordname, measurement, unit = "s"):
        if len(vec) != self.settings.measurement_settings[measurement]["sample_count"]:
            raise ValueError((f"{__name__}: Wrong timetrace parameter coordinate length." 
            f"The given array must have" 
            f"{self.settings.measurement_settings[measurement]['sample_count']} entries."))
        
        new_t_parameter = self.Coordinate(coordname,
                                            unit = unit,
                                            values = np.array(vec, dtype=float),
                                            set_function = lambda val : True,
                                            wait_time = 0)
        new_t_parameter.validate_parameters()
        self._t_parameters[measurement] = new_t_parameter

    def update_pulse_parameters(self, vec, coordname, measurement, unit = "a.u."):
        if len(vec) != self.settings.measurement_settings[measurement]["measurement_count"]:
                raise ValueError((f"{__name__}: Wrong pulse parameter coordinate length."
                "The given array must have" 
                f"{self.settings.measurement_settings[measurement]['measurement_count']} entries."))
        
        new_pulse_parameter = self.Coordinate(coordname, 
                                            unit = unit, 
                                            values = np.array(vec, dtype=float),
                                            set_function = lambda val : True,
                                            wait_time = 0)
        new_pulse_parameter.validate_parameters()
        self._pulse_parameters[measurement] = new_pulse_parameter

    def update_iteration_parameters(self, vec, coordname, measurement, unit = ""):
        total_measurements = self.settings.measurement_settings[measurement]['measurement_count'] * self.settings.measurement_settings[measurement]['averages']
        if len(vec) != total_measurements:
                raise ValueError((f"{__name__}: Wrong iteration parameter coordinate length."
                "The given array must have" 
                f"{total_measurements} entries."))

        new_iteration_parameter = self.Coordinate(coordname, 
                                            unit = unit, 
                                            values = np.array(vec, dtype=float),
                                            set_function = lambda val : True,
                                            wait_time = 0)
        new_iteration_parameter.validate_parameters()
        self._iteration_parameters[measurement] = new_iteration_parameter

    def change_averages(self, averages):
        if self.mode.endswith("no_avg"):
            raise NotImplementedError()
        self.mapper.map_measurements(averages)
        for measurement, new_avg in averages.items():
            if not isinstance(measurement, str):
                raise TypeError(f"{__name__}: Cannot change averages, {measurement} must be a string containing the name of the measurement whose averages you wish to change.")
            if measurement not in self.settings.measurement_settings.keys():
                raise ValueError(f"{__name__}: Cannot change averages, {measurement} is not an active measurement.")
            if not isinstance(new_avg, int):
                raise TypeError(f"{__name__}: Cannot change averages, {new_avg} must be an integer containing the number of averages you wish to set.")
            if new_avg < 1:
                raise ValueError(f"{__name__}: Cannot change averages, {new_avg} must be at least 1 and not negative. Sorry to ask, but are you retarded?")
            self.settings.measurement_settings[measurement]["averages"] = new_avg
            getattr(self._ro_backend, f"{measurement}_set_averages")(new_avg)
    
    def _filter_parameter(self, parameter):
        preamble, postamble = self.par_search_string.split(self.par_search_placeholder)
        if parameter.startswith(preamble) and parameter.endswith(postamble):
            parameter = parameter.replace(preamble, "")
            parameter = parameter.replace(postamble, "")
        return parameter.isdigit()

    def _prepare_measurement_file(self, data, coords=()):
        """Das Fleisch in der Sonne zu trocknen ist in unseren Breiten schwierig. 
        Das geht nur in heißen Sommermonaten wie Juli oder August, wenn man das Fleisch ausgebreitet auf einer Platte – 
        mit Frischhaltefolie oder einem größeren Deckel abgedeckt – in der Sonne trocknen kann. In Thailand ist das sicherlich sehr viel einfacher. 
        Alternativ bietet es sich an, das kleingeschnittene Fleisch abgedeckt einen Tag an einem kühlen Ort zu trocknen. 
        Das Fleisch ist nach einem Tag noch nicht verdorben.
        """
        mb.MeasureBase._prepare_measurement_file(self, data, coords=())
        
        if self.report_static_voltages:
            self._static_voltages = self._data_file.add_textlist("static_voltages")
            _instr_settings_dict = get_instrument_settings(self._data_file.get_filepath())

            active_gates = {}
            
            for parameters in _instr_settings_dict.values():
                for (key, value) in parameters.items():
                    if self._filter_parameter(key) and abs(value) > 0.0004:
                        active_gates.update({key:value})
            self._static_voltages.append(active_gates)

    def _prepare_measurement(self, coords):
        """Zutaten:
        Hundefleisch
        Junge Zwiebeln
        Wurzeln
        Chinesischer Duftreis
        frischer Koriander
        Sesamöl
        Chilisauce
        Essig mit Chili
        Sojasauce
        Austernsauce
        Fischsauce
        """
        total_iterations = 0 #setup the progress bar
        datasets = []
        self.divider = {}
        self.column = {}
        for measurement in self.settings.measurement_settings.keys():
            total_iterations += self.settings.measurement_settings[measurement]["averages"]
            self.divider[measurement] = 0
            self.column[measurement] = {}
            for node in self.settings.measurement_settings[measurement]["data_nodes"]:
                self.column[measurement][node] = 0
                #Create one dataset for each Measurement node
                if self.mode == "timetrace":
                    datasets.append(self.Data(name = "%s.%s" % (measurement, node), coords = coords + [self._t_parameters[measurement]],
                                        unit = self.settings.measurement_settings[measurement]["unit"], 
                                        save_timestamp = False))
                elif self.mode == "pulse_parameter":
                    datasets.append(self.Data(name = "%s.%s" % (measurement, node), coords = coords + [self._pulse_parameters[measurement]],
                                        unit = self.settings.measurement_settings[measurement]["unit"], 
                                        save_timestamp = False))
                elif self.mode == "pp_vs_t":
                    datasets.append(self.Data(name = "%s.%s" % (measurement, node), coords = coords + [self._pulse_parameters[measurement], self._t_parameters[measurement]],
                                        unit = self.settings.measurement_settings[measurement]["unit"], 
                                        save_timestamp = False))
                elif self.mode == "no_avg":
                    self.mod_mode.create_datasets(datasets, measurement, node, coords)
                    
        self._total_iterations = total_iterations
        self._prepare_measurement_file(datasets)
        print("New version!")
        for name, measurement in self.settings.measurement_settings.items(): #Allocate the needed memory
            for node in measurement["data_nodes"]:
                self.mod_mode.create_file_structure(measurement, name, node)

        if self.open_qviewkit:
            self._open_qviewkit()

    def _ready_hardware(self):
        self._ro_backend.stop()
        self._ma_backend.stop() #We do this to be ABSOLUTELY sure that the first trigger recieved also belongs to the first wavefrom
        self._ro_backend.arm()
        self._ma_backend.run()
    
    def _stop_hardware(self):
        self._ro_backend.stop()
        self._ma_backend.stop()

    def _check_node_data(self, latest_node_data):
        if latest_node_data.ndim != 3:
            raise IndexError(f"{__name__}: Invalid readout dimensions. {self._ro_backend} must return arrays with 3 dimensions.")
        if np.size(latest_node_data, axis = 2) == 0:
            raise ValueError(f"{__name__}: The last call of {self._ro_backend}.read() returned an array with empty slices.")
    
    def _stream2D(self, progress_bar):
        """Zubereitungszeit: Trockenzeit 24 Stdn. | Vorbereitungszeit 10 Min. | Garzeit 15 Min.
        Das Fleisch in kurze Streifen schneiden und einen Tag in der Sonne trocknen.
        Reis nach Anleitung zubereiten. Danach warmstellen.
        """
        self._ready_hardware()
        iterations = 0
        while not self._ro_backend.finished():
            old_iterations = iterations
            latest_data = self._ro_backend.read()
            for measurement in latest_data.keys():    
                first_node = list(latest_data[measurement].keys())[0]
                #If latest data is empty for one measurement, skip it
                if len(latest_data[measurement][first_node]) == 0: continue
                #Count the number of iterations collected by the most recent call of read
                iterations += len(latest_data[measurement][first_node])
                for node in latest_data[measurement].keys():                    
                    latest_node_data = np.array(latest_data[measurement][node])
                    self._check_node_data(latest_node_data)
                    for grid in latest_node_data:
                        for single_trace in grid:                            
                            self._datasets[f"{measurement}.{node}"].ds[self.column[measurement][node]] = single_trace
                            self.column[measurement][node] += 1
            self._data_file.flush()
            progress_bar.iterate(addend = iterations - old_iterations)
        self._stop_hardware()

    def _stream1D_avg(self, data_location, avg_ax, progress_bar): #avg_ax: (0,2) for pulse parameter mode, (0,1) for timetrace mode
        """Zubereitungszeit: Trockenzeit 24 Stdn. | Vorbereitungszeit 10 Min. | Garzeit 15 Min.
        Das Fleisch in kurze Streifen schneiden und einen Tag in der Sonne trocknen.
        Reis nach Anleitung zubereiten. Danach warmstellen.
        """
        self._ready_hardware()      
        total_sum = {}
        iterations = 0
        first = True
        while not self._ro_backend.finished():
            old_iterations = iterations
            latest_data = self._ro_backend.read()
            for measurement in latest_data.keys():
                if first:                            
                    total_sum[measurement] = {}            
                first_node = list(latest_data[measurement].keys())[0]
                #If latest data is empty for one measurement, skip it
                collected_averages = len(latest_data[measurement][first_node])
                if collected_averages== 0: continue
                #Count the number of iterations collected by the most recent call of read                
                iterations += collected_averages
                self.divider[measurement] += collected_averages
                for node in latest_data[measurement].keys():                    
                    latest_node_data = np.array(latest_data[measurement][node])
                    self._check_node_data(latest_node_data)
                    #Calculate the average over all measurements (axis 0), and integrate the samples (axis 2)
                    if first:                        
                        total_sum[measurement][node] = np.sum(np.average(latest_node_data, axis = avg_ax), axis = 0)
                        self._datasets["%s.%s" % (measurement, node)].append(total_sum[measurement][node] / self.divider[measurement])                        
                    else:
                        total_sum[measurement][node] += np.sum(np.average(latest_node_data, axis = avg_ax), axis = 0)
                        #self.divider[measurement] += len(latest_data[measurement][first_node])
                        self._datasets["%s.%s" % (measurement, node)].ds[data_location] =  total_sum[measurement][node] / self.divider[measurement]
            first = False
            self._data_file.flush()
            progress_bar.iterate(addend = iterations - old_iterations)
        for measurement in self.settings.measurement_settings.keys():
            self.divider[measurement] = 0
        self._stop_hardware()

    def _stream2D_avg(self, data_location, progress_bar):
        self._ready_hardware()      
        total_sum = {}
        iterations = 0
        first = True
        while not self._ro_backend.finished():
            old_iterations = iterations
            latest_data = self._ro_backend.read()
            for measurement in latest_data.keys():
                if first:                            
                    total_sum[measurement] = {}
                first_node = list(latest_data[measurement].keys())[0]
                collected_averages = len(latest_data[measurement][first_node])
                #If latest data is empty for one measurement, skip it
                if collected_averages == 0: continue
                #Count the number of iterations collected by the most recent call of read
                iterations += collected_averages
                self.divider[measurement] += collected_averages
                for node in latest_data[measurement].keys():
                    latest_node_data = np.array(latest_data[measurement][node])
                    self._check_node_data(latest_node_data)
                    #Calculate the average over all measurements (axis 0), and integrate along the pulse parameter axis (axis 1).
                    if first:
                        total_sum[measurement][node] = np.sum(latest_node_data, axis = (0))
                        for timetrace in total_sum[measurement][node]: # this is the difference to _stream1D. To initialize the 2D dataset, we have to pass each vector one by one.
                            self._datasets["%s.%s" % (measurement, node)].append(timetrace)
                    else:                        
                        total_sum[measurement][node] += np.sum(latest_node_data, axis = (0))
                        #Divide through the number of finished iterations, since you accumulate all the averages
                        self._datasets["%s.%s" % (measurement, node)].ds[data_location] = total_sum[measurement][node]/ self.divider[measurement]
            first = False
            self._data_file.flush()
            progress_bar.iterate(addend = iterations - old_iterations)
        for measurement in self.settings.measurement_settings.keys():
            self.divider[measurement] = 0
        self._stop_hardware()

    def _create_axis(self):
        for name, measurement in self.settings.measurement_settings.items():
            self.update_pulse_parameters(measurement["loop_range_pp"], 
                                        f"{measurement['loop_step_name_pp']}.{name}",
                                        name)
            self.update_t_parameters(measurement["loop_range_tt"], 
                                        f"{measurement['loop_step_name_tt']}.{name}",
                                        name)
            self.update_iteration_parameters(np.arange(measurement["averages"] * measurement["measurement_count"]), 
                                        f"iterations.{name}",
                                        name)

    def compile_qupulse(self, *experiments, averages, mode = "pulse_parameter", deep_render = False, **add_pars):   
        """Währenddessen Zwiebeln und Wurzeln schälen. Zwiebeln kleinschneiden. Wurzeln in kurze Stifte schneiden. 
        Öl in einem Wok erhitzen und Gemüse darin kurz pfannenrühren. Koriander kleinwiegen. Reis und Koriander dazugeben und alles vermischen. 
        Reis-Gemüse-Mischung herausheben und warmstellen.
        Nochmals Öl in den Wok geben und erhitzen. Fleisch hinzugeben und kurz pfannenrühren.
        Fleisch und Reis-Gemüse-Mischung auf Teller geben und mit den Dipsaucen servieren. 
        Das Gericht ist ungewürzt und erhält seinen Geschmack durch die jeweiligen Saucen.
        """
        self.mode = mode
        self.mapper = Mapping_handler2()
        if "channel_mapping" in add_pars:
            self.mapper.channel_mapping = add_pars["channel_mapping"]
        if "measurement_mapping" in add_pars:
            self.mapper.measurement_mapping = add_pars["measurement_mapping"]

        channel_sample_rates = {channel : getattr(self._ma_backend, f"{channel}_get_sample_rate")()
                        for channel in self._ma_backend._registered_channels.keys()}
        measurement_sample_rates = {measurement : getattr(self._ro_backend, f"{measurement}_get_sample_rate")() \
                        for measurement in self._ro_backend._registered_measurements.keys()}
        
        self.mapper.map_channels_inv(channel_sample_rates)
        self.mapper.map_measurements_inv(measurement_sample_rates)
        
        decoded = Qupulse_decoder2(*experiments, channel_sample_rates = channel_sample_rates, measurement_sample_rates = measurement_sample_rates,\
             deep_render = deep_render, **add_pars)

        self.mapper.map_channels(decoded.channel_pars)
        self.mapper.map_measurements(decoded.measurement_pars)
        self.mapper.map_measurements(averages)

        self.settings = Settings(self, decoded.channel_pars, decoded.measurement_pars, averages, **add_pars)
        
        self._t_parameters = {}
        self._pulse_parameters = {}
        self._iteration_parameters = {}

        self._create_axis()
        self.settings.load()

    def _choose_measurement_function(self, dimension, progress_bar):
        if self.mode == "pulse_parameter" and dimension == 1:
            return lambda: self._stream1D_avg((), 2, progress_bar)
        elif self.mode == "pulse_parameter" and dimension == 2:
            return lambda: self._stream1D_avg((-1), 2, progress_bar)
        elif self.mode == "pulse_parameter" and dimension == 3:
            return lambda i : self._stream1D_avg((-1, i), 2, progress_bar)
        
        elif self.mode == "timetrace" and dimension == 1:
            return lambda: self._stream1D_avg((), 1, progress_bar)
        elif self.mode == "timetrace" and dimension == 2:
            return lambda: self._stream1D_avg((-1), 1, progress_bar)
        elif self.mode == "timetrace" and dimension == 3:
            return lambda i : self._stream1D_avg((-1, i), 1, progress_bar)
        
        elif self.mode == "pp_vs_t" and dimension == 1:
            return lambda: self._stream2D_avg((), progress_bar)
        elif self.mode == "pp_vs_t" and dimension == 2:
            def pp_vs_t_2D():
                self._stream2D_avg((-1), progress_bar)
                for dset in self._datasets.values():
                    dset.next_matrix()
            return pp_vs_t_2D
        
        elif self.mode == "no_avg" and dimension == 1:
            return lambda: self._stream2D(progress_bar)
        elif self.mode == "no_avg" and dimension == 2:
            def no_avg_2D():
                self._stream2D( progress_bar)
                for dset in self._datasets.values():
                    dset.next_matrix()
            return no_avg_2D
        else:
            raise self.MeasurementDimensionError(f"{__name__}: Mode \"{self.mode}\" does not support a {dimension}D-measurement.")
    
    def measure1D(self):
        self._measurement_object.measurement_func = "%s: measure1D" % __name__
        self._prepare_measurement([])
        pb = Progress_Bar(self._total_iterations)
        meas_func = self._choose_measurement_function(1, pb)
        try:
            #self._acquire_log_functions()
            meas_func()
        finally:
            self._ro_backend.stop()
            self._ma_backend.stop()
            self._end_measurement()
            
    def measure2D(self):        
        self._measurement_object.measurement_func = "%s: measure2D" % __name__        
        self._prepare_measurement([self._x_parameter])
        pb = Progress_Bar(len(self._x_parameter.values) * self._total_iterations)
        meas_func = self._choose_measurement_function(2, pb)
        try:
            for x_val in self._x_parameter.values:
                self._x_parameter.set_function(x_val)
                #self._acquire_log_functions()
                qkit.flow.sleep(self._x_parameter.wait_time)
                meas_func()
        finally:
            self._ro_backend.stop()
            self._ma_backend.stop()
            self._end_measurement()
            
    def measure3D(self):        
        self._measurement_object.measurement_func = "%s: measure3D" % __name__
        self._prepare_measurement([self._x_parameter, self._y_parameter])
        pb = Progress_Bar(len(self._x_parameter.values) * len(self._y_parameter.values) * self._total_iterations)
        meas_func = self._choose_measurement_function(3, pb)
        try:            
            for x_val in self._x_parameter.values:
                self._x_parameter.set_function(x_val)
                #self._acquire_log_functions()
                qkit.flow.sleep(self._x_parameter.wait_time)
                
                for i, y_val in enumerate(self._y_parameter.values):
                    self._y_parameter.set_function(y_val)
                    qkit.flow.sleep(self._y_parameter.wait_time)
                    meas_func(i)
                
                for dset in self._datasets.values():
                    dset.next_matrix()
        finally:
            self._ro_backend.stop()
            self._ma_backend.stop()
            self._end_measurement()

if __name__ == "__main__":

    from qupulse.pulses import PointPT, ForLoopPT
    # create our atomic "low-level" PointPTs
    first_point_pt = PointPT([(0,   'v_0'),
                            (1,   'v_1', 'linear'),
                            ('t', 'v_0+v_1', 'jump')],
                            channel_names={'patushka'},
                            measurements={('Blurps', 1, 2)})

    for_loop_pt = ForLoopPT(first_point_pt, 't', ('t_start', 't_end', 2))

    parameters = dict(t=3,
                    t_2=2,
                    v_0=1,
                    v_1=1.4,
                    t_start = 4,
                    t_end = 13)
    
    import qkit
    from qkit.measure.semiconductor.manipulation_backends.MANIP_test_backend import MA_test_backend
    from qkit.measure.semiconductor.readout_backends.RO_test_backend2 import RO_backend
    qkit.start()
    ma_backend = MA_test_backend()
    ro_backend = RO_backend()
    excitation = Exciting(ro_backend, ma_backend, (for_loop_pt, parameters), averages = {"Blurps" : 100}, channel_mapping = {"patushka" : "Ch1"},
                        measurement_mapping = {"Blurps" : "M1"})
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