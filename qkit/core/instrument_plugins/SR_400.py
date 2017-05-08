# SR_400, Stanford Research 400 photon counter driver
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

class SR_400(Instrument):

    SCALE_LOG = 0
    SCALE_987 = 1
    SCALE_876 = 2
    SCALE_765 = 3
    SCALE_654 = 4
    SCALE_543 = 5
    SCALE_432 = 6
    SCALE_321 = 7

    def __init__(self, name, address, reset=False):
        Instrument.__init__(self, name)

        self._address = address
        self._visa = visa.instrument(self._address)

        self.add_parameter('identification',
            flags=Instrument.FLAG_GET)

        self.add_parameter('mode',
            flags=Instrument.FLAG_GETSET,
            type=types.IntType,
            minval=0, maxval=3,
            format_map={
                0: 'A, B for preset T',
                1: 'A - B for preset T',
                2: 'A + B for preset T',
                3: 'A for preset B',
            },
            doc="""Get / set mode""")

        self.add_parameter('counter',
            flags=Instrument.FLAG_GET,
            type=types.IntType,
            channels=('A', 'B'))

        self.add_parameter('count',
            flags=Instrument.FLAG_GET,
            channels=('A', 'B', 'T'),
            doc="""
            Start counting and return data (all n periods).
            Channel A, B, or T (= A and B as tuple)
            """)

        self.add_parameter('counter_input',
            flags=Instrument.FLAG_GETSET,
            type=types.IntType,
            channels=('A', 'B', 'T'),
            minval=0, maxval=3,
            format_map = {
                0: '10MHz',
                1: 'Input 1',
                2: 'Input 2',
                3: 'Trigger'
            },
            doc="""Get / set input""")

        self.add_parameter('counter_preset',
            flags=Instrument.FLAG_GETSET,
            type=types.IntType,
            channels=('B', 'T'),
            minval=1, maxval=9e11,
            format = '%1.1e',
            doc="""
            Get / set preset count for a channel, 1 <= n <= 9e11.
            If input is 10MHz the units are 100ns periods,
            only one significant digit can be used.
            """)

        self.add_parameter('periods',
            flags=Instrument.FLAG_GETSET,
            type=types.IntType,
            minval=1, maxval=2000,
            doc="""
            Get / set number of periods to measure.
            """)

        self.add_parameter('current_period',
            flags=Instrument.FLAG_GET,
            type=types.IntType,
            doc="""
            Get current period number.
            """)

        self.add_parameter('disc_slope',
            flags=Instrument.FLAG_GETSET,
            type=types.IntType,
            channels=('A', 'B', 'T'),
            format_map={
                0: 'RISE',
                1: 'FALL',
            },
            minval=0, maxval=1,
            doc="""Get/set discriminator scope""")

        self.add_parameter('disc_level',
            flags=Instrument.FLAG_GETSET,
            type=types.FloatType,
            channels=('A', 'B', 'T'),
            minval=-0.3, maxval=0.3,
            units='V',
            doc="""
            Get/set discriminator level, -0.3V < 0 < 0.3V
            """)

        if reset:
            self.reset()
        else:
            self.get_all()

    def _counter_num(self, counter):
        if type(counter) == types.IntType:
            return counter
        elif type(counter) == types.StringType:
            nummap = {'A': 0, 'B': 1, 'T': 2}
            return nummap.get(counter.upper(), None)
        else:
            return None

    def reset(self):
        self._visa.write('*RST')

    def get_all(self):
        self.get_mode()
        self.get_periods()
        for chan in 'A', 'B':
            self.get('counter%s' % chan)
            self.get('counter_input%s' % chan)
            self.get('disc_level%s' % chan)
            self.get('disc_slope%s' % chan)

        self.get('counter_presetB')
        self.get('counter_presetT')

    def do_get_identification(self):
        return self._visa.ask('*IDN?')

    def do_get_mode(self):
        ans = self._visa.ask('CM')
        return ans

    def do_set_mode(self, mode):
        self._visa.write('CM %d' % mode)

    def do_get_counter(self, channel):
        ans = self._visa.ask('Q%s' % channel)
        return int(ans)

    def do_get_count(self, channel):
        ans = self._visa.ask('CR; F%s' % channel)
        if channel == 'T':
            ans2 = self._visa.read()
            return int(ans), int(ans2)
        else:
            return int(ans)

    def do_get_counter_input(self, channel):
        ans = self._visa.ask('CI %d' % self._counter_num(channel))
        return int(ans)

    def do_set_counter_input(self, val, channel):
        self._visa.write('CI %d,%d' % (self._counter_num(channel), val))

    def do_get_counter_preset(self, channel):
        ret = self._visa.ask('CP %d' % self._counter_num(channel))
        return float(ret)

    def do_set_counter_preset(self, val, channel):
        self._visa.write('CP %d,%d' % (self._counter_num(channel), val))

    def do_get_periods(self):
        ans = self._visa.ask('NP')
        return ans

    def do_set_periods(self, val):
        self._visa.write('NP %d' % val)

    def do_get_disc_slope(self, channel):
        ans = self._visa.ask('DS %d' % self._counter_num(channel))
        return ans

    def do_set_disc_slope(self, val, channel):
        self._visa.write('DS %d,%d' % (self._counter_num(channel), val))

    def do_get_disc_level(self, channel):
        ans = self._visa.ask('DL %d' % self._counter_num(channel))
        return ans

    def do_set_disc_level(self, val, channel):
        self._visa.write('DL %d,%f' % (self._counter_num(channel), val))

    def do_set_periods(self, val):
        self._visa.write('NP %d' % val)

    def do_get_current_period(self):
        ans = self._visa.ask('NN')
        return int(ans)

    def start(self):
        """
        Reset counter and start counting
        """
        self._visa.write('CR; CS')

    def stop(self):
        """
        Stop counting
        """
        self._visa.write('CS')
