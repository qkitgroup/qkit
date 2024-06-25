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


class MeasurementScript():
    ''' The Measurement Script generates a set of values for the WorkingPoint'''

    def __init__(self):
        # define valid inputs
        self.valid_step_vars = ['vg','vd','N','bt','phi','psi','theta']
        self.valid_sweep_vars = ['vg','vd','bt','bp','phi','psi','theta']
        self.valid_wp_mode = ['normal','sweep']
        self.valid_measure_mode = ['static','sweep']        # static mode not availible yet
        self.valid_inputs = ['raw','inph','quad']
        self.valid_traces = ['trace','retrace','difference']
        self.valid_calc = ['amplitude','phase']
        self.max_rate_config = {'bp':0.1,'bt':0.1,'vg':0.1,'vd':0.1}     	# rate in T(/V) per sec

        # define needed value dicts
        self._sph = {'theta': 0, 'phi': 0, 'psi': 0, 'bp': 0, 'bt': 0}
        self._sweep = {'var_name':None,'start':None,'stop':None,
                        'rate':None,'duration':None,'values':None}
        self._step = {'var_name':None,'start':None,'stop':None,
                        'step_size':None,'values':None}
        self._modes = {'wp':None,'measure':None}
        self._gain = {'vd':None,'vg':None}
        self._lockin = {'freq':None,'ampl':None,'tao':None,'init_time':None,'sample_rate':500e3}
        self._data = {'measure':{'retrace':False,'inputs':[]},
                        'save':{'inputs':{'inph':[],'quad':[],'raw':[]},
                                'calc':{'ampl':[],'phase':[]}},
                        'plot':{'inputs':{'inph':[],'quad':[],'raw':[]},
                                'calc':{'ampl':[],'phase':[]}}}
        self.functions = {'sph':self.set_sph,'sweep':self.set_sweep,
                          'step':self.set_step,'modes':self.set_modes,
                          'gain':self.set_gain,'lockin':self.set_lockin,'data':self.set_data}
        self.valids = {'step':self.valid_step_vars,'sweep':self.valid_sweep_vars,
                       'wp':self.valid_wp_mode,'measure':self.valid_measure_mode,
                       'traces':self.valid_traces,'inputs':self.valid_inputs,
                       'calc':self.valid_calc,'maxrate':self.max_rate_config}


    def set_sph(self, **kwargs):
        ''' update all given spherical b parameters '''
        for key,val in kwargs.items():
            if key in self._sph.keys():
                if isinstance(val,(int,float)):
                    self._sph[key] = val
                else:
                    log.error(f'Value of {key} must be float or integer!')

    def set_sweep(self, **kwargs):
        ''' setter func for sweep'''
        for key,val in kwargs.items():
            if key in self._sweep.keys():
                match key:
                    case 'var_name':
                        if val in self.valids['sweep']:
                            self._sweep[key] = val
                        else:
                            log.error(f'{val} is no valid value for sweep_{key}!')
                    case 'start' | 'stop':
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
        ''' setter func for gains'''
        for key,val in kwargs.items():
            if key in self._modes.keys():
                if val in self.valids[key]:
                    self._modes[key] = val
                else:
                    log.error(f'{val} is no valid mode for {key}!')

    def set_gain(self, **kwargs):
        ''' setter func for gains'''
        for key,val in kwargs.items():
            if key in self._gain.keys():
                if isinstance(val,(int,float)):
                    self._gain[key] = val
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
        for key,val in kwargs.items(): #measure,save,plot
            if key in self._data.keys():    
                for key2,val2 in val.items():  #traces,inputs,calc
                    if key2 in self._data[key].keys():
                        if not isinstance(val2,dict):
                            for val3 in val2:
                                self._data[key][key2].append(val3)
                        else:
                            for key3,val3 in val2.items():
                                if key3 in self._data[key][key2].keys():
                                    for val4 in val3:
                                        self._data[key][key2][key3].append(val4)
                                else:
                                    log.error(f'{key3} is not defined in vars of {key}_{key2}!')
                    else:
                        log.error(f'{key2} is not defined in vars of {key}!')
            else:
                log.error(f'{key} is not defined!')

    def generate_steps(self):
        ''' generate steps for step variable if possible'''
        if self._step['start'] is not None and self._step['stop'] is not None and self._step['step_size'] is not None:
            self._step['values'] = np.arange(self._step['start'], self._step['stop'],
                                             self._step['step_size'],dtype=np.float32)
        else:
            log.error("Couldn't generate step value list, inputs missing!")

    def generate_sweep(self):
        ''' generate steps for sweep variable if possible'''
        if self._sweep['start'] is not None and self._sweep['stop'] is not None and self._sweep['rate'] is not None:
            self._sweep['duration'] = (self._sweep['stop']-self._sweep['start'])/self._sweep['rate']
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

    def get_gain(self):
        ''' getter func for gain'''
        for key,val in self._gain.items():
            if val is None:
                log.error(f'Value for {key} is not set!')
        return self._gain

    def get_lockin(self):
        ''' getter func for lockin signal pars'''
        for key,val in self._lockin.items():
            if val is None:
                log.warning(f'No value for {key} set, measurement will start without lockin signal!')
                self._lockin[key] = 0
        return self._lockin

    def get_data(self):
        ''' getter func for data measurement, saving and live plotting'''
        for key,val in self._data['plot'].items():
            for key1,val1 in val.items():
                for val2 in val1:
                    if val2 not in self._data['save'][key][key1]:
                        self._data['save'][key][key1].append(val2)
        for key,val in self._data['save']['inputs'].items():
            if val:
                if key not in self._data['measure']['inputs']:
                    self._data['measure']['inputs'].append(key)
        for val in self._data['save']['calc'].values():
            if 'inph' not in self._data['measure']['inputs']:
                self._data['measure']['inputs'].append('inph')
            if 'quad' not in self._data['measure']['inputs']:
                self._data['measure']['inputs'].append('quad')
        temp = str(self._data['save'])
        if ('difference' in temp) or ('retrace' in temp):
            self._data['measure']['retrace']=True
        return self._data

    def set_(self,**kwargs):
        ''' setter for multiple vars'''
        for key,val in kwargs.items():
            if key in self.functions.keys() and isinstance(val,dict):
                self.functions[key](**val)
            else:
                log.error(f'{self} have no var called {key} of type {val}!')

    def get_(self):         # todo: filter not needed informations
        ''' getter for all vars'''
        sweep=self.get_sweep().copy()
        del sweep['values']
        step=self.get_step().copy()
        del step['values']
        return {'sph':self.get_sph(),'sweep':sweep,'step':step,
                'modes':self.get_modes(),'gain':self.get_gain(),'lockin':self.get_lockin(),
                'saved_data':self.get_data()['save']}
