''' The measurement script is similar to the working point modul.
    It uses a step variable to generate a list of values
    that the working point runs through during a measurement
    and ensures that all output parameters are valid.
    A list of values for the sweep variable is also generated 
    to save and plot the measurement traces.
    It should be noted that the values generated for the sweep variable
    are not the true values that are set during the measurement,
    as the true values are set with a lower rate than the sample rate
    You could think of it as a list of operating points,
    which it is not really, as it only contains the values
    of the working points.
        Ensuring for valid outputs should mostly be set in the measurement instruments driver,
        cause valid values for outputs depends on hard wired measurement setup.
        So some validation thats not needed here is not implemented. '''

import logging as log
import numpy as np
import time
import qkit
from qkit.measure.magnetoconductance.spin_tune_ST import Tuning_ST
from qkit.measure.magnetoconductance.working_point import WorkingPoint
from qkit.storage.hdf_constants import analysis_types
from qkit.drivers.adwin_spin_transistor import adwin_spin_transistor


def calc_r(x, y):
    ''' calc func for amplitude from lockin'''
    return np.sqrt(np.square(x) + np.square(y))

def calc_theta(x, y):
    ''' calc func for phase shift from lockin'''
    return np.arctan2(y, x)

class MeasurementScript():
    ''' The Measurement Script generates a set of values for the WorkingPoint'''

    def __init__(self,anna:adwin_spin_transistor,hf=None,**kwargs):
        # define valid inputs
        self.valid_step_vars = ['vg','vd','N','bt','bp','phi','psi','theta']
        self.valid_sweep_vars = ['vg','vd','bt','bp','phi','psi','theta']
        self.valid_wp_mode = ['normal','sweep']
        self.valid_measure_mode = ['static','sweep']        # static mode not availible yet
        self.valid_inputs = ['raw','inph','quad']
        self.valid_traces = ['trace','retrace','difference']
        self.valid_calc = ['amp','phase']
        self.valid_analysis = ['polarplot','histogramm']
        self.max_rate_config = {'bx':0.1,'by':0.1,'bz':0.1,'bp':0.1,'bt':0.1,'vg':0.1,'vd':0.1}     	# rate in T(/V) per sec
        self.unit = {'inph':'V','quad':'V','raw':'V','amp':'V','phase':''}
        self.valids = {'step':self.valid_step_vars,'sweep':self.valid_sweep_vars,
                        'wp':self.valid_wp_mode,'measure':self.valid_measure_mode,
                        'traces':self.valid_traces,'inputs':self.valid_inputs,
                        'calc':self.valid_calc,'maxrate':self.max_rate_config,
                        'analysis':self.valid_analysis}

        # define needed value dicts and lists
        self.analysis = []
        self.analysis_params = {}
        self._sph = {'theta': 0, 'phi': 0, 'psi': 0, 'bp': 0, 'bt': 0}
        self._sweep = {'var_name':None,'start':None,'stop':None,'unit':None,
                        'rate':None,'duration':None,'values':None}
        self._step = {'var_name':None,'start':None,'stop':None,'unit':None,
                        'step_size':None,'values':None}
        self._modes = {'wp':None,'measure':None}
        self._volts = {'vd':None,'vg':None}
        self._lockin = {'freq':None,'amp':None,'tao':None,'init_time':None,'sample_rate':500e3}
        self._inputs = {'retrace':False,'inputs':[]}
        self._data = {'temp_save':{'inph':[],'quad':[],'raw':[],
                                'amp':[],'phase':[]},              # todo: add create_temp_save
                        'save':{'inph':[],'quad':[],'raw':[],
                                'amp':[],'phase':[]},
                        'plot':{'inph':[],'quad':[],'raw':[],
                                'amp':[],'phase':[]}}
        self.set_functions = {'sph':self.set_sph,'sweep':self.set_sweep,'step':self.set_step,
                            'modes':self.set_modes,'volts':self.set_volts,'lockin':self.set_lockin,
                            'data':self.set_data,'hard_config':self.set_hard_config,'analysis':self.set_analysis,
                            'soft_config':self.set_soft_config,'adwin_bootload':self.set_adwin_bootload,
                            'analysis_params':self.set_analysis_params}

        # if hf is not None:
        #     self.load_settings()              # todo: load measurement setup from h5file
        self.set_(**kwargs)             # set all values
        self.anna = anna
        self.update_script()            # start script for generating measurement

    def update_script(self):
        ''' genererate measurement setup'''
        self.create_tuning()            # create Tuning instance
        self.create_output_channel()    # create output channel for adwin
        self.complete_data()            # generate data save and temp_save dicts
        self.add_inputs()               # generate input dict
        self.create_inputs()            # create a dict of the input variables from the measurement
        self.register_measurement()     # register measure function
        self.set_node_bounds()          # create bounds for input variables from the measurement
        self.activate_measurement()     # activate measurement
        self.start_lockin()             # start lockin signal
        self.update_lockin()            # get real lockin data from adwin
        self.generate_sweep()           # generate sweep values
        self.generate_steps()           # generate step values, if not possible -> later only 1D measurement
        self.set_parameter()            # set x/y coordinates from sweep (and step) values
        self.init_wps()                 # init start and stop wp of first sweep
        self.start_sweep()              # start sweep to the first wp of the measurement
        self.show_plots()               # certain names from datasets to plot
        self.prepare_measurement_datasets()
        self.prepare_measurement_datafile()
        self.add_view()                 # add view datasets with information for additional live plots
        self.add_analysis()             # add analysis datasets with information for analysis plots

    def end_measurement(self):
        ''' end measurement'''
        self.anna.stop_measurement()
        self.tune._qvk_process.terminate()

    def prepare_measurement_datasets(self):
        ''' prepare datasets for measurement'''
        if self.dim == 2:
            self.ds = self.tune.multiplexer.prepare_measurement_datasets([self._x_parameter, self._y_parameter])
        elif self.dim == 1:
            self.ds = self.tune.multiplexer.prepare_measurement_datasets([self._x_parameter])

    def prepare_measurement_datafile(self):
        ''' prepare .hdf/h5 file for measurement'''
        self.tune._prepare_measurement_file(self.ds)
        self.coordinates = self.tune._coordinates
        self.datasets = self.tune._datasets
        self.datafile = self.tune._data_file

    def create_tuning(self):
        ''' creates instance of class Tuning_ST(Tuning)'''
        self.tune = Tuning_ST()
        self.tune.qviewkit_singleInstance = True

    def create_output_channel(self):
        ''' create output channel dictionary'''
        self.outs = {key: val['channel'] for key, val in self.hard_config['outputs'].items()}

    def show_plots(self):
        ''' create list of datasets to plot'''
        plotted_data = []
        if self._modes['measure'] == 'sweep':
            for key, val in self._data['plot'].items():
                for key1 in val:
                        plotted_data.append(f'sweep_measure.{key}_{key1}')
        if plotted_data:
            self.plots = plotted_data
        else:
            self.plots = None

    def start_measurement(self):
        ''' start activated measurement'''
        if self.dim == 1:
            self.tune.measure1D(self.plots)
        elif self.dim == 2:
            self.tune.measure2D(self.plots)
        else:
            assert ModuleNotFoundError

    def add_view(self):
        ''' adds 1D views'''
        for key in self.inputs_dict.keys():
            if 'retrace' in key:
                if self.dim == 2:
                    view = self.datafile.add_view(name=key.replace("_retrace",""),x=self.coordinates[self._y_parameter.name],y=self.datasets['sweep_measure.'+key])
                    view.add(x=self.coordinates[self._y_parameter.name], y=self.datasets['sweep_measure.'+key.replace("retrace","trace")])
                else:
                    view = self.datafile.add_view(name=key.replace("_retrace",""), x=self.coordinates[self._x_parameter.name], y=self.datasets['sweep_measure.'+key])
                    view.add(x=self.coordinates[self._x_parameter.name], y=self.datasets['sweep_measure.'+key.replace("retrace","trace")])
            if 'difference' in key:
                if self.dim == 2:
                    view = self.datafile.add_view(name=key, x=self.coordinates[self._y_parameter.name], y=self.datasets['sweep_measure.'+key])
                else:
                    view = self.datafile.add_view(name=key, x=self.coordinates[self._x_parameter.name], y=self.datasets['sweep_measure.'+key])

    def add_analysis(self):
        ''' adds analysis, like polar plot or histogramm'''
        for key in self.inputs_dict.keys():
            if 'difference' in key:
                if 'polarplot' in self.analysis:
                    self.datafile.add_analysis(name=f'{key}_polarplot', x=self.coordinates[self._x_parameter.name],
                                                y=self.coordinates[self._y_parameter.name], z=self.datasets['sweep_measure.'+key],
                                                analysis_type = analysis_types['polarplot'], analysis_params=self.analysis_params)
            elif 'trace' in key:
                if 'histogramm' in self.analysis:
                    self.datafile.add_analysis(name=f'{key}_histogramm', x=self.coordinates[self._x_parameter.name],
                                            y=self.coordinates[self._y_parameter.name], z=self.datasets['sweep_measure.'+key],
                                            analysis_type = analysis_types['histogramm'], analysis_params=self.analysis_params)

    def set_parameter(self):
        ''' setter for x/y parameter of measurement'''
        if self.dim == 1:
            self.tune.set_x_parameters(self._sweep['values'], self._sweep['var_name'], None, self._sweep['unit'])
            self._x_parameter = self.tune._x_parameter
        elif self.dim == 2:
            self.tune.set_x_parameters(self._step['values'], self._step['var_name'], self.wp_setter, self._step['unit'])
            self.tune.set_y_parameters(self._sweep['values'], self._sweep['var_name'], None, self._sweep['unit'])
            self._x_parameter = self.tune._x_parameter
            self._y_parameter = self.tune._y_parameter

    def update_lockin(self):
        ''' updates the sample rate and lockin frequency data in the script
        with real data readout from adwin -> no new lockin signal'''
        self.set_lockin(**{'freq':self.anna.adw.Get_FPar(24),'sample_rate':self.anna.adw.Get_FPar(26)})

    def get_wp(self):
        ''' getter function for last working point of adwin'''
        return self.anna.read_outputs()

    def start_sweep(self):
        ''' start sweep from adwin outputs to the first wp of the measurement'''
        outs_start = self.get_wp()
        start_time=0
        for key,val in self.wp_start.outs.items():
            duration = abs(val - outs_start[self.hard_config['outputs'][key]['channel']-1])/self.valids['maxrate'][key]
            if start_time < duration:
                start_time = duration
        log.info(f"Sweeping to start working point! Sweep durtion is {round(start_time,2)}s")
        self.ramp_to_wp(dt=start_time)
        time.sleep(5)

    def get_hard_config(self):
        ''' getter function for hard config of adwin'''
        return self.hard_config

    def get_soft_config(self):
        ''' getter function for soft config of adwin'''
        return self.soft_config

    def start_lockin(self):
        ''' start lockin signal'''
        self.anna.init_measurement('lockin', self._lockin['sample_rate'], bias=self._volts['vd'], inputs=self._inputs['inputs'],
                                    amplitude=self._lockin['amp'], frequency=self._lockin['freq'], tao=self._lockin['tao'])
        time.sleep(1)

    def stop_lockin(self):
        ''' stop lockin signal'''
        self.anna.init_measurement('lockin', self._lockin['sample_rate'], bias=self._volts['vd'], inputs=self._data['measure']['inputs'],
                                    amplitude=0, frequency=self._lockin['freq'], tao=self._lockin['tao'])

    def sweep_measure(self):
        ''' measure sweep and generate data dict'''
        trace,retrace=None,None
        trace = self.anna.sweep_measure(self.wp_stop.outs, duration=self._sweep['duration'])
        if self._inputs['retrace']:
            retrace = self.anna.sweep_measure(self.wp_start.outs, duration=self._sweep['duration'])
        sample_rate = int(self.anna.adw.Get_FPar(26)*self.anna.adw.Get_FPar(21))
        values_dict = {}    # dictionary contains all the data required to calculate the data to be saved
        for key,val in self._data['temp_save'].items():
            if val:
                if key in self.valid_inputs:                        # inph, quad and raw data
                    tr, rt, diff = [], [], []
                    for key1 in val:
                        if key1 == 'trace':
                            tr = trace[key].astype(np.float32)[:sample_rate]
                        elif key1 == 'retrace':
                            rt = np.flip(retrace[key].astype(np.float32)[:sample_rate])
                    if 'difference' in val:
                        if isinstance(tr, np.ndarray) and isinstance(rt, np.ndarray):
                            diff = rt - tr
                        else:
                            assert ValueError
                    if isinstance(tr, np.ndarray):
                        values_dict[f'{key}_trace']=tr
                    if isinstance(rt, np.ndarray):
                        values_dict[f'{key}_retrace']=rt
                    if isinstance(diff, np.ndarray):
                        values_dict[f'{key}_difference']=diff
        for key,val in self._data['temp_save'].items():             # amp and phase data calculation
            if val:
                if key in self.valid_calc:
                    amp, phase = {'trace':[],'retrace':[],'difference':[]}, {'trace':[],'retrace':[],'difference':[]}
                    for key1 in val:
                        if (values_dict.get(f'inph_{key1}') is not None) and (values_dict.get(f'quad_{key1}') is not None):
                            if key == 'amp':
                                amp[key1] = calc_r(values_dict.get(f'inph_{key1}'), values_dict.get(f'quad_{key1}'))
                            elif key == 'phase':
                                phase[key1] = calc_theta(values_dict.get(f'inph_{key1}'), values_dict.get(f'quad_{key1}'))
                            else:
                                assert KeyError
                        else:
                            assert ValueError
                    if 'difference' in val:
                        if key == 'amp':
                            if isinstance(amp['trace'],np.ndarray) and isinstance(amp['retrace'],np.ndarray):
                                amp[key1] = amp.get('retrace') - amp.get('trace')
                            else:
                                assert ValueError
                        elif key == 'phase':
                            if isinstance(phase['trace'],np.ndarray) and isinstance(phase['retrace'],np.ndarray):
                                phase[key1] = phase.get('retrace') - phase.get('trace')
                            else:
                                assert ValueError
                        else:
                            assert KeyError
                    for key1,val1 in amp.items():
                        if isinstance(val1, np.ndarray):
                            values_dict[f'{key}_{key1}']=val1
                    for key1,val1 in phase.items():
                        if isinstance(val1, np.ndarray):
                            values_dict[f'{key}_{key1}']=val1
        save_dict = {}      # dictionary with the data to be saved
        for key, val in self._data['save'].items():
            for key1 in val:
                save_dict[f'{key}_{key1}'] = values_dict[f'{key}_{key1}']
        return save_dict

    def create_inputs(self):
        ''' create dictionary for measurement inputs with unit'''
        self.inputs_dict = {}
        for key, val in self._data['save'].items():
            for key1 in val:
                self.inputs_dict[f'{key}_{key1}'] = self.unit[key]

    def register_measurement(self):
        ''' register measurement with needed data input dict'''
        if self._modes['measure'] == 'sweep':
            self.tune.register_measurement('sweep_measure', self.inputs_dict, self.sweep_measure)

    def set_node_bounds(self):
        ''' set bounds for data input dict'''
        if self._modes['measure'] == 'sweep':
            for key,val in self.inputs_dict.items():
                    self.tune.set_node_bounds('sweep_measure', key, -10e9, 10e9)
    def activate_measurement(self):
        ''' activate measurement'''
        if self._modes['measure'] == 'sweep':
            self.tune.activate_measurement('sweep_measure')

    def init_wps(self):
        self.wp_start = WorkingPoint(self.outs.keys(), magnet='vector3d')
        self.wp_start.set_sph(**self._sph)
        self.wp_start.set_wp(**self._volts)
        self.wp_start.set_mode(self._modes['wp'])
        self.wp_stop = WorkingPoint(self.outs.keys(), magnet='vector3d')
        self.wp_stop.set_sph(**self._sph)
        self.wp_stop.set_wp(**self._volts)
        self.wp_stop.set_mode(self._modes['wp'])
        if (self._sweep['var_name'] in self.wp_start.get_sph().keys()):
            self.wp_start.set_sph(**{self._sweep['var_name']:self._sweep['start']})
            self.wp_stop.set_sph(**{self._sweep['var_name']:self._sweep['stop']})
        elif (self._sweep['var_name'] in self.wp_start._outputs.keys()):
            self.wp_start.set_wp(**{self._sweep['var_name']:self._sweep['start']})
            self.wp_stop.set_wp(**{self._sweep['var_name']:self._sweep['stop']})
        if self.dim == 2:
            self.set_start_wp()
            self.set_stop_wp()

    def set_start_wp(self,**kwargs):
        ''' setter function for start working point of sweep'''
        if self._step['var_name'] in self.wp_start.get_sph().keys():
            self.wp_start.set_sph(**kwargs)
        elif self._step['var_name'] in self.wp_start._outputs.keys():
            self.wp_start.set_wp(**kwargs)

    def set_stop_wp(self,**kwargs):
        ''' setter function for stop working point of sweep'''
        if self._step['var_name'] in self.wp_stop.get_sph().keys():
            self.wp_stop.set_sph(**kwargs)
        elif self._step['var_name'] in self.wp_stop._outputs.keys():
            self.wp_stop.set_wp(**kwargs)

    def ramp_to_wp(self,dt):
        ''' sweep to wp without measurement'''
        self.anna.sweep(self.wp_start.outs,duration=dt)

    def wp_setter(self, x=None, dt=None):
        ''' set new step val of step var for wp'''
        if self._inputs['retrace']:
            temp_wp_outs=self.wp_start.outs
        else:
            temp_wp_outs=self.wp_stop.outs
        self.set_start_wp(**{self._step['var_name']:x})
        self.set_stop_wp(**{self._step['var_name']:x})
        min_duration=0
        for key,val in self.wp_start.outs.items():
            duration = abs(val - temp_wp_outs[key])/self.max_rate_config[key]
            if min_duration < duration:
                min_duration = duration
        if dt is None:
            dt = min_duration
        elif dt<min_duration:
            log.warning(f'Fixed ramp duration {dt}s is not safe, duration was set to minimal possible duration {min_duration}s!')
            dt = min_duration
        self.ramp_to_wp(dt=dt)

    def generate_steps(self):
        ''' generate steps for step variable if possible'''
        if self._step['start'] is not None and self._step['stop'] is not None and self._step['step_size'] is not None:
            self._step['values'] = np.arange(self._step['start'], self._step['stop'],
                                            self._step['step_size'],dtype=np.float32)
            self.dim = 2
        else:
            log.info("Couldn't generate step value list, inputs missing!")
            self.dim = 1

    def generate_sweep(self):
        ''' generate steps for sweep variable if possible'''
        if self._sweep['start'] is not None and self._sweep['stop'] is not None and self._sweep['rate'] is not None:
            dur = (self._sweep['stop']-self._sweep['start'])/self._sweep['rate']
            if self._sweep['duration'] is not None:
                if dur > self._sweep['duration']:
                    self._sweep['duration'] = dur
            else:
                self._sweep['duration'] = dur
            self._sweep['values'] = np.linspace(
                self._sweep['start'],self._sweep['stop'],
                round(self._sweep['duration']*self._lockin['sample_rate']),dtype=np.float32)
        else:
            log.error("Couldn't generate sweep value list, inputs missing!")

    def get_sph(self):
            ''' getter func for sph vars'''
            return self._sph

    def get_step(self):
        ''' getter func for steps'''
        if self._step['values'] is None:
            self.generate_steps()
        return self._step

    def get_sweep(self):
        ''' getter func for steps'''
        if self._sweep['values'] is None:
            self.generate_sweep()
        return self._sweep

    def get_modes(self):
        ''' getter func for modes of wp and measurement'''
        if None in self._modes.values():
            log.error('Mode for working point or measurement not set!')
        else:
            return self._modes

    def get_volts(self):
        ''' getter func for volts'''
        for key,val in self._volts.items():
            if val is None:
                log.error(f'Value for {key} is not set!')
        return self._volts

    def get_lockin(self):
        ''' getter func for lockin signal pars'''
        for key,val in self._lockin.items():
            if val is None:
                log.warning(f'No value for {key} set, measurement will start without lockin signal!')
                self._lockin[key] = 0
        return self._lockin

    def complete_data(self):
        ''' getter func for data measurement, saving and live plotting'''
        for key,val in self._data['plot'].items():      # keys: inph, quad, raw, amp, phase
            for key1 in val:                            # keys: trace, retrace, difference
                if key1 not in self._data['save'][key]:
                    self._data['save'][key].append(key1)
        for key,val in self._data['save'].items():
            temp = str(val)
            if 'difference' in temp:
                for key1 in self.valids['traces']:
                    if key1 not in self._data['temp_save'][key]:
                        self._data['temp_save'][key].append(key1)
            elif 'retrace' in temp:
                for key1 in ['trace','retrace']:
                    if key1 not in self._data['temp_save'][key]:
                        self._data['temp_save'][key].append(key1)
            elif 'trace' in temp:
                if 'trace' not in self._data['temp_save'][key]:
                    self._data['temp_save'][key].append('trace')
        for key,val in self._data['temp_save'].items():
            if key == 'amp':
                for key1 in val:
                    for val1 in ['inph', 'quad']:
                        if key1 not in self._data['temp_save'][val1]:
                            self._data['temp_save'][val1].append(key1)
            elif key == 'amp':
                for key1 in val:
                    for val1 in ['inph', 'quad']:
                        if key1 not in self._data['temp_save'][val1]:
                            self._data['temp_save'][val1].append(key1)
        return self._data
    
    def add_inputs(self):
        ''' getter func for adwin inputs'''
        for key, val in self._data['temp_save'].items():
            if key in self.valids['inputs'] and val:
                if key not in self._inputs['inputs']:
                    self._inputs['inputs'].append(key)
        temp = str(self._data['temp_save'])
        if 'retrace' in temp:
            self._inputs['retrace'] = True

    def set_(self,**kwargs):
        ''' setter for multiple vars'''
        for key,val in kwargs.items():
            if key in self.set_functions.keys() and isinstance(val,dict):
                self.set_functions[key](**val)
            elif key in self.set_functions.keys():
                self.set_functions[key](val)
            else:
                log.error(f'{self} have no var called {key} of type {val}!')

    def set_adwin_bootload(self, bootlead):
        ''' setter function for bootload of adwin (True/False)'''
        if isinstance(bootlead,bool):
            self.adwin_bootload = bootlead
        else:
            log.error("Bootload value only allows booleans!")

    def set_hard_config(self, **kwargs):
        ''' setter function to update adwin hard config'''
        if isinstance(kwargs,dict):
            self.hard_config = kwargs
            log.warning("Hard config for Adwin was changed!")
        else:
            assert ValueError

    def set_soft_config(self, **kwargs):
        ''' setter function to update adwin soft config'''
        if isinstance(kwargs,dict):
            self.soft_config = kwargs
            log.warning("Soft config for adwin was changed!")
        else:
            assert ValueError

    def set_analysis(self, analysis):
        ''' setter function for analysis'''
        if isinstance(analysis,list):
            for key in analysis:
                if key in self.valids['analysis']:
                    self.analysis.append(key)
        elif isinstance(analysis,str):
            if analysis in self.valids['analysis']:
                self.analysis.append(analysis)
        else:
            assert ValueError

    def set_analysis_params(self,**kwargs):     # todo: possible parameter?
        ''' setter function for additional parameter for analysis'''
        self.analysis_params = kwargs.values()[0]

    def set_sweep(self, **kwargs):
        ''' setter func for sweep'''
        for key,val in kwargs.items():
            if key in self._sweep.keys():
                match key:
                    case 'unit':
                        if isinstance(val,str):
                            self._sweep[key] = val
                    case 'var_name':
                        if val in self.valids['sweep']:
                            self._sweep[key] = val
                        else:
                            log.error(f'{val} is no valid value for sweep_{key}!')
                    case 'start' | 'stop' | 'duration':
                        if isinstance(val,(int,float)):
                            self._sweep[key] = val
                        else:
                            log.error(f'Value of {key} must be float or integer!')
        if 'rate' in kwargs.keys() and self._sweep['var_name'] is not None:
            if kwargs['rate'] >= self.max_rate_config[self._sweep['var_name']]:
                self._sweep['rate'] = kwargs['rate']
            else:
                self._sweep['rate'] = self.max_rate_config[self._sweep['var_name']]
                log.warning(f"Rate of {kwargs['rate']} is not valid! Set rate to max rate {self._sweep['rate']}")

    def set_step(self, **kwargs):
        ''' setter func for step'''
        for key,val in kwargs.items():
            if key in self._step.keys():
                match key:
                    case 'unit':
                        if isinstance(val,str):
                            self._step[key] = val
                    case 'var_name':
                        if val in self.valids['step']:
                            self._step[key] = val
                        else:
                            log.error(f'{val} is no valid value for step_{key}!')
                    case 'start' | 'stop' | 'step_size':
                        if isinstance(val,(int,float)):
                            self._step[key] = val
                        else:
                            log.error(f'Value of {key} must be float or integer!')

    def set_modes(self, **kwargs):
        ''' setter func for modes'''
        for key,val in kwargs.items():
            if key in self._modes.keys():
                if val in self.valids[key]:
                    self._modes[key] = val
                else:
                    log.error(f'{val} is no valid mode for {key}!')

    def set_volts(self, **kwargs):
        ''' setter func for volts'''
        for key,val in kwargs.items():
            if key in self._volts.keys():
                if isinstance(val,(int,float)):
                    self._volts[key] = val
                else:
                    log.error(f'Value of {key} must be float or integer!')

    def set_lockin(self, **kwargs):
        ''' setter func for lockin signal'''
        for key,val in kwargs.items():
            if key in self._lockin.keys():
                if isinstance(val,(int,float)):
                    self._lockin[key] = val
                else:
                    log.error(f'Value of {key} must be float or integer!')

    def set_data(self, **kwargs):
        ''' setter func for data measurement, saving and live plotting'''
        for key,val in kwargs.items(): # keys: temp_save, save, plot
            if key in self._data.keys(): 
                for key1,val1 in val.items():   # keys: inph, quad, raw, amp, phase
                    if (key1 in self.valids['calc']) or (key1 in self.valids['inputs']):
                        for key2 in val1:       # keys: trace, retrace, difference
                            if key2 in self.valids['traces']:
                                self._data[key][key1].append(key2)
                            else:
                                log.error(f'{key2} is no valid input for {key}_{key1}!')
                    else:
                        log.error(f'{key1} is not defined in vars of {key}!')
            else:
                log.error(f'{key} is not defined!')

    def set_sph(self, **kwargs):
        ''' update all given spherical b parameters '''
        for key,val in kwargs.items():
            if key in self._sph.keys():
                if isinstance(val,(int,float)):
                    self._sph[key] = val
                else:
                    log.error(f'Value of {key} must be float or integer!')

    # def get_(self):         # todo: filter not needed informations
    #     ''' getter for all vars'''
    #     sweep=self.get_sweep().copy()
    #     del sweep['values']
    #     step=self.get_step().copy()
    #     del step['values']
    #     return {'sph':self.get_sph(),'sweep':sweep,'step':step,
    #             'modes':self.get_modes(),'volts':self.get_volts(),'lockin':self.get_lockin(),
    #             'saved_data':self.get_data()['save']}

    def save_settings(self):    # todo: consider save settings
        pass

    def load_settings(self):    # todo: consider load settings
        pass