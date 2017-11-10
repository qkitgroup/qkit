# Yokogawa_GS820.py driver for Yokogawa GS820 multi channel source measure unit
#
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

from instrument import Instrument
import visa
import logging
import numpy
from sympy.functions.special.delta_functions import Heaviside
import time

class Yokogawa(Instrument):
    '''
    This is the driver for the Yokogawa GS820 Multi Channel Source Measure Unit
    
    
    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Yokogawa', address='<GBIP address>, reset=<bool>')
    '''
    
    def __init__(self, name, address, reset=False):
        '''
        Initializes the Yokogawa_GS820, and communicates with the wrapper.
        
        Input:
          name (string)    : name of the instrument
          address (string) : GPIB address
          reset (bool)     : resets to default values, default=False
        '''
        
        logging.info(__name__ + ' : Initializing instrument Yokogawa_GS820')
        Instrument.__init__(self, name, tags=['physical'])
        
        # Add some global constants
        self._address = address
        self._visainstrument = visa.instrument(self._address)
        
        self._bias_status_register  = { 'EOS1':0 , 'RDY1':1  , 'LL01':2  , 'LHI1':3  , 'TRP1':4  , 'EMR1':5  , 'EOS2':8  , 'RDY2':9  , 'LL02':10  , 'LHI2':11  , 'TRP2':12  , 'EMR2':13  , 'ILC':14  , 'SSB':15  }
        self._sense_status_register = { 'EOM1':0 , 'CLO1':2  , 'CHI1':3  , 'OVR1':5  , 'EOM2':8  , 'CLO2':10  , 'CHI2':11  , 'OVR2':13 , 'EOT':14 , 'TSE':15 }
        
        self._dAdV = 1
        self._dVdA = 1
        self._amp = 1
        
        self._average = 1
        self._integration_time = 2e-2
        self._sense_delay = 15e-6
        self._intrument_delay = 2.1e-3 # fixed
        
#        self._starts = [self._start, self._stop,  self._start, -self._stop]
#        self._stops  = [self._stop,  self._start, -self._stop, self._start]
#        self._steps  = [self._step, -self._step, -self._step, self._step]
#        self._IV_sweep_types = { 0:1 , 1:2, 2:3, 3:4 }
#        self._IV_sweep_type = 1
        
#        self.add_function('set_mode_4W')
#        self.add_function('get_mode_4W')
#        self.add_function('set_bias_mode')
#        self.add_function('get_bias_mode')
#        self.add_function('set_sense_mode')
#        self.add_function('get_sense_mode')
#        self.add_function('set_bias_range')
#        self.add_function('get_bias_range')
#        self.add_function('set_sense_range')
#        self.add_function('get_sense_range')
#        self.add_function('set_sync')
#        self.add_function('get_sync')
#        self.add_function('set_bias_trigger')
#        self.add_function('get_bias_trigger')
#        self.add_function('set_sense_trigger')
#        self.add_function('get_sense_trigger')
#        self.add_function('set_bias_delay')
#        self.add_function('get_bias_delay')
#        self.add_function('set_sense_delay')
#        self.add_function('get_sense_delay')
#        self.add_function('set_sense_average')
#        self.add_function('get_sense_average')
#        self.add_function('set_sense_nplc')
#        self.add_function('get_sense_nplc')
#        self.add_function('set_plc')
#        self.add_function('get_plc')
#        self.add_function('set_sense_integration_time')
#        self.add_function('get_sense_integration_time')
#        
#        self.add_function('set_status')
#        self.add_function('get_status')
#        
#        self.add_function('set_bias_value')
#        self.add_function('get_bias_value')
#        self.add_function('get_sense_value')
#        self.add_function('set_voltage')
#        self.add_function('get_voltage')
#        self.add_function('set_current')
#        self.add_function('get_current')
#        
#        self.add_function('set_sweep_start')
#        self.add_function('get_sweep_start')
#        self.add_function('set_sweep_stop')
#        self.add_function('get_sweep_stop')
#        self.add_function('set_sweep_step')
#        self.add_function('get_sweep_step')
#        self.add_function('set_step_time')
#        self.add_function('get_step_time')
#        self.add_function('get_nop')
#        self.add_function('get_sweep_time')
#    #        self.add_function('get_sweep_parameters')
#        self.add_function('get_sweep')
#        
#        self.add_function('set_defaults')
#        self.add_function('get_all')
#        self.add_function('reset')
#        self.add_function('get_error')
#        self.add_function('clear_error')
#        self.add_function('get_bias_status_register')
#        
#        self.reset()
#        
#        self.add_function('set_dAdV')
#        self.add_function('get_dAdV')
#        self.add_function('set_dVdA')
#        self.add_function('get_dVdA')
#        self.add_function('set_amp')
#        self.add_function('get_amp')
#        self.add_function('get_V_from_I')
#        
#        self.add_function('set_sweep_type')
        
    
    
    def set_dAdV(self, val=1):
        self._dAdV = val
    
    def get_dAdV(self):
        return(self._dAdV)
    
    def set_dVdA(self, val=1):
        self._dVdA = val
    
    def get_dVdA(self):
        return(self._dVdA)
        
    def set_amp(self, val=1):
        self._amp = val
    
    def get_amp(self):
        return(self._amp)
        
    def get_V_from_I(self, I):
        return I*self._dAdV
    
        
        
    def set_mode_4W(self, val, channel=1):
        '''
        Sets wiring system of channel <channel> to <val>
        
        Input:
            channel (int): 1 | 2
            val (bool): True (4W) | False (3W)
        Output:
            None
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SENSe:REMote 1|0|ON|OFF
        try:
            logging.debug(__name__ + ' : set wiring system of channel %s to %s' % (channel, str(val)))
            self._visainstrument.write(':chan%s:sens:rem %i' % (channel, int(val)))
        except AttributeError:
            logging.error('invalid input: cannot set wiring system of channel %s to %f' % (channel, val))
        
        
    def get_mode_4W(self, channel=1):
        '''
        Gets wiring system of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            val (bool): True | False
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SENSe:REMote 1|0|ON|OFF
        try:
            return bool(int(self._visainstrument.ask(':chan%s:sens:rem?' % channel)))
        except ValueError:
            logging.debug('Wiring system of channel %i not specified:' % channel)
    
    
    def set_bias_mode(self, mode, channel=1):
        '''
        Sets bias mode of channel <channel> to <mode> regime.
        
        Input:
            mode (str): 'volt' | 'curr'
            channel (int): 1 | 2
        Output:
            None
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce:FUNCtion VOLTage|CURRent
        try:
            logging.debug('Set bias mode of channel %s to %s' % (channel, mode))
            self._visainstrument.write(':chan%i:sour:func %s' % (channel, mode))
        except AttributeError:
            logging.error('invalid input: cannot set bias mode of channel %s to %s' % (channel, mode))
        
        
    def get_bias_mode(self, channel=1):
        '''
        Gets bias mode <output> of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            mode (str): 'volt' | 'curr'
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce:FUNCtion VOLTage|CURRent
        try:
            return str(self._visainstrument.ask(':chan%i:sour:func?' % channel).lower())
        except ValueError:
            logging.debug('Bias mode of channel %i not specified:' % channel)
        
        
    def set_sense_mode(self, mode, channel=1):
        '''
        Sets sense mode of channel <channel> to <mode> regime.
        
        Input:
            mode (str): 'volt' | 'curr'
            channel (int): 1 | 2
        Output:
            None
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SENSe:FUNCtion VOLTage|CURRent
        try:
            logging.debug('Set sense mode of channel %s to %s' % (channel, mode))
            self._visainstrument.write(':chan%i:sens:func %s' % (channel, mode))
        except AttributeError:
            logging.error('invalid input: cannot set sense mode of channel %s to %s' % (channel, mode))
        
        
    def get_sense_mode(self, channel=1):
        '''
        Gets sense mode <output> of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            mode (str): 'volt' | 'curr'
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SENSe:FUNCtion VOLTage|CURRent
        try:
            return str(self._visainstrument.ask(':chan%i:sens:func?' % channel).lower())
        except ValueError:
            logging.debug('Sense mode of channel %i not specified:' % channel)
        
        
    def set_bias_range(self, val, channel=1):
        '''
        Sets bias range of channel <channel> to <val>
        
        Input:
            val (float): 200mV | 2V | 20V | 50V | 200nA | 2uA | 20uA | 200uA | 2mA | 20mA | 200mA | 1 A | 3A
            channel (int): 1 | 2
        Output:
            None
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce[:VOLTage]:RANGe <voltage>|MINimum|MAXimum|UP|DOWN 
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce[:CURRent]:RANGe <current>|MINimum|MAXimum|UP|DOWN 
        try:
            logging.debug('Set bias voltage range of channel %s to %s' % (channel, val))
            if (val == 'auto'):
                self._visainstrument.write(':chan%d:sour:rang:auto 1' % channel)
            else:
                self._visainstrument.write(':chan%i:sour:rang %s' % (channel, val))
        except AttributeError:
            logging.error('invalid input: cannot set bias range of channel %s to %s' % (channel, val))
        
        
    def get_bias_range(self, channel=1):
        '''
        Gets bias range for the current mode.
        
        Input:
            channel (int): 1 | 2
        Output:
            range (float): 
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce[:VOLTage]:RANGe <voltage>|MINimum|MAXimum|UP|DOWN 
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce[:CURRent]:RANGe <current>|MINimum|MAXimum|UP|DOWN 
        try:
            return float(self._visainstrument.ask(':chan%i:sour:rang?' % channel))
        except ValueError:
            logging.debug('Bias range of channel %i not specified:' % channel)
        
        
    def set_sense_range(self, val, channel=1):
        '''
        Sets sense range of channel <channel> to <val>
        
        Input:
            val (float): 'auto' | 200mV | 2V | 20V | 50V | 200nA | 2uA | 20uA | 200uA | 2mA | 20mA | 200mA | 1 A | 3A
            channel (int): 1 | 2
        Output:
            None
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SENSe[:VOLTage]:RANGe <voltage>|MINimum|MAXimum|UP|DOWN
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SENSe[:CURRent]:RANGe <current>|MINimum|MAXimum|UP|DOWN
        try:
            logging.debug('Set sense range of channel %s to %s' % (channel, val))
            if val == 'auto':
                self._visainstrument.write(':chan%d:sens:rang:auto 1' % channel)
            else:
                self._visainstrument.write(':chan%i:sens:rang %f' % (channel, val))
        except AttributeError:
            logging.error('invalid input: cannot set sense range of channel %s to %f' % (channel, val))
        
        
    def get_sense_range(self, channel=1):
        '''
        Gets sense range for the current mode.
        
        Input:
            channel(int): 
        Output:
            range (float) : 
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SENSe[:VOLTage]:RANGe <voltage>|MINimum|MAXimum|UP|DOWN
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SENSe[:CURRent]:RANGe <current>|MINimum|MAXimum|UP|DOWN
        try:
            return float(self._visainstrument.ask(':chan%i:sens:rang?' % channel))
        except ValueError:
            logging.debug('Sense range of channel %i not specified:' % channel)
        
        
    def set_sync(self, val):
        '''
        Sets the interchannel synchronization to <val>
        (The first channel is always the "master", the second the "slave")
        
        Input:
            val (bool): 1 (ON) | 2 (OFF)
        Output:
            None
        '''
        # <<Corresponding Command Mnemonic>>: :SYNChronize:CHANnel 1|0|ON|OFF
        try:
            logging.debug('Set the channels in synchronized regime to %i' % val)
            self._visainstrument.write(':sync:chan %i' % val)
        except AttributeError:
            logging.error('invalid input: cannot set the interchannel synchronization to %f' % val)
        
        
    def get_sync(self):
        '''
        Gets the interchannel synchronization
        
        Input:
            None
        Output:
            val (bool): 1 (ON) | 2 (OFF)
        '''
        # <<Corresponding Command Mnemonic>>: :SYNChronize:CHANnel 1|0|ON|OFF
        try:            
            return bool(int(self._visainstrument.ask(':sync:chan?')))
        except ValueError:
            logging.debug('Interchannel synchronization not specified:')
        
        
    def set_bias_trigger(self, mode, channel=1, **val):
        '''
        Sets bias trigger mode of channel <channel> to <mode> and value <val>
        
        Input:
            mode (str): ext (external) | aux (auxiliary) | tim1 (timer1) | tim2 (timer2) | sens (sense)
            channel (int): 1 | 2
            **val: 100us <= time (float) <= 3600.000000s
        Output:
            None
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce:TRIGger EXTernal|AUXiliary|TIMer1|TIMer2|SENSe
        # <<Corresponding Command Mnemonic>>: :TRIGger:TIMer1 <time>|MINimum|MAXimum
        try:
            logging.debug('Set bias trigger of channel %s to %s' % (channel, mode))
            self._visainstrument.write(':chan%i:sour:trig %s' % (channel, mode))
            if 'time' in val: self._visainstrument.write(':trig:%s %f' % (mode, val.get('time', 50e-3)))
        except AttributeError:
            logging.error('invalid input: cannot set bias trigger of channel %s to %s' % (channel, mode))
        
        
    def get_bias_trigger(self, channel=1):
        '''
        Gets bias trigger <output> of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            trigger (str): ext (external) | aux (auxiliary) | tim1 (timer1) | tim2 (timer2) | sens (sense)
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce:TRIGger EXTernal|AUXiliary|TIMer1|TIMer2|SENSe
        try:
            return str(self._visainstrument.ask(':chan%i:sour:trig?' % channel).lower())
        except ValueError:
            logging.debug('Bias trigger of channel %i not specified:' % channel)
        
        
    def set_sense_trigger(self, mode, channel=1, **val):
        '''
        Sets sense trigger mode of channel <channel> to <trigger> and value <val>
        
        Input:
            mode (str): ext (external) | aux (auxiliary) | tim1 (timer1) | tim2 (timer2) | sens (sense)
            channel (int): 1 | 2
            **val: 100us <= time (float) <= 3600.000000s
        Output:
            None
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SENSe:TRIGger EXTernal|AUXiliary|TIMer1|TIMer2|SENSe
        # <<Corresponding Command Mnemonic>>: :TRIGger:TIMer1 <time>|MINimum|MAXimum
        try:
            logging.debug('Set sense trigger of channel %s to %s' % (channel, mode))
            self._visainstrument.write(':chan%i:sens:trig %s' % (channel, mode))
            if 'time' in val: self._visainstrument.write(':trig:%s %f' % (mode, val.get('time', 50e-3)))
        except AttributeError:
            logging.error('invalid input: cannot set sense trigger of channel %s to %s' % (channel, mode))
        
        
    def get_sense_trigger(self, channel=1):
        '''
        Gets sense trigger <output> of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            trigger (str): ext (external) | aux (auxiliary) | tim1 (timer1) | tim2 (timer2) | sens (sense)
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SENSe:TRIGger EXTernal|AUXiliary|TIMer1|TIMer2|SENSe
        try:
            return str(self._visainstrument.ask(':chan%i:sens:trig?' % channel).lower())
        except ValueError:
            logging.debug('Sense trigger of channel %i not specified:' % channel)
        
        
    def set_bias_delay(self, val, channel=1):
        '''
        Sets bias delay of channel <channel> to <val>
        
        Input:
            delay (float): 15us <= delay <= 3600s
            channel (int): 1 | 2
        Output:
            None
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce:DELay <time>|MINimum|MAXimum
        try:
            logging.debug('Set bias delay of channel %s to %s' % (channel, val))
            self._visainstrument.write(':chan%i:sour:del %s' % (channel, val))
        except AttributeError:
            logging.error('invalid input: cannot set bias delay of channel %s to %s' % (channel, val))
        
        
    def get_bias_delay(self, channel=1):
        '''
        Gets bias delay <output> of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            delay (float):
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce:DELay <time>|MINimum|MAXimum
        try:
            return float(self._visainstrument.ask(':chan%i:sour:del?' % channel))
        except ValueError:
            logging.debug('Bias delay of channel %i not specified:' % channel)
        
        
    def set_sense_delay(self, val, channel=1):
        '''
        Sets sense delay of channel <channel> to <val>
        
        Input:
            val (float): 15us <= delay <= 3600s
            channel (int): 1 | 2
        Output:
            None
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce:DELay <time>|MINimum|MAXimum
        try:
            logging.debug('Set sense delay of channel %s to %s' % (channel, val))
            self._visainstrument.write(':chan%i:sens:del %s' % (channel, val))
        except AttributeError:
            logging.error('invalid input: cannot set sense delay of channel %s to %s' % (channel, val))
    
    
    def get_sense_delay(self, channel=1):
        '''
        Gets sense delay <output> of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            delay (float):
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SENSe:DELay <time>|MINimum|MAXimum
        try:
            return float(self._visainstrument.ask(':chan%i:sens:del?' % channel))
        except ValueError:
            logging.debug('Sense delay of channel %i not specified:' % channel)
    
    
    def set_sense_average(self, avg, channel=1):
        '''
        Sets sense average of channel <channel> to <avg>
        
        Input:
            avg (int)
            channel (int): 1 | 2
        Output:
            None
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SENSe:AVERage[:STATe] 1|0|ON|OFF
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SENSe:AVERage:COUNt <integer>|MINimum|MAXimum
        try:
            status = bool(Heaviside(avg-1.0000001))
            logging.debug('Set sense average of channel %s to %i' % (channel, avg))
            self._visainstrument.write(':chan%i:sens:aver:stat %i' % (channel, status))
            if status: self._visainstrument.write(':chan%i:sens:aver:coun %i' % (channel, avg))
        except AttributeError:
            logging.error('invalid input: cannot set sense average of channel %s to %i' % (channel, avg))
    
    
    def get_sense_average(self, channel=1):
        '''
        Gets sense average of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            status (bool)
            avg (int)
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SENSe:AVERage[:STATe] 1|0|ON|OFF
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SENSe:AVERage:COUNt <integer>|MINimum|MAXimum
        try:
            status = bool(int(self._visainstrument.ask(':chan%i:sens:aver:stat?' % channel)))
            avg = int(self._visainstrument.ask(':chan%i:sens:aver:coun?' % channel))
            return status, avg
        except ValueError:
            logging.debug('Sense average of channel %i not specified:' % channel)
    
    
    def set_sense_nplc(self, nplc, channel=1):
        '''
        Sets sense integrarion time of channel <channel> with the <nplc>-fold of one power line cycle
        
        Input:
            channel (int): 1 | 2
            nplc (float)
        Output:
            None
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SENSe:NPLC <real number>|MINimum|MAXimum
        try:
            logging.debug('Set sense integrarion time of channel %s to %i PLC' % (channel, nplc))
            self._visainstrument.write(':chan%i:sens:nplc %i' % (channel, nplc))
        except ValueError:
            logging.debug('Number of PLC of channel %i not specified:' % channel)
    
    
    def get_sense_nplc(self, channel=1):
        '''
        Gets sense integrarion time of channel <channel>
        
        Input:
            channel (int): 1 | 2
            nplc (float)
        Output:
            None
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SENSe:NPLC <real number>|MINimum|MAXimum
        try:
            return float(self._visainstrument.ask(':chan%i:sens:nplc?' % channel))
        except ValueError:
            logging.debug('Number of PLC of channel %i not specified:' % channel)
    
    
    def set_plc(self, plc):
        '''
        Sets power line cycle (PLC) to <plc>
        
        Input:
            plc: 'auto' | 50 | 60
        Output:
            None
        '''
        # <<Corresponding Command Mnemonic>>: :SYSTem:LFRequency 50|60
        # <<Corresponding Command Mnemonic>>: :SYSTem:LFRequency:AUTO 1|0|ON|OFF
        try:
            logging.debug('Set PLC to %s' % str(plc))
            cmd = {'auto':':auto 1', '50':' 50', '60':' 60'}
            self._visainstrument.write('syst:lfr%s' % cmd[str(plc)])
        except ValueError:
            logging.debug('PLC not specified:')
    
    
    def get_plc(self):
        '''
        Gets power line cycle (PLC)
        
        Input:
            None
        Output:
            plc (float): 50 | 60
        '''
        # <<Corresponding Command Mnemonic>>: :SYSTem:LFRequency 50|60
        # <<Corresponding Command Mnemonic>>: :SYSTem:LFRequency:AUTO 1|0|ON|OFF
        try:
            return float(self._visainstrument.ask('syst:lfr?'))
        except ValueError:
            logging.debug('PLC not specified:')
    
    
    def set_sense_integration_time(self, time, channel=1):
        '''
        Gets get sense integration time
        
        Input:
            time (float): integer multiples of PLC (default 2e-2 )
            channel (int): 1 | 2
        Output:
            None
        '''
        try:
            nplc = int(time*self.get_plc())
            logging.debug('Set sense integration time of channel %i to %f' % (channel, time))
            self.set_sense_nplc(nplc=nplc, channel=channel) 
        except ValueError:
            logging.debug('Sense integrarion time of channel %i not specified:' % channel)
    
    
    def get_sense_integration_time(self, channel=1):
        '''
        Gets get sense integration time
        
        Input:
            None
        Output:
            time
        '''
        try:
            return self.get_sense_nplc(channel=channel)/self.get_plc()
        except ValueError:
            logging.debug('Sense integration time not specified:')
        
    
    def set_status(self, status, channel=1):
        '''
        Sets output status of channel <channel> to <status>
        
        Input:
            status (bool): True (ON) | False (OFF)
            channel (int): 1 | 2
        Output:
            None
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:OUTput:STATus 1|0|ON|OFF
        try:
            logging.debug('Set output status of channel %s to %r' % (channel, status))
            self._visainstrument.write(':chan%i:outp:stat %i' % (channel, status))
        except AttributeError:
            logging.error('invalid input: cannot set output status of channel %s to %r' % (channel, status))
        
        
    def get_status(self, channel=1):
        '''
        Gets output status of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            status (bool): True (ON) | False (OFF)
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:OUTput:STATus 1|0|ON|OFF
        try:
            return bool(int(self._visainstrument.ask(':chan%i:outp:stat?' % channel)))
        except ValueError:
            logging.debug('Status of channel %i not specified:' % channel)
        
        
    def set_bias_value(self, val, channel=1):
        '''
        Sets bias value of channel <channel> to value >val>
        
        Input:
            val (float): arb.
            channel (int): 1 | 2
        Output:
            None
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce[:VOLTage]:LEVel <voltage>|MINimum|MAXimum
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce[:CURRent]:LEVel <current>|MINimum|MAXimum
        try:
            logging.debug(__name__ + ' : set bias value of channel %s to %s' % (channel, str(val)))
            self._visainstrument.write(':chan%s:sour:lev %f' % (channel, val))
        except AttributeError:
            logging.error('invalid input: cannot set bias value of channel %s to %f' % (channel, val))
        
        
    def get_bias_value(self, channel=1):
        '''
        Gets bias value of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            val (float)
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce[:VOLTage]:LEVel <voltage>|MINimum|MAXimum
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce[:CURRent]:LEVel <current>|MINimum|MAXimum
        try:
            return float(self._visainstrument.ask(':chan%s:sour:lev?' % channel))
        except ValueError:
            logging.error('Cannot get bias value of channel %i:' % channel)
        
        
    def get_sense_value(self, channel=1):
        '''
        Gets sense value of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            val (float)
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:MEASure?
        try:
            return float(self._visainstrument.ask(':chan%d:meas?' % channel))
        except ValueError:
            logging.error('Cannot get sense value of channel %i:' % channel)
        
        
    def set_voltage(self, val, channel=1):
        '''
        Sets voltage value of channel <channel> to <val>
        
        Input:
            val (float): arb.
            channel (int): 1 | 2
        Output:
            None
        '''
        if self.get_bias_mode(channel) == 'volt':
            return self.set_bias_value(val, channel)
        elif self.get_bias_mode(channel) == 'curr':
            logging.error('Cannot set set voltage value of channel %i: in the current bias' % channel)
        
        
    def get_voltage(self, channel=1):
        '''
        Gets voltage value of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            val (float)
        '''
        if self.get_bias_mode(channel) == 'volt':
            return self.get_bias_value(channel)
        elif self.get_sense_mode(channel) == 'volt':
            return self.get_sense_value(channel)
        
        
    def set_current(self, val, channel=1):
        '''
        Sets current value of channel <channel> to <val>
        
        Input:
            val (float): arb.
            channel (int): 1 | 2
        Output:
            None
        '''
        if self.get_bias_mode(channel) == 'curr':
            return self.set_bias_value(val, channel)
        elif self.get_bias_mode(channel) == 'volt':
            logging.error('Cannot set set current value of channel %i: in the voltage bias' % channel)
        
        
    def get_current(self, channel=1):
        '''
        Gets current value of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            val (float)
        '''
        if self.get_bias_mode(channel) == 'curr':
            return self.get_bias_value(channel)
        elif self.get_sense_mode(channel) == 'curr':
            return self.get_sense_value(channel)
    
    
    def set_sweep_start(self, start, channel=1):
        '''
        Sets sweep start value of channel <channel> to <start>
        
        Input:
            start arr((float))
            channel (int): 1 | 2
        Output:
            None
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce[:VOLTage]:SWEep:STARt <voltage>|MINiumum|MAXimum
        try:
            logging.debug('Set sweep start of channel %s to %s' % (channel, start))
            self._visainstrument.write(':chan%s:sour:%s:swe:star %f' % (channel, self.get_bias_mode(channel), start))
        except AttributeError:
            logging.error('invalid input: cannot set sweep start of channel %s to %s' % (channel, start))
    
    
    def get_sweep_start(self, channel=1):
        '''
        Gets sweep start value <output> of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            start (float)
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce[:VOLTage]:SWEep:STARt <voltage>|MINiumum|MAXimum
        try:
            return float(self._visainstrument.ask(':chan%s:sour:%s:swe:star?' % (channel, self.get_bias_mode(channel))))
        except ValueError:
            logging.debug('Sweep start of channel %i not specified:' % channel)
    
    
    def set_sweep_stop(self, stop=0, channel=1):
        '''
        Sets sweep stop value of channel <channel> to <stop>
        
        Input:
            stop (float)
            channel (int): 1 | 2
        Output:
            None
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce[:VOLTage]:SWEep:STARt <voltage>|MINiumum|MAXimum
        try:
            logging.debug('Set sweep stop of channel %s to %s' % (channel, stop))
            self._visainstrument.write(':chan%s:sour:%s:swe:stop %f' % (channel, self.get_bias_mode(channel), stop))
        except AttributeError:
            logging.error('invalid input: cannot set sweep stop of channel %s to %s' % (channel, stop))
    
    
    def get_sweep_stop(self, channel=1):
        '''
        Gets sweep stop value <output> of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            stop (float)
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce[:VOLTage]:SWEep:STARt <voltage>|MINiumum|MAXimum
        try:
            return float(self._visainstrument.ask(':chan%s:sour:%s:swe:stop?' % (channel, self.get_bias_mode(channel))))
        except ValueError:
            logging.debug('Sweep stop of channel %i not specified:' % channel)
    
    
    def set_sweep_step(self, step=0, channel=1):
        '''
        Sets sweep step value of channel <channel> to <step>
        
        Input:
            step (float)
            channel (int): 1 | 2
        Output:
            None
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce[:VOLTage]:SWEep:STARt <voltage>|MINiumum|MAXimum
        try:
            logging.debug('Set sweep step of channel %s to %s' % (channel, step))
            self._visainstrument.write(':chan%s:sour:%s:swe:step %f' % (channel, self.get_bias_mode(channel), step))
        except AttributeError:
            logging.error('invalid input: cannot set sweep step of channel %s to %s' % (channel, step))
    
    
    def get_sweep_step(self, channel=1):
        '''
        Gets sweep step value <output> of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            step (float)
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce[:VOLTage]:SWEep:STARt <voltage>|MINiumum|MAXimum
        try:
            return float(self._visainstrument.ask(':chan%s:sour:%s:swe:step?' % (channel, self.get_bias_mode(channel))))
        except ValueError:
            logging.debug('Sweep step of channel %i not specified:' % channel)
    
    
    def set_sweep_parameters(self, sweep, channel=1):
        self.set_sweep_start(float(sweep[0]))
        self.set_sweep_stop(float(sweep[1]))
        self.set_sweep_step(float(sweep[2]))
        print('sweep', sweep)
        
        self._step_time = self._integration_time*self._average+2.*self._sense_delay+self._intrument_delay
        self.set_step_time(step_time=self._step_time, trigger='tim1', channel=channel)
        self.set_sense_trigger(mode='sour', channel=channel)
        self.set_sense_delay(self._sense_delay, channel=channel)
        self.set_sense_integration_time(time=self._integration_time, channel=channel)
        self.set_sense_average(avg=self._average, channel=channel)
    
    
    def set_step_time(self, step_time, trigger='tim1', channel=1):
        self.set_bias_trigger(mode=trigger, time=step_time, channel=channel)
        
    def get_step_time(self, channel=1):
        try:
            if self.get_bias_trigger(channel=channel)[0:3] == 'tim': return(float(self._visainstrument.ask(':trig:%s?' % self.get_bias_trigger(channel=channel))))
        except ValueError:
            logging.debug('Sweep step time of channel %i not specified:' % channel)
    
    
    def get_nop(self, channel=1):
        '''
        Gets sweep nop <output> of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            nop (int)
        '''
        try:
            return int((self.get_sweep_stop(channel=channel)-self.get_sweep_start(channel=channel))/self.get_sweep_step(channel=channel)+1)
        except ValueError:
            logging.debug('Sweep nop of channel %i not specified:' % channel)
    
    
    def get_sweep_time(self, channel=1):
        '''
        Gets sweep time <output> of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            sweeptime (float)
        '''
        try:
            return float(self.get_step_time(channel=channel)*(self.get_nop(channel=channel)-1))
        except ValueError:
            logging.debug('Sweep time of channel %i not specified:' % channel)
    
    
    def take_sweep(self, channel=1):
        '''
        Starts bias sweep of channel <channel> with parameters <start>, <stop>, <step>, <average>
        
        Input:
            channel (int): 1 | 2
        Output:
            bias_value (numpy.array(float))
            sense_value (numpy.array(float))
        '''
        
        self._visainstrument.write(':chan%i:sour:mode swe' % channel)
        #self._visainstrument.write(':trac:poin %i' % self.get_nop(channel=channel))
        self._visainstrument.write(':trac:poin max')
        self._visainstrument.write(':trac:chan1:data:form asc')
        self._visainstrument.write(':trac:bin:repl asc')
        #self.set_bias_value(self._start, channel=channel)
        
        self._visainstrument.write(':chan%i:init' % channel)
        #self.set_status(True, channel=channel)
        self._wait_for_ready_for_sweep(channel=channel)
        self._visainstrument.write(':trac:stat 1')
        self._visainstrument.write(':star')
        self._wait_for_end_of_sweep(channel=channel)
        self._wait_for_end_of_measure(channel=channel)
        self._visainstrument.write(':trac:stat 0')
        #self.set_status(False, channel=channel)
        print 'Sweep finished'
        
        bias_values = numpy.array([float(v) for v in self._visainstrument.ask('trac:chan%i:data:read? sl' % channel).split(',')])*self._dAdV
        sense_values = numpy.array([float(v) for v in self._visainstrument.ask('trac:chan%i:data:read? ml' % channel).split(',')])/self._amp
        
        return bias_values, sense_values
            
    
    def set_sweep_type(self, sweep_type = 1):
        '''
        # FIXME: HR this should go into the IVD driver 
        Sets the sweep type, in the moment only simple sweep types are defined: 
        Input:
        sweep_type:
            0: single sweep START -> END 
            1: double sweep START -> END -> START (default)
            2: triple sweep START -> END -> START -> -END
            3: quad sweep   START -> END -> START -> -END -> START
            ...
        
        '''
        # define the number of datasets for each sweep type
        self._IV_sweep_types = { 0:1 , 1:2, 2:3, 3:4 }
        self._IV_sweep_type = sweep_type
        
        self._starts = [self._start, self._stop,  self._start, -self._stop][:self._IV_sweep_types[self._IV_sweep_type]]
        self._stops  = [self._stop,  self._start, -self._stop, self._start][:self._IV_sweep_types[self._IV_sweep_type]]
        self._steps  = [self._step, -self._step, -self._step, self._step][:self._IV_sweep_types[self._IV_sweep_type]]
    
    
    def set_defaults(self, channel=1):
        self._channel = 1
        self.set_mode_4W(val=True, channel=channel)
        self.set_bias_mode(mode='curr', channel=channel)
        self.set_sense_mode(mode='volt', channel=channel)
        self.set_bias_range(val=200e-3, channel=channel)
        self.set_sense_range(val=18, channel=channel)
        self.set_bias_trigger(mode='tim1', channel=channel)
        self.set_sense_trigger(mode='sour', channel=channel)
        self.set_bias_delay(val=15e-6, channel=channel)
        self.set_sense_delay(val=15e-6, channel=channel)
        self.set_bias_value(val=0, channel=channel)
        self._visainstrument.write('chan%i:sens:zero:auto 0' % channel)
        
        
    def get_all(self, channel=1):
        print('mode 4W = %r' % self.get_mode_4W(channel=channel))
        print('bias mode = %s' % self.get_bias_mode(channel=channel))
        print('sense mode = %s' % self.get_sense_mode(channel=channel))
        print('bias range = %f' % self.get_bias_range(channel=channel))
        print('sense range = %f' % self.get_sense_range(channel=channel))
        print('bias trigger = %s' % self.get_bias_trigger(channel=channel))
        print('sense trigger = %s' % self.get_sense_trigger(channel=channel))
        print('bias delay = %e' % self.get_bias_delay(channel=channel))
        print('sense delay = %e' % self.get_sense_delay(channel=channel))
        print('sense average = %i' % self.get_sense_average(channel=channel)[1])
        print('sense nplc = %i' % self.get_sense_nplc(channel=channel))
        print('plc = %f' % self.get_plc())
        print('get sense integration time = %f' % self.get_sense_integration_time(channel=channel))
        print('status = %r' % self.get_status(channel=channel))
        #print('bias value = %f' % self.get_bias_value(channel=channel))
        #print('sense value = %f' % self.get_sense_value(channel=channel))
        print('sweep start = %f' % self.get_sweep_start(channel=channel))
        print('sweep stop = %f' % self.get_sweep_stop(channel=channel))
        print('sweep step = %f' % self.get_sweep_step(channel=channel))
        print('sync = %r' % self.get_sync())
        print('error = %r' % self.get_error())
    
    
    def reset(self):
        '''
        Resets <self>
        
        Input:
            None
        Output:
            None
        '''
        try:
            self._visainstrument.write('*RST')
            logging.debug('Reset %s' % __name__)
        except AttributeError:
            logging.error('invalid input: cannot reset %s' % __name__)
    
    
    def get_error(self):
        '''
        Gets error of <self>
        
        Input:
            None
        Output:
            error (str)
        '''
        try:            
            return str(self._visainstrument.ask(':syst:err?'))
        except ValueError:
            logging.debug('Error not specified:')
    
    
    def clear_error(self):
        '''
        Clears error of <self>
        
        Input:
            None
        Output:
            None
        '''
        try:
            self._visainstrument.write('*CLS')
            logging.debug('Clear error of %s' % __name__)
        except AttributeError:
            logging.error('invalid input: cannot clear error of %s' % __name__)
    
    
    def get_bias_status_register(self):
        '''
        Gets the entire bias status register
        
        Input:
            None
        Output:
            status_register (bool):
                0:  CH1 End of Sweep
                1:  CH1 Ready for Sweep
                2:  CH1 Low Limiting
                3:  CH1 High Limiting
                4:  CH1 Tripped
                5:  CH1 Emergency (Temperature/Current over)
                6:  ---
                7:  ---
                8:  CH2 End of Sweep
                9:  CH2 Ready for Sweep
                10: CH2 Low Limiting
                11: CH2 High Limiting
                12: CH2 Tripped
                13: CH2 Emergency (Temperature/Current over)
                14: Inter Locking
                15: Start Sampling Error
        '''
        # <<Corresponding Command Mnemonic>>: :STATus:SOURce:CONDition?
        try:            
            bias_status_register = int(self._visainstrument.ask(':stat:sour:cond?'))
            ans = []
            for i in range(16):
                ans.append(2**i == (bias_status_register) & 2**i)
            return ans
        except ValueError:
            logging.debug('Bias status register not specified:')
    
    
    def is_end_of_sweep(self, channel=1):
        '''
        Gets event of bias status register entry "End for Sweep" of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            val (bool): True | False
        '''
        # <<Corresponding Command Mnemonic>>: :STATus:SOURce:EVENt?
        try:            
            return 2**(0+8*(channel-1)) == (int(self._visainstrument.ask(':stat:sour:even?'))) & 2**(0+8*(channel-1))
        except ValueError:
            logging.debug('Status register event "End of Sweep" of channel %i not specified:' % channel)
    
    
    def _wait_for_end_of_sweep(self, channel=1):
        '''
        Waits until the event of status register entry "End for Sweep" of channel <channel> occurs
        
        Input:
            None
        Output:
            None
        '''
        while not (self.is_end_of_sweep(channel=channel)):
            time.sleep(1e-6)
    
    
    def is_ready_for_sweep(self, channel=1):
        '''
        Gets condition of bias status register entry "Ready for Sweep" of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            val (bool): True | False
        '''
        # <<Corresponding Command Mnemonic>>: :STATus:SOURce:CONDition?
        try:            
            return 2**(1+8*(channel-1)) == (int(self._visainstrument.ask(':stat:sour:cond?'))) & 2**(1+8*(channel-1))
        except ValueError:
            logging.debug('Status register condition "Ready for Sweep" of channel %i not specified:' % channel)
    
    
    def _wait_for_ready_for_sweep(self, channel=1):
        '''
        Waits until the condition of status register entry "Ready for Sweep" of channel <channel> occurs
        
        Input:
            None
        Output:
            None
        '''
        while not (self.is_ready_for_sweep(channel=channel)):
            time.sleep(1e-6)
    
    
    def get_sense_status_register(self):
        '''
        Gets the entire sense status register
        
        Input:
            None
        Output:
            status_register (bool):
                0:  CH1 End of Measure
                1:  ---
                2:  CH1 Compare result is Low
                3:  CH1 Compare result is High
                4:  ---
                5:  CH1 Over Range
                6:  ---
                7:  ---
                8:  CH2 End of Measure
                9:  ---
                10: CH2 Compare result is Low
                11: CH2 Compare result is High
                12: ---
                13: CH2 Over Range
                14: End of Trace
                15: Trigger Sampling Error
        '''
        # <<Corresponding Command Mnemonic>>: :STATus:SENSe:CONDition?
        try:            
            sense_status_register = int(self._visainstrument.ask(':stat:sens:cond?'))
            ans = []
            for i in range(16):
                ans.append(2**i == (sense_status_register) & 2**i)
            return ans
        except ValueError:
            logging.debug('Sense status register not specified:')
    
    
    def is_end_of_measure(self, channel=1):
        '''
        Gets condition of sense status register entry "End of Measure" of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            val (bool): True | False
        '''
        # <<Corresponding Command Mnemonic>>: :STATus:SENSe:CONDition?
        try:            
            return 2**(0+8*(channel-1)) == (int(self._visainstrument.ask(':stat:sens:cond?'))) & 2**(0+8*(channel-1))
        except ValueError:
            logging.debug('Status register event "End of Measure" of channel %i not specified:' % channel)
    
    
    def _wait_for_end_of_measure(self, channel=1):
        '''
        Waits until the condition of sense register entry "End for Measure" of channel <channel> occurs
        
        Input:
            channel (int): 1 | 2
        Output:
            None
        '''
        while not (self.is_end_of_measure(channel=channel)):
            time.sleep(1e-6)
    
    