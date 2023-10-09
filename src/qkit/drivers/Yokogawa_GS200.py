# Yokogawa_GS200.py driver for Yokogawa GS200 DC voltag/current source
# adapted from GS820 driver, Lukas Gruenhaupt @KIT 07/2017
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

from qkit.core.instrument_base import Instrument
from qkit import visa
import logging
import numpy
import struct
import time
from distutils.version import LooseVersion

class Yokogawa_GS200(Instrument):
    '''
    This is the driver for the Yokogawa GS200 multi channel source measure unit

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Yokogawa_GS200', address='<GBIP address>',
        reset=<bool>)
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the Yokogawa GS200, and communicates with the wrapper.

        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address
            reset (bool)     : resets to default values

        Output:
            None
        '''
        # Initialize wrapper functions
        logging.info(__name__ + ' : Initializing instrument Yokogawa_GS200')
        Instrument.__init__(self, name, tags=['physical'])

        # Add some global constants
        self._address = address
        self._visainstrument = visa.instrument(self._address)
        
        # Set termination characters (nessecarry for Ethernet communication)
        if  LooseVersion(visa.__version__) < LooseVersion("1.5.0"):            # pyvisa 1.4
            self._visainstrument.term_chars = ''
        else:                                                                  # pyvisa 1.8
            self._visainstrument.read_termination  = ''
            self._visainstrument.write_termination = ''

        # Add parameters to wrapper

#        self.add_parameter('source_function',
#            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
#            type=str, units='')

#        
#        self.add_parameter('operation_mode',
#            flags=Instrument.FLAG_SET,
#            type=str, units='')

        self.add_parameter('source_mode',
            flags=Instrument.FLAG_GETSET,
            type=str, units='')

        self.add_parameter('source_range',
            flags=Instrument.FLAG_GETSET ,
            units='', type=str)
           
        self.add_parameter('output',
            flags=Instrument.FLAG_GETSET ,
            units='', type=str)
        
        self.add_parameter('level', 
            flags=Instrument.FLAG_GETSET,
            type=float, units='')

#        self.add_parameter('voltage_protection', 
#            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
#            type=float, units='V')
#
#        self.add_parameter('current_protection', 
#            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
#            type=float, units='A')
#            
#        self.add_parameter('4W',
#            flags=Instrument.FLAG_GETSET ,
#            units='', type=str)
#
#        self.add_parameter('ramp_wait_time', 
#            flags=Instrument.FLAG_GET,
#            type=float, units = 's')

        # Add functions to wrapper
        
        self.add_function('reset')
        self.add_function('get_all')
        #self.add_function('set_range_auto')
        self.add_function('set_defaults')
        self.add_function('ramp_current')
        #self.add_function('ramp_ch2_current')

        
        if reset:
            self.reset()
        else:
            self.get_all()
            self.set_defaults()

# functions
            
    def reset(self):     
        '''
        Resets instrument to default values

        Input:
            None
    
        Output:
            None
        '''
        logging.debug(__name__ + ' : Resetting instrument')
        self._write('*RST')
        self.get_all()
      
    def get_all(self):
        '''
        Reads all relevant parameters from instrument

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Get all relevant data from device')
        
        #self._ask(':outp?')
        
        
        #self.get_sync()
        #self.get('source_function')
        
        #self.get_sync()
        


#        self.get('sense_range')
#        self.get('sense_mode')
#        self.get('source_trig')
#        self.get('sense_trig')
#        self.get('source_delay')
#        self.get('sense_delay')
#        self.get('4W')
        #self.get('level')
#        self.get('output')
           
    def do_get_output(self):
        '''
        Gets output state
        '''
        logging.debug('Get status of output')
        ans = self._ask(':outp?')
        
        if ans=='zero':    # TODO what is this
            return 'off'
        
        if int(ans):
            print('Attention: Output is set on; Be careful!')      #warning if output is on! No fast current changes if coil is attached
            return 'on'
        else:
            return 'off'
        
    def do_set_output(self, val):
        '''
        Sets outputs of channels in "on" or "off" position.
        
        '''
        if val in ['on','off']:
            logging.debug('Set output to %s' % val)
            self._write(':outp:stat %s' % val)
        else:
            logging.error('Invalid value %s' % val)
    
    def do_get_source_mode(self):
        
        logging.debug('Get source function mode')
        return self._ask(':sour:func?')
        
    def do_set_source_mode(self, mode):
        
        logging.debug('Set source function mode to CURR or VOLT')
        
        if mode in ['curr','volt']:
            
            logging.debug('Set mode to %s mode' % mode)
            self._write(':sour:func %s' % mode)
            
        else:
            logging.error('Invalid mode %s' % mode)
    
            
    
#    
#    def set_range_auto(self, channel):
#        '''
#        Switch autorange on.
#        '''
#        logging.debug('Set range to auto mode')
#        self._visainstrument.write(':chan%d:sens:rang:auto on' % channel)
#        
    def set_defaults(self):
        
        '''
        Set to driver defaults:
            
            TODO

        '''
        
        self._write(':syst:beep 0')
        self.set_source_mode('curr')
        self.set('source_range', '10e-3')
        
        
#        self.set('4W', 'off')

#        self.set('sense_mode', 'volt')
#        self.set('sense_range', '200mV')
#        self.set('source_delay', 15e-6)
#        self.set('sense_delay', 0.3)
#        self.set('source_trig', 'ext')
#        self.set('sense_trig', 'sour')
    

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
    def do_set_source_range(self, val):
        '''
        sets source range to definite channel 
         
        Input:
            val (string)  :
            channel (int) : 
        
        Output:
        
        '''
        logging.debug('Set source range to %s' % val)
        self._set_func_par_value('sour', 'rang', val)
       
       

    def do_get_source_range(self):
        '''
        Get source range 
        '''
        logging.debug('Get source range')
        return self._get_func_par('sour', 'rang')
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
#
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
    def do_set_level(self, val):
        '''
        Set measuring level
        '''
        logging.debug('Set measuring level')
        #if self.get('ch%d_output' % channel, query = False) == 'off':
        #    self.set('ch%d_output' % channel, 'on')
        
        self._write(':sour:lev %s' % val)
        
    def do_get_level(self):
        '''
        Get measuring level
        '''
        logging.debug('Get measuring level')
        return self._ask(':sour:lev?')
        
#
#    def do_get_value(self, channel):
#        '''
#        Gets measured value
#        '''
#        logging.debug('Get measured value')
#        return float(self._visainstrument.ask(':chan%d:fetc?' % channel))
#
#
    def ramp_current(self,target, step, wait=0.1, showvalue=False):
        
        '''
        Ramps the current starting from the actual value to a target value
        Attention: all values are given in A
        'step' determines the step size
        'wait' determines the sleep time after every step
        'showvalue' print current value - default is False
        '''
        
        start = self.get_level()
        if showvalue==True: print("{:g}mA".format(round(start*1e3, 3)))
        
        if(target < start): step = -step
        a = numpy.concatenate( (numpy.arange(start, target, step)[1:], [target]) )
        for i in a:
            if showvalue==True: print("{:g}mA".format(round(i*1e3, 3)), end=" ")
            self.set_level(i)
            time.sleep(wait)
            
# core communication
  
    def _write(self, msg):
        
        '''
        Sends a visa command <msg>
        
        Input:
            msg (str)
        Output:
            None
        '''
        return self._visainstrument.write(msg)
    
    
    def _ask(self, msg):
        '''
        Sends a visa command <msg> and returns the read answer <ans>
        
        Input:
            msg (str)
        Output:
            ans (str)
        '''
        return self._visainstrument.query(msg).rstrip()
        
        
        
    def _set_func_par_value(self, func, par, val):
        '''
        For internal use only!!
        Changes the value of the parameter for the function specified
        
        Input:
            ch (int)
            func (string) :
            par (string)  :
            val (depends) :
        
        Output:
            None
        '''
        string = ':%s:%s %s' %(func, par, val)
        logging.debug(__name__ + ' : Set instrument to %s' % string)
        self._visainstrument.write(string)
       
       

    def _get_func_par(self, func, par):
        '''
        For internal use only!!
        Reads the value of the parameter for the function specified
        from the instrument
        
        Input:
            ch (int)      :
            func (string) :
            par (string)  :
        
        Output:
            val (string) :
        '''
        string = ':%s:%s?' %(func, par)
        ans = self._visainstrument.query(string)
        logging.debug(__name__ + ' : ask instrument for %s (result %s)' % \
            (string, ans))
        return ans.lower()
