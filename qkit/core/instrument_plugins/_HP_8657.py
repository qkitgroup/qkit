# _HP_8657.py HP 8657A/B signal generator driver
# Pieter de Groot <pieterdegroot@gmail.com>, 2008
# Martijn Schaafsma <qtlab@mcschaafsma.nl>, 2008
# Reinier Heeres <reinier@heeres.eu>, 2008
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
from time import sleep

class HP_8657(Instrument):
    '''
    This is the python driver for the HP 8657A/B signal generator

    Usage:
    Initialise with
    <name> = instruments.create('<name>', 'HP_8657A/B', address='<GPIB address>',
        reset=<bool>, freq=<float>, pow=<float>)

    The last three parameters are optional. Default parameters are
    reset=False, freq=1e6, pow=None (minimum)

    Note that readout of device is not implemented

    TODO:
    2. Adjust timing/sleep
    3. Units
    '''

    LIMITS = {
        '8656B': {
            'minfreq': 100e3,
            'maxfreq': 990e6,
            'minpow': -127,
            'maxpow': 13
        },
        '8657A': {
            'minfreq': 100e3,
            'maxfreq': 1040e6,
            'minpow': -143.5,
            'maxpow': 13
        },
        '8657B': {
            'minfreq': 100e3,
            'maxfreq': 2060e6,
            'minpow': -143.5,
            'maxpow': 17
        }
    }

    def __init__(self, name, address, type, reset=False, freq=1e6, pow=None):
        '''
        Initializes the HP_8657A/B, and communicates with the wrapper.
        This instrument does not support GPIB talking, so 'get' functions
        are not available.
        Only use with reset=True, otherwise warning will be given.

        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address
            reset (bool)     : resets to default values, default=False
            freq (float)     : initial frequency in Hz, default=1e9
            pow (float)      : initial power in dBm, default=-143.4
        '''
        logging.info(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])

        lim = HP_8657.LIMITS[type]

        self._address = address
        self._visainstrument = visa.instrument(self._address)
        sleep(1)

        # Implement parameters
        self.add_parameter('frequency', type=types.FloatType,
            flags=Instrument.FLAG_SET,
            minval=lim['minfreq'], maxval=lim['maxfreq'],
            units='Hz', format='%.04e',
            tags=['sweep'])
        self.add_parameter('power', type=types.FloatType,
            flags=Instrument.FLAG_SET,
            minval=lim['minpow'], maxval=lim['maxpow'],
            units='dBm', tags=['sweep'])
        self.add_parameter('status', type=types.StringType,
            flags=Instrument.FLAG_SET)

        # Implement functions
        self.add_function('reset')

        # (re)set device to specified values
        if reset:
            if pow is None:
                pow = lim['minpow']
            self.reset(freq, pow)
        else:
            logging.warning('instrument does not support getting of values \
                you need to run set_power and set_frequency manually!')

    # initialization related
    def reset(self, freq=1e9, pow=-143.4):
        '''
        Reset device to default values, has to be ajusted jet

        Input:
            freq (float) : Frequency in Hz
            pow (float)  : Power in dBm

        Output:
            None
        '''
        logging.info(__name__ + ' : Resetting instrument')
        self.set_power(pow)
        sleep(0.1)
        self.set_frequency(freq)
        sleep(0.1)

    #Communication with device
    def do_set_frequency(self, frequency):
        '''
        Set frequency of device

        Input:
            freq (float) : Frequency in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting frequency to %s GHz' % frequency)
        # sending value to instrument
        self._visainstrument.write('FR%.0fHZ' % frequency)

    def do_set_power(self,power):
        '''
        Set output power of device

        Input:
            pow (float) : Power in dBm

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting power to %s dBm' % power)
        # sending value to instrument
        self._visainstrument.write('AP%.1fDM' % power)

    def do_set_status(self,status):
        '''
        Set status of output channel

        Input:
            status (string) : 'on' or 'off'

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting status to "%s"' % status)
        if status.upper() == 'ON':
            self._visainstrument.write('R3')
        elif status.upper() == 'OFF':
            self._visainstrument.write('R2')
        else:
            raise ValueError('set_status(): can only set on or off')

    # shortcuts
    def off(self):
        '''
        Set status to 'off'

        Input:
            None

        Output:
            None
        '''
        self.set_status('off')

    def on(self):
        '''
        Set status to 'on'

        Input:
            None

        Output:
            None
        '''
        self.set_status('on')
