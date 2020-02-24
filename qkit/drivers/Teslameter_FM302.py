# -*- coding: utf-8 -*-

# Teslameter_FM302.py driver for the Projekt Elektronic GmbH Teslameter FM302
# Micha Wildermuth, micha.wildermuth@kit.edu 2020
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
from distutils.version import LooseVersion
import time


class Teslameter_FM302(Instrument):
    """
    This is the driver for the Projekt Elektronic GmbH Teslameter FM302
    """

    def __init__(self, name, address, reset=False):
        """
        Initializes VISA communication with the instrument Yokogawa GS820.

        Parameters
        ----------
        name: string
            Name of the instrument (driver).
        address: string
            Serial address for the communication with the instrument.
        reset: bool, optional
            Resets the instrument to default conditions. Default is False.

        Returns
        -------
        None

        Examples
        --------
        >>> import qkit
        QKIT configuration initialized -> available as qkit.cfg[...]

        >>> qkit.start()
        Starting QKIT framework ... -> qkit.core.startup
        Loading module ... S10_logging.py
        Loading module ... S12_lockfile.py
        Loading module ... S14_setup_directories.py
        Loading module ... S20_check_for_updates.py
        Loading module ... S25_info_service.py
        Loading module ... S30_qkit_start.py
        Loading module ... S65_load_RI_service.py
        Loading module ... S70_load_visa.py
        Loading module ... S80_load_file_service.py
        Loading module ... S85_init_measurement.py
        Loading module ... S98_started.py
        Loading module ... S99_init_user.py

        >>> TM = qkit.instruments.create('TM', 'Teslameter_FM302', address='ASRL1::INSTR')
        Initialized the file info database (qkit.fid) in 0.000 seconds.
        """
        self.__name__ = __name__
        # Start VISA communication
        Instrument.__init__(self, name, tags=['physical'])
        self._address = address
        self._visainstrument = visa.instrument(self._address)
        # Set termination characters (necessary for Ethernet communication)
        if LooseVersion(visa.__version__) < LooseVersion("1.5.0"):  # pyvisa 1.4
            self._visainstrument.term_chars = '\n'
        else:  # pyvisa 1.5
            self._visainstrument.write_termination = '\n'
            self._visainstrument.read_termination = '\r\n'
        if reset:
            self.reset()
        self.add_parameter('coupling',
                           type=int,
                           flags=Instrument.FLAG_GETSET,
                           minval=0,
                           maxval=1)
        self.add_parameter('filter',
                           type=int,
                           flags=Instrument.FLAG_GETSET,
                           minval=1,
                           maxval=64)
        self.add_parameter('integration_time',
                           type=float,
                           flags=Instrument.FLAG_GETSET,
                           minval=100e-3,
                           maxval=5,
                           unit='s')
        self.add_parameter('gain',
                           type=int,
                           flags=Instrument.FLAG_GETSET,
                           minval=1,
                           maxval=100)
        self.add_parameter('relative',
                           type=float,
                           flags=Instrument.FLAG_GETSET,
                           minval=-70,
                           maxval=70,
                           units='T')
        self.add_parameter('zero',
                           type=int,
                           flags=Instrument.FLAG_GETSET,
                           minval=-39320,
                           maxval=26213)
        self.add_parameter('value',
                           type=float,
                           flags=Instrument.FLAG_GET,
                           minval=-1.,
                           maxval=1.,
                           units='T')
        self.add_function('reset')

    def _write(self, cmd):
        return self._visainstrument.write(cmd)

    def _read(self):
        return self._visainstrument.read_raw().decode('latin1').strip('\r\n')

    def do_set_coupling(self, val):
        """
        Sets measurement signal coupling to <val>.

        Parameters
        ----------
        val: int
            Signal coupling mode. Must be 0 (DC) or 1 (AC).

        Returns
        -------
        None
        """
        if val==0:  # DC
            self._visainstrument.query('coupling DC')
        elif val==1:  # AC
            self._visainstrument.query('coupling AC')

    def do_get_coupling(self):
        """
        Gets the measurement signal coupling <val>.

        Parameters
        ----------
        None

        Returns
        -------
        val: int
            Signal coupling mode. Meanings are 0 (DC) and 1 (AC).
        """
        return {'DC':0, 'AC':1}[self._visainstrument.query('coupling').strip('coupling is ')]

    def do_set_filter(self, val):
        """
        Sets the moving average filter length to <val>.

        Parameters
        ----------
        val: int
            Moving average filter length. Can be 1, 2, 4, 8, 16, 32, 64.

        Returns
        -------
        None
        """
        self._write('filter {:d}'.format(val))
        return int(self._read().strip('filter is '))

    def do_get_filter(self):
        """
        Gets the moving average filter length <val>.

        Parameters
        ----------
        None

        Returns
        -------
        val: int
            Moving average filter length. Possible values are 1, 2, 4, 8, 16, 32, 64.
        """
        self._write('filter')
        return int(self._read().strip('filter is '))

    def do_set_integration_time(self, val):
        """
        Sets the integration time to <val>. The internal sampling rate is 10Hz.

        Parameters
        ----------
        val: int
            Integration time in seconds. Must be in [0.1s, 25.5s].

        Returns
        -------
        None
        """
        self._write('inttime {:d}'.format(val*1e3))
        return float(self._read().strip('integration time is '))*1e-3

    def do_get_integration_time(self):
        """
        Gets the integration time <val>. The internal sampling rate is 10Hz.

        Parameters
        ----------
        None

        Returns
        -------
        val: int
            Integration time in seconds.
        """
        self._write('inttime')
        return float(self._read().strip('integration time is '))*1e-3

    def do_set_gain(self, val):
        """
        Sets the analog gain to <val>.

        Parameters
        ----------
        val: int
            Analog gain. Must be in {1, 10, 100}.

        Returns
        -------
        None
        """
        self._write('gain {:d}'.format(val))
        return int(self._read().strip('analog gain is x'))

    def do_get_gain(self):
        """
        Gets the analog gain <val>.

        Parameters
        ----------
        None

        Returns
        -------
        val: int
            Analog gain. Can be in {1, 10, 100}.
        """
        self._write('gain')
        return int(self._read().strip('analog gain is x'))

    def do_set_relative(self, val):
        """
        Sets measurement relative value.

        Parameters
        ----------
        val: float:
            Absolute measurement (0) or relative measurement (<val> or 1 for current value as relative measurement value).

        Returns
        -------
        None
        """
        if bool(val) is False:
            self._write('absolute')
        else:
            if bool(val) == val:
                self._write('relative set')
            else:
                self._write('relative {:1.2f}'.format(val))
        return self._read()

    def do_get_relative(self):
        """
        Gets measurement relative value.

        Parameters
        ----------
        None

        Returns
        -------
        val: float
            Relative measurement value.
        """
        self._write('relative')
        ans = self._read()
        if ans is 'display is not relative':
            return 0
        elif 'display is relative' in ans:
            ans = ans.strip('display is relative, reference = ').split(' ')
            return float(ans[0]) * {'m': 1e-3, u'\xb5': 1e-6, 'n':1e-9}[ans[1][0]]

    def do_set_zero(self, val):
        """
        Sets the offset compensation.

        Parameters
        ----------
        val: float
            Offset compensation value.
        val: float:
            Absolute measurement (0) or relative measurement (<val> or 1 for current value as relative measurement value).

        Returns
        -------
        None
        """
        if bool(val) == val:
            self._write('zero set')
            time.sleep(5)
        else:
            self._write('zero {:d}'.format(val))
        while True:
            ans = self._read()
            if 'zero compensation value is ' in ans:
                return int(ans.strip('zero compensation value is '))
            else:
                time.sleep(1)

    def do_get_zero(self):
        """
        Gets the offset compensation.

        Parameters
        ----------
        None

        Returns
        -------
        val: float
            Offset compensation value.
        """
        self._write('zero')
        return int(self._read().strip('zero compensation value is '))

    def reset(self):
        """
        Resets the instrument to factory settings.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self._write('default')
        return self._read()

    def do_get_value(self):
        """
        Gets the measurement value.

        Parameters
        ----------
        None

        Returns
        -------
        val: float
            Measured value (in Tesla).
        """
        self._visainstrument.query('logging 1')
        ans = self._read().split(' ')
        return float(ans[0]) * {'m': 1e-3, u'\xb5': 1e-6, 'n':1e-9}[ans[1][0]]
