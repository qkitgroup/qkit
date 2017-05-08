# picoquant_ph.py, python wrapper for picoquant picoharp library
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

import ctypes
import numpy as np

phlib = ctypes.windll.phlib

MAXDEVNUM = 8

HISTCHAN = 65536
TTREADMAX = 131072
RANGES = 8

MODE_HIST = 0
MODE_T2 = 2
MODE_T3 = 3

FLAG_OVERFLOW = 0x0040
FLAG_FIFOFULL = 0x0003

# in mV
ZCMIN = 0
ZCMAX = 20
DISCRMIN = 0
DISCRMAX = 800

# in ps
OFFSETMIN = 0
OFFSETMAX = 1000000000

# in ms
ACQTMIN = 1
ACQTMAX = 10*60*60*1000

# in mV
PHR800LVMIN = -1600
PHR800LVMAX = 2400

def get_version():
    buf = ctypes.create_string_buffer(16)
    phlib.PH_GetLibraryVersion(buf)
    return buf.value

def get_error_string(errcode):
    buf = ctypes.create_string_buffer(64)
    phlib.PH_GetErrorString(buf, errcode)
    return buf.value

def ph_check(val):
    if val >= 0:
        return val
    else:
        raise ValueError(get_error_string(val))

class PHDevice():

    def __init__(self, devid, mode=MODE_HIST):
        self._devid = devid
        self.open()
        self.initialize(mode)

    def __del__(self):
        self.close()

    def open(self):
        buf = ctypes.create_string_buffer(16)
        ret = phlib.PH_OpenDevice(self._devid, buf)
        self._serial = buf.value
        return ph_check(ret)

    def close(self):
        ret = phlib.PH_CloseDevice(self._devid)
        return ph_check(ret)

    def initialize(self, mode):
        '''
        Initialize picoharp.
        Modes:
            0: histogramming
            2: T2
            3: T3
        '''
        ret = phlib.PH_Initialize(self._devid, mode)
        return ph_check(ret)

    def get_hardware_version(self):
        model = ctypes.create_string_buffer(32)
        version = ctypes.create_string_buffer(16)
        ret = phlib.PH_GetHardwareVersion(model, version)
        ph_check(ret)
        return (model.value, version.value)

    def get_serial_number(self):
        buf = ctypes.create_string_buffer(16)
        ret = phlib.PH_GetSerialNumber(self._devid, buf)
        ph_check(ret)
        return buf.value

    def get_base_resolution(self):
        ret = phlib.PH_GetBaseResolution(self._devid)
        return ph_check(ret)

    def calibrate(self):
        ret = phlib.PH_Calibrate(self._devid)
        return ph_check(ret)

    def set_cfd_level(self, chan, val):
        '''
        Set CFD level (in mV) for channel chan.
        '''
        ret = phlib.PH_SetCFDLevel(self._devid, chan, int(val))
        return ph_check(ret)

    def set_cfd_zero_cross(self, chan, val):
        '''
        Set CFD level 0 cross level (in mV) for channel chan.
        '''
        ret = phlib.PH_SetCFDZeroCross(self._devid, chan, int(val))
        return ph_check(ret)

    def set_sync_div(self, div):
        ret = phlib.PH_SetSyncDiv(self._devid, div)
        return ph_check(ret)

    def set_stop_overflow(self, stop_of, stopcount):
        ret = phlib.PH_SetStopOverflow(self._devid, stop_of, stopcount)
        return ph_check(ret)

    def set_range(self, range):
        '''
        range = Measurement range code
            minimum = 0 (smallest, i.e. base resolution)
            maximum = RANGES-1 (largest)
        Note: Range code 0 = base resolution, 1 = 2x base resolution, 2=4x, 3=8x and so on.
        '''
        ret = phlib.PH_SetRange(self._devid, range)
        return ph_check(ret)

    def set_offset(self, offset):
        ret = phlib.PH_SetOffset(self._devid, offset)
        return ph_check(ret)

    def clear_hist_mem(self, block=0):
        ret = phlib.PH_ClearHistMem(self._devid, block)
        return ph_check(ret)

    def start(self, acq_time):
        '''
        Start acquisition for 'acq_time' ms.
        '''
        ret = phlib.PH_StartMeas(self._devid, acq_time)
        return ph_check(ret)

    def stop(self):
        ret = phlib.PH_StopMeas(self._devid)
        return ph_check(ret)

    def get_status(self):
        '''
        Check status, returns 0 when a measurement is running, >0
        when finished.
        '''
        ret = phlib.PH_CTCStatus(self._devid)
        return ph_check(ret)

    def get_block(self, block=0, xdata=True):
        buf = np.zeros((65536,), dtype=np.int32)
        ret = phlib.PH_GetBlock(self._devid, buf.ctypes.data, block)
        if xdata:
            xbuf = np.arange(65536) * self.get_resolution() / 1000
            return xbuf, buf
        return buf
        
    def get_resolution(self):
        ret = phlib.PH_GetResolution(self._devid)
        return ph_check(ret)

    def get_count_rate(self, chan):
        ret = phlib.PH_GetCountRate(self._devid, chan)
        return ph_check(ret)

    def get_flags(self):
        ret = phlib.PH_GetFlags(self._devid)
        return ph_check(ret)

    def get_elepased_meas_time(self):
        '''
        Return elapsed measurement time in ms.
        '''
        ret = phlib.PH_GetElapsedMeasTime(self._devid)
        return ph_check(ret)

    def tt_read_data(self, count):
        buf = np.zeros(count, dtype=np.int32)
        ret = phlib.PH_TTReadData(self._devid, buf.ctypes.data, count)
        ph_check(ret)
        return buf[:ret]

    def tt_set_marker_edges(self, me0, me1, me2, me3):
        ret = phlib.PH_TTSetMarkerEdges(self._devid, me0, me1, me2, me3)
        return ph_check(ret)

    # FIXME: routing functions not yet wrapped
