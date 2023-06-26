#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Electroautomatic_PS9000.py driver for Electroautomatic_PS9000 source measure unit
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

from qkit.core.instrument_base import Instrument
from qkit import visa
from qkit.gui.notebook.Progress_Bar import Progress_Bar
import numpy as np
import time
import logging


class EA_PS9360(Instrument):
    sleep_time = 1e-4
    error_codes = {0: "No error",
                   -100: "Command error",
                   -102: "Syntax error",
                   -108: "Parameter not allowed",
                   -200: "Execution error",
                   -201: "Invalid while in local",
                   -220: "Parameter error",
                   -221: "Settings conflict",
                   -222: "Data out of range",
                   -223: "Too much data",
                   -224: "Illegal parameter value",
                   -999: "Safety OVP"}

    def __init__(self, name, address, reset=False):
        """
        creates the "driver object" of the EA_PS9360 current source
        :param name: name of the device in qkit
        :param address: "TCPIP0::10.22.197.93::5028::SOCKET"
        :param reset: bool device reset
        """
        self.__name__ = __name__
        # Start VISA communication
        logging.info(__name__ + ': Initializing instrument EA_PS900')
        Instrument.__init__(self, name, tags=['physical'])
        self._address = address
        self._visainstrument = visa.instrument(self._address, read_termination='\n', write_termination='\n')

        self.add_parameter('bias_voltage', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('bias_current', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('power', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('output', type=bool, flags=Instrument.FLAG_GETSET)
        self.add_parameter('measure_voltage', type=float, flags=Instrument.FLAG_GET)
        self.add_parameter('measure_current', type=float, flags=Instrument.FLAG_GET)

        self.add_function('set_remote_control')
        self.add_function('reset')
        self.add_function('ramp_voltage')
        self.add_function('ramp_current')

        if reset:
            self.reset()
        else:
            self.set_remote_control(True)

    def _write(self, cmd):
        """
        sends a visa command <cmd>, waits until "operation complete" and raises eventual errors of the device.
        -------
        none
        """
        self._visainstrument.write(cmd)
        # TODO:self._raise_error()

    def _ask(self, cmd):
        """
        sends a visa command <cmd>, waits until "operation complete", raises eventual errors of the device and
        returns the read answer <ans>.

        parameters
        ----------
        cmd: str
            command that is send to the instrument via pyvisa and ni-visa backend.

        returns
        -------
        answer: str
            answer that is returned at query after the sent <cmd>.
        """
        if '?' in cmd:
            ans = self._visainstrument.query(cmd).rstrip()
        else:
            ans = self._visainstrument.query('{:s}?'.format(cmd)).rstrip()
        # TODO: self._raise_error()
        return ans

    def set_remote_control(self, status):
        """
        remote control needs to be activated to change device parameters
        status: 1 activated, 0 deactivated (local mode)
        """
        self._write("SYST:LOCK {:d}".format(status))

    def do_set_bias_voltage(self, bias_voltage):
        """
        sets the bias (output) voltage of the current source
        :param bias_voltage: float
        :return:
        """
        self._write("source:voltage {}".format(bias_voltage))

    def do_get_bias_voltage(self):
        """

        :return:
        """
        return float(self._ask("source:voltage?")[:-2])

    def do_set_bias_current(self, bias_current):
        """
        sets the bias (output) current
        :param bias_current: bias current value (float)
        :return:
        """
        self._write("source:current {}".format(bias_current))

    def do_get_bias_current(self):
        """
        returns the (previously) set bias current
        :return:
        """
        return float(self._ask("source:current?")[:-2])

    def do_set_power(self, power):
        """
        sets the output power (limit) of the device. (Voltage or current can have lower limits)
        power: (float) power limit in Watts
        """
        self._write("source:power {}".format(power))

    def do_get_power(self):
        """
        sets the output power (limit) of the device. (Voltage or current can have lower limits)
        power: (float) power limit in Watts
        """
        return float(self._ask("source:power?")[:-2])

    def do_get_measure_voltage(self):
        """
        returns the measured voltage
        """
        return float(self._ask("meas:voltage?")[:-2])

    def do_get_measure_current(self):
        """
        returns the measured current
        """
        return float(self._ask("meas:current?")[:-2])

    def do_set_output(self, status):
        """
        turns output on/off
        :param status: on (1) off (0)
        """
        self._write("output {:d}".format(status))

    def do_get_output(self):
        """
        gets the output state of the device
        """
        state = self._ask("output?")
        if state == "ON":
            return True
        elif state == "OFF":
            return False
        else:
            raise ValueError("wrong response")

    def ramp_current(self, current, ramp_rate=1e-3, progress_bar=False):
        """
        ramps the bias current to a specified value with the specified ramp_rate.
        current: float, end current
        ramp_rate: float, change of voltage per second
        progress_bar: bool, weather the progress_bar should be displayed
        """
        start_current = self.do_get_measure_current()
        if np.sign(current-start_current) != np.sign(ramp_rate):
            ramp_rate *= (-1)
        current_values = np.arange(start_current, current, 0.1*ramp_rate)
        if progress_bar:
            pb = Progress_Bar(len(current_values))
        for c in current_values:
            self.do_set_bias_current(c)
            time.sleep(0.1)
            if progress_bar:
                pb.iterate()

    def ramp_voltage(self, voltage, ramp_rate=1e-3, progress_bar=False):
        """
        ramps the bias voltage to a specified value with the specified ramp_rate.
        Keep in mind the defined current limit
        voltage: float, end voltage
        ramp_rate: float, change of voltage per second
        progress_bar: bool, weather the progress_bar should be displayed
        """
        start_voltage = self.do_get_measure_voltage()
        if np.sign(voltage-start_voltage) != np.sign(ramp_rate):
            ramp_rate *= (-1)
        voltage_values = np.arange(start_voltage, voltage, 0.1*ramp_rate)
        if progress_bar:
            pb = Progress_Bar(len(voltage_values))
        for v in voltage_values:
            self.do_set_bias_voltage(v)
            time.sleep(0.1)
            if progress_bar:
                pb.iterate()

    def reset(self):
        """
        resets the device
        """
        self._write('*RST')

    def get_error(self):
        """
        gets the errors from the device
        """
        return self._ask("system:error:all?")

    def release_remote_lock(self):
        """
        releases the remote lock of the device so that it can be used locally.
        """
        self.set_remote_control(False)
