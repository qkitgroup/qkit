# RS_Step_Attenuator.py class, to perform the communication between the Wrapper and the device
# Pieter de Groot <pieterdegroot@gmail.com>, 2008
# Martijn Schaafsma <qtlab@mcschaafsma.nl>, 2008
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

class RS_Step_Attenuator(Instrument):
    '''
    This is the python driver for the Step attenuator

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'RS_Step_Attenuator', address='<GBIP address>')
    '''

    def __init__(self, name, address):
        '''
        Initializes the RS_Step_Attenuator, and communicates with the wrapper.

        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address

        Output:
            None
        '''
        logging.info(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])


        # Add some global constants
        self._address = address
        self._visainstrument = visa.instrument(self._address)

        self.add_parameter('attenuation',
            flags=Instrument.FLAG_SET, units='dB', minval=1, maxval=139, type=types.IntType)

        self.set_attenuation(139)

    def do_set_attenuation(self, dB):
        '''
        Apply the desired attenuation

        Input:
            dB (int) : Range from 1-139 db

        Output:
            None
        '''
        logging.debug(__name__ + ' : Setting attenuation to %s dB' %dB)
        if (dB<10):
            self._visainstrument.write('A00%s,' %dB)
        elif (dB<100):
            self._visainstrument.write('A0%s,' %dB)
        else:
            self._visainstrument.write('A%s,' %dB)
