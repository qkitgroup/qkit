# Driver for OPTO Dac  0.1
# Stevan Nadj-Perge <s.nadj-perge@tudelft.nl>, 2008
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

import pyvisa.vpp43 as vpp43
from time import sleep
import types
import logging
from instrument import Instrument


class OPTO(Instrument):

    def __init__(self, name, address, numdacs=8):
        logging.info(__name__+ ': Initializing instrument OPTO')
        Instrument.__init__(self, name, tags=['physical'])
        self._address=address
        self._numdacs=8
        self._sleeptime=0.0
        self.add_parameter('dac', type=types.FloatType,
                        flags=Instrument.FLAG_SET, channels=(1, self._numdacs),
                           minval=-5000.00, maxval=5000, units='mV',
                           format='%.02f', tags=['sweep'])

        self._open_serial_connection()

    def _open_serial_connection(self):
        logging.debug(__name__+':Opening serial connection')
        self._session = vpp43.open_default_resource_manager()
        self._vi = vpp43.open(self._session, self._address)
        vpp43.set_attribute(self._vi, vpp43.VI_ATTR_ASRL_BAUD, 115200)
        vpp43.set_attribute(self._vi, vpp43.VI_ATTR_ASRL_DATA_BITS, 8)
        vpp43.set_attribute(self._vi, vpp43.VI_ATTR_ASRL_STOP_BITS,
                            vpp43.VI_ASRL_STOP_ONE)
        vpp43.set_attribute(self._vi, vpp43.VI_ATTR_ASRL_PARITY,
                            vpp43.VI_ASRL_PAR_ODD)
        vpp43.set_attribute(self._vi, vpp43.VI_ATTR_ASRL_END_IN,
                            vpp43.VI_ASRL_END_NONE)

    def _close_serial_connection(self):
        vpp43.close(self._vi)

    def _send_message(self, message):
        vpp43.write(self._vi, message)
        sleep(self._sleeptime)

    def _dac_voltage_to_message(self, dac, voltage):
        bytevalue=int(round(voltage*1000/5000*32768+32768))
        dataH=int(bytevalue/256)
        dataL=bytevalue-dataH*256
        bytedac=128
        tdac=dac
        while (tdac>1):
            tdac=tdac-1
            bytedac=int(bytedac/2)
        message="%c%c%c%c%c%c%c" % (7, 0, 3, 10, bytedac, dataH, dataL)
        return message

    def _read_buffer(self):
        response=vpp43.read(self._vi, vpp43.get_attribute(self._vi,
                            vpp43.VI_ATTR_ASRL_AVAIL_NUM))
        sleep(self._sleeptime)
        return response

    def do_set_dac(self, mvoltage, channel):
        logging.debug(__name__ + 'setting the dacs')
        voltage=mvoltage/1000.0
        message=self._dac_voltage_to_message(channel, voltage)
        self._send_message(message)
        r=self._read_buffer()
        czero='%c'%0
        if (r!=''):
            if (r[1]!=czero):
                logging.debug(__name__+' possible error in optodac' + r)
