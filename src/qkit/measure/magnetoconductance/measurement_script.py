''' The measurement script is a class to describe and run
    a 1D or 2D measurement, therefore several vars must be set.
    These variables describe the working points (wp) to sweep between
    during the measurement. Additional needed parameter is the mode
    (normal/sweep) of the wp, more about this in the wp class.
    The measurement can run with and without lockin signal,
    if there should no lockin signal be applied, set no amplitude
    or set amplitude to zero.

    *Required keywords:
        -anna:  *adwin instrument

    (all below listed variables are saved as dictionaries,
    some vars vaulues are restricted to certain values,
    these are defined in the init of the class as valid values)

        -sph:       *spherical coordinates and values for wp
                    *phi, theta, psi, bp, bt
                    *if a sph coordinate is used as step or sweep var
                    it is not needed, because the value will be overwritten

        -modes:     *mode of wp and measure mode
                    *wp: normal, sweep; measure: sweep, static
                    *the "static" measure mode is not yet implemented!

        -volts:     *source-drain and gate voltage
                    *vd, vg

        -sweep:     *vars to generate virtual sweep values array
                    *name, start, stop, unit
                    *optional: rate, duration
                    *if no rate or duration is set, max_rate_config of sweep var will be used

        -step:      *vars to generate step values array (only needed for 2D measurement)
                    *name, start, stop, stepsize, unit
                    *stop value is incuded in step values array

        -inputs:    *inputs to measure and return from adwin instrument
                    *raw, inph, quad (for "inph" and "quad" is a lockin signal required)
                    *optional: retrace (default=False, describes if retrace is measured)
                    *if "save" is set in data, needed outputs will be generated automatically

        -data:      *vars that should be saved and plotted from the measurement
                    *save: (traces, inputs); plot: (traces, inputs)
                    *traces and inputs in "plot" will automatically be added to save,
                    cause its required to save the data to plot it with qviewkit.
                    *additional inputs: amp, phase (inph, quad needed for calculation)

    *Optional keywords:
        -h5_path:   *path of .h/hdf5 file to extract and load measurement config
                     from previous measurement

                     
    *ToDo:  -static measurement:        *measurement without sweep or step
            -interactive measurement:   *measurement with adwin communication while sweep
            !!! B to zero, all to zero !!!

'''
#imports
import logging as log
import numpy as np
import json
import time
import h5py
import qkit
from qkit.measure.magnetoconductance.spin_tune_ST import Tuning_ST
from qkit.measure.magnetoconductance.working_point import WorkingPoint
from qkit.drivers.adwin_spin_transistor import adwin_spin_transistor


def calc_r(x, y):
    ''' calc func for amplitude from lockin'''
    return np.sqrt(np.square(x) + np.square(y))

def calc_theta(x, y):
    ''' calc func for phase shift from lockin'''
    return np.arctan2(y, x)

class MeasurementScript():
    ''' The Measurement Script generates a 
    measurement routine with given params'''

    def __init__(self, adwin:adwin_spin_transistor,
                 h5_path=None, **kwargs):
        self.def_valids()   # define valid inputs for params
        self.setup_params() # setup needed measurement params
        self.def_setter()   # define params setter funcs

        # load measurement params from h5file
        if h5_path is not None:
            self.load_config(h5_path)

        self.set_(**kwargs) # set imported param values

        self.anna = adwin    # connect ADwin instrument

        self.update_script()    # generate measurement routine

    def def_valids(self):
        ''' define validations'''
        self.valid_step_vars = ['vg','vd','N','bt','bp','phi','psi','theta']
        self.valid_sweep_vars = ['vg','vd','bt','bp','phi','psi','theta']
        self.valid_wp_mode = ['normal','sweep']
        self.valid_measure_mode = ['static','sweep']        # static mode not availible yet
        self.valid_inputs = ['raw','inph','quad']
        self.valid_traces = ['trace','retrace','difference']
        self.valid_calc = ['amp','phase']
        self.max_rate_config = {'bx':0.1,'by':0.1,'bz':0.1,'bp':0.1,'bt':0.1,'vg':0.1,'vd':0.1} # rate in T(/V) per sec
        self.unit = {'inph':'S','quad':'S','raw':'V','amp':'S','phase':'rad'}
        self.valids = {'step':self.valid_step_vars,'sweep':self.valid_sweep_vars,
                        'wp':self.valid_wp_mode,'measure':self.valid_measure_mode,
                        'traces':self.valid_traces,'inputs':self.valid_inputs,
                        'calc':self.valid_calc,'maxrate':self.max_rate_config}

    def setup_params(self):
        ''' setup params for the measurement'''
        self._sph = {'theta': 0, 'phi': 0, 'psi': 0, 'bp': 0, 'bt': 0}
        self._sweep = {'name':None,'start':None,'stop':None,'unit':None,
                        'rate':None,'duration':None,'values':None}
        self._step = {'name':None,'start':None,'stop':None,'unit':None,
                        'step_size':None,'values':None}
        self._modes = {'wp':None,'measure':None}
        self._volts = {'vd':None,'vg':None}
        self._lockin = {'freq':None,'amp':None,'tao':None,'init_time':None,'sample_rate':500e3}
        self._inputs = {'retrace':False,'inputs':[]}
        self._data = {'temp_save':{'inph':[],'quad':[],'raw':[],
                                'amp':[],'phase':[]},
                        'save':{'inph':[],'quad':[],'raw':[],
                                'amp':[],'phase':[]},
                        'plot':{'inph':[],'quad':[],'raw':[],
                                'amp':[],'phase':[]}}

    def def_setter(self):
        ''' define setter functions of params'''
        self.set_functions = {'sph':self.set_sph,'sweep':self.set_sweep,'step':self.set_step,
                            'modes':self.set_modes,'volts':self.set_volts,'lockin':self.set_lockin,
                            'data':self.set_data,'hard_config':self.set_hard_config,
                            'soft_config':self.set_soft_config,'adwin_bootload':self.set_adwin_bootload}

    def update_script(self):
        ''' genererate measurement setup'''
        self.generate_sweep()       # generate sweep values
        self.generate_steps()       # generate step values

        self.create_output_channel()# create output channel for adwin
        self.add_saves()            # generate data save and temp_save dicts
        self.add_inputs()           # generate ADwin inputs
        self.start_lockin()         # start lockin signal
        self.update_lockin()        # get real lockin data from adwin
        self.init_wps()             # init start and stop wp of first sweep
        self.start_sweep()          # start sweep to the first wp

        self.create_tuning()        # create Tuning_ST instance
        self.create_inputs()        # create a dict of the input nodes
        self.register_measurement() # register measure function
        self.set_node_bounds()      # create bounds for input variables
        self.activate_measurement() # activate measurement
        self.set_parameter()        # set x/y coordinate parameter
        self.prepare_measurement_datasets()
        self.prepare_measurement_datafile()

        self.show_plots()           # determine names from datasets to plot
        self.add_view()             # add view datasets

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
        self.save_config()
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
        if 'amp_difference' in self.inputs_dict.keys():
            if 'deg' in self._step.get('unit') or '°' in self._step.get('unit'):
                view = self.datafile.add_polarview(name='polar_colormap', x=self.coordinates[self._x_parameter.name], y=self.coordinates[self._y_parameter.name], z=self.datasets['sweep_measure.amp_difference'])

    def set_parameter(self):
        ''' setter for x/y parameter of measurement'''
        if self.dim == 1:
            self.tune.set_x_parameters(self._sweep['values'], self._sweep['name'], None, self._sweep['unit'])
            self._x_parameter = self.tune._x_parameter
        elif self.dim == 2:
            self.tune.set_x_parameters(self._step['values'], self._step['name'], self.wp_setter, self._step['unit'])
            self.tune.set_y_parameters(self._sweep['values'], self._sweep['name'], None, self._sweep['unit'])
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
        if self._lockin['amp']:
            self.anna.init_measurement('lockin', self._lockin['sample_rate'], bias=self._volts['vd'], inputs=self._inputs['inputs'],
                                    amplitude=self._lockin['amp'], frequency=self._lockin['freq'], tao=self._lockin['tao'])
        else:
            log.warning("No lockin signal applied!")
            self.stop_lockin()
        time.sleep(1)

    def stop_lockin(self):
        ''' stop lockin signal'''
        self.anna.init_measurement('lockin', sample_rate=100, bias=self._volts['vd'], inputs=['raw'],
                                    amplitude=0, frequency=100, tao=1/100)

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
        if (self._sweep['name'] in self.wp_start.get_sph().keys()):
            self.wp_start.set_sph(**{self._sweep['name']:self._sweep['start']})
            self.wp_stop.set_sph(**{self._sweep['name']:self._sweep['stop']})
        elif (self._sweep['name'] in self.wp_start._outputs.keys()):
            self.wp_start.set_wp(**{self._sweep['name']:self._sweep['start']})
            self.wp_stop.set_wp(**{self._sweep['name']:self._sweep['stop']})
        if self.dim == 2:
            self.set_start_wp()
            self.set_stop_wp()

    def set_start_wp(self,**kwargs):
        ''' setter function for start working point of sweep'''
        if self._step['name'] in self.wp_start.get_sph().keys():
            self.wp_start.set_sph(**kwargs)
        elif self._step['name'] in self.wp_start._outputs.keys():
            self.wp_start.set_wp(**kwargs)

    def set_stop_wp(self,**kwargs):
        ''' setter function for stop working point of sweep'''
        if self._step['name'] in self.wp_stop.get_sph().keys():
            self.wp_stop.set_sph(**kwargs)
        elif self._step['name'] in self.wp_stop._outputs.keys():
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
        self.set_start_wp(**{self._step['name']:x})
        self.set_stop_wp(**{self._step['name']:x})
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
        if (self._step['start'] is not None and self._step['stop'] is not None and self._step['step_size'] is not None):
            self._step['values'] = np.arange(self._step['start'], self._step['stop']+self._step['step_size'],
                                            self._step['step_size'],dtype=np.float32)
            self.dim = 2
        else:
            log.info("Couldn't generate step value list, inputs missing!")
            self.dim = 1

    def generate_sweep(self):
        ''' generate steps for sweep variable if possible'''
        # Validation of sweep rate/duration
        if self._sweep['rate'] and (self._sweep['start'] is not None and self._sweep['stop'] is not None):
            print(self._sweep['name'])
            if self.max_rate_config[self._sweep['name']] < self._sweep['rate']:
                log.warning(f"Rate of {self._sweep['rate']} is not valid! Set rate to max rate {self.max_rate_config[self._sweep['name']]}")
                self._sweep['rate'] = self.max_rate_config[self._sweep['name']]
            self._sweep['duration'] = abs(self._sweep['stop']-self._sweep['start'])/self._sweep['rate']
            log.info(f"Set sweep duration to {self._sweep['duration']}")
        elif self._sweep['duration'] and (self._sweep['start'] is not None and self._sweep['stop'] is not None):
            rate = abs(self._sweep['stop']-self._sweep['start'])/self._sweep['duration']
            if self.max_rate_config[self._sweep['name']] < rate:
                self._sweep['rate'] = self.max_rate_config[self._sweep['name']]
                log.warning(f"Sweep duration {self._sweep['duration']} with rate {rate} is not valid! Set rate to max rate {self.max_rate_config[self._sweep['name']]}!")
                self._sweep['duration'] = abs(self._sweep['stop']-self._sweep['start'])/self._sweep['rate']
            else:
                self._sweep['rate'] = rate
        elif (self._sweep['start'] is not None and self._sweep['stop'] is not None):
            log.warning(f"No rate set! Set rate to max rate {self.max_rate_config[self._sweep['name']]}")
            self._sweep['rate'] = self.max_rate_config[self._sweep['name']]
            self._sweep['duration'] = abs(self._sweep['stop']-self._sweep['start'])/self._sweep['rate']
            log.info(f"Set sweep duration to {self._sweep['duration']}")
        else:
            assert ValueError("Values for sweep missing!")
        if (self._sweep['start'] is not None and self._sweep['stop'] is not None and self._sweep['rate'] is not None):
            self._sweep['values'] = np.linspace(
                self._sweep['start'],self._sweep['stop'],
                round(self._sweep['duration']*self._lockin['sample_rate']),dtype=np.float32)
            log.info("Generated sweep values!")
        else:
            log.error("Couldn't generate sweep value list, inputs missing!")

    def get_sph(self):
        ''' getter func for sph vars'''
        return self._sph

    def get_step(self):
        ''' getter func for step vars'''
        step = {'name':self._step['name'],'start':self._step['start'],'stop':self._step['stop'],
                'step_size':self._step['step_size'],'unit':self._step['unit']}
        return step

    def get_sweep(self):
        ''' getter func for sweep vars'''
        sweep = {'name':self._sweep['name'],'start':self._sweep['start'],'stop':self._sweep['stop'],
                    'rate':self._sweep['rate'],'unit':self._sweep['unit'],'duration':self._sweep['duration']}
        return sweep

    def get_step_val(self):
        ''' getter func for step values'''
        if self._step['values'] is None:
            self.generate_steps()
        return self._step

    def get_sweep_val(self):
        ''' getter func for sweep values'''
        if self._sweep['values'] is None:
            self.generate_sweep()
        return self._sweep

    def get_modes(self):
        ''' getter func for modes of wp and measurement'''
        return self._modes

    def get_volts(self):
        ''' getter func for volts'''
        return self._volts

    def get_lockin(self):
        ''' getter func for lockin signal pars'''
        return self._lockin

    def get_inputs(self):
        ''' getter func for inputs of adwin'''
        return self._inputs

    def get_data(self):
        ''' getter func for data save and plot information'''
        return self._data

    def add_saves(self):
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
        ''' generate adwin inputs'''
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
            # log.warning("Hard config for Adwin was changed!")
        else:
            assert ValueError

    def set_soft_config(self, **kwargs):
        ''' setter function to update adwin soft config'''
        if isinstance(kwargs,dict):
            self.soft_config = kwargs
            # log.warning("Soft config for adwin was changed!")
        else:
            assert ValueError

    def set_sweep(self, **kwargs):
        ''' setter func for sweep'''
        for key,val in kwargs.items():
            if key in self._sweep.keys():
                match key:
                    case 'unit':
                        if isinstance(val,str):
                            self._sweep[key] = val
                    case 'name':
                        if val in self.valids['sweep']:
                            self._sweep[key] = val
                        else:
                            log.error(f'{val} is no valid value for sweep_{key}!')
                    case 'start' | 'stop' | 'duration' | 'rate':
                        if isinstance(val,(int,float)):
                            self._sweep[key] = val
                        else:
                            log.error(f'Value of {key} must be float or integer!')


    def set_step(self, **kwargs):
        ''' setter func for step'''
        for key,val in kwargs.items():
            if key in self._step.keys():
                match key:
                    case 'unit':
                        if isinstance(val,str):
                            self._step[key] = val
                    case 'name':
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

    def save_config(self):
        ''' save measurement config in dataset of .h/hdf5 file'''
        save = self.datafile.add_config()
        save.add('ds_type','config')
        save.add('sph',self.get_sph())
        save.add('sweep',self.get_sweep())
        save.add('step',self.get_step())
        save.add('modes',self.get_modes())
        save.add('volts',self.get_volts())
        save.add('lockin',self.get_lockin())
        save.add('inputs',self.get_inputs())
        save.add('data',self.get_data())
        save.add('soft_config',self.get_soft_config())
        save.add('hard_config',self.get_hard_config())

    def load_config(self,h5_path):
        ''' load measurement config from .h/hdf5 file'''
        try:
            hf = h5py.File(h5_path)
            config_ds = hf["entry/data0/measurement.config"]
            config = {}
            for key,val in config_ds.attrs.items():
                try:
                    config[key] = json.loads(val)
                except:
                    pass
            log.info('Load measurement config from .h/hdf5 file...')
            if 'hard_config' not in config.keys():
                log.error('Could not load hard_config for adwin!')
            if 'soft_config' not in config.keys():
                log.error('Could not load soft_config for adwin!')
            self.set_(**config)
            log.info('Config from .h/hdf5 file loaded.')
        except ImportError:
            log.error('Load config from .h/hdf5 file failed!')