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
import types
import logging
import numpy
import struct
import time

class Yokogawa_GS820(Instrument):
#    '''
#    This is the driver for the Yokogawa GS820 multi channel source measure unit
#
#    Usage:
#    Initialize with
#    <name> = instruments.create('<name>', 'Yokogawa_GS820', address='<GBIP address>',
#        reset=<bool>)
#    '''
#
#    def __init__(self, name, address, reset=False):
#        '''
#        Initializes the Yokogawa GS820, and communicates with the wrapper.
#
#        Input:
#            name (string)    : name of the instrument
#            address (string) : GPIB address
#            reset (bool)     : resets to default values
#
#        Output:
#            None
#        '''
#        # Initialize wrapper functions
#        logging.info(__name__ + ' : Initializing instrument Yokogawa_GS820')
#        Instrument.__init__(self, name, tags=['physical'])
#
#        # Add some global constants
#        self._address = address
#        self._numchs = 2
#        self._visainstrument = visa.instrument(self._address)
#
#        # Add parameters to wrapper
#        self.add_parameter('source_range',
#            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
#            channels=(1, self._numchs), channel_prefix='ch%d_',
#            units='', type=types.StringType)
#        self.add_parameter('sense_range',
#            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
#            channels=(1, self._numchs), channel_prefix='ch%d_',
#            units='', type=types.StringType)
#        self.add_parameter('source_mode',
#            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
#            channels=(1, self._numchs), channel_prefix='ch%d_',
#            type=types.StringType, units='')
#        self.add_parameter('sense_mode',
#            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
#            channels=(1, self._numchs), channel_prefix='ch%d_',
#            type=types.StringType, units='')
#        self.add_parameter('source_trig',
#            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
#            channels=(1, self._numchs), channel_prefix='ch%d_',
#            type=types.StringType, units='')
#        self.add_parameter('sense_trig',
#            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
#            channels=(1, self._numchs), channel_prefix='ch%d_',
#            type=types.StringType, units='')
#        self.add_parameter('source_delay',
#            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
#            channels=(1, self._numchs), channel_prefix='ch%d_',
#            type=types.FloatType, minval=15e-6, maxval=3600, units='s')
#        self.add_parameter('sense_delay',
#            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
#            channels=(1, self._numchs), channel_prefix='ch%d_',
#            type=types.FloatType, minval=15e-6, maxval=3600, units='s')
#        self.add_parameter('sweep_mode',
#            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
#            channels=(1, self._numchs), channel_prefix='ch%d_',
#            type=types.StringType, units='')
#        self.add_parameter('4W',
#            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
#            channels=(1, self._numchs), channel_prefix='ch%d_',
#            type=types.StringType, units='')
#        self.add_parameter('level', 
#            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
#            channels=(1,self._numchs),channel_prefix='ch%d_',
#            type=types.FloatType, units='')
#        self.add_parameter('value', flags=Instrument.FLAG_GET,
#            channels=(1, self._numchs), channel_prefix='ch%d_',
#            type=types.FloatType, units='')
#        self.add_parameter('output',
#            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
#            channels=(1,self._numchs),channel_prefix='ch%d_',
#            type=types.StringType, units='')
#        self.add_parameter('sync',
#            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
#            type=types.StringType, units='')
#
#
#        # Add functions to wrapper
#        self.add_function('reset')
#        self.add_function('get_all')
#        self.add_function('set_range_auto')
#        self.add_function('set_defaults')
#        self.add_function('ramp_ch1_current')
#        self.add_function('ramp_ch2_current')
#
#
#        if reset:
#            self.reset()
#        else:
#            self.get_all()
#            self.set_defaults()
#
## functions
#    def reset(self):
#        '''
#        Resets instrument to default values
#
#        Input:
#            None
#    
#        Output:
#            None
#        '''
#        logging.debug(__name__ + ' : Resetting instrument')
#        self._visainstrument.write('*RST')
#        self.get_all()
#      
#    def get_all(self):
#        '''
#        Reads all relevant parameters from instrument
#
#        Input:
#            None
#
#        Output:
#            None
#        '''
#        logging.debug(__name__ + ' : Get all relevant data from device')
#        self.get_sync()
#        for ch in range(self._numchs):
#            self.get('ch%d_source_range' % (ch+1))
#            self.get('ch%d_sense_range' % (ch+1))
#            self.get('ch%d_source_mode' % (ch+1))
#            self.get('ch%d_sense_mode' % (ch+1))
#            self.get('ch%d_source_trig' % (ch+1))
#            self.get('ch%d_sense_trig' % (ch+1))
#            self.get('ch%d_source_delay' % (ch+1))
#            self.get('ch%d_sense_delay' % (ch+1))
#            self.get('ch%d_4W' % (ch+1))
#            self.get('ch%d_level' % (ch+1))
#            self.get('ch%d_output' % (ch+1))
#
#    def set_range_auto(self, channel):
#        '''
#        Switch autorange on.
#        '''
#        logging.debug('Set range to auto mode')
#        self._visainstrument.write(':chan%d:sens:rang:auto on' % channel)
#        
#    def set_defaults(self):
#        '''
#        Set to driver defaults:
#        Source range for channel 2 +-18 V
#        Source mode for channel 2 voltage mode
#        Source mode for channel 1 voltage mode
#        Source range for channel 1 +-200 mV
#        Sense mode for channel 1 voltage mode
#        Sensee range for channel 1 +-200 mV
#        Sourse trigger is set to external
#        Sense trigger is set connected to source
#        Source delay is set to 15 us
#        Sense delay is set to 300 ms
#        The measuring mode is set to 2-wire sense
#        '''
#        channel = 1
#        self.set('ch%d_4W' % channel, 'off')
#        self.set('ch%d_source_mode' % channel, 'volt')
#        self.set('ch%d_sense_mode' % channel, 'volt')
#        self.set('ch%d_source_range' % channel, '200mV')
#        self.set('ch%d_sense_range' % channel, '200mV')
#        self.set('ch%d_source_delay' % channel, 15e-6)
#        self.set('ch%d_sense_delay' % channel, 0.3)
#        self.set('ch%d_source_trig' % channel, 'ext')
#        self.set('ch%d_sense_trig' % channel, 'sour')
#        self._set_func_par_value(channel, 'sour', 'mode', 'sing')
#    
#        channel = 2
#        self.set('ch%d_4W' % channel, 'off')
#        self.set('ch%d_source_mode' % channel, 'volt')
#        self.set('ch%d_sense_mode' % channel, 'volt')
#        self.set('ch%d_source_range' % channel, '18V')
#        self.set('ch%d_sense_range' % channel, '18V')
#        self.set('ch%d_source_delay' % channel, 15e-6)
#        self.set('ch%d_sense_delay' % channel, 0.3)
#        self.set('ch%d_source_trig' % channel, 'ext')
#        self.set('ch%d_sense_trig' % channel, 'sour')
#        
# # parameters
# 
# 
#    def do_set_sync(self, val):
#        '''
#        Turns "on"/"off" the interchannel synchronization.
#        The first channel is always " The master", second - "the slave"
#        '''    
#        logging.debug('Sets the channels in synchronized regime')
#        if val in ['on','off']:
#            logging.debug('Set mode to %s' % val)
#            self._visainstrument.write(':sync:chan %s' % val)
#        else:
#            logging.error('Invalid value %s' % val)
#            
#    def do_get_sync(self):
#        '''
#        Gets synchronization mode.
#        '''
#        logging.debug('Gets synchronization mode')
#        ans = self._visainstrument.ask(':sync:chan?')
#        
#        if int(ans):
#            return 'on'
#        else:
#            return 'off'
#
#    def do_set_source_range(self, val, channel):
#        '''
#        sets source range to definite channel 
#         
#        Input:
#            val (string)  :
#            channel (int) : 
#
#        Output:
#
#        '''
#        logging.debug('Set source range to %s' % val)
#        self._set_func_par_value(channel, 'sour', 'rang', val)
#        
#        
#
#    def do_get_source_range(self, channel):
#        '''
#        Get source range 
#        '''
#        logging.debug('Get source range')
#        return self._get_func_par(channel, 'sour', 'rang')
#        
#        
#    def do_set_sense_range(self, val, channel):
#        '''
#        Set sense range to the specified channel
#
#        Input:
#            val (string)      : 
#            channel (int)     : 
#
#        Output:
#            None
#        '''
#        logging.debug('Set sense range to %s' % val)
#        if (val == 'auto'):
#            self.set_range_auto(channel)
#        else:
#            self._set_func_par_value(channel, 'sens', 'rang', val)
#
#    def do_get_sense_range(self, channel):
#        '''
#        Get sense range for the current mode.
#        
#        Input:
#            channel(int): 
#        Output:
#            range (string) : 
#        '''
#        logging.debug('Get sense range')
#        return self._get_func_par(channel, 'sens', 'rang')
#        
#    def do_set_source_mode(self, mode, channel):
#        '''
#        Set source mode to current regime.
#        '''    
#        if mode in ['curr','volt']:
#            logging.debug('Set mode to %s mode', mode)
#            self._set_func_par_value(channel, 'sour', 'func', mode)
#        else:
#            logging.error('invalid mode %s' % mode)
#        self.get_all()
#
#    def do_get_source_mode(self, channel):
#        '''
#        Get source mode 
#        
#        Input:
#            channel (int) : 
#        '''
#        logging.debug('Get source mode')
#        return self._get_func_par(channel, 'sour', 'func')
#        
#    def do_set_sweep_mode(self, mode, channel):
#        '''
#        Set source mode to current regime.
#        '''    
#        if mode in ['fix']:
#            logging.debug('Set mode to %s sweep mode', mode)
#            self._set_func_par_value(channel, 'sour', 'mode', mode)
#        else:
#            logging.error('invalid sweep mode %s' % mode)
#        self.get_all()
#
#    def do_get_sweep_mode(self, channel):
#        '''
#        Get source mode 
#        
#        Input:
#            channel (int) : 
#        '''
#        logging.debug('Get source sweep mode')
#        return self._get_func_par(channel, 'sour', 'mode')
#
#    def do_set_sense_mode(self, mode, channel):
#        '''
#        Set sense mode to current regime.
#        '''    
#        if mode in ['curr','volt']:
#            logging.debug('Set sense mode to %s mode', mode)
#            self._set_func_par_value(channel, 'sens', 'func', mode)
#        else:
#            logging.error('invalid mode %s' % mode)
#        self.get_all()
#        
#    def do_get_sense_mode(self, channel):
#        '''
#        Get sense mode for the current mode.
#        
#        Input:
#            channel (int) : 
#        '''
#        logging.debug('Get sense mode')
#        return self._get_func_par(channel, 'sens', 'func')
#        
#    def do_set_source_trig(self, trig, channel):
#        '''
#        Set source trigger.
#        '''    
#        if trig in ['ext','sens', 'aux']:
#            logging.debug('Set source trig to %s trigger', trig)
#            self._set_func_par_value(channel, 'sour', 'trig', trig)
#        else:
#            logging.error('invalid trig %s' % trig)
#        self.get_all()
#
#    def do_get_source_trig(self, channel):
#        '''
#        Get source trigger
#        '''
#        logging.debug('Get source trigger')
#        return self._get_func_par(channel, 'sour', 'trig')
#
#
#    def do_set_sense_trig(self, trig, channel):
#        '''
#        Set sense trigger.
#        '''    
#        if trig in ['ext','sour', 'aux']:
#            logging.debug('Set sense trig to %s trigger', trig)
#            self._set_func_par_value(channel, 'sens', 'trig', trig)
#        else:
#            logging.error('invalid trig %s' % trig)
#        self.get_all()
#
#    def do_get_sense_trig(self, channel):
#        '''
#        Get sense trigger
#        
#        '''
#        logging.debug('Get sense trigger')
#        return self._get_func_par(channel, 'sens', 'trig')
#        
#    def do_set_source_delay(self, val, channel):
#        '''
#        Set source delay
#        '''
#        logging.debug('Set source delay to %s' % val)
#        self._set_func_par_value(channel, 'sour', 'del', val)
#
#    def do_get_source_delay(self, channel):
#        '''
#        Get source delay
#        '''
#        logging.debug('Get source delay')
#        return float(self._get_func_par(channel, 'sour','del'))
#        
#    def do_set_sense_delay(self, val, channel):
#        '''
#        Set sense delay
#        '''
#        logging.debug('Set sense delay to %s' % val)
#        self._set_func_par_value(channel, 'sens', 'del', val)
#
#
#    def do_get_sense_delay(self, channel):
#        '''
#        Get sense delay
#        '''
#        logging.debug('Get sense delay')
#        return float(self._get_func_par(channel, 'sens','del'))
#        
#    def do_set_4W(self, val, channel):
#        '''
#        Sets measurement mode to 4-wire or 2-wire mode.
#        Value should be on or off. 
#        "On" devotes to 4-wire mode. "Off" devotes to 2-wire mode.
#        In the instrument appropriate command is ":sens:rem on/off"
#        '''
#        if val in ['on','off']:
#            logging.debug('Set 4W to %s' % val)
#            self._set_func_par_value(channel, 'sens', 'rem', val)
#        else:
#            logging.error('Invalid value %s' % val)
#
#    def do_get_4W(self, channel):
#        '''
#        Gets measurement mode
#        '''
#        logging.debug('Get 4-wire measurement mode')
#        ans = self._get_func_par(channel, 'sens', 'rem')
#        
#        if int(ans):
#            return 'on'
#        else:
#            return 'off'
#        
#    def do_set_level(self, val, channel):
#        '''
#        Set measuring level
#        '''
#        logging.debug('Set measuring level')
#        if self.get('ch%d_output' % channel, query = False) == 'off':
#            self.set('ch%d_output' % channel, 'on')
#        self._set_func_par_value(channel, 'sour', 'lev', val)
#        self._visainstrument.write(':chan%d:init' % channel)
#        self._visainstrument.write(':trig')
#        
#    def do_get_level(self, channel):
#        '''
#        Gets source output level
#        '''
#        logging.debug('Get measuring level')
#        return float(self._get_func_par(channel, 'sour','lev'))
#        
#    def do_set_output(self, val, channel):
#        '''
#        Sets outputs of channels in "on" or "off" position.
#        
#        '''
#        if val in ['on','off']:
#            logging.debug('Set output to %s' % val)
#            self._set_func_par_value(channel, 'outp', 'stat', val)
#            if (self.get_sync() == 'on')  and (channel == 1):
#                self.set_ch2_output(self.get_ch2_output(query = False))
#                
#        else:
#            logging.error('Invalid value %s' % val)
#            
#    def do_get_output(self, channel):
#        '''
#        Gets output state
#        '''
#        logging.debug('Get status of output')
#        ans=self._get_func_par(channel, 'outp','stat')
#        if ans=='zero':
#            return 'off'
#        if int(ans):
#            return 'on'
#        else:
#            return 'off'
#        
#    def do_get_value(self, channel):
#        '''
#        Gets measured value
#        '''
#        logging.debug('Get measured value')
#        return float(self._visainstrument.ask(':chan%d:fetc?' % channel))
#
#
#
#
#  # core communication
#    def _set_func_par_value(self, ch, func, par, val):
#        '''
#        For internal use only!!
#        Changes the value of the parameter for the function specified
#
#        Input:
#            ch (int)
#            func (string) :
#            par (string)  :
#            val (depends) :
#
#        Output:
#            None
#        '''
#        string = ':chan%d:%s:%s %s' %(ch, func, par, val)
#        logging.debug(__name__ + ' : Set instrument to %s' % string)
#        self._visainstrument.write(string)
#
#    def _get_func_par(self, ch, func, par):
#        '''
#        For internal use only!!
#        Reads the value of the parameter for the function specified
#        from the instrument
#
#        Input:
#            ch (int)      :
#            func (string) :
#            par (string)  :
#
#        Output:
#            val (string) :
#        '''
#        string = ':chan%d:%s:%s?' %(ch, func, par)
#        ans = self._visainstrument.ask(string)
#        logging.debug(__name__ + ' : ask instrument for %s (result %s)' % \
#            (string, ans))
#        return ans.lower()
#
#    def ramp_ch1_current(self,target, step, wait=0.1, showvalue=True):
#        start = self.get_ch1_level()
#        if(target < start): step = -step
#        a = numpy.concatenate( (numpy.arange(start, target, step)[1:], [target]) )
#        for i in a:
#            if showvalue==True: print i,
#            self.set_ch1_level(i)
#            time.sleep(wait)
#
#
#    def ramp_ch2_current(self,target, step, wait=0.1, showvalue=True):
#        start = self.get_ch2_level()
#        if(target < start): step = -step
#        a = numpy.concatenate( (numpy.arange(start, target, step)[1:], [target]) )
#        for i in a:
#            if showvalue==True: print i,
#            self.set_ch2_level(i)
#            time.sleep(wait)



    '''
    This is the driver for the Yokogawa GS820 Multi Channel Source Measure Unit


    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Yokogawa_GS820', address='<GBIP address>, reset=<bool>')
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
        
        self.add_function('set_mode_4W')
        self.add_function('get_mode_4W')
        self.add_function('set_source_mode')
        self.add_function('get_source_mode')
        self.add_function('set_sense_mode')
        self.add_function('get_sense_mode')
        self.add_function('set_source_range')
        self.add_function('get_source_range')
        self.add_function('set_sense_range')
        self.add_function('get_sense_range')
        self.add_function('set_sync')
        self.add_function('get_sync')
        self.add_function('set_source_trigger')
        self.add_function('get_source_trigger')
        self.add_function('set_sense_trigger')
        self.add_function('get_sense_trigger')
        self.add_function('set_source_delay')
        self.add_function('get_source_delay')
        self.add_function('set_sense_delay')
        self.add_function('get_sense_delay')
        
        
        self.add_function('set_status')
        self.add_function('get_status')
        
        self.add_function('set_source_value')
        self.add_function('get_source_value')
        self.add_function('get_sense_value')
        self.add_function('set_voltage')
        self.add_function('get_voltage')
        self.add_function('set_current')
        self.add_function('get_current')
        self.add_function('sweep_source')
        
        self.add_function('set_defaults')
        self.add_function('get_all')
        self.add_function('reset')
        
        
        
        
        
    def set_source_mode(self, mode, channel=1):
        '''
        Set source mode of channel <channel> to <mode> regime.
        
        Input:
            mode (str): 'volt' | 'curr'
            channel (int): 1 | 2
        Output:
            None
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce:FUNCtion VOLTage|CURRent
        try:
            logging.debug('Set source mode of channel %s to %s' % (channel, mode))
            self._visainstrument.write(':chan%i:sour:func %s' % (channel, mode))
        except AttributeError:
            logging.error('invalid input: cannot set source mode of channel %s to %s' % (channel, mode))
        
        
    def get_source_mode(self, channel=1):
        '''
        Get source mode <output> of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            mode (str): 'volt' | 'curr'
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce:FUNCtion VOLTage|CURRent
        try:
            return str(self._visainstrument.ask(':chan%i:sour:func?' % channel).lower())
        except ValueError:
            logging.debug('Source mode of channel %i not specified:' % channel)
        
        
    def set_sense_mode(self, mode, channel=1):
        '''
        Set sense mode of channel <channel> to <mode> regime.
        
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
        Get sense mode <output> of channel <channel>
        
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
        
        
    def set_source_range(self, val, channel=1):
        '''
        Set source range of channel <channel> to <val>
        
        Input:
            val (float): 200mV | 2V | 20V | 50V | 200nA | 2uA | 20uA | 200uA | 2mA | 20mA | 200mA | 1 A | 3A
            channel (int): 1 | 2
        Output:
            None
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce[:VOLTage]:RANGe <voltage>|MINimum|MAXimum|UP|DOWN 
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce[:CURRent]:RANGe <current>|MINimum|MAXimum|UP|DOWN 
        try:
            logging.debug('Set source voltage range of channel %s to %s' % (channel, val))
            if (val == 'auto'):
                self.set_range_auto(channel)
            else:
                self._visainstrument.write(':chan%i:sour:rang %s' % (channel, val))
        except AttributeError:
            logging.error('invalid input: cannot set source range of channel %s to %s' % (channel, val))
        
        
    def get_source_range(self, channel=1):
        '''
        Get source range for the current mode.
        
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
            logging.debug('Source range of channel %i not specified:' % channel)
        
        
    def set_sense_range(self, val, channel=1):
        '''
        Set sense range of channel <channel> to <val>
        
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
                self._visainstrument.write(':chan%d:sens:rang:auto on' % channel)
            else:
                self._visainstrument.write(':chan%i:sens:rang %f' % (channel, val))
        except AttributeError:
            logging.error('invalid input: cannot set sense range of channel %s to %f' % (channel, val))
        
        
    def get_sense_range(self, channel=1):
        '''
        Get sense range for the current mode.
        
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
        
        
    def set_mode_4W(self, val, channel=1):
        '''
        Set wiring system of channel <channel> to <val>
        
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
        Get wiring system of channel <channel>
        
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
        
        
    def set_source_value(self, val, channel=1):
        '''
        Set source value of channel <channel> to value >val>
        
        Input:
            val (float): arb.
            channel (int): 1 | 2
        Output:
            None
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce[:VOLTage]:LEVel <voltage>|MINimum|MAXimum
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce[:CURRent]:LEVel <current>|MINimum|MAXimum
        try:
            logging.debug(__name__ + ' : set source value of channel %s to %s' % (channel, str(val)))
            self._visainstrument.write(':chan%s:sour:lev %f' % (channel, val))
        except AttributeError:
            logging.error('invalid input: cannot set source value of channel %s to %f' % (channel, val))
        
        
    def get_source_value(self, channel=1):
        '''
        Get source value of channel <channel>
        
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
            logging.error('Cannot get source value of channel %i:' % channel)
        
        
    def get_sense_value(self, channel=1):
        '''
        Get sense value of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            val (float)
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:FETCh?
        try:
            return float(self._visainstrument.ask(':chan%d:fetc?' % channel))
        except ValueError:
            logging.error('Cannot get sense value of channel %i:' % channel)
        
        
    def set_voltage(self, val, channel=1):
        '''
        Set voltage value of channel <channel> to <val>
        
        Input:
            val (float): arb.
            channel (int): 1 | 2
        Output:
            None
        '''
        if self.get_source_mode(channel) == 'volt':
            return self.set_source_value(val, channel)
        elif self.get_source_mode(channel) == 'curr':
            logging.error('Cannot set set voltage value of channel %i: in the current bias' % channel)
        
        
    def get_voltage(self, channel=1):
        '''
        Get voltage value of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            val (float)
        '''
        if self.get_source_mode(channel) == 'volt':
            return self.get_source_value(channel)
        elif self.get_sense_mode(channel) == 'volt':
            return self.get_sense_value(channel)
        
        
    def set_current(self, val, channel=1):
        '''
        Set current value of channel <channel> to <val>
        
        Input:
            val (float): arb.
            channel (int): 1 | 2
        Output:
            None
        '''
        if self.get_source_mode(channel) == 'curr':
            return self.set_source_value(val, channel)
        elif self.get_source_mode(channel) == 'volt':
            logging.error('Cannot set set current value of channel %i: in the voltage bias' % channel)
        
        
    def get_current(self, channel=1):
        '''
        Get current value of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            val (float)
        '''
        if self.get_source_mode(channel) == 'curr':
            return self.get_source_value(channel)
        elif self.get_sense_mode(channel) == 'curr':
            return self.get_sense_value(channel)
        
        
    def set_sync(self, val):
        '''
        Set the interchannel synchronization to <val>
        Start | Stop the interchannel synchronization
        The first channel is always the "master", the second the "slave"
        
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
        
        
    def set_source_trigger(self, trigger, channel=1):
        '''
        Set source trigger of channel <channel> to <trigger>
        
        Input:
            trigger (str): ext (external) | aux (auxiliary) | tim1 (timer1) | tim2 (timer2) | sens (sense)
            channel (int): 1 | 2
        Output:
            None
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce:TRIGger EXTernal|AUXiliary|TIMer1|TIMer2|SENSe
        try:
            logging.debug('Set source trigger of channel %s to %s' % (channel, trigger))
            self._visainstrument.write(':chan%i:sour:trig %s' % (channel, trigger))
        except AttributeError:
            logging.error('invalid input: cannot set source trigger of channel %s to %s' % (channel, trigger))
        
        
    def get_source_trigger(self, channel=1):
        '''
        Get source trigger <output> of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            trigger (str): ext (external) | aux (auxiliary) | tim1 (timer1) | tim2 (timer2) | sens (sense)
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce:TRIGger EXTernal|AUXiliary|TIMer1|TIMer2|SENSe
        try:
            return str(self._visainstrument.ask(':chan%i:sour:trig?' % channel).lower())
        except ValueError:
            logging.debug('Source trigger of channel %i not specified:' % channel)
        
        
    def set_sense_trigger(self, trigger, channel=1):
        '''
        Set sense trigger of channel <channel> to <trigger>
        
        Input:
            trigger (str): ext (external) | aux (auxiliary) | tim1 (timer1) | tim2 (timer2) | sens (sense)
            channel (int): 1 | 2
        Output:
            None
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SENSe:TRIGger EXTernal|AUXiliary|TIMer1|TIMer2|SENSe
        try:
            logging.debug('Set sense trigger of channel %s to %s' % (channel, trigger))
            self._visainstrument.write(':chan%i:sens:trig %s' % (channel, trigger))
        except AttributeError:
            logging.error('invalid input: cannot set sense trigger of channel %s to %s' % (channel, trigger))
        
        
    def get_sense_trigger(self, channel=1):
        '''
        Get sense trigger <output> of channel <channel>
        
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
        
        
    def set_source_delay(self, val, channel=1):
        '''
        Set source dely of channel <channel> to <val>
        
        Input:
            delay (float): 15us <= delay <= 3600s
            channel (int): 1 | 2
        Output:
            None
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce:DELay <time>|MINimum|MAXimum
        try:
            logging.debug('Set source delay of channel %s to %s' % (channel, val))
            self._visainstrument.write(':chan%i:sour:del %s' % (channel, val))
        except AttributeError:
            logging.error('invalid input: cannot set source delay of channel %s to %s' % (channel, delay))
        
        
    def get_source_delay(self, channel=1):
        '''
        Get source delay <output> of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            delay (float):
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce:DELay <time>|MINimum|MAXimum
        try:
            return float(self._visainstrument.ask(':chan%i:sour:del?' % channel))
        except ValueError:
            logging.debug('Source delay of channel %i not specified:' % channel)
        
        
    def set_sense_delay(self, val, channel=1):
        '''
        Set sense delay of channel <channel> to <val>
        
        Input:
            delay (float): 15us <= delay <= 3600s
            channel (int): 1 | 2
        Output:
            None
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:SOURce:DELay <time>|MINimum|MAXimum
        try:
            logging.debug('Set sense delay of channel %s to %s' % (channel, val))
            self._visainstrument.write(':chan%i:sens:del %s' % (channel, val))
        except AttributeError:
            logging.error('invalid input: cannot set sense delay of channel %s to %s' % (channel, delay))
        
        
    def get_sense_delay(self, channel=1):
        '''
        Get sense delay <output> of channel <channel>
        
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
        
        
    def set_status(self, status, channel=1):
        '''
        Set output status of channel <channel> to <status>
        
        Input:
            status (bool): True (ON) | False (OFF)
            channel (int): 1 | 2
        Output:
            None
        '''
        # <<Corresponding Command Mnemonic>>: [:CHANnel<n>]:OUTput:STATus 1|0|ON|OFF
        try:
            print('need to start trigger seperately??')
            logging.debug('Set output status of channel %s to %r' % (channel, status))
            self._visainstrument.write(':chan%i:outp:stat %i' % (channel, status))
        except AttributeError:
            logging.error('invalid input: cannot set output status of channel %s to %r' % (channel, status))
        
        
    def get_status(self, channel=1):
        '''
        Get output status of channel <channel>
        
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
        
        
    def set_defaults(self, channel=1):
        self._channel = 1
        self.set_mode_4W(val=True, channel=channel)
        self.set_source_mode(mode='curr', channel=channel)
        self.set_sense_mode(mode='volt', channel=channel)
        self.set_source_range(val=20e-6, channel=channel)
        self.set_sense_range(val=200e-3, channel=channel)
        self.set_source_trigger(trigger='tim1', channel=channel)
        self.set_sense_trigger(trigger='tim1', channel=channel)
        self.set_source_delay(val=15e-6, channel=channel)
        self.set_sense_delay(val=15e-6, channel=channel)
        self.set_source_value(val=0, channel=channel)
        
        
    def get_all(self, channel=1):
        print('mode 4W = %r' % self.get_mode_4W(channel=channel))
        print('source mode = %s' % self.get_source_mode(channel=channel))
        print('sense mode = %s' % self.get_sense_mode(channel=channel))
        print('source range = %f' % self.get_source_range(channel=channel))
        print('sense range = %f' % self.get_sense_range(channel=channel))
        print('source trigger = %s' % self.get_source_trigger(channel=channel))
        print('sense trigger = %s' % self.get_sense_trigger(channel=channel))
        print('source delay = %f' % self.get_source_delay(channel=channel))
        print('sense delay = %f' % self.get_sense_delay(channel=channel))
        print('sync = %r' % self.get_sync())
       
       
    def reset(self, channel=1):
        try:
            self._visainstrument.write('*RST')
            logging.debug('Reset channel %s' % channel)
        except AttributeError:
            logging.error('invalid input: cannot reset channel %s' % channel)
        
        
    def sweep_source(self, start, stop, step, points, spacing = 'lin', channel=1):
        print('need to do: sweep_source')
        self._visainstrument.write(':chan%s:sour:%s:swe:spac %s' % (channel, self.get_source_mode(channel), spacing))
        self._visainstrument.write(':chan%s:sour:%s:swe:star %f' % (channel, self.get_source_mode(channel), start))
        self._visainstrument.write(':chan%s:sour:%s:swe:stop %f' % (channel, self.get_source_mode(channel), stop))
        self._visainstrument.write(':chan%s:sour:%s:swe:step %f' % (channel, self.get_source_mode(channel), step))
        self._visainstrument.write(':chan%s:sour:%s:swe:poin %f' % (channel, self.get_source_mode(channel), points))
        self._visainstrument.write(':star')
        
        
        
        
        
