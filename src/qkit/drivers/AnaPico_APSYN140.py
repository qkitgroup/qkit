# AnaPico_APSYN140.py
# Jonas Kaemmerer 
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
import sys
from qkit import visa


import logging
import numpy

###
### work in progress !!!
###


class AnaPico_APSYN140(Instrument):
    '''
    This is the driver for the Ana Pico APSYN140 Signal Genarator

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'AnaPico_APSYN140', address='<GBIP address>, reset=<bool>')
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the Ana Pico APSYN140, and communicates with the wrapper.

        Input:
          name (string)    : name of the instrument
          address (string) : GPIB address
          reset (bool)     : resets to default values, default=False
        '''
        logging.info(__name__ + ' : Initializing instrument Ana Pico APSYN140')
        super().__init__(name, tags=['physical'])


        # Add some global constants
        self._address = address
        self._visainstrument = visa.instrument(self._address)

        self.add_parameter('power',
            flags=super().FLAG_GETSET, units='dBm', minval=-10, maxval=20,
            type=float)
        self.add_parameter('frequency',
            flags=super().FLAG_GETSET, units='Hz', minval=1e5, maxval=40e9,
            type=float)
        self.add_parameter('status', flags=super().FLAG_GETSET,
            type=bool)
        self.add_parameter('blanking', flags=super().FLAG_GETSET,
            type=bool)
        #self.add_parameter('phase',
        #   flags=Instrument.FLAG_GETSET, units='rad', minval=-numpy.pi, maxval=numpy.pi, type=types.FloatType)

        self.add_function('reset')
        self.add_function ('get_all')

        if (reset):
            self.reset()
        else:
            self.get_all()



    def get_all(self):
        '''
        Reads all implemented parameters from the instrument,
        and updates the wrapper.

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : get all')
        self.get_frequency()

        self.get_power()

        self.get_status()

        self.get_blanking()
        
        #self.get_phase()


    def do_get_status(self):
        '''
        Reads the output status from the instrument

        Input:
            None

        Output:
            status (string) : 'On' or 'Off'
        '''
        logging.debug(__name__ + ' : get status')
        return bool(int(self._visainstrument.query('OUTP?')))


    def do_set_status(self, status):
        '''
        Set the output status of the instrument

        Input:
            status (string) : 'On' or 'Off'

        Output:
            None
        '''
        logging.debug(__name__ + ' : set status to %s' % status)
        
        if status == True:
            self._visainstrument.write('OUTP ON')
        elif status == False:
            self._visainstrument.write('OUTP OFF')
        else:
            raise ValueError('set_status(): can only set True or False')


    def do_set_blanking(self, blanking_status=False):
        '''
        Set the output blanking of the instrument (blanking means the ouput 
                                                   will be turned off when the 
                                                   frequency changes)

        Input:
            status (bool) : True or False

        Output:
            None
        '''
        logging.debug(__name__ + ' : set blanking to {blanking_status}')

        if blanking_status == True:
            self._visainstrument.write('OUTPut:BLANking ON')
        elif blanking_status == False:
            self._visainstrument.write(':OUTPut:BLANking OFF')
        else:
            raise ValueError('set_status(): can only set True or False')


    def do_get_blanking(self):
        '''
        Get the output blanking of the instrument (blanking means the output will be turned off when the frequency changes)

        Input:
            NONE

        Output:
            bool True, False
        '''
        logging.debug(__name__ + ' : get blanking status')

        return self._visainstrument.query(':OUTPut:BLANking?')


    def do_get_frequency(self):
        '''
        Reads the frequency of the signal from the instrument

        Input:
            None

        Output:
            freq (float) : Frequency in Hz
        '''
        logging.debug(__name__ + ' : get frequency')
        return self._visainstrument.query(':SOURce:FREQuency?')

    def do_set_frequency(self, freq):
        '''
        Set the frequency of the instrument

        Input:
            freq (float) : Frequency in Hz

        Output:
            None
        '''
        logging.debug(__name__ + f' : set frequency to {freq}')
        self._visainstrument.write(f':SOURce:FREQuency {freq}')


    def do_get_power(self):
        '''
        Reads the power of the signal from the instrument

        Input:
            None

        Output:
            ampl (?) : power in ?
        '''
        logging.debug(__name__ + ' : get power')
        return float(self._visainstrument.query(':SOURce:POWer?'))


    def do_set_power(self, amp):
        '''
        Set the power of the signal

        Input:
            amp (float) : power in ??

        Output:
            None
        '''
        logging.debug(__name__ + f' : set power to {amp}')
        self._visainstrument.write(f':SOURce:POWer {amp}')
        
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
    
    def reset(self):
        '''
        Resets the instrument to default values

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : resetting instrument')
        self._visainstrument.write('*RST')
        self.get_all()