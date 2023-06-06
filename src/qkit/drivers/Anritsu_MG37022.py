# qtLAB driver for microwave sources Anritsu MG37022, Anritsu MG3692C (*)
# filename: Anritsu_MG37022.py
# Pascal Macha <pascalmacha@googlemail.com>, 2010
# Jochen Braumueller <jochen.braumueller@kit.edu> 2016

# (*) phase offset functions not supported by Anritsu MG3692C

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

import qkit
from qkit.core.instrument_base import Instrument
from qkit import visa
import types
import logging
import math
from time import sleep

class Anritsu_MG37022(Instrument):
    '''
    This is the python driver for the Anritsu_MG37022 microwave source

    Usage:
    Initialise with
    <name> = instruments.create('<name>', address='<GPIB address>')
    '''

    def __init__(self, name, address, model = 'Anritsu'):
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
        self._slope = None   #set _slope to True if frequency dependent power compensation is requested
        sleep(1)

        # Implement parameters
        self.add_parameter('frequency', type=float,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=20e9,
            units='Hz',tags=['sweep'])
        self.add_parameter('phase_offset', type=float,
            flags=Instrument.FLAG_GETSET,
            minval=-360, maxval=360,
            units='deg')
        self.add_parameter('slope', type=float,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=100,
            units='dB@10GHz')
        self.add_parameter('power', type=float,
            flags=Instrument.FLAG_GETSET,
            minval=-130, maxval=29,   #29dBm possible, this is security JB
            units='dBm', tags=['sweep'])
        self.add_parameter('status', type=bool,
            flags=Instrument.FLAG_GETSET)
        self.add_parameter('high_power', type=bool,
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
        '''
        Get frequency of device

        Input:
            -

        Output:
            microwave frequency (Hz)
        '''
        self._frequency = float(self.ask('SOUR:FREQ:CW?'))
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
        self.write('SOUR:FREQ:CW %i' % (int(frequency)))
        self._frequency = float(frequency)
        if(self._slope != None): 
            self.do_set_power()
            
    def do_get_slope(self):
        '''
        Get attribute '_slope'

        Input:
            -

        Output:
            slope applied to calculate power values
            None if no slope is set
        '''
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
        '''
        Get output power of device

        Input:
            -

        Output:
            microwave power (dBm)
        '''
        self._power = float(self.ask('POW:LEV?'))
        return self._power
        
    def do_set_power(self,power = None):
        '''
        Set output power of device, limited to +12dBm
        upper bound can be increased by setting self.enable_high_power to True

        Input:
            power (float) : Power in dBm
            If a slope is set, this is the power at 10GHz.

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting power to %s dBm' % power)
        if(power == None): #This block is needed for the slope function.
            power = self._power
        else:
            self._power = power
        # compensate cables
        if(self._slope != None):
            power = power+self._slope*(math.sqrt(self._frequency/10.e9)-1)
        self.write('POW:LEV %.2f' % power)
            
    def do_get_status(self):
        '''
        Get status of output channel

        Input:
            -

        Output:
            True (on) or False (off)
        '''
        stat = bool(int(self.ask('OUTP:STAT?')))
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
            self.write('OUTP:STAT ON')
        elif status == False:
            self.write('OUTP:STAT OFF')
        else:
            logging.error('set_status(): can only set True or False')
        
        
    def do_get_phase_offset(self):
        '''
        Get the RF output phase offset

        Input:
            -

        Output:
            phase offset (deg)
        '''
        return float(self.ask('PHAS:ADJ?'))
        
    def do_set_phase_offset(self, phase_offset):
        '''
        Set the RF output phase offset and display phase offset

        Input:
            phase offset in degrees (-360.0 .. 360.0)

        Output:
            Nones
        '''
        self.write('PHAS:ADJ %.1f DEG' %phase_offset)
        self.write('PHAS:DISP ON')
            
    def do_set_high_power(self, enabled):
        '''
        As default, the power parameter is limited to +12dB, to avoid
        any damage by careless use.
        You can enable the high power mode to increase the power to +30dBm.
        Be careful.
        
        Input:
            enabled: True or False
        '''
        if enabled:
            self.set_parameter_bounds('power',-20,30)
        else:
            self.set_parameter_bounds('power',-130,12)
            
    def do_get_high_power(self):
        '''
        Gets the current state of the high_power option.
        '''
        return self.get_parameter_options('power')['maxval'] > 13
            
    #shortcuts
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
        
    #sending customized messages
    def write(self,msg):
      return self._visainstrument.write(msg)
    
    if qkit.visa.qkit_visa_version == 1:
        def ask(self,msg):
            return self._visainstrument.ask(msg)
    else:
        def ask(self, msg):
            return self._visainstrument.query(msg)
