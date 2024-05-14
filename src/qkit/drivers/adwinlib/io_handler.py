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

EXAMPLE CONFIGS:

hard_config = {
    'no_output_channels': 8,
    'outputs': {
        'bx': {'card': 3, 'channel': 1, 'scale': 0.995, 'unit': 'T'},
        'by': {'card': 3, 'channel': 3, 'scale': 0.945, 'unit': 'T'},
        'bz': {'card': 3, 'channel': 5, 'scale': 1.265, 'unit': 'T'},
        'vg': {'card': 3, 'channel': 7, 'scale': 10, 'unit': 'V'},
        'vd': {'card': 3, 'channel': 8, 'scale': 10, 'unit': 'V'}
        },
    'inputs': {
        'id': {'channel': 8, 'scale': 10, 'unit': 'A', 'bits': 18}
        }
    }

soft_config = {
    'vdivs': {'vg':0.5, 'vd':0.01},
    'iv_gain': {'id':1e8},
    'readout_channel': 'id'
}

'''
import numpy as np
from numpy import ndarray

__version__ = '1.0_20240425'
__author__ = 'Luca Kosche'

def bit2volt(bit_vals: int|float|ndarray|list, bits=16, vrange=10):
    """ Calculate voltage from bit value for card with voltage range -10V
        to 10V with 16-bits (default). """
    if isinstance(bit_vals, (float, int)):
        return bit_vals * vrange / 2**(bits-1) - vrange
    if isinstance(bit_vals, list):
        return [bit2volt(x, bits, vrange) for x in bit_vals]
    if isinstance(bit_vals, np.ndarray):
        return np.vectorize(bit2volt)(bit_vals, bits, vrange)
    raise AdwinArgumentError

def volt2bit(volt_val, bits=16, vrange=10):
    """ Calculating bit value from voltage for card with voltage range -10V
        to 10V with 16-bits (default). """
    if isinstance(volt_val, (float, int)):
        bit_val = round(volt_val * 2**(bits-1) / vrange + 2**(bits-1))
        if 0 <= bit_val <= 2**bits:
            return bit_val
        raise AdwinInvalidOutputError
    if isinstance(volt_val, list):
        return [volt2bit(x, bits, vrange) for x in volt_val]
    if isinstance(volt_val, np.ndarray):
        return np.vectorize(volt2bit)(volt_val, bits, vrange)
    raise AdwinArgumentError

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
        self.__hard_config = dict(hard_config)
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

    def qty2bit(self,
                values:dict|list|ndarray|int|float,
                channel:str|int=None,
                inout:str='out'):
        ''' Transform the physical quantities of the outputs into bit
            values using the given information about the used setup 
            All configured output channels will be translated based on
            the index in the given list. Index 0 will be treated as
            output channel 1 an so for. All undefined channels will be
            set to zero.'''
        # if channel is specified, only translate a single value
        if channel is not None:
            # if list is given, only select the value belonging to channel
            if isinstance(values, (list, ndarray)):
                values = values[self._get_channel_no(channel, inout)-1]
            # return translated value
            return self._qty2bit_single(values, channel, inout)
        # else translate all given outputs
        bit_vals = np.empty(self._no_output_channels)
        # fill with DAC 'zero' (THIS ONLY WORKS IF ALL CHANNELS HAVE THE SAME
        # BIT VALUES SO FAR)
        if self._all_outputs_same_bit_res():
            bit_vals.fill(2 ** (self._all_outputs_same_bit_res() - 1))
        # if dictionary is given, only change the given values, rest stays '0'
        if isinstance(values, dict):
            for name, qty in values.items():
                idx = self._cfg[inout][name]['channel'] - 1
                bit_vals[idx] = self._qty2bit_single(qty, name, inout)
        # if a list or numpy array is given
        elif isinstance(values, (list, ndarray)):
            # lists should always have the expected amount of channels
            if len(values) == self._no_output_channels:
                for idx, val in enumerate(values):
                    bit_vals[idx] = self._qty2bit_single(val, idx+1, inout)
        else:
            raise AdwinArgumentError
        return bit_vals

    def bit2qty(self, values:ndarray|list|int, channel:str|int=None,
                inout:str='out'):
        ''' Translate bit values of dac outputs to physical
            quantities. If a channel '''
        # if channel is specified, only translate a single value
        if inout == 'in':
            channel = self._readout_ch
            if isinstance(values, (list, ndarray)):
                values = values[self._get_channel_no(channel, inout)-1]
            # return translated value
            return self._bit2qty_single(values, channel, inout)
        if channel is not None:
            # if list is given, only select the value belonging to channel
            if isinstance(values, (list, ndarray)):
                values = values[self._get_channel_no(channel, inout)-1]
            # return translated value
            return self._bit2qty_single(values, channel, inout)
        # else translate all given outputs
        outs = np.empty(len(values))
        outs.fill(np.NaN)
        for idx, val in enumerate(values):
            outs[idx] = self._bit2qty_single(val, idx+1, inout)
        return outs

    def list_channels(self, inout:str):
        ''' return a list of the names of all configured inout (inputs/outputs)
            channels '''
        return self._cfg[inout].keys()

    def _bit2qty_single(self, value:int, channel:str|int, inout:str):
        ''' Translate bit values of out/inputs physical quantity into bit value
            using the information of the scaling factor of the out/input and
            how many bits the corresponding card has. The value should be a
            single value of a list of values of one channel.'''
        # get channel name
        name = self._get_channel_name(channel, inout)
        # if channel has name (is configured) translate value
        if name:
            scale = self._cfg[inout][name]['scale']
            bits = self._cfg[inout][name]['bits']
            return bit2volt(value, bits, scale)
        return None

    def _qty2bit_single(self, value:float|int|list|ndarray,
                        channel:str|int, inout:str):
        ''' Translate physical quantity into bit value using the information of
            the scaling factor of the out/input and how many bits the
            corresponding card has. The value should be a single value of a
            list of values of one channel'''
        # get channel name
        name = self._get_channel_name(channel, inout)
        # if channel has name (is configured) translate value
        if name:
            scale = self._cfg[inout][name]['scale']
            bits = self._cfg[inout][name]['bits']
            return volt2bit(value, bits, scale)
        return None

    def _get_channel_name(self, channel:str|int, inout:str):
        ''' Return channel name when either channel name or channel number is
            given. Be careful to not give an int value and mean the channel idx
            which is channel_number-1 '''
        # if channel is int (channel number, not index!), return the channel if
        # it exists.
        if isinstance(channel, int):
            for key, val in self._cfg[inout].items():
                if val['channel'] == channel:
                    return key
        # if channel if str and is configured channel, return it back
        if isinstance(channel, str):
            if channel in self._cfg[inout]:
                return channel
        return None

    def _get_channel_no(self, channel:str|int, inout:str):
        ''' Return channel number when either channel name or channel number is
            given. Be careful to not give an int value and mean the channel idx
            which is channel_number-1 '''
        # if channel name is given, return number
        if isinstance(channel, str):
            return self._cfg[inout][channel]['channel']
        # if int is given, check if channel number
        # is configure and return it back
        if isinstance(channel, int):
            channels = [val['channel'] for val in self._cfg[inout].values()]
            if channel in channels:
                return channel
        return None

    def _get_channel_idx(self, channel:str|int, inout:str):
        ''' Return channel index. Channel numbers start with 1 and mean the
            physical numbering of the input/output channels of the adwin as
            used in the channel configuration dictionary while idx start with 0
            and are used by python lists/arrays. '''
        return self._get_channel_no(channel, inout) - 1

    def _all_outputs_same_bit_res(self):
        out_bits = [value['bits'] for value in self._cfg['out'].values()]
        if all(x==out_bits[0] for x in out_bits):
            return out_bits[0]
        raise AdwinNotImplementedError

if __name__ == '__main__':
    pass
