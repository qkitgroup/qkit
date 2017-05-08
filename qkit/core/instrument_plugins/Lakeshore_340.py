# Lakeshore 340, Lakeshore 340 temperature controller driver
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

class Lakeshore_340(Instrument):

    def __init__(self, name, address, reset=False):
        Instrument.__init__(self, name)

        self._address = address
        self._visa = visa.instrument(self._address)
        self._channels = ('A', 'B', 'C', 'D')
        
        self.add_parameter('identification',
            flags=Instrument.FLAG_GET)

        self.add_parameter('kelvin',
            flags=Instrument.FLAG_GET,
            type=types.FloatType,
            channels=self._channels,
            units='K')

        self.add_parameter('sensor',
            flags=Instrument.FLAG_GET,
            type=types.FloatType,
            channels=self._channels,
            units='')

        self.add_parameter('heater_range',
            flags=Instrument.FLAG_GETSET,
            type=types.IntType,
            format_map={
                1: '25 W',
                2: '2.5 W',
                3: '250 mW',
                4: '25 mW',
                5: '2.5 mW',
                })

        self.add_parameter('heater_output',
            flags=Instrument.FLAG_GET,
            type=types.FloatType,
            units='%')

        self.add_parameter('mode',
            flags=Instrument.FLAG_GETSET,
            type=types.IntType,
            format_map={1: 'Local', 2: 'Remote', 3: 'Remote, local lock'})

        self.add_parameter('pid',
            flags=Instrument.FLAG_GETSET,
            type=types.TupleType,
            channels=(1,4))

        self.add_parameter('setpoint',
            flags=Instrument.FLAG_GETSET,
            type=types.FloatType,
            channels=(1,4))

        self.add_function('local')
        self.add_function('remote')

        if reset:
            self.reset()
        else:
            self.get_all()

    def reset(self):
        self._visa.write('*RST')

    def get_all(self):
        self.get_identification()
        self.get_mode()

    def do_get_identification(self):
        return self._visa.ask('*IDN?')
        
    def do_get_kelvin(self, channel):
        ans = self._visa.ask('KRDG? %s' % channel)
        return float(ans)
        
    def do_get_sensor(self, channel):
        ans = self._visa.ask('SRDG? %s' % channel)
        return float(ans)
        
    def do_get_heater_range(self):
        ans = self._visa.ask('RANGE?')
        return ans
        
    def do_set_heater_range(self, val):
        self._visa.write('RANGE %d' % val)
        
    def do_get_heater_output(self):
        ans = self._visa.ask('HTR?')
        return ans
        
    def do_get_mode(self):
        ans = self._visa.ask('MODE?')
        return int(ans)

    def do_set_mode(self, mode):
        self._visa.write('MODE %d' % mode)

    def local(self):
        self.set_mode(1)

    def remote(self):
        self.set_mode(2)

    def do_get_pid(self, channel):
        ans = self._visa.ask('PID? %d' % channel)
        fields = ans.split(',')
        if len(fields) != 3:
            return None
        fields = [float(f) for f in fields]
        return fields
        
    def do_set_pid(self, val, channel):
        pass
        
    def do_get_setpoint(self, channel):
        ans = self._visa.ask('SETP? %s' % channel)
        return float(ans)
        
    def do_set_setpoint(self, val, channel):
        self._visa.write('SETP %s, %f' % (channel, val))
        