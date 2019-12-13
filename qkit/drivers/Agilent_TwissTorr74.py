# Agilent_TwissTorr74 version 1.0 written by YS@KIT 2019

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


import qkit
from qkit.core.instrument_base import Instrument
import logging
import serial
import time
import atexit
import sys

class Agilent_TwissTorr74(Instrument):

    def __init__(self, name, address, reset=False):
        Instrument.__init__(self, name, tags=['physical'])
        logging.info(__name__ + ': Initializing instrument Twisstorr')
        if sys.version_info[0] < 3:
            def enc(string):
                return string
            def dec(string):
                return string
        else:
            def enc(string):
                return string.encode('latin-1')
            def dec(byte):
                return byte.decode('latin-1')
        self._enc = enc
        self._dec = dec
        self.setup(address)

    def setup(self, device="COM4"):
        # Open serial port, 9600, 8,N,1, timeout 1s
        baudrate = 9600
        timeout = 0.1

        # Serial port configuration
        ser = serial.Serial()
        ser.baudrate = baudrate
        ser.timeout = timeout
        self.ser = self._std_open(device, baudrate, timeout)
        atexit.register(self.ser.close)
        self._set_remote_serial(serial=True)
        if self.get_status == 0:
            self._set_active_stop(active_stop=True)

    def _std_open(self, device, baudrate, timeout):
        return serial.Serial(device, baudrate, timeout=timeout)

    def close(self):
        # Close serial port
        self.ser.close()

    def _remote_cmd(self, cmd):
        """
        Function sending the command string to the device.

        Args:
            cmd (str): Command string to be sent. Function "command" can be used to build it
                       from supplied window and data information (see pump manual for possible values)

        Returns:
            value (str): Answer from the device. Function "answer" can be use to unpack useful info.
        """
        self.ser.write(cmd)
        time.sleep(0.1)
        rem_char = self.ser.inWaiting()
        value = self.ser.read(rem_char)
        return value

    def command(self, addr=0x80, window='205', write=False, data=None):
        """
        Function building the command string sent to the device.
        For possible commands, see manual or use predefined functions in this module.

        Args:
            addr (hex): Unit address = 0x80 for RS-232, 0x80 + device number for RS-485
            window (str): String of 3 numeric character indicating the window number (defining the command)
            write (bool): Is the command used to read (False) or write (True) to the device
            data (str):  Alphanumeric ASCII string with the data to be written in case write==True

        Returns:
            cmd (str): Complete string to be sent to the device including a CRC
        """

        start = '\x02'
        command_string = start + chr(addr) + window

        if write:
            command_string += '1'
            command_string += data
        else:
            command_string += '0'

        end = '\x03'
        command_string += end

        crc = ord(command_string[1]) ^ ord(command_string[2])
        for i in range(3, len(command_string)):
            crc = crc ^ ord(command_string[i])
        crch = hex(crc)
        crc1 = crch[-2]
        crc2 = crch[-1]

        cmd = command_string + crc1 + crc2

        cmd = self._enc(cmd)

        return cmd

    def answer(self, answer):
        """
        Function unpacking the device answer.
        If the returned string has the length corresponding to one char of information,
        this information is decoded using the described meanings from the manual.
        In the case that the returned string is longer, the characters containing the data are returned.

        Args:
            answer (str): Answer string as it came from the device

        Returns:
            Decoded answer as described above.
        """
        answer = self._dec(answer)
        start = answer[0]
        address = answer[1]
        if len(answer) == 6:
            if answer[2] == chr(0x06):
                return answer[2], 'ACK'
            if answer[2] == chr(0x15):
                return answer[2], 'NACK'
            if answer[2] == chr(0x32):
                return answer[2], 'Unknown Window'
            if answer[2] == chr(0x33):
                return answer[2], 'Data Type Error'
            if answer[2] == chr(0x34):
                return answer[2], 'Out of Range'
            if answer[2] == chr(0x35):
                return answer[2], 'Window Read Only or Disabled'
            else:
                return answer
        else:
            window = answer[2] + answer[3] + answer[4]
            rw = answer[5]
            data = ''
            for i in range(6, len(answer) - 3):
                data += answer[i]
            return data

    def _set_remote_serial(self, serial=True):
        window = "008"
        write = True
        if serial:
            data = '0'
        else:
            data = '1'
        cmd = self.command(window=window, write=write, data=data)
        answer = self.answer(self._remote_cmd(cmd))
        return answer

    def _get_remote_serial(self):
        window = "008"
        write = False
        cmd = self.command(window=window, write=write)
        answer = self.answer(self._remote_cmd(cmd))
        return answer

    def _set_active_stop(self, active_stop=False):
        window = "107"
        write = True
        if active_stop:
            data = '1'
        else:
            data = '0'
        cmd = self.command(window=window, write=write, data=data)
        answer = self.answer(self._remote_cmd(cmd))
        return answer

    def _get_active_stop(self):
        window = "107"
        write = False
        cmd = self.command(window=window, write=write)
        answer = self.answer(self._remote_cmd(cmd))
        return int(answer)

    def get_status(self):
        """
        Get the pump status.

        Returns:
            status (int):
                0: 'Stop'
                1: 'Waiting Interlock'
                2: 'Starting'
                3: 'Auto-tuning'
                4: 'Breaking'
                5: 'Normal'
                6: 'Fail'
        """
        window = '205'
        write = False
        cmd = self.command(window=window, write=write)
        answer = self.answer(self._remote_cmd(cmd))
        meaning = ['Stop', 'Waiting Interlock', 'Starting', 'Auto-tuning', 'Braking', 'Normal', 'Fail']
        return int(answer), meaning[int(answer)]

    def get_error(self):
        """
        Get error code.

        Returns:
            Error code (Bitstring).
            Bit description as taken from manual: |7|6|5|4|3|2|1|0|
                7: Too high load
                6: Short circuit
                5: Over voltage
                4:
                3:
                2: Control over temperature
                1: Pump over temperature
                0: No connection
        """
        window = "206"
        write = False
        cmd = self.command(window=window, write=write)
        answer = self.answer(self._remote_cmd(cmd))
        return answer

    def get_rot_freq(self):
        """
        Get rotation frequency (Hz)

        Returns:
            freq (int): Rotation frequency in Hz
        """
        window = "226"
        write = False
        cmd = self.command(window=window, write=write)
        answer = self.answer(self._remote_cmd(cmd))
        answer = int(answer) / 60.
        return answer

    def get_temp(self):
        """
        Get pump temperature

        Returns:
            temp (int): Pump temperature in degC
        """
        window = '204'
        write = False
        cmd = self.command(window=window, write=write)
        answer = self.answer(self._remote_cmd(cmd))
        return int(answer)

    def get_power(self):
        """
        Get pump power

        Returns:
            power (int): Pump power in Watts
        """
        window = '202'
        write = False
        cmd = self.command(window=window, write=write)
        answer = self.answer(self._remote_cmd(cmd))
        return int(answer)

    def get_cycles(self):
        """
        Get pump cycle number

        Returns:
            cycle (int): Cycle number
        """
        window = '301'
        write = False
        cmd = self.command(window=window, write=write)
        answer = self.answer(self._remote_cmd(cmd))
        return int(answer)

    def get_pump_life(self):
        """
        Get pump life time

        Returns:
            pump life (int): Pump life in hours
        """
        window = '302'
        write = False
        cmd = self.command(window=window, write=write)
        answer = self.answer(self._remote_cmd(cmd))
        return int(answer)

    def start(self):
        """
        Start the pump
        """
        window = '000'
        write = True
        data = '1'
        cmd = self.command(window=window, write=write, data=data)
        answer = self.answer(self._remote_cmd(cmd))
        return answer

    def stop(self):
        """
        Stop the pump
        """
        window = "000"
        write = True
        data = '0'
        cmd = self.command(window=window, write=write, data=data)
        answer = self.answer(self._remote_cmd(cmd))
        return answer

    def set_softstart(self, status=False):
        """
        Set soft start option.
        Makes the pump start slower. Manual recommends after longer standing times.
        See manual.

        Args:
            status (bool): Status of soft start option to be set (standard: False)
        """
        window = "100"
        write = True
        if status:
            data = "1"
        else:
            data = "0"
        cmd = self.command(window=window, write=write, data=data)
        answer = self.answer(self._remote_cmd(cmd))
        return answer

    def get_softstart(self):
        """
        Get status of soft start option.
        Makes the pump start slower. Manual recommends after longer standing times.
        See manual.

        Returns:
            status (bool): Status of soft start option
        """
        window = "100"
        write = False
        cmd = self.command(window=window, write=write)
        answer = self.answer(self._remote_cmd(cmd))
        return int(answer)

    def set_rot_freq_setting(self, freq=1167):
        """
        Rotational frequency setting (Hz)

        Args:
            freq (int): Rotational frequency [1100..1167], default = 1167
        """
        window = "120"
        write = True
        data = str(freq)
        while len(data) < 6:
            data = '0' + data
        cmd = self.command(window=window, write=write, data=data)
        answer = self.answer(self._remote_cmd(cmd))
        return answer

    def get_rot_freq_setting(self):
        """
        Get rotational frequency setting (Hz)

        Returns:
            freq (int): Rotational frequency [1100..1167], default = 1167
        """
        window = "120"
        write = False
        cmd = self.command(window=window, write=write)
        answer = self.answer(self._remote_cmd(cmd))
        return int(answer)