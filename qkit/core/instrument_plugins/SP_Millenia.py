# SP_Millenia.py class, qtlab driver for Spectra Physics Millennia pump laser
#
# Reinier Heeres <reinier@heeres.eu>, 2012
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
import logging
import re

class SP_Millenia(Instrument):

    def __init__(self, name, address, reset=False):
        '''
        address = COM port
        '''
        logging.info(__name__ + ' : Initializing Spectra Physics Millenia')
        Instrument.__init__(self, name, tags=['physical'])

        # Set parameters
        self._address = address

        self.add_parameter('id',
            flags=Instrument.FLAG_GET,
            type=types.StringType)

        self.add_parameter('power',
            flags=Instrument.FLAG_GETSET,
            format='%.02f',
            type=types.FloatType)

        # Add functions
        self.add_function('reset')
        self.add_function('on')
        self.add_function('off')
        self.add_function('get_all')

        self._open_serial_connection()

        if reset:
            self.reset()
        else:
            self.get_all()
 
    # Open serial connection
    def _open_serial_connection(self):
        logging.debug(__name__ + ' : Opening serial connection')

        self._visa = visa.SerialInstrument(self._address,
                baud_rate=9600, data_bits=8, stop_bits=1,
                parity=visa.no_parity, term_chars="",
                send_end=False)

    # Close serial connection
    def _close_serial_connection(self):
        '''
        Closes the serial connection
        '''
        logging.debug(__name__ + ' : Closing serial connection')
        self._visa.close()

    def get_all(self):
        self.get_id()
        self.get_power()

    def reset(self):
        pass
        
    def do_get_id(self):
        return self._visa.ask('?IDN\r')
        
    def do_get_power(self):
        ret = self._visa.ask('?P\r')
        m = re.search('([0123456789\.]+)W', ret)
        if m:
            return float(m.group(1))
        else:
            return 0

    def do_set_power(self, val):
        self._visa.write('P:%.02f\r' % val)
        return True
        
    def on(self):
        self._visa.write('ON\r')
        
    def off(self):
        self._visa.write('OFF\r')

