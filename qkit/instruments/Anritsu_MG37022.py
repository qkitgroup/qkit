# Anritsu_MG37022.py
# Pascal Macha <pascalmacha@googlemail.com>, 2010
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
import math
from time import sleep

class Anritsu_MG37022(Instrument):
    '''
    This is the python driver for the Anritsu_MG37022 microwave source

    Usage:
    Initialise with
    <name> = instruments.create('<name>', address='<GPIB address>',
        reset=<bool>)

    TODO:
    1. Everzthing
    '''

    def __init__(self, name,address, model = 'Anritsu'):
        '''
        Initializes the Anritsu_MG37022, and communicates with the wrapper.
        
        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address
        '''
        logging.info(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])

        self._address = address
        self._model = model
        self._visainstrument = visa.instrument(self._address)
        self._slope = None
        sleep(1)

        # Implement parameters
        self.add_parameter('frequency', type=types.FloatType,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=20e9,
            units='Hz',tags=['sweep'])
        self.add_parameter('slope', type=types.FloatType,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=100,
            units='dB@10GHz')
        self.add_parameter('power', type=types.FloatType,
            flags=Instrument.FLAG_GETSET,
            minval=-130, maxval=10,
            units='dBm', tags=['sweep'])
        self.add_parameter('status', type=types.BooleanType,
            flags=Instrument.FLAG_GETSET)
          
        # Implement functions
        self.add_function('get_all')

        self.get_all()
        
    # initialization related
    def get_all(self):
        self.get_frequency()
        self.get_power()
        self.get_status()

    #Communication with device
    def do_get_frequency(self):
        # sending value to instrument
        self._frequency = float(self._visainstrument.ask('SOUR:FREQ:CW?'))
        return self._frequency
    def do_set_frequency(self, frequency):
        '''
        Set frequency of device

        Input:
            freq (float) : Frequency in Hz

        Output:
            None
        '''
        #logging.debug(__name__ + ' : setting frequency to %s Hz' % (frequency*1.0e9))
        # sending value to instrument
        self._visainstrument.write('SOUR:FREQ:CW %i' % (int(frequency)))
        self._frequency = float(frequency)
        if(self._slope != None): 
            self.do_set_power()
    def do_get_slope(self):
        return self._slope
    def do_set_slope(self, slope):
        '''
        Set slope of output power to use at different frequencies.
        Assumes a cable attenuation of attn[dB] ~ attn(f0)*sqrt(f/f0), f0=10GHz

        Input:
            slope (float) : Slope to apply to power values.
        '''
        self._slope = slope
    def do_get_power(self):
        # sending value to instrument
        self._power = float(self._visainstrument.ask('POW:LEV?'))
        return self._power
    def do_set_power(self,power = None):
        '''
        Set output power of device

        Input:
            pow (float) : Power in dBm
            If a slope is set, this is the power at 10GHz.

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting power to %s dBm' % power)
        if(power == None):
            power = self._power
        else:
            self._power = power
        # compensate cables
        if(self._slope != None):
            power = power+self._slope*(math.sqrt(self._frequency/10.e9)-1)
        # sending value to instrument
        self._visainstrument.write('POW:LEV %.2f' % power)
            
    def do_get_status(self):
        stat = bool(int(self._visainstrument.ask('OUTP:STAT?')))
        return stat        
    def do_set_status(self,status):
        '''
        Set status of output channel

        Input:
            status : True or False

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting status to "%s"' % status)
        if status == True:
            self._visainstrument.write('OUTP:STAT ON')
        elif status == False:
            self._visainstrument.write('OUTP:STAT OFF')
        else:
            raise ValueError('set_status(): can only set True or False')

          
    # shortcuts
    def off(self):
        '''
        Set status to 'off'

        Input:
            None

        Output:
            None
        '''
        self.set_status(False)

    def on(self):
        '''
        Set status to 'on'

        Input:
            None

        Output:
            None
        '''
        self.set_status(True)
        
    def write(self,msg):
      return self._visainstrument.write(msg)    
    def ask(self,msg):
      return self._visainstrument.ask(msg)
