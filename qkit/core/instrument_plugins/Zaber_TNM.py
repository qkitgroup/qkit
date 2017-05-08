# Zaber_TNM.py class, qtlab driver for Zaber T-NM stepper motor
# Device manual at http://www.zaber.com/wiki/Manuals/T-NM
#
# Umberto Perinetti <umberto.perinetti@gmail.com>, 2009
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

from instrument import Instrument
import types
import visa
import pyvisa.vpp43 as vpp43
import qt
import logging
import numpy
import time

class Zaber_TNM(Instrument):
    '''
    This is the python driver for the Zaber T-NM Stepper motor.
    '''

    def __init__(self, name, address, deviceid=2, reset=False):
        '''
        address = COM port
        deviceid = device id
        '''
        logging.info(__name__ + ' : Initializing Zaber TNM')
        Instrument.__init__(self, name, tags=['physical'])

        # Set parameters
        self._address = address
        self._deviceid = deviceid

        self.add_parameter('firmware',
            flags=Instrument.FLAG_GET,
            type=types.IntType)

        self.add_parameter('position',
            flags=Instrument.FLAG_GETSET,
            type=types.IntType)

        self.add_parameter('speed',
            flags=Instrument.FLAG_GETSET,
            type=types.IntType)

        self.add_parameter('acceleration',
            flags=Instrument.FLAG_GETSET,
            type=types.IntType)

        # Add functions
        self.add_function('reset')
        self.add_function('home')
        self.add_function('renumber')
        self.add_function('store_pos')
        self.add_function('move_rel')
        self.add_function('get_all')

        self._open_serial_connection()

        if reset:
            self.reset()
        else:
            self.get_all()

    # Open serial connection
    def _open_serial_connection(self):
        '''
        Opens the ASRL connection using vpp43
        baud=9600, databits=8, stop=one, parity=none, no end char for reads

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Opening serial connection')

        self._visa = visa.SerialInstrument(self._address,
                baud_rate=9600, data_bits=8, stop_bits=1,
                parity=visa.no_parity, term_chars="",
                send_end=False, chunk_size=8)
        vpp43.set_attribute(self._visa.vi, vpp43.VI_ATTR_ASRL_END_IN,
                vpp43.VI_ASRL_END_NONE)

    # Close serial connection
    def _close_serial_connection(self):
        '''
        Closes the serial connection

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Closing serial connection')
        self._visa.close()

    # LOW LEVEL FUNCTIONS : communication, conversions

    def convert_number(self, n):
        ret = []
        for i in range(4):
            ret.append(n & 0xff)
            n = n >> 8
        return ret

    def convert_bytes(self, bytes):
        ret = 0
        bytes.reverse()
        for b in bytes:
            ret = ret << 8
            ret += b
        return ret

    def _clear_buffer(self):
        navail = vpp43.get_attribute(self._visa.vi, vpp43.VI_ATTR_ASRL_AVAIL_NUM)
        if navail > 0:
            reply = vpp43.read(self._visa.vi, navail)

    def _read_reply(self, max_sleeps=100):
        '''
        Read reply from the Zaber.
        <max_sleeps> is the maximum number of 50msec sleeps. The default is
        100 for a maximum delay of 5 seconds.
        '''

        i = 0
        while i < max_sleeps:
            navail = vpp43.get_attribute(self._visa.vi, vpp43.VI_ATTR_ASRL_AVAIL_NUM)
            if navail >= 6:
                reply = vpp43.read(self._visa.vi, navail)
                reply = [ord(ch) for ch in reply]
                return reply

            i += 1
            time.sleep(0.05)

        return None

    def _send_raw_cmd(self, data, get_reply=True):
        '''
        Send raw command data
            1: command #
            2: data, lsb
            3: data
            4: data
            5: data, msb
        '''

        self._clear_buffer()

        tosend = "%c" % self._deviceid
        if len(data) != 5:
            print "Data should contain 5 elements"
        for ch in data:
            tosend += "%c" % ch

        self._visa.write(tosend)
        time.sleep(0.01)
        if get_reply:
            return self._read_reply()

        return None

    def send_cmd(self, cmd, arg, get_reply=True, signedpos=True):
        '''
        Send command <cmd> with argument <arg>.
        '''

        values = self.convert_number(arg)
        reply = self._send_raw_cmd([cmd] + values, get_reply)
        if get_reply and reply is not None:
            val = self.convert_bytes(reply[2:])
            if len(reply) == 6 and signedpos and (val&0xf0000000):
                val -= 0x100000000
            return val

        return None

    # FUNCTIONS CORRESPONDING TO DEVICE COMMANDS

    def reset(self):
        logging.info(__name__ + ' : resetting instrument')
        self.send_cmd(0, 0, get_reply=False)

    def home(self):
        pos = self.send_cmd(1, 0)
        if pos is not None:
            self.update_value('position', pos)

    def renumber(self, newnumber):
        newid = self.send_cmd(2, newnumber)
        if newid is not None:
            self.update_value('position', newid)

    def store_pos(self, store_address):
        if store_address < 1 or store_address > 16:
            print 'Storage address should be an integer between 1 to 16'
            return None

        reply = self.send_cmd(16, values)
        print 'Position stored at address %r' % reply

    def return_store_pos(self, store_address):
        if store_address < 1 or store_address > 16:
            print 'Storage address should be an integer between 1 to 16'
            return None

        pos = self.send_cmd(17, store_address)
        return pos

    def move_store_pos(self, store_address):
        if store_address < 1 or store_address > 16:
            print 'Storage address should be an integer between 1 to 16'
            return None

        pos = self.send_cmd(17, store_address)
        return pos

    def move_abs(self, abs_pos):
        newpos = self.send_cmd(20, abs_pos)
        if newpos is not None:
            self.update_value('position', newpos)
        return newpos

    def move_rel(self, steps):
        newpos = self.send_cmd(21, steps)
        if newpos is not None:
            self.update_value('position', newpos)
        return newpos

    def move_const_speed(self, speed):
        newspeed = self.send_cmd(22, speed)
        if newspeed is not None:
            self.update_value('speed', newspeed)
        return newspeed

    def stop(self):
        newpos = self.send_cmd(23, 0)
        if newpos is not None:
            self.update_value('position', newpos)
        return newpos

    def get_all(self):
        logging.info(__name__ + ' : get all')
        self.get_firmware()
        self.get_speed()
        self.get_position()
        self.get_acceleration()

    def do_get_firmware(self):
        fwversion = self.send_cmd(51, 0)
        return fwversion

    def do_get_speed(self):
        speed = self.send_cmd(53, 42)
        return speed

    def do_set_speed(self, val):
        speed = self.send_cmd(42, val)
        return speed

    def do_get_acceleration(self):
        accel = self.send_cmd(53, 43)
        return accel

    def do_set_acceleration(self, val):
        accel = self.send_cmd(43, val)
        return accel

    def do_get_position(self):
        pos = self.send_cmd(53, 45)
        return pos

    def do_set_position(self, pos):
        self.move_abs(pos)

