# Fianium AOTF driver
# Reinier Heeres <reinier@heeres.eu>, 2011
# Maria Barkelid
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
import types
import time
import sys
import numpy as np

from instrument import Instrument
import qt

d = ctypes.cdll.LoadLibrary('c:/Program Files/Fianium/config files/AotfLibrary.dll')

class Fianium_AOTF(Instrument):

    CRYST1 = np.array((
        (600, 27),
        (670, 20),
        (740, 22),
        (810, 25),
        (880, 29),
        (950, 28),
        (1020, 28),
        (1100, 32),
    ))
    CRYST2 = np.array((
        (1100, 35),
        (1175, 38),
        (1250, 45),
        (1325, 38),
        (1400, 40),
        (1475, 34),
        (1550, 45),
        (1650, 50),
    ))
    
    MAX_POWER = 16000
    
    def __init__(self, name, id=0):
        Instrument.__init__(self, name, tags=['physical'])

        self._h = 0
        self._id = id

        self.add_parameter('wavelength',
            flags=Instrument.FLAG_SET|Instrument.FLAG_SOFTGET,
            type=types.IntType,
            units='nm')

        self.add_parameter('power',
            flags=Instrument.FLAG_SET|Instrument.FLAG_SOFTGET,
            type=types.IntType,
            units='%',
            help='Set crystal power')

        self.add_parameter('wlenopt',
            flags=Instrument.FLAG_SET,
            type=types.IntType,
            units='nm',
            help='Set wavelength and optimal power')
            
        self.add_function('enable')
        self._open()
        self.enable()
        
        # Close AOTF before exiting QTlab
        qt.flow.register_exit_handler(self._close)

    def get_all(self):
        return
        
    def _open(self):
        self._h = d.AotfOpen(self._id)
        if self._h == 0:
            raise ValueError('AOTF open failed')

    def _close(self):
        if self._h:
            d.AotfClose(self._h)

    def send_cmd(self, cmd):
        strbuf = ctypes.create_string_buffer(8192)
        bytesread = ctypes.c_uint()

        # Clear buffer
        for i in range(10):
            if d.AotfIsReadDataAvailable(self._h):
                ret = d.AotfRead(self._h, len(strbuf), ctypes.byref(strbuf), ctypes.byref(bytesread))

        d.AotfWrite(self._h, len(cmd), cmd)
        time.sleep(0.020)

        # Read reply
        ret = ''
        for i in range(0, 10):
            if d.AotfIsReadDataAvailable(self._h):
                val = d.AotfRead(self._h, len(strbuf), ctypes.byref(strbuf), ctypes.byref(bytesread))
                ret += strbuf[:bytesread.value]
                if bytesread.value == 0:
                    break
                if bytesread.value > 0 and strbuf.value[-1] == '*':
                    break
                time.sleep(0.002)
        return ret
        
    def enable(self):
        # Enable, set gain, set wavelength 650, set power to 0
        s = 'dau en\r dau gain 0 255\r dds f 0 #650\r dds a 0 0\r'
#        s = 'dau en\r dau gain 0 255\r dds f 0 #650\r dds a 0 8000\r dds a 0 0\r'
        self.send_cmd(s)

    def do_set_wavelength(self, wlen):
        s = 'dds f 0 #%d \r' % (wlen)
        self.send_cmd(s)
        
    def do_set_power(self, pow):
        val = pow * self.MAX_POWER / 100
        s = 'dds a 0 %d \r' % (val)
        self.send_cmd(s)

    def do_set_wlenopt(self, wlen):
        if wlen < 1100:
            table = self.CRYST1
        else:
            table = self.CRYST2
            
        i = np.searchsorted(table[:,0], wlen)
        if i == len(table[:,0]):
            i = i - 1
        dwlen = np.abs(table[i,0] - wlen)
        if i > 0:
            dwlen2 = np.abs(table[i-1,0] - wlen)
            if dwlen2 < dwlen:
                i = i - 1
        self.set_wavelength(wlen)
        self.set_power(table[i,1])
