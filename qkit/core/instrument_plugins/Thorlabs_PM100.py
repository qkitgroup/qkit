# Thorlabs_PM100, Thorlabs PM100 power meter driver
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
import math

class Thorlabs_PM100(Instrument):

    _RE_FREQ = re.compile('(\d+)HZ')

    STAT_RESERVED1 = 0x80
    STAT_RQS_MSS = 0x40
    STAT_ESB = 0x20
    STAT_MAV = 0x10
    STAT_OSM = 0x08
    STAT_EAV = 0x04
    STAT_RESERVED2 = 0x02
    STAT_CHARGER = 0x01

    def __init__(self, name, address, reset=False):
        Instrument.__init__(self, name)

        self._address = address
        self._visa = visa.instrument(self._address,
                        baud_rate=115200, data_bits=8, stop_bits=1,
                        parity=visa.no_parity, term_chars='\r\n')

        self.add_parameter('identification',
            flags=Instrument.FLAG_GET)

        self.add_parameter('power',
            flags=Instrument.FLAG_GET,
            type=types.FloatType,
            units='W')

        self.add_parameter('head_info',
            flags=Instrument.FLAG_GET,
            type=types.StringType)

        self.add_parameter('wavelength',
            flags=Instrument.FLAG_GETSET,
            type=types.FloatType,
            units='m')

        self.add_parameter('filter_freq',
            flags=Instrument.FLAG_GETSET,
            type=types.IntType,
            units='Hz')

        if reset:
            self.reset()
        else:
            self.get_all()

    def reset(self):
        self._visa.write('*RST')

    def get_all(self):
        self.get_power()
        self.get_head_info()
        self.get_wavelength()
        self.get_filter_freq()

    def do_get_identification(self):
        return self._visa.ask('*IDN?')

    def do_get_power(self):
        ans = self._visa.ask(':POWER?')
        return float(ans)

    def do_get_head_info(self):
        ans = self._visa.ask(':HEAD:INFO?')
        return ans

    def do_get_wavelength(self):
        ans = self._visa.ask(':WAVELENGTH?')
        return float(ans)

    def do_set_wavelength(self, val):
        self._visa.write(':WAVELENGTH %e' % val)

    def do_get_filter_freq(self):
        ans = self._visa.ask(':FILTER?')
        m = self._RE_FREQ.match(ans)
        if m is not None:
            return float(m.group(1))
        else:
            return None

    def do_set_filter_freq(self, val):
        self._visa.write(':FILTER %dHz' % val)

