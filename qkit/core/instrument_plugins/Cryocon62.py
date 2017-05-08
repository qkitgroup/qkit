# Cryocon62.py class, to perform the communication between the Wrapper and the device
# Pieter de Groot <pieterdegroot@gmail.com>, 2008
# Martijn Schaafsma <mcschaafsma@gmail.com>, 2008
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
import types
import visa
from time import sleep
import logging

class Cryocon62(Instrument):
    '''
    This is the python driver for the Cryocon62

    Usage:
    Initialize with
    <name> = instruments.create('name', 'Cryocon62', address='<GPIB address>')

    TODO:
    1) Logging
    2) dataformats
    '''

    def __init__(self, name, address):
        '''
        Initializes the Cryocon62, and comunicates with the wrapper.

        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address

        Output:
            None
        '''
        logging.info(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])

        self._address = address
        self._visainstrument = visa.instrument(self._address)

        self.add_parameter('temperature', type=types.FloatType,
            channel_prefix='ch%d_',
            flags=Instrument.FLAG_GET, channels=(1,2))
        self.add_parameter('units', type=types.StringType,
            channel_prefix='ch%d_',
            flags=Instrument.FLAG_GET, channels=(1,2))
        self.add_parameter('sensor_index', type=types.IntType,
            channel_prefix='ch%d_',
            flags=Instrument.FLAG_GET, channels=(1,2))
        self.add_parameter('vbias', type=types.StringType,
            channel_prefix='ch%d_',
            flags=Instrument.FLAG_GET, channels=(1,2))
        self.add_parameter('channel_name', type=types.StringType,
            channel_prefix='ch%d_',
            flags=Instrument.FLAG_GET, channels=(1,2))
        self.add_parameter('sensor_name', type=types.StringType,
            channel_prefix='ch%d_',
            flags=Instrument.FLAG_GET, channels=(1,2))

    def do_get_temperature(self, channel):
        '''
        Reads the temperature of the designated channel from the device.

        Input:
            channel (int) : 1 or 2, the number of the designated channel

        Output:
            temperature (float) : Temperature in the specified units
        '''
        logging.debug(__name__ + ' : get temperature for channel %i' % channel)
        if (channel==1):
            value = self._visainstrument.ask('INPUT? A')
        elif (channel==2):
            value = self._visainstrument.ask('INPUT? B')
        else:
            return 'Channel does not exist'

        try:
            value = float(value)
        except ValueError:
            value = 0.0
        return value

    def do_get_units(self, channel):
        '''
        Reads the units of the designated channel from the device
        in which the temperature is measured.

        Input:
            channel (int) : 1 or 2, the number of the designated channel

        Output:
            units (string) : units of temperature
        '''
        logging.debug(__name__ + ' : get units for channel %i' % channel)
        if (channel==1):
            return self._visainstrument.ask('INPUT A:UNITS?')
        elif (channel==2):
            return self._visainstrument.ask('INPUT B:UNITS?')
        else:
            raise ValueError('Channel %i does not exist' % channel)

    def do_get_sensor_index(self, channel):
        '''
        Reads the index of the designated channel from the device.

        Input:
            channel (int) : 1 or 2, the number of the designated channel

        Output:
            index (int) : Sensor index
        '''
        logging.debug(__name__ + ' : get units for channel %i' % channel)
        if (channel==1):
            return int(self._visainstrument.ask('INPUT A:SENIX?'))
        elif (channel==2):
            return int(self._visainstrument.ask('INPUT B:SENIX?'))
        else:
            raise ValueError('Channel %i does not exist' % channel)

    def do_get_vbias(self, channel):
        '''
        Reads the bias of the designated channel from the device.

        Input:
            channel (int) : 1 or 2, the number of the designated channel

        Output:
            bias (string) : bias
        '''
        logging.debug(__name__ + ' : get units for channel %i' % channel)
        if (channel==1):
            return self._visainstrument.ask('INPUT A:VBIAS?')
        elif (channel==2):
            return self._visainstrument.ask('INPUT B:VBIAS?')
        else:
            raise ValueError('Channel %i does not exist' % channel)

    def do_get_channel_name(self, channel):
        '''
        Reads the name of the designated channel from the device.

        Input:
            channel (int) : 1 or 2, the number of the designated channel

        Output:
            name (string) : Name of the device
        '''
        if (channel==1):
            return self._visainstrument.ask('INPUT A:NAME?')
        elif (channel==2):
            return self._visainstrument.ask('INPUT B:NAME?')
        else:
            raise ValueError('Channel %i does not exist' % channel)

    def do_get_sensor_name(self, channel):
        '''
        Reads the name of the designated sensor from the device.

        Input:
            channel (int) : 1 or 2, the number of the designated sensor

        Output:
            name (string) : Name of the device
        '''
        if (channel==1):
            sensor_index = self.get_ch1_sensor_index()
            return self._visainstrument.ask('SENTYPE %i:NAME?' % sensor_index)
        elif (channel==2):
            sensor_index = self.get_ch2_sensor_index()
            return self._visainstrument.ask('SENTYPE %i:NAME?' % sensor_index)
        else:
            raise ValueError('Channel %i does not exist' % channel)
