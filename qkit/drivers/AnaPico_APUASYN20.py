# AnaPico_APUASYN20.py
# Nicolas Gosling <Nicolas.Gosling@partner.kit.edu> 04/21
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

class AnaPico_APUASYN20(Instrument):
    '''
    This is the driver for the Ana Pico APUASYN20 Signal Genarator

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'AnaPico_APUASYN20', address='<GBIP address>, reset=<bool>')
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the Ana Pico APUASYN20, and communicates with the wrapper.

        Input:
          name (string)    : name of the instrument
          address (string) : GPIB address
          reset (bool)     : resets to default values, default=False
        '''
        logging.info(__name__ + ' : Initializing instrument Ana Pico APUASYN20')
        super().__init__(name, tags=['physical'])


        # Add some global constants
        self._address = address
        self._visainstrument = visa.instrument(self._address)
        self._numchannels = 4

        self.add_parameter('power',
            flags=super().FLAG_GETSET, units='dBm', minval=-10, maxval=23,
            channels=(1, self._numchannels), channel_prefix='ch%d_', type=float)
        self.add_parameter('frequency',
            flags=super().FLAG_GETSET, units='Hz', minval=1e5, maxval=20e9,
            channels=(1, self._numchannels), channel_prefix='ch%d_', type=float)
        self.add_parameter('status', flags=super().FLAG_GETSET,
            channels=(1, self._numchannels), channel_prefix='ch%d_', type=bool)
        self.add_parameter('blanking', flags=super().FLAG_GETSET,
            channels=(1, self._numchannels), channel_prefix='ch%d_', type=bool)
        #self.add_parameter('channel',
            #flags=super().FLAG_GETSET, type=int, minval = 1, maxval = 4)



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
        self.get_ch1_frequency()
        self.get_ch2_frequency()
        self.get_ch3_frequency()
        self.get_ch4_frequency()
        self.get_ch1_power()
        self.get_ch2_power()
        self.get_ch3_power()
        self.get_ch4_power()
        self.get_ch1_status()
        self.get_ch2_status()
        self.get_ch3_status()
        self.get_ch4_status()
        self.get_ch1_blanking()
        self.get_ch2_blanking()
        self.get_ch3_blanking()
        self.get_ch4_blanking()


    def do_get_status(self, channel):
        '''
        Reads the output status from the instrument

        Input:
            None

        Output:
            status (string) : 'On' or 'Off'
        '''
        logging.debug(__name__ + f' : get status of channel {channel}')
        return self._visainstrument.query(f'OUTPut{channel}?')


    def do_set_status(self,  status, channel):
        '''
        Set the output status of the instrument

        Input:
            status (bool) : True or False

        Output:
            None
        '''
        logging.debug(__name__ + f' : set status of channel {channel} to {status}')

        if status == True:
            self._visainstrument.write(f'OUTPut{channel} ON')
        elif status == False:
            self._visainstrument.write(f':OUTPut{channel} OFF')
        else:
            raise ValueError('set_status(): can only set True or False')

    def do_set_blanking(self, channel, blanking_status=False):
        '''
        Set the output blanking of the instrument (blanking means the ouput will be turned off when the frequency changes)

        Input:
            status (bool) : True or False

        Output:
            None
        '''
        logging.debug(__name__ + f' : set blanking to {blanking_status}')

        if blanking_status == True:
            self._visainstrument.write(f'OUTPut{channel}:BLANking ON')
        elif blanking_status == False:
            self._visainstrument.write(f':OUTPut{channel}:BLANking OFF')
        else:
            raise ValueError('set_status(): can only set True or False')


    def do_get_blanking(self, channel):
        '''
        Get the output blanking of the instrument (blanking means the output will be turned off when the frequency changes)

        Input:
            NONE

        Output:
            bool True, False
        '''
        logging.debug(__name__ + f' : get blanking status of channel: {channel}')

        return self._visainstrument.query(f':OUTPut{channel}:BLANking?')



    def do_get_channel(self):
        '''
        Reads the channel selection from the instrument

        Input:
            None

        Output:
            default channel number
        '''

        logging.debug(__name__ + ' : get channel')
        return self._visainstrument.query('SELect?')


    def do_set_channel(self, channel):
        '''
        Sets the channel selection from the instrument

        Input:
            channel (int): 1,2,3, or 4

        Output:
            NONE
        '''
        self._channel = channel
        logging.debug(__name__ + f' : set channel to {channel}')
        self._visainstrument.write(f'SELect {channel}')


    def do_get_frequency(self, channel):
        '''
        Reads the frequency of the signal from the instrument

        Input:
            None

        Output:
            freq (float) : Frequency in Hz
        '''
        logging.debug(__name__ + f' : get frequency of channel {channel}')
        return self._visainstrument.query(f':SOURce{channel}:FREQuency?')

    def do_set_frequency(self, freq, channel):
        '''
        Set the frequency of the instrument

        Input:
            freq (float) : Frequency in Hz

        Output:
            None
        '''
        logging.debug(__name__ + f' : set frequency of channel {channel} to {freq}')
        self._visainstrument.write(f':SOURce{channel}:FREQuency {freq}')


    def do_get_power(self, channel):
        '''
        Reads the power of the signal from the instrument

        Input:
            None

        Output:
            ampl (?) : power in ?
        '''
        logging.debug(__name__ + f' : get power of channel {channel}')
        return float(self._visainstrument.query(f':SOURce{channel}:POWer?'))


    def do_set_power(self, amp, channel):
        '''
        Set the power of the signal

        Input:
            amp (float) : power in ??

        Output:
            None
        '''
        logging.debug(__name__ + f' : set power of channel {channel} to {amp}')
        self._visainstrument.write(f':SOURce{channel}:POWer {amp}')