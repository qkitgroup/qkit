# Attocube_ARC200, attocube resistive readout module ARC200 driver
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
import re
import time

class Attocube_ARC200(Instrument):


    def __init__(self, name, address, reset=False, **kwargs):
        Instrument.__init__(self, name, address=address, reset=reset, **kwargs)

        self._address = address
        self._visa = visa.instrument(self._address,
                        baud_rate=57600, data_bits=8, stop_bits=1,
                        parity=visa.no_parity, term_chars='',
                        timeout=2)

        self.add_parameter('mode',
            flags=Instrument.FLAG_SET,
            type=types.IntType,
            format_map={
                0: 'CONT',
                1: 'SINGLE',
            },
            doc="""
            Get/set mode:
                0: Continuous
                1: Single measurement
            """)

        self.add_parameter('refvoltage',
            flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
            type=types.IntType,
            format_map={
                0: 5,
                1: 3,
                2: 1,
                3: 0.5,
                4: 0.3,
                5: 0.1,
            }, units='V')

        self.add_parameter('units',
            flags=Instrument.FLAG_SET,
            type=types.IntType,
            format_map={
                0: '%',
                1: 'um',
                2: 'mm',
                3: 'V',
                4: 'mS',
                5: 'S',
            })

        self.add_parameter('position',
            flags=Instrument.FLAG_GET,
            format='%.03f, %.03f, %.03f')

        if reset:
            self.reset()
        else:
            self.set_mode(1)
            self.set_units('%')
            self.get_all()

    def write(self, query):
        for char in query:
            self._visa.write(char)
            time.sleep(0.025)

    def write_line(self, query):
        return self.write('%s\r' % query)

    def ask(self, query):
        try:
            self.write(query)
            reply = self._visa.read()
            return reply.rstrip(' \t\r\n')
        except Exception, e:
            logging.error('Failed to ask ARC200')
            return ''
        
    def reset(self):
        self.write_line('resetp')

    def get_all(self):
        self.get_position()

    def do_set_mode(self, mode):
        '''
        Set the measurement mode to continuous (0) or interval (1)
        '''

        if int(mode) not in (0, 1):
            return False

        logging.info('Setting mode %s' % mode)
                
        self.write_line('SM%d' % mode)
        self._visa.clear()

    def do_set_refvoltage(self, ref):
        self.write_line('SRE %d' % ref)

    def do_get_position(self):
        reply = self.ask('C')
        str_list = reply.split(',')
        try:
            float_list = [float(str_item) for str_item in str_list]
            return float_list
        except Exception, e:
            return None

    def do_set_channel_units(self, channel, units_id):
        self.write_line('SU%d%d' % (channel, units_id))

    def do_set_units(self, units_id):
        self.do_set_channel_units(1, units_id)
        self.do_set_channel_units(2, units_id)
        self.do_set_channel_units(3, units_id)
        map = self.get_parameter_options('units')['format_map']
        self.set_parameter_options('position', units=map[units_id])
