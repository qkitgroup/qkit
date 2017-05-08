# Cryomagnetics_LM500, Cryomagnetics LM500 level meter driver
# Reinier Heeres <reinier@heeres.eu>, 2010
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
import time

class Cryomagnetics_LM500(Instrument):

    UNITS = ('CM', 'IN', 'PERCENT', '%')
    
    def __init__(self, name, address, reset=False):
        Instrument.__init__(self, name)

        self._address = address
        self._visa = visa.instrument(self._address)

        self.add_parameter('identification',
            flags=Instrument.FLAG_GET)

        self.add_parameter('units',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType)

        self.add_parameter('mode',
            flags=Instrument.FLAG_GETSET,
            format_map={'S': 'Sample', 'C': 'Continuous'},
            type=types.StringType)

        self.add_parameter('length',
            flags=Instrument.FLAG_GET,
            type=types.FloatType)

        self.add_parameter('lastval',
            flags=Instrument.FLAG_GET,
            type=types.FloatType,
            units='cm')

        self.add_parameter('interval',
            flags=Instrument.FLAG_GETSET,
            type=types.IntType,
            minval=0,
            units='s')

        self.add_parameter('alarmlim',
            flags=Instrument.FLAG_GETSET,
            type=types.FloatType,
            minval=0,
            units='cm')

        self.add_function('local')
        self.add_function('remote')
        self.add_function('measure')

        if reset:
            self.reset()
        else:
            self.get_all()

    def reset(self):
        self._visa.write('*RST')

    def get_all(self):
        self.get_identification()
        self.get_interval()
        self.get_units()
        self.get_length()
        self.get_alarmlim()
        self.get_lastval()
        
    def do_get_identification(self):
        return self._visa.ask('*IDN?')

    def _update_units(self, unit):
        params = ('length', 'alarmlim', 'lastval')
        for p in params:
            self.set_parameter_options(p, units=unit)
            
    def do_get_units(self):
        ans = self._visa.ask('UNITS?')
        self._update_units(ans)
        return ans.upper()

    def do_set_units(self, unit):
        unit = unit.upper()
        if unit not in self.UNITS:
            logging.error('Trying to set invalid unit: %s', unit)
            return False
        self._visa.write('UNITS %s' % unit)
        self._update_units(unit)

    def do_get_mode(self):
        return self._visa.ask('MODE?')
        
    def do_set_mode(self, mode):
        self._visa.write('MODE %s' % mode)

    def _check_ans_unit(self, ans):
        try:
            val, unit = ans.split(' ')
        except:
            logging.warning('Unable to parse answer: %s', ans)
            return False

        set_unit = self.get_units(query=False)
        if unit.upper() != set_unit:
            logging.warning('Returned units (%s) differ from set units (%s)!',
                unit, set_unit)
                
        return float(val)

    def do_get_interval(self):
        ans = self._visa.ask('INTVL?')
        fields = ans.split(':')
        if len(fields) == 3:
            fields = [int(i) for i in fields]
            return fields[0] * 3600 + fields[1] * 60 + fields[2]
        return -1

    def do_set_interval(self, interval):
        h = math.floor(interval / 3600)
        m = math.floor((interval - h * 3600) / 60)
        s = math.floor(interval - h * 3600 - m * 60)
        self._visa.write('INTVL %02d:%02d:%02d' % (h, m, s))

    def do_get_length(self):
        ans = self._visa.ask('LNGTH?')
        return self._check_ans_unit(ans)

    def do_get_lastval(self):
        ans = self._visa.ask('MEAS?')
        return self._check_ans_unit(ans)

    def do_set_alarmlim(self, val):
        self._visa.write('ALARM %f' % val)
        
    def do_get_alarmlim(self):
        ans = self._visa.ask('ALARM?')
        return self._check_ans_unit(ans)

    def do_set_alarmlim(self, val):
        self._visa.write('ALARM %f' % val)

    def local(self):
        self._visa.write('LOCAL')

    def remote(self):
        self._visa.write('REMOTE')

    def measure(self):
        self._visa.write('MEAS')
        time.sleep(0.1)
        ans = self._visa.ask('MEAS?')
        return self._check_ans_unit(ans)
