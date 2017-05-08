# Standa_USMC.py, Standa USMC motor driver
# Reinier Heeres <reinier@heeres.eu>, 2009
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

import types
import ctypes
import logging
from lib.dll_support import standa_usmc as standa
from instrument import Instrument
import qt

class Standa_USMC(Instrument):

    def __init__(self, name, id, serial, version):
        Instrument.__init__(self, name)

        self._id = id
        self._serial = serial
        self._version = version

        self.add_parameter('serial',
            flags=Instrument.FLAG_GET,
            type=types.StringType)

        self.add_parameter('version',
            flags=Instrument.FLAG_GET,
            type=types.StringType)

        self.add_parameter('position',
            flags=Instrument.FLAG_GETSET,
            type=types.IntType,
            units='#')

        self.add_parameter('power',
            flags=Instrument.FLAG_GETSET,
            type=types.BooleanType)

        self.add_parameter('speed',
            flags=Instrument.FLAG_GETSET,
            type=types.FloatType,
            doc="Speed, in (partial) steps per second")

        self.add_parameter('limits',
            flags=Instrument.FLAG_GET,
            doc="State of limit switches")

        self.add_function('move')
        self.add_function('reset')
        self.add_function('stop')

        self.reset()
        self.get_all()

    def get_all(self):
        self.get_serial()
        self.get_version()
        self.get_position()
        self.get_power()
        self.get_limits()

    def reset(self):
        '''Reset standard parameters.'''
        self.set_speed(1000)

    def _check(self, ret):
        if ret != 0:
            raise ValueError('Error communicating with Stand USMC device')
        return True

    def do_get_serial(self):
        return self._serial

    def do_get_version(self):
        return self._version

    def _get_mode(self):
        struct = standa.USMC_Mode()
        ret = standa.USMC_GetMode(self._id, ctypes.byref(struct))
        self._check(ret)
        return struct

    def _set_mode(self, struct):
        ret = standa.USMC_SetMode(self._id, ctypes.byref(struct))
        return self._check(ret)

    def _get_state(self):
        struct = standa.USMC_State()
        ret = standa.USMC_GetState(self._id, ctypes.byref(struct))
        self._check(ret)
        return struct

    def do_get_position(self):
        state = self._get_state()
        return state.CurPos

    def do_set_position(self, pos):
        return standa.USMCSetPosition(self._id, pos)

    def do_get_power(self):
        mode = self._get_mode()
        return mode.ResetD == 0

    def do_set_power(self, state):
        mode = self._get_mode()
        if state:
            mode.ResetD = 0
        else:
            mode.ResetD = 1
        return self._set_mode(mode)

    def do_get_speed(self):
        return self._speed

    def do_set_speed(self, speed):
        self._speed = speed

    def _get_start_parameters(self):
        struct = standa.USMC_StartParameters()
        ret = standa.USMC_GetStartParameters(self._id, ctypes.byref(struct))
        self._check(ret)
        return struct

    def move(self, pos):
        '''
        Move to a position 'pos' at the currently set speed.
        '''
        params = self._get_start_parameters()
        speed = ctypes.c_float(self._speed)
        ret = standa.USMC_Start(self._id, pos, ctypes.byref(speed), \
                ctypes.byref(params))
        return self._check(ret)

    def stop(self):
        '''Stop motion.'''
        ret = standa.USMC_Stop(self._id)
        return self._check(ret)

    def do_get_limits(self):
        state = self._get_state()
        return (state.Trailer1, state.Trailer2)

def detect_instruments():
    '''Refresh Standa USMC devices.'''

    devs = standa.USMC_Devices()
    standa.USMC_Init(ctypes.byref(devs))
    logging.info('Standa_USMC: detected %d devices', devs.NOD)
    for i in range(devs.NOD):
        qt.instruments.create('Standa%d' % i, 'Standa_USMC', id=i, \
                serial=devs.Serial[i], version=devs.Version[i])

