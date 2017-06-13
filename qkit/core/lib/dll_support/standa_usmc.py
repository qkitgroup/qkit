# standa_usmc.py, python wrapper for Standa USMC DLL
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

"""
Wrapper for Standa USMC Stepper motor driver.

Use USMC_* functions for low-level communication, or the 'devices' object
(an instance of Devices) for a bit more abstraction.
"""

from ctypes import *

c_bool = c_int

class USMC_Devices(Structure):
    _fields_ = [
        ('NOD', c_long),
        ('Serial', POINTER(c_char_p)),
        ('Version', POINTER(c_char_p)),
    ]

class USMC_State(Structure):
    _fields_ = [
        ('CurPos', c_int),
        ('Temp', c_float),
        ('SDivisor', c_char),
        ('Loft', c_bool),
        ('FullPower', c_bool),
        ('CW_CCW', c_bool),
        ('Power', c_bool),
        ('FullSpeed', c_bool),
        ('AReset', c_bool),
        ('RUN', c_bool),
        ('SyncIN', c_bool),
        ('SyncOUT', c_bool),
        ('RotTr', c_bool),
        ('RotTrErr', c_bool),
        ('EmReset', c_bool),
        ('Trailer1', c_bool),
        ('Trailer2', c_bool),
        ('Voltage', c_float),
        ('Reserved', c_char * 8),
    ]

class USMC_Mode(Structure):
    _fields_ = [
        ('PMode', c_bool),
        ('PReg', c_bool),
        ('ResetD', c_bool),
        ('EMReset', c_bool),
        ('Tr1T', c_bool),
        ('Tr2T', c_bool),
        ('RotTrT', c_bool),
        ('TrSwap', c_bool),
        ('Tr1En', c_bool),
        ('Tr2En', c_bool),
        ('RotTeEn', c_bool),
        ('RotTrOp', c_bool),
        ('Butt1T', c_bool),
        ('Butt2T', c_bool),
        ('ResetRT', c_bool),
        ('SyncOUTEn', c_bool),
        ('SyncOUTR', c_bool),
        ('SyncINOp', c_bool),

	    ('SyncCount', c_long),
	    ('SyncInvert', c_bool),

	    ('EncoderEn', c_bool),
	    ('EncoderInv', c_bool),
	    ('ResBEnc', c_bool),
	    ('ResEnc', c_bool),

	    ('Reserved', c_char * 8),
    ]

class USMC_Parameters(Structure):
    _fields_ = [
        ('AccelT', c_float),
        ('DecelT', c_float),
        ('PTimeout', c_float),
        ('BTimeout1', c_float),
        ('BTimeout2', c_float),
        ('BTimeout3', c_float),
        ('BTimeout4', c_float),
        ('BTimeoutR', c_float),
        ('BTimeoutD', c_float),
        ('MinP', c_float),
        ('BTO1P', c_float),
        ('BTO2P', c_float),
        ('BTO3P', c_float),
        ('BTO4P', c_float),
        ('MaxLoft', c_short),
        ('StartPos', c_long),
        ('RTDelta', c_short),
        ('RTMinError', c_short),
        ('MaxTemp', c_float),
        ('SynOUTP', c_int8),
        ('LoftPeriod', c_float),
        ('EncMult', c_float),
        ('Reserved', c_char * 16),
    ]

class USMC_StartParameters(Structure):
    _fields_ = [
        ('SDivisor', c_int8),
        ('DefDir', c_bool),
        ('LoftEn', c_bool),
        ('SlStart', c_bool),
        ('WSyncIN', c_bool),
        ('SyncOUTR', c_bool),
        ('ForceLoft', c_bool),
        ('Reserved', c_char * 4),
    ]

class USMC_EncoderState(Structure):
    _fields_ = [
        ('serial', c_char * 17),
        ('dwVersion', c_long),
        ('DevName', c_char * 32),
        ('CurPos', c_int),
        ('DestPos', c_int),
        ('Speed', c_float),
        ('ErrState', c_bool),
        ('Reserverd', c_char * 16),
    ]

# Get the low-level functions and specify argument types

usmc = cdll.usmcdll
USMC_Init = usmc.USMC_Init
USMC_Init.argtype = [POINTER(USMC_Devices)]

USMC_GetState = usmc.USMC_GetState
USMC_GetState.argtype = [c_long, POINTER(USMC_State)]

USMC_GetMode = usmc.USMC_GetMode
USMC_GetMode.argtype = [c_long, POINTER(USMC_Mode)]

USMC_SetMode = usmc.USMC_SetMode
USMC_SetMode.argtype = [c_long, POINTER(USMC_Mode)]

USMC_GetStartParameters = usmc.USMC_GetStartParameters
USMC_GetStartParameters.argtype = [c_long, POINTER(USMC_StartParameters)]

USMC_Start = usmc.USMC_Start
USMC_Start.argtype = \
    [c_long, c_int, POINTER(c_float), POINTER(USMC_StartParameters)]

USMC_Stop = usmc.USMC_Stop
USMC_Stop.argtype = [c_long]

USMC_Close = usmc.USMC_Close

USMC_SetCurrentPosition = usmc.USMC_SetCurrentPosition
USMC_SetCurrentPosition.argtype = [c_long, c_int]

def struct_to_object(struct, fields):
    pass

# Object wrappers for devices

class Devices():

    def __init__(self):
        devs = USMC_Devices()
        USMC_Init(byref(devs))

        self.devices = []
        self._ndevices = devs.NOD
        for i in range(devs.NOD):
            self.devices.append(Device(i, devs.Serial[i], devs.Version[i]))

    def __str__(self):
        return 'usmc.Devices container for %d devices' % \
            len(self.devices)

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, index):
        return self.devices[index]

    def close(self):
        USMC_Close()

class Device():

    def __init__(self, devid, serial, version):
        self.devid = devid
        self.serial = serial
        self.version = version

    def __str__(self):
        return 'usmc.Device %d (%s version %s)' % \
            (self.devid, self.serial, self.version)

    def __repr__(self):
        return self.__str__()

    def get_state(self):
        struct = USMC_State()
        ret = USMC_GetState(self.devid, byref(struct))
        if ret != 0:
            print 'Error!'
        return struct

    def get_mode(self):
        struct = USMC_Mode()
        ret = USMC_GetMode(self.devid, byref(struct))
        if ret != 0:
            print 'Error!'
        return struct

    def set_mode(self, struct):
        ret = USMC_SetMode(self.devid, byref(struct))
        return ret

    def get_current_pos(self):
        s = self.get_state()
        return s.CurPos

    def get_power(self):
        m = self.get_mode()
        return m.ResetD

    def set_power(self, state):
        '''
        Set power, state=True turns it on, otherwise off.
        '''
        m = self.get_mode()
        if state:
            m.ResetD = 0
        else:
            m.ResetD = 1
        return self.set_mode(m)

    def get_start_parameters(self):
        struct = USMC_StartParameters()
        USMC_GetStartParameters(self.devid, byref(struct))
        return struct

    def start(self, destpos, speed, params=None):
        if params is None:
            params = self.get_start_parameters()
        speed = c_float(speed)
        return USMC_Start(self.devid, destpos, byref(speed), byref(params))

    def stop(self):
        ret = USMC_Stop(self.devid)
        return ret

    def set_current_position(self, pos):
        ret = USMC_SetCurrentPosition(self.devid, pos)
        return ret

if __name__ == '__main__':
    '''Try to move first device.'''
    devices = Devices()
    dev = devices[0]
    dev.set_power(True)
    dev.start(0, 1000.0)
    time.sleep(10)
    dev.start(10000, 1000.0)
