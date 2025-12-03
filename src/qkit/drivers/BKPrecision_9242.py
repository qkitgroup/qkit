# BKPrecision_9242.py driver for BK Precision 9242  DC voltag/current source
# adapted from Yokogawa GS200 driver, Sergei Masis @KIT 06/2025
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

class BKPrecision_9242(Instrument):
    '''
    This is the driver for the BK Precision 9242  DC voltage/current source

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'BKPrecision_9242', address='<GBIP address>',
        reset=<bool>)
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the BK Precision 9242, and communicates with the wrapper.

        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address
            reset (bool)     : resets to default values

        Output:
            None
        '''
        # Initialize wrapper functions
        logging.info(__name__ + ' : Initializing instrument BK Precision 9242')
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

#        self.add_parameter('source_mode',
#            flags=Instrument.FLAG_GETSET,
#            type=str, units='')

        self.add_parameter('current_protection',
            flags=Instrument.FLAG_GETSET ,
            units='', type=str)
           
        self.add_parameter('output',
            flags=Instrument.FLAG_GETSET ,
            units='', type=str)
        
        self.add_parameter('current', 
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
            #self.set_defaults()

# functions
    def __del__(self):
        self.close_connection()
        print("Session closed.")
        
    def close_connection(self):
        """
        Closes the VISA-instrument to disconnect the instrument.

        Parameters
        ----------
                None

        Returns
        -------
                None
        """
        try:
            logging.info(
                __name__
                + " : Closing connection to QDAC-II server {:s}".format(self._address)
            )
            self._visainstrument.close()
        except Exception as e:
            logging.error("{!s}: Cannot close VISA-instrument".format(__name__))
            raise type(e)(
                "{!s}: Cannot close VISA-instrument\n{!s}".format(__name__, e)
            )
        return
            
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
    
       
    def set_defaults(self):
        
        '''
        Set to driver defaults:
            
            TODO

        '''
        
#        self._write(':syst:beep 0')
#        self.set_source_mode('curr')
#        self.set('current_protection', '10e-3')
        
        
#        self.set('4W', 'off')

#        self.set('sense_mode', 'volt')
#        self.set('sense_range', '200mV')
#        self.set('source_delay', 15e-6)
#        self.set('sense_delay', 0.3)
#        self.set('source_trig', 'ext')
#        self.set('sense_trig', 'sour')
    

#        
# # parameters

    def do_set_current_protection(self, val):
        '''
        sets current protection
         
        Input:
            val (string)  :
        
        Output:
        
        '''
        logging.debug('Set current protection to %s' % val)
        self._set_func_par_value('curr', 'prot', val)
       
       

    def do_get_current_protection(self):
        '''
        Get current protection
        '''
        logging.debug('Get current protection')
        return self._get_func_par('curr', 'prot')

    def do_set_voltage_protection(self, val):
        '''
        sets voltage protection
         
        Input:
            val (string)  :
               
        Output:
        
        '''
        logging.debug('Set voltage protection to %s' % val)
        self._set_func_par_value('volt', 'prot', val)
       
       

    def do_get_voltage_protection(self):
        '''
        Get voltage protection
        '''
        logging.debug('Get voltage protection')
        return self._get_func_par('volt', 'prot')


    def do_set_current(self, val):
        '''
        Set current 
        '''
        logging.debug('Set current')   
        self._write(':curr %s' % val)
        
    def do_get_current(self):
        '''
        Get current
        '''
        logging.debug('Get current')
        return self._ask(':curr?')

    def do_set_voltage(self, val):
        '''
        Set voltage
        '''
        logging.debug('Set voltage')   
        self._write(':volt %s' % val)
        
    def do_get_voltage(self):
        '''
        Get current
        '''
        logging.debug('Get voltage')
        return self._ask(':volt?')
                

    def ramp_current(self,target, step, wait=0.1, showvalue=False):
        
        '''
        Ramps the current starting from the actual value to a target value
        Attention: all values are given in A
        'step' determines the step size
        'wait' determines the sleep time after every step
        'showvalue' print current value - default is False
        '''
        
        start = self.get_current()
        if showvalue==True: print("{:g}mA".format(round(start*1e3, 3)))
        
        if(target < start): step = -step
        a = numpy.concatenate( (numpy.arange(start, target, step)[1:], [target]) )
        for i in a:
            if showvalue==True: print("{:g}mA".format(round(i*1e3, 3)), end=" ")
            self.set_current(i)
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
