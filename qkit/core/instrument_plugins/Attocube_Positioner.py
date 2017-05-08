# Attocube_Positioner, Attocube positioner with software feedback
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
import types
import logging
import qt
from addons import positioning

class Attocube_Positioner(Instrument):

    def __init__(self, name, anc=None, arc=None, channels=3):
        Instrument.__init__(self, name, tags=['positioner'])

        self._anc = qt.instruments[anc]
        self._arc = qt.instruments[arc]

        # Instrument parameters
        self.add_parameter('position',
            type=types.TupleType,
            flags=Instrument.FLAG_GET,
            format='%.03f, %.03f, %.03f')
        self.add_parameter('speed',
            type=types.TupleType,
            flags=Instrument.FLAG_GETSET)
        self.add_parameter('channels',
            type=types.IntType,
            flags=Instrument.FLAG_SET|Instrument.FLAG_SOFTGET)

        self.set_channels(channels)

        # Instrument functions
        self.add_function('start')
        self.add_function('stop')
        self.add_function('move_abs')

    def do_get_position(self, query=True):
        if self._arc:
            return self._arc.get_position(query=query)
        else:
            return [0, 0, 0]

    def do_set_channels(self, val):
        return True

    def start(self):
        self._anc.start()

    def stop(self):
        self._anc.stop()

    def step(self, chan, nsteps):
        self._anc.step(chan + 1, nsteps)

    def do_get_speed(self):
        return self._anc.get_speed()

    def do_set_speed(self, val):
        self._anc.set_speed(val)

    def move_abs(self, pos, **kwargs):
        '''
        move_abs, move to an absolute position using feedback read-out.

        Input:
            x (float): x position
            y (float): y position
            startstep: start steps to use
            maxstep: maximum steps
            minstep: minimum steps for fine position
        '''

        if self._arc is None:
            logging.warning('ARC read-out not available, not moving')
            return False

        self._anc.set_mode1('stp')
        self._anc.set_frequency1(200)
        self._anc.set_mode2('stp')
        self._anc.set_frequency2(200)
        self._anc.set_mode3('stp')
        self._anc.set_frequency3(200)
        positioning.move_abs(self._arc, self._anc, pos,
            startstep=4, maxstep=512, minstep=1,
            channel_ofs=1)

