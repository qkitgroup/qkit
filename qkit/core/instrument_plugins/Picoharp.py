# Picoharp.py, instrument driver for Picoquant Picoharp
# Reinier Heeres <reinier@heeres.eu>, 2010
# Modified by Guenevere Prawiroatmodjo <guen@vvtp.tudelft.nl>, 2011
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

from lib.dll_support import picoquant_ph
from instrument import Instrument
import types
import logging

class Picoharp(Instrument):
    '''
    This is the python driver for the Picoquant Picoharp
    '''

    def __init__(self, name, devid, reset=False):
        Instrument.__init__(self, name, tags=['physical'])

        self._devid = devid
        self._create_dev()

        self.add_parameter('resolution', type=types.IntType,
            flags=Instrument.FLAG_GET,
            units='ps',
            doc='''Bin size''')

        self.add_parameter('range', type=types.IntType,
            flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
            doc='''Range, 0 = 1xbase, 1 = 2xbase, 2 = 4xbase, up to 7''')

        self.add_parameter('counts', type=types.IntType,
            channels=(0, 1),
            flags=Instrument.FLAG_GET)

        self.add_parameter('inttime', type=types.FloatType,
            units='sec',
            flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET)

        self.add_parameter('divider', type=types.IntType,
            flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET)

        self.add_function('reset')
        self.add_function('get_all')
        self.add_function('start')
        self.add_function('plot')

        self.set_inttime(10)

        if reset:
            self.reset()
        else:
            self.get_all()

    def _create_dev(self):
        try:
            self._dev = picoquant_ph.PHDevice(self._devid)
        except:
            logging.error('Error loading Picoharp. In use? Check USB connection?')
            self._dev = None

    def reset(self):
        self.get_all()

    def get_all(self):
        self.get_resolution()
        self.get_counts0()
        self.get_counts1()

    def do_get_resolution(self):
        if self._dev:
            return self._dev.get_resolution()
        return 0

    def do_set_range(self, val):
        if not self._dev:
            return
        self._dev.set_range(val)
        self.get_resolution()

    def do_get_counts(self, channel):
        if self._dev:
            return self._dev.get_count_rate(channel)

    def do_set_inttime(self, time):
        self._inttime = time

    def start(self):
        if not self._dev:
            return
        self._dev.clear_hist_mem()
        self._dev.start(int(self._inttime * 1000))

    def plot(self):
        if not self._dev:
            return
        import qt
        x, trace = self._dev.get_block()
        qt.plot(trace, name='picoharp', clear=True)

    def do_set_divider(self, value):
        if not self._dev:
            return
        self._dev.set_sync_div(value)

    def get_data(self):
        '''
        Returns histogram data (x,trace)
        '''
        if not self._dev:
            return None
        return self._dev.get_block()

    def get_status(self):
        '''
        Returns acquisition status
        0 : acquisition still running
        >0: acquisition has ended
        '''
        if not self._dev:
            return None
        return self._dev.get_status()

    def get_elepased_meas_time(self):
        '''
        Returns elapsed measurement time in ms
        '''
        if not self._dev:
            return None
        return self._dev.get_elepased_meas_time()

    def set_offset(self,offset):
        '''
        Set the offset in ps
        '''
        if not self._dev:
            return None
        return self._dev.set_offset(offset)

    def set_cfd_level(self, chan, val):
        '''
        Set CFD level (in mV) for channel chan.
        '''
        if not self._dev:
            return None
        return self._dev.set_cfd_level(chan, val)

    def set_cfd_zero_cross(self, chan, val):
        '''
        Set CFD level 0 cross level (in mV) for channel chan.
        '''
        if not self._dev:
            return None
        return self._dev.set_cfd_zero_cross(chan, val)

