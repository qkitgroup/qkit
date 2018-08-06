import qkit
from qkit.core.instrument_base import Instrument
import logging
import numpy as np

class virtual_tunnel_electronic(Instrument):
    '''
    This is the virtual driver for the home made tunnel electronic combined with a Multi Channel Source Measure Unit <SMU>.
    
    Usage:
    Initialize with
    <name> = qkit.instruments.create('<name>', 'virtual_tunnel_electronic', SMU=SMU)
    '''

    def __init__(self, name, SMU):
        # create instrument
        logging.info(__name__ + ' : Initializing instrument virtual tunnel electronic')
        Instrument.__init__(self, name, tags=['virtual'])
        self._instruments = qkit.instruments.get_instruments()
        # Source Measure Unit (SMU)
        self._SMU = SMU
        # external measurement setup
        self._dAdV = 2e-6 # for external current bias
        self._amp = 1e3   # for external voltage amplifier
        self._dVdA = 1e8  # for external voltage bias
        self._Vdiv = 1e3  # for external voltage divider
        
        ### FIXME: time constant of amplifier and bandwidth for get_all and setting file
        
        self.set_sweep_mode(mode=0)  # VV-mode
        self._sweep_modes = {0: 'VV-mode', 1: 'IV-mode', 2: 'VI-mode'}
        self.set_pseudo_bias_mode(mode=0)  # current bias
        self._pseudo_bias_modes = {0: 'current bias', 1: 'voltage bias'}

    def set_dAdV(self, val=1):
        '''
        Sets voltage-current conversion of external current source used for current bias to <val> (in A/V)
        
        Input:
            val (float): 1 (default)
        Output:
            None
        '''
        self._dAdV = val

    def get_dAdV(self):
        '''
        Gets voltage-current conversion of external current source used for current bias (in A/V)
        
        Input:
            None
        Output:
            val (float)
        '''
        return self._dAdV

    def set_amp(self, val=1):
        '''
        Sets amplification factor of external measurement setup to <val>
        
        Input:
            val (float): 1 (default)
        Output:
            None
        '''
        self._amp = val

    def get_amp(self):
        '''
        Gets amplification factor of external measurement setup
        
        Input:
            None
        Output:
            val (float)
        '''
        return self._amp

    def set_dVdA(self, val=1):
        '''
        Sets current-voltage conversion of external voltage source used for voltage bias to <val> (in V/A)
        
        Input:
            val (float): 1 (default)
        Output:
            None
        '''
        self._dVdA = val

    def get_dVdA(self):
        '''
        Gets current-voltage conversion of external voltage source used for voltage bias (in V/A)
        
        Input:
            None
        Output:
            val (float)
        '''
        return self._dVdA

    def set_Vdiv(self, val=1):
        '''
        Sets voltage divider factor of external measurement setup to <val>
        
        Input:
            val (float): 1 (default)
        Output:
            None
        '''
        self._Vdiv = val

    def get_Vdiv(self):
        '''
        Gets voltage divider factor of external measurement setup
        
        Input:
            None
        Output:
            val (float)
        '''
        return self._Vdiv

    def set_measurement_mode(self, val, channel=1):
        '''
        Sets measurement mode (wiring system) of channel <channel> to <val>

        Input:
            channel (int) : 1 (default) | 2
            val (int)     : 0 (2-wire) | 1 (4-wire)
        Output:
            None
        '''
        return self._SMU.set_measurement_mode(val=val, channel=channel)

    def get_measurement_mode(self, channel=1):
        '''
        Gets measurement mode (wiring system) of channel <channel>

        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (int)     : 0 (2-wire) | 1 (4-wire)
        '''
        return self._SMU.get_measurement_mode(channel=channel)

    def set_bias_mode(self, mode, channel=1):
        '''
        Sets bias mode of channel <channel> to <mode> regime.

        Input:
            mode (int)    : 0 (current) | 1 (voltage)
            channel (int) : 1 | 2
        Output:
            None
        '''
        return self._SMU.set_bias_mode(mode=mode, channel=channel)

    def get_bias_mode(self, channel=1):
        '''
        Gets bias mode <output> of channel <channel>

        Input:
            channel (int) : 1 | 2
        Output:
            mode (int)    : 0 (current) | 1 (voltage)
        '''
        return self._SMU.get_bias_mode(channel=channel)

    def set_sense_mode(self, mode, channel=1):
        '''
        Sets sense mode of channel <channel> to <mode> regime.

        Input:
            mode (str)    : 0 (current) | 1 (voltage)
            channel (int) : 1 | 2
        Output:
            None
        '''
        return self._SMU.set_sense_mode(mode=mode, channel=channel)

    def get_sense_mode(self, channel=1):
        '''
        Gets sense mode <output> of channel <channel>

        Input:
            channel (int) : 1 | 2
        Output:
            mode (str)    : 0 (current) | 1 (voltage)
        '''
        return self._SMU.get_sense_mode(channel=channel)

    def set_bias_range(self, val, channel=1):
        '''
        Sets bias range of channel <channel> to <val>

        Input:
            val (float)   : -1 (auto) | ...
            channel (int) : 1 | 2
        Output:
            None
        '''
        return self._SMU.set_bias_range(val=val, channel=channel)

    def get_bias_range(self, channel=1):
        '''
        Gets bias mode <output> of channel <channel>

        Input:
            channel (int) : 1 | 2
        Output:
            val (float)
        '''
        return self._SMU.get_bias_range(channel=channel)
    
    def set_sense_range(self, val, channel=1):
        '''
        Sets sense range of channel <channel> to <val>

        Input:
            val (float)   : -1 (auto) | 200mV | 2V | 20V | 200V | 100pA | 1nA | 10nA |100nA | 1uA | 10uA | 100uA | 1mA | 10mA | 100mA | 1 A | 1.5A
            channel (int) : 1 | 2
        Output:
            None
        '''
        return self._SMU.set_sense_range(val=val, channel=channel)

    def get_sense_range(self, channel=1):
        '''
        Gets sense mode <output> of channel <channel>
        
        Input:
            channel (int) : 1 | 2
        Output:
            val (float)   : 200mV | 2V | 20V | 200V | 100pA | 1nA | 10nA |100nA | 1uA | 10uA | 100uA | 1mA | 10mA | 100mA | 1 A | 1.5A
        '''
        return self._SMU.get_sense_range(channel=channel)

    def set_bias_delay(self, val, channel=1):
        '''
        Sets bias delay of channel <channel> to <val>
        
        Input:
            val (float)   : -1 (auto) | 0 (off) | positive number
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        return self._SMU.set_bias_delay(val=val, channel=channel)

    def get_bias_delay(self, channel=1):
        '''
        Gets bias delay of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (float)
        '''
        return self._SMU.get_bias_delay(channel=channel)

    def set_sense_delay(self, val, factor=1, channel=1):
        '''
        Sets sense delay of channel <channel> to <val>
        
        Input:
            val (float)   : -1 (auto) | 0 (off) | positive number
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        return self._SMU.set_sense_delay(val=val, channel=channel)

    def get_sense_delay(self, channel=1):
        '''
        Gets sense delay of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (float)
        '''
        return self._SMU.get_sense_delay(channel=channel)

    def set_sense_average(self, val, mode=1, channel=1):
        '''
        Sets sense average of channel <channel> to <val>
        
        Input:
            val (int)     : [1, 100]
            mode (str)    : 0 (moving average) | 1 (repeat average) (default) | 2 (median)
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        return self._SMU.set_sense_average(val=val, mode=mode, channel=channel)

    def get_sense_average(self, channel=1):
        '''
        Gets sense average of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            status (bool)
            val (int)
            mode (int)
        '''
        return self._SMU.get_sense_average(channel=channel)

    def set_plc(self, val):
        '''
        Sets power line cycle (PLC) to <val>
        
        Input:
            plc (int) : -1 (auto) | 50 | 60
        Output:
            None
        '''
        return self._SMU.set_plc(val=val)

    def get_plc(self):
        '''
        Gets power line cycle (PLC)
        
        Input:
            None
        Output:
            val (float) : 50 | 60
        '''
        return self._SMU.get_plc()

    def set_sense_nplc(self, val, channel=1):
        '''
        Sets sense nplc (number of power line cycle) of channel <channel> with the <val>-fold of one power line cycle
        
        Input:
            channel (int) : 1 (default) | 2
            val (float)   : [0.001, 25]
        Output:
            None
        '''
        return self._SMU.set_sense_nplc(val=val, channel=channel)

    def get_sense_nplc(self, channel=1):
        '''
        Gets sense nplc (number of power line cycle) of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (int)
        '''
        return self._SMU.get_sense_nplc(channel=channel)

    def set_sense_autozero(self, val, channel=1):
        '''
        Sets autozero of channel <channel> to <val>.
        
        Input:
            val (int): 0 (off) | 1 (on) | 2 (once)
        Output:
            None
        '''
        return self._SMU.set_sense_autozero(val=val, channel=channel)

    def get_sense_autozero(self, channel=1):
        '''
        Gets autozero of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (int)
        '''
        return self._SMU.get_sense_autozero(channel=channel)

    def set_status(self, status, channel=1):
        '''
        Sets output status of channel <channel> to <status>
        
        Input:
            status (int)  : 0 (off) | 1 (on)
            channel (int) : 1 | 2
        Output:
            None
        '''
        return self._SMU.set_status(status=status, channel=channel)

    def get_status(self, channel=1):
        '''
        Gets output status of channel <channel>
        
        Input:
            channel (int) : 1 | 2
        Output:
            status (int)  : 0 (off) | 1 (on)
        '''
        return self._SMU.get_status(channel=channel)

    def set_sweep_mode(self, mode=0, **kwargs):
        '''
        Sets an internal variable to decide weather voltage is both applied and measured (default), current is applied and voltage is measured or voltage is applied and current is measured.
        VV-mode needs two different channels (bias channel <channel_bias> and sense channel <channel_sense>), IV-mode and VI-mode only one (<channel>).

        Input:
            mode (int) : 0 (VV-mode) (default) | 1 (IV-mode) | 2 (VI-mode)
            **kwargs   : channel_bias (int)  : 1 (default) | 2 for VV-mode
                         channel_sense (int) : 1 | 2 (default) for VV-mode
                         channel (int)       : 1 (default) | 2 for IV-mode or VI-mode
        Output:
            None
        '''
        self._sweep_mode = mode
        self._SMU.set_sweep_mode(mode=mode)

    def get_sweep_mode(self):
        '''
        Gets an internal variable to decide weather voltage is both applied and measured (default), current is applied and voltage is measured or voltage is applied and current is measured.

        Input:
            None
        Output:
            mode (int) : 0 (VV mode) | 1 (IV mode) | 2 (VI-mode)
        '''
        if self._sweep_mode != self._SMU.get_sweep_mode():
            raise ValueError(__name__ + ': sweep mode of {:s} and {:s} coincide: {:s} and {:s}'.format(__name__, self._SMU.__name__, self._sweep_modes[self._sweep_mode], self._sweep_modes[self._SMU.get_sweep_mode()]))
        else:
            return self._sweep_mode

    def set_pseudo_bias_mode(self, mode):
        '''
        Sets an internal variable to decide weather bias or sense values are converted to currents

        Input:
            mode (int) : 0 (current bias) | 1 (voltage bias)
        Output:
            None
        '''
        self._pseudo_bias_mode = mode

    def get_pseudo_bias_mode(self):
        '''
        Gets an internal variable to decide weather bias or sense values are converted to currents

        Input:
            None
        Output:
            mode (int) : 0 (current bias) | 1 (voltage bias)
        '''
        return self._pseudo_bias_mode

    def get_bias(self):
        '''
        Gets the real bias mode as combination of <self._sweep_mode> and <self._pseudo_bias_mode>
        
        Input:
            None
        Output:
            mode (int) : 0 (current bias) | 1 (voltage bias)
        '''
        self._bias = int(not bool(self._sweep_mode))*self._pseudo_bias_mode+int(bool(self._sweep_mode))*(self._sweep_mode-1)   # 0 (current bias) | 1 (voltage bias)
        return self._bias

    def set_voltage(self, val, channel=1):
        '''
        Sets voltage value of channel <channel> to <val> taking tunnel settings of the electronic into accout (<sweep_mode>, <pseudo_bias_mode>)
        
        Input:
            val (float)
            channel (int) : 1 | 2
        Output:
            None
        '''
        if self._sweep_mode == 0: # 0 (VV mode)
            if not self._pseudo_bias_mode: # 0 (current bias)
                logging.error(__name__ + ': Cannot set voltage of channel {:d} in the current bias.'.format(channel))
                raise AttributeError(__name__ + ': Cannot set voltage of channel {:d} in the current bias.'.format(channel))
            elif self._pseudo_bias_mode: # 1 (voltage bias)
                return self._SMU.set_bias_value(val=val*self._Vdiv, channel=channel)
        elif self._sweep_mode == 1: # 1 (IV mode)
            logging.error(__name__ + ': Cannot set voltage of channel {:d} in the current bias.'.format(channel))
            raise AttributeError(__name__ + ': Cannot set voltage of channel {:d} in the current bias.'.format(channel))
        elif self._sweep_mode == 2: # 2 (VI-mode)
            return self._SMU.set_bias_value(val=val, channel=channel)

    def get_voltage(self, channel=1, **readingBuffer):
        '''
        Gets voltage value of channel <channel> taking tunnel settings of the electronic into accout (<sweep_mode>, <pseudo_bias_mode>)
        
        Input:
            channel (int)   : 1 | 2
            **readingBuffer : readingBuffer (str)
        Output:
            val (float)
        '''
        if self._sweep_mode == 0: # 0 (VV mode)
            if not self._pseudo_bias_mode: # 0 (current bias)
                return self._SMU.get_sense_value(channel=channel)/self._amp
            elif self._pseudo_bias_mode: # 1 (voltage bias)
                return self._SMU.get_bias_value(channel=channel)/self._Vdiv
        elif self._sweep_mode == 1: # 1 (IV mode)
            return self._SMU.set_sense_value(channel=channel)
        elif self._sweep_mode == 2: # 2 (VI-mode)
            return self._SMU.set_bias_value(channel=channel)

    def set_current(self, val, channel=1):
        '''
        Sets current value of channel <channel> to <val> taking tunnel settings of the electronic into accout (<sweep_mode>, <pseudo_bias_mode>)
        
        Input:
            val (float): arb.
            channel (int): 1 | 2
        Output:
            None
        '''
        if self._sweep_mode == 0: # 0 (VV mode)
            if not self._pseudo_bias_mode: # 0 (current bias)
                return self._SMU.set_bias_value(val=val/self._dAdV, channel=channel)
            elif self._pseudo_bias_mode: # 1 (voltage bias)
                logging.error(__name__ + ': Cannot set current of channel {:d} in the voltage bias.'.format(channel))
                raise AttributeError(__name__ + ': Cannot set current of channel {:d} in the voltage bias.'.format(channel))
        elif self._sweep_mode == 1: # 1 (IV mode)
            return self._SMU.set_bias_value(val=val, channel=channel)
        elif self._sweep_mode == 2: # 2 (VI-mode)
            logging.error(__name__ + ': Cannot set current of channel {:d} in the voltage bias.'.format(channel))
            raise AttributeError(__name__ + ': Cannot set current of channel {:d} in the voltage bias.'.format(channel))

    def get_current(self, channel=1, **readingBuffer):
        '''
        Gets current value of channel <channel> taking tunnel settings of the electronic into accout (<sweep_mode>, <pseudo_bias_mode>)
        
        Input:
            channel (int)   : 1 | 2
            **readingBuffer : readingBuffer (str)
        Output:
            val (float)
        '''
        if self._sweep_mode == 0: # 0 (VV mode)
            if not self._pseudo_bias_mode: # 0 (current bias)
                return self._SMU.get_bias_value(channel=channel)*self._dAdV
            elif self._pseudo_bias_mode: # 1 (voltage bias)
                return self._SMU.get_sense_value(channel=channel)/self._dVdA
        elif self._sweep_mode == 1: # 1 (IV mode)
            return self._SMU.set_bias_value(channel=channel)
        elif self._sweep_mode == 2: # 2 (VI-mode)
            return self._SMU.set_sense_value(channel=channel)

    def set_sweep_parameters(self, sweep, **kwargs):
        '''
        Sets sweep parameters <sweep> and prepares instrument for VV-mode or IV-mode.
        VV-mode needs two different channels (bias channel <channel_bias> and sense channel <channel_sense>), IV-mode and VI-mode only one (<channel>).
        
        Input:
            sweep (list(float)) : start, stop, step
            **kwargs            : sweep_mode (int)       : 0 (VV-mode) | 1 (IV-mode) (default) | 2 (VI-mode)
                                  pseudo_bias_mode (int) : 0 (current bias) (default) | 1 (voltage bias)
                                  channel_bias (int)     : 1 (default) | 2 for VV-mode
                                  channel_sense (int)    : 1 | 2 (default) for VV-mode
                                  channel (int)          : 1 (default) | 2 for IV-mode or VI-mode
                                  iReadingBuffer (str)
                                  vReadingBuffer (str)
        Output:
            None
        '''
        sweep_mode = kwargs.get('sweep_mode', self._sweep_mode)
        pseudo_bias_mode = kwargs.get('pseudo_bias_mode', self._pseudo_bias_mode)
        if not sweep_mode: # 0 (VV-mode)
            if not pseudo_bias_mode: # 0 (current bias)
                self._sweep = np.array(sweep).astype(float)/self._dAdV
                self._sweep[2] = np.abs(self._sweep[2])
                # alternative: self._sweep = np.array((lambda a: [a[0], a[1], np.abs(a[-1])])(sweep)).astype(float)/self._dAdV
            elif pseudo_bias_mode: # 0 (voltage bias)
                self._sweep = np.array(sweep).astype(float)*self._Vdiv
                self._sweep[2] = np.abs(self._sweep[2])
        return self._SMU.set_sweep_parameters(self._sweep, sweep_mode=sweep_mode, pseudo_bias_mode=pseudo_bias_mode, **kwargs)

    def get_tracedata(self, **kwargs):
        '''
        Starts bias sweep and gets trace data in the VV-mode, IV-mode (default) or VI-mode.
        VV-mode needs two different channels (bias channel <channel_bias> and sense channel <channel_sense>), IV-mode and VI-mode only one (<channel>).
        
        Input:
            sweep (list(float)) : start, stop, step
            **kwargs            : sweep_mode (int)       : 0 (VV-mode) | 1 (IV-mode) (default) | 2 (VI-mode)
                                  pseudo_bias_mode (int) : 0 (current bias) (default) | 1 (voltage bias)
                                  channel_bias (int)     : 1 (default) | 2 for VV-mode
                                  channel_sense (int)    : 1 | 2 (default) for VV-mode
                                  channel (int)          : 1 (default) | 2 for IV-mode or VI-mode
                                  iReadingBuffer (str)
                                  vReadingBuffer (str)
        Output:
            bias_values (numpy.array(float))
            sense_values (numpy.array(float))
        '''
        sweep_mode = kwargs.get('sweep_mode', self._sweep_mode)
        pseudo_bias_mode = kwargs.get('pseudo_bias_mode', self._pseudo_bias_mode)
        bias_values, sense_values = self._SMU.get_tracedata(sweep_mode=sweep_mode, **kwargs)
        if sweep_mode == 0:  # IV-mode
            if not pseudo_bias_mode:  # 0 (current bias)
                I_values = bias_values*self._dAdV
                V_values = sense_values/self._amp
            elif pseudo_bias_mode: # 1 (voltage bias)
                V_values = bias_values/self._Vdiv
                I_values = sense_values/self._dVdA
        elif sweep_mode == 1:  # IV-mode
            I_values = bias_values
            V_values = sense_values
        elif sweep_mode == 2:  # VI-mode
            V_values = bias_values
            I_values = sense_values
        return I_values, V_values

    def take_IV(self, sweep, **kwargs):
        '''
        Takes IV curve with sweep parameters <sweep> in the VV-mode or IV-mode.
        VV-mode needs two different channels (bias channel <channel> and sense channel <channel2>), IV-mode and VI-mode only one (<channel>).
        
        Input:
            sweep (list(float)) : start, stop, step
            **kwargs            : sweep_mode (int)       : 0 (VV-mode) | 1 (IV-mode) (default) | 2 (VI-mode)
                                  pseudo_bias_mode (int) : 0 (current bias) (default) | 1 (voltage bias)
                                  channel_bias (int)     : 1 (default) | 2 for VV-mode
                                  channel_sense (int)    : 1 | 2 (default) for VV-mode
                                  channel (int)          : 1 (default) | 2 for IV-mode or VI-mode
                                  iReadingBuffer (str)
                                  vReadingBuffer (str)
        Output:
            bias_values (numpy.array(float))
            sense_values (numpy.array(float))
        '''
        self.set_sweep_parameters(sweep=sweep, **kwargs)
        return self.get_tracedata(**kwargs)

    def set_defaults(self, pseudo_bias_mode=None, SMU=True, **kwargs):
        '''
        Sets default settings for different pseudo bias modes <pseudo_bias_mode> and optional of the used source measure unit <SMU> of channel <channel>, too, if <SMU>.
        VV-mode needs two different channels (bias channel <channel_bias> and sense channel <channel_sense>), IV-mode and VI-mode only one (<channel>).
        
        Input:
            pseudo_bias_modes (int): None <self._sweep_mode> (default) | 0 (VV-mode) | 1 (IV-mode) | 2 (VI-mode)
            SMU (bool)             : False | True
            **kwargs               : sweep_mode (int)    : None <self._sweep_mode> (default) | 0 (VV-mode) | 1 (IV-mode) | 2 (VI-mode)
                                     channel_bias (int)  : 1 (default) | 2 for VV-mode
                                     channel_sense (int) : 1 | 2 (default) for VV-mode
                                     channel (int)       : 1 (default) | 2 for IV-mode or VI-mode
        Output:
            None
        '''
        # dict of defaults values: defaults[<pseudo_bias_mode>][<parameter>][<value>]
        defaults = {0:{'dAdV':2e-6,
                       'amp':1e3},
                    1:{'dVdA':1e8,
                       'Vdiv':1e3}}
        # distiguish different pseudo bias modes
        if pseudo_bias_mode is not None: self._pseudo_bias_mode = pseudo_bias_mode
        # set values
        for key_parameter, val_parameter in defaults[self._pseudo_bias_mode].items():
            eval('self.set_{:s}(val={!s})'.format(key_parameter, val_parameter))
        if SMU:
            self._SMU.set_defaults(**kwargs)

    def get_all(self, SMU=False, channel=1):
        '''
        Prints all settings and optional of the used source measure unit <SMU> of channel <channel>, too.
        
        Input:
            SMU (bool)   : True | False
            channel (int): 1 | 2
        Output:
            None
        '''
        logging.info(__name__ + ': Get all')
        print('dAdV               = {:1.0e}A/V'.format(self.get_dAdV()))
        print('amplification      = {:1.0e}'.format(self.get_amp()))
        print('dVdA               = {:1.0e}V/A'.format(self.get_dVdA()))
        print('voltage divider    = {:1.0e}'.format(self.get_Vdiv()))
        print('sweep mode         = {:d} ({:s})'.format(self._sweep_mode, self._sweep_modes[self._sweep_mode]))
        print('pseudo bias mode   = {:d} ({:s})'.format(self._pseudo_bias_mode, self._pseudo_bias_modes[self._pseudo_bias_mode]))
        if SMU: self._SMU.get_all(channel=channel)
        return

    def reset(self, SMU=True):
        '''
        Resets internal variables for external bias and optional the instrument to factory settings, if source measure unit <SMU>.
        
        Input:
            SMU (bool): True | False
        Output:
            None
        '''
        self.set_dAdV()
        self.set_amp()
        self.set_dVdA()
        self.set_Vdiv()
        if SMU: self._SMU.reset()

    def get_parameters(self):
        '''
        Gets a parameter list <parlist> of measurement specific setting parameters.
        Needed for .set-file in 'write_additional_files', if qt parameters are not used.
        
        Input:
            None
        Output:
            parlist (dict): Parameter as key, corresponding channels as value
        '''
        parlist = {'measurement_mode': [1, 2],
                   'bias_mode': [1, 2],
                   'sense_mode': [1, 2],
                   'bias_range': [1, 2],
                   'sense_range': [1, 2],
                   'bias_delay': [1, 2],
                   'sense_delay': [1, 2],
                   'sense_average': [1, 2],
                   'plc': [None],
                   'sense_nplc': [1, 2],
                   'sweep_mode': [None],
                   'pseudo_bias_mode': [None]}
        if not self._pseudo_bias_mode: # 0 (current bias)
            parlist['dAdV'] = [None]
            parlist['amp']  = [None]
        elif self._pseudo_bias_mode: # 1 (voltage bias)
            parlist['dVdA'] = [None]
            parlist['Vdiv'] = [None]
        return parlist

    def get(self, param, **kwargs):
        '''
        Gets the current parameter <param> by evaluation 'get_'+<param> and corresponding channel if needed
        In combination with <self.get_parameters> above.
        
        Input:
            param (str): parameter to be got
            **kwargs   : channels (list[int]): certain channel {1, 2} for channel specific parameter or None if no channel (global parameter)
        Output:
            parlist (dict): Parameter as key, corresponding channels as value
        '''
        channels = kwargs.get('channels')
        if channels != [None]:
            return tuple([eval('self.get_{:s}(channel={!s})'.format(param, channel)) for channel in channels])
        else:
            return eval('self.get_{:s}()'.format(param))
