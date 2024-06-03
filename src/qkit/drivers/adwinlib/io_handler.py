''' The io_handler is meant to build the interface between the bit
    values of the adc's and dac's and the physical quantities the user
    wants to apply at the DUT. Therefore, i see the Adwin Outputs in
    combination with everything between the adc/dac and the DUT:
    * Magnetic fields: The current sources and the supraconducting
        coils determine the translation factor between bit_values and
        magnetic fields.
    * Current outputs: voltage_dividers, gain_stages, and filters
        determine the voltage which is applied at the sample.
    * Inputs: IV_converters, gain_stages, voltage_dividers determine
        what quantity is measured (can be voltage in 4-point measurement
        or current in IV-converter measurements, inphase/quadrature for
        lokin_measurmeent)
    For all cases the outputs are defined in two seperate configs:
    * Hard_config: Holds of config parameters, which need to be changed
        by physically altering the setup and are not reguarly changed
        like: output_channels, vector_magnet, current sources ...
    * Soft_config: Holds all parameters, which can be easily changed
        between measurements by flipping switches like voltage dividers.
    * WARNING THIS SRIPT HANDLES ONLY 16 bit output channels!

EXAMPLE CONFIGS:

# 'hard wired' configuration of the adwin and accessories
hard_config = {
    'no_output_channels': 8,
    'outputs': {
        'bx': {'card': 3, 'channel': 1, 'scale': 0.995, 'unit': 'T', 'bits':16},
        'by': {'card': 3, 'channel': 3, 'scale': 0.945, 'unit': 'T', 'bits':16},
        'bz': {'card': 3, 'channel': 5, 'scale': 1.265, 'unit': 'T', 'bits':16},
        'vg': {'card': 3, 'channel': 7, 'scale': 10, 'unit': 'V', 'bits':16},
        'vd': {'card': 3, 'channel': 8, 'scale': 10, 'unit': 'V', 'bits':16}
        },
    'inputs': {
        'id': {'card': 2, 'channel': 8, 'scale': 10, 'unit': 'A', 'bits': 18}
        }
    }

# between measurement 'switchable' configuration of adwin accessories 
soft_config = {
    'vdivs': {'vg':0.5, 'vd':0.01},
    'iv_gain': {'id':1e8},
    'readout_channel': 'id'
}

'''

from copy import deepcopy
import math
from math import sqrt, atan2
import logging as log
from numpy import ndarray, float32
import numpy as np

__version__ = '1.0_20240425'
__author__ = 'Luca Kosche'

def bit2volt(val: int|float|ndarray|list, bits, vrange, absolute):
    """ Calculate voltage from bit value for card with voltage range -10V
        to 10V with 16-bits (default). 
        absolute=True: 0 -> -vrange
        absolute=False: 0 -> 0"""
    match val:
        case float32() | float() | int():
            if absolute:
                res = val * vrange / 2**(bits-1) - vrange
            else:
                res = val * vrange / 2**(bits-1)
            return res
        case list():
            return [bit2volt(v, bits, vrange, absolute) for v in val]
        case ndarray():
            return np.vectorize(bit2volt)(val, bits, vrange, absolute)
        case _:
            raise AdwinArgumentError

def volt2bit(val, bits=16, vrange=10, absolute=True):
    """ Calculating bit value from voltage for card with voltage range -10V
        to 10V with 16-bits (default). """
    bit0 = 2**(bits-1)
    match val:
        case float32() | float() | int():
            if not math.isnan(val):
                if absolute:
                    res = round(val * bit0 / vrange + bit0)
                    if 0 <= res <= 2**bits:
                        return res
                else:
                    res = round(val * bit0 / vrange)
                    if -bit0 <= res <= bit0:
                        return res
            # if there is no return so far, raise error
            raise AdwinInvalidOutputError
        case list():
            return [volt2bit(v, bits, vrange) for v in val]
        case ndarray():
            return np.vectorize(volt2bit)(val, bits, vrange)
        case _:
            raise AdwinArgumentError

def calc_r(x, y):
    ''' Calc R of lockin signal from X and Y. '''
    match x:
        case int() | float():
            return sqrt(x**2 + y**2)
        case list():
            return [calc_r(x[i], y[i]) for i in range(len(x))]
        case np.ndarray():
            return np.vectorize(calc_r)(x, y)

def calc_theta(x, y):
    ''' Calc theta of lockin signal from X and Y. '''
    match x:
        case int() | float():
            return atan2(y, x)
        case list():
            return [calc_theta(x[i], y[i]) for i in range(len(x))]
        case np.ndarray():
            return np.vectorize(calc_theta)(x, y)

class AdwinTransmissionError(Exception):
    """ Error which happens, when the adwin does send more or less than
        expected samples during readout. There might be some handlers in
        place accpeting some deviation """

class AdwinModeError(Exception):
    """ Error when unsupported functions for the currently seleted mode
        are used """

class AdwinLimitError(Exception):
    """ Error when unsupported parameters are used for the Adwin
        functions """

class AdwinInvalidOutputError(Exception):
    """ Error when the Adwin is supposed to put out a value outside of
        it's range """

class AdwinArgumentError(Exception):
    """ Error raised, when function arguments are systematically of the
        wrong type """

class AdwinNotImplementedError(Exception):
    """ Error raised, when a specific case or function is not implemented"""

class AdwinIO():
    ''' This class holds Adwin output and input configuration and
        translates between physical quantities and bit_values values.
        So far 16-bit output cards are assumed. '''
    def __init__(self, hard_config:dict, soft_config:dict):
        # save a copy of hard_config (which should never be changed)
        self.__hard_config = deepcopy(hard_config)
        # save configuration outputs, in which the scaling factor will be
        # updated by the soft_config and runtime changes
        self._cfg = {'out': hard_config['outputs'],
                     'in': hard_config['inputs']}
        self._no_output_channels = hard_config['no_output_channels']
        # soft config
        self._readout_ch = None
        self.update_soft_config(**soft_config)

    def update_soft_config(self,
                           vdivs: dict = None,
                           iv_gain: dict = None,
                           readout_channel: str = None):
        ''' update soft configuration parameters '''
        if readout_channel:
            self._readout_ch = readout_channel
        if vdivs:
            self.set_voltage_diviers(vdivs)
        if iv_gain:
            self.set_iv_converters(iv_gain)

    def set_voltage_diviers(self, dividers: dict):
        ''' set total voltage divider for output channels between 
            adwin and sample including dividers, gain or filters.
            Sanity check might need an update. '''
        if isinstance(dividers, dict):
            for name, vdiv in dividers.items():
                # sanity check
                if not 0.0001 <= vdiv <= 1:
                    raise AdwinLimitError
                base_scale = self.__hard_config['outputs'][name]['scale']
                self._cfg['out'][name]['scale'] = base_scale * vdiv
        else:
            raise AdwinArgumentError

    def set_iv_converters(self, iv_gain: dict):
        ''' set the total gain of the iv_converters for input channels
            (total gain of the IV_stage including potential voltage
            or filters after the IV converter itself)'''
        if isinstance(iv_gain, dict):
            for name, gain in iv_gain.items():
                base_scale = self.__hard_config['inputs'][name]['scale']
                self._cfg['in'][name]['scale'] = base_scale / gain
        else:
            raise AdwinArgumentError

    def qty2bit(self, values:dict|ndarray|int|float,
                channel:str|int=None, absolute:bool=True):
        ''' Transform the physical quantities of the outputs into bit
            values using the given information about the used setup 
            All configured output channels will be translated based on
            the index in the given list. Index 0 will be treated as
            output channel 1 an so for. All undefined channels will be
            set to zero.'''
        # check the type of values to decide what the function should do
        match values:
            # if values is dict, the keys should be channels, the values
            # should be single values|list|array of values.
            # Then for each channel the function will recursively be
            # called to transform each channel seperately.
            case dict():
                # create output array and initialize with DAC_ZERO
                res = np.empty(self._no_output_channels)
                res.fill(2**15)
                for name, qty in values.items():
                    if name in self._cfg['out']:
                        idx = self._cfg['out'][name]['channel'] - 1
                    else:
                        msg = 'ADwinIO: neglected given input ch.'
                        log.warning(msg)
                    res[idx] = self.qty2bit(qty, name, absolute)
                return res
            # if channel number is given instead of name, translate
            # into channel name (only works for output channels).
            case list() | ndarray() | int() | float():
                if isinstance(channel, int):
                    channel = self._get_output_channel_name(channel)
                if not self.is_channel(channel):
                    log.critical('ADwinIO: channel %s does not exist.',
                                 channel)
                    raise AdwinArgumentError
                inout = self._channel_direction(channel)
                scale = self._cfg[inout][channel]['scale']
                bits = self._cfg[inout][channel]['bits']
                return volt2bit(values, bits, scale, absolute)
            # in all other cases raise error
            case _:
                log.critical('AdwnIO: type(values) not supported.')
                raise AdwinArgumentError


    def bit2qty(self, values:ndarray|list|int|float, channel:str|int,
                absolute:bool):
        ''' Translate bit values of out/inputs physical quantity into bit value
            using the information of the scaling factor of the out/input and
            how many bits the corresponding card has. The value should be a
            single value of a list of values of one channel.'''
        if channel == 'readout':
            channel = self._readout_ch
        if isinstance(channel, int):
            channel = self._get_output_channel_name(channel)
        # Now the channel name should be known -> translate values
        if self.is_channel(channel):
            inout = self._channel_direction(channel)
            scale = self._cfg[inout][channel]['scale']
            bits = self._cfg[inout][channel]['bits']
            return bit2volt(values, bits, scale, absolute)
        # if nothing could be returned, raise error
        raise AdwinArgumentError

    def is_channel(self, channel:str):
        ''' check if channel is configured '''
        if self._channel_direction(channel) in ['in', 'out']:
            return True
        return False


    def list_channels(self, inout:str):
        ''' return a list of the names of all configured inout (inputs/outputs)
            channels '''
        return self._cfg[inout].keys()

    def _channel_direction(self, channel):
        if channel in self._cfg['out']:
            return 'out'
        if channel in self._cfg['in']:
            return 'in'
        return None

    def _get_output_channel_name(self, channel):
        if isinstance(channel, int):
            for key, val in self._cfg['out'].items():
                if val['channel'] == channel:
                    return key
        return None

if __name__ == '__main__':
    pass
