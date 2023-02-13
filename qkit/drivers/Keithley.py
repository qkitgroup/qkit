# -*- coding: utf-8 -*-

# Keithley.py driver for Keithley 2636A multi channel source measure unit
# Hannes Rotzinger, hannes.rotzinger@kit.edu 2010
# Micha Wildermuth, micha.wildermuth@kit.edu 2017
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
import numpy as np
import time
import logging
from distutils.version import LooseVersion


class Keithley(Instrument):
    """
    This is the driver for the Keithley 2636A multi channel source measure unit.
    """
    
    def __init__(self, name, address, reset=False):
        """
        Initializes VISA communication with the instrument Keithley 2636A.
        
        Parameters
        ----------
        name: string
            Name of the instrument (driver).
        address: string
            GPIB address for the communication with the instrument.
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
        
        >>> IVD = qkit.instruments.create('IVD', 'Keithley', address='TCPIP0::00.00.000.00::INSTR', reset=True)
        Initialized the file info database (qkit.fid) in 0.000 seconds.
        """
        self.__name__ = __name__
        # Start VISA communication
        logging.info(__name__ + ': Initializing instrument Keithley_2636A')
        Instrument.__init__(self, name, tags=['physical'])
        self._address = address
        self._visainstrument = visa.instrument(self._address)
        # distinguish high level commands to query status bit for different pyvisa versions
        if LooseVersion(visa.__version__) < LooseVersion('1.5.0'):  # pyvisa 1.4
            self._read_stb = lambda: visa.vpp43.read_stb(self._visainstrument.vi)
        else:  # pyvisa 1.5
            self._read_stb = lambda: visa.visalib.read_stb(self._visainstrument.session)[0]
        # internal variables
        self._sweep_mode = 1  # IV-mode
        self._sweep_channels = (1,)
        self._readingbuffer_bias = None
        self._readingbuffer_sense = None
        self._readingbuffer = ()
        self._measurement_modes = {0: '2-wire', 1: '4-wire'}
        self._mode_types = {0: 'curr', 1: 'volt', 2: 'res', 3: 'pow'}
        self._smu_command = {0: 'i', 1: 'v'}
        self._IV_units = {0: 'A', 1: 'V'}
        self._avg_types = ['moving average', 'repeat average', 'median']
        # dict of defaults values: defaults[<sweep_mode>][<channel>][<parameter>][<value>]
        self._defaults = {0: [{self.set_measurement_mode: 0,  # bias channel
                               self.set_bias_mode:  1,
                               self.set_sense_mode: 1,
                               self.set_bias_range: -1,
                               self.set_sense_range: -1,
                               self.set_bias_delay: 15e-6,
                               self.set_sense_delay: 15e-6,
                               self.set_sense_nplc: 1,
                               self.set_sense_average: 1,
                               self.set_sense_autozero: 0},
                              {self.set_measurement_mode: 0,  # sense channel
                               self.set_bias_mode: 0,
                               self.set_sense_mode: 1,
                               self.set_bias_range: -1,
                               self.set_sense_range: -1,
                               self.set_bias_delay: 15e-6,
                               self.set_sense_delay: 15e-6,
                               self.set_sense_nplc: 1,
                               self.set_sense_average: 1,
                               self.set_sense_autozero: 0}],
                          1: [{self.set_measurement_mode: 1,
                               self.set_bias_mode: 0,
                               self.set_sense_mode: 1,
                               self.set_bias_range: -1,
                               self.set_sense_range: -1,
                               self.set_bias_delay: 15e-6,
                               self.set_sense_delay: 15e-6,
                               self.set_sense_nplc: 1,
                               self.set_sense_average: 1,
                               self.set_sense_autozero: 0}],
                          2: [{self.set_measurement_mode: 1,
                               self.set_bias_mode: 1,
                               self.set_sense_mode: 0,
                               self.set_bias_range: -1,
                               self.set_sense_range: -1,
                               self.set_bias_delay: 15e-6,
                               self.set_sense_delay: 15e-6,
                               self.set_sense_nplc: 1,
                               self.set_sense_average: 1,
                               self.set_sense_autozero: 0}]}
        self._default_str = 'default parameters'
        self.__set_defaults_docstring()
        # error messages
        self.err_msg = {-430: '''Query Deadlocked''',
                        -420: '''Query Unterminated''',
                        -410: '''Query Interrupted''',
                        -363: '''Input Buffer Over-run''',
                        -350: '''Queue Overflow''',
                        -315: '''Configuration Memory Lost''',
                        -314: '''Save/ Recall Memory Lost''',
                        -292: '''Referenced name does not exist''',
                        -286: '''TSP Runtime error''',
                        -285: '''Program Syntax''',
                        -282: '''Illegal program name''',
                        -281: '''Cannot Create Program''',
                        -225: '''Out of Memory or TSP Memory allocation error''',
                        -224: '''Illegal Parameter Value''',
                        -223: '''Too Much Data''',
                        -222: '''Parameter Data Out of Range''',
                        -221: '''Settings Conflict''',
                        -220: '''Parameter''',
                        -203: '''Command protected''',
                        -154: '''String Too Long''',
                        -151: '''Invalid String Data''',
                        -144: '''Character Data Too Long''',
                        -141: '''Invalid Character Data''',
                        -121: '''Invalid Character In Number''',
                        -120: '''Numeric Data''',
                        -109: '''Missing Parameter''',
                        -108: '''Parameter Not Allowed''',
                        -105: '''Trigger Not Allowed''',
                        -104: '''Data Type''',
                        -101: '''Invalid Character''',
                        0: '''Queue Is Empty''',
                        603: '''Power On State Lost''',
                        702: '''Unresponsive digital FPGA''',
                        802: '''Output Blocked By Interlock''',
                        820: '''Parsing Value''',
                        900: '''Internal System''',
                        1100: '''Command Unavailable''',
                        1101: '''Parameter Too Big''',
                        1102: '''Parameter Too Small''',
                        1103: '''Max Greater Than Min''',
                        1104: '''Too many digits for param type''',
                        1106: '''Battery Not Present''',
                        1107: '''Cannot modify factory menu''',
                        1108: '''Menu name does not exist''',
                        1109: '''Menu name already exists''',
                        1110: '''Catastrophic analog supply failure''',
                        1200: '''TSPlink initialization failed''',
                        1201: '''TSPlink initialization failed''',
                        1202: '''TSPlink initialization failed''',
                        1203: '''TSPlink initialization failed (possible loop in node chain)''',
                        1204: '''TSPlink initialization failed''',
                        1205: '''TSPlink initialization failed (no remote nodes found)''',
                        1206: '''TSPlink initialization failed''',
                        1207: '''TSPlink initialization failed''',
                        1208: '''TSPlink initialization failed''',
                        1209: '''TSPlink initialization failed''',
                        1210: '''TSPlink initialization failed (node ID conflict)''',
                        1211: '''Node %u is inaccessible''',
                        1212: '''Invalid node ID''',
                        1400: '''Expected at least %d parameters''',
                        1401: '''Parameter %d is invalid''',
                        1402: '''User scripts lost''',
                        1403: '''Factory scripts lost''',
                        1404: '''Invalid byte order''',
                        1405: '''Invalid ASCII precision''',
                        1406: '''Invalid data format''',
                        1500: '''Invalid baud rate setting''',
                        1501: '''Invalid parity setting''',
                        1502: '''Invalid terminator setting''',
                        1503: '''Invalid bits setting''',
                        1504: '''Invalid flow control setting''',
                        1600: '''Maximum GPIB message length exceeded''',
                        1700: '''Display area boundary exceeded''',
                        1800: '''Invalid Digital Trigger Mode''',
                        1801: '''Invalid digital I/O Line''',
                        2000: '''Flash download error''',
                        2001: '''Cannot flash with error in queue''',
                        2100: '''Could not open socket''',
                        2101: '''Could not close socket''',
                        2102: '''LAN configuration already in progress''',
                        2103: '''LAN disabled''',
                        2104: '''Socket error''',
                        2105: '''Unreachable gateway''',
                        2106: '''Could not acquire ip address''',
                        2107: '''Duplicate IP address detected''',
                        2108: '''DHCP lease lost''',
                        2109: '''LAN cable disconnected''',
                        2110: '''Could not resolve hostname''',
                        2111: '''DNS name (FQDN) too long''',
                        2112: '''Connection not established''',
                        2200: '''File write error''',
                        2201: '''File read error''',
                        2202: '''Cannot close file''',
                        2203: '''Cannot open file''',
                        2204: '''Directory not found''',
                        2205: '''File not found''',
                        2206: '''Cannot read current working directory''',
                        2207: '''Cannot change directory''',
                        2208: '''Cannot create directory''',
                        2209: '''Cannot remove directory''',
                        2210: '''File is not a valid script format''',
                        2211: '''File system error''',
                        2212: '''File system command not supported''',
                        2213: '''Too many open files''',
                        2214: '''File access denied''',
                        2215: '''Invalid file handle''',
                        2216: '''Invalid drive''',
                        2217: '''File system busy''',
                        2218: '''Disk full''',
                        2219: '''File corrupt''',
                        2220: '''File already exists''',
                        2221: '''File seek error''',
                        2222: '''End-of-file error''',
                        2223: '''Directory not empty''',
                        2401: '''Invalid specified connection''',
                        2402: '''TSPnet remote error: %s, where %s explains the remote error''',
                        2403: '''TSPnet failure''',
                        2404: '''TSPnet read failure''',
                        2405: '''TSPnet read failure, aborted''',
                        2406: '''TSPnet read failure, timeout''',
                        2407: '''TSPnet write failure''',
                        2408: '''TSPnet write failure, aborted''',
                        2409: '''TSPnet write failure, timeout''',
                        2410: '''TSPnet max connections reached''',
                        2411: '''TSPnet connection failed''',
                        2412: '''TSPnet invalid termination''',
                        2413: '''TSPnet invalid reading buffer table''',
                        2414: '''TSPnet invalid reading buffer index range''',
                        2415: '''TSPnet feature only supported on TSP connections''',
                        2416: '''TSPnet must specify both port and init''',
                        2417: '''TSPnet disconnected by other side''',
                        4900: '''Reading buffer index %s is invalid''',
                        4901: '''The maximum index for this buffer is %d''',
                        4903: '''Reading buffer expired''',
                        4904: '''ICX parameter count mismatch, %s (Line #%d)''',
                        4905: '''ICX parameter invalid value, %s (Line #%d)''',
                        4906: '''ICX invalid function id, %s (Line #%d)''',
                        5001: '''SMU is unresponsive''',
                        5003: '''Saved calibration constants corrupted''',
                        5004: '''Operation conflicts with CALA sense mode''',
                        5005: '''Value too big for range''',
                        5007: '''Operation would exceed safe operating area of the instrument''',
                        5008: '''Operation not permitted while output is on''',
                        5009: '''Unknown sourcing function''',
                        5010: '''No such SMU function''',
                        5011: '''Operation not permitted while cal is locked''',
                        5012: '''Cal data not saved - save or restore before lock''',
                        5013: '''Cannot save cal data - unlock before save''',
                        5014: '''Cannot restore cal data - unlock before restore''',
                        5015: '''Save to cal set disallowed''',
                        5016: '''Cannot change cal date - unlock before operation''',
                        5017: '''Cannot change cal constants - unlock before operation''',
                        5018: '''Cal version inconsistency''',
                        5019: '''Cannot unlock - invalid password''',
                        5021: '''Cannot restore default calset. Using previous calset''',
                        5022: '''Cannot restore previous calset. Using factory calset''',
                        5023: '''Cannot restore factory calset. Using nominal calset''',
                        5024: '''Cannot restore nominal calset. Using firmware defaults''',
                        5025: '''Cannot set filter.count > 1 when measure.count > 1''',
                        5027: '''Unlock cal data with factory password''',
                        5028: '''Cannot perform requested operation while source autorange is enabled''',
                        5029: '''Cannot save without changing cal date and cal due values''',
                        5032: '''Cannot change this setting unless buffer is cleared''',
                        5033: '''Reading buffer not found within device''',
                        5038: '''Index exceeds maximum reading''',
                        5040: '''Cannot use same reading buffer for multiple overlapped measurements''',
                        5041: '''Output Enable not asserted''',
                        5042: '''Invalid while overlapped measure''',
                        5043: '''Cannot perform requested operation while voltage measure autorange is enabled''',
                        5044: '''Cannot perform requested operation while current measure autorange is enabled''',
                        5045: '''Cannot perform requested operation while filter is enabled''',
                        5046: '''SMU too hot''',
                        5047: '''Minimum timestamp resolution is 1μs''',
                        5048: '''Contact check not valid with HIGH-Z output off''',
                        5049: '''Contact check not valid while an active current source''',
                        5050: '''I limit too low for contact check''',
                        5051: '''Model number/SMU hardware mismatch. Disconnect DUT and cycle power''',
                        5052: '''Interlock engaged; system stabilizing''',
                        5053: '''Unstable output detected - Measurements may not be valid''',
                        5054: '''High C voltage limit exceeded''',
                        5055: '''Cannot change adjustment date - change cal constants before operation''',
                        5059: '''trigger.source.action enabled without configuration''',
                        5060: '''trigger.measure.action enabled without configuration''',
                        5061: '''Operation not permitted while OUTPUT is off''',
                        5063: '''Cannot perform requested operation while measure autozero is on''',
                        5064: '''Cannot use reading buffer that collects source values''',
                        5065: '''I range too low for contact check''',
                        5066: '''source.offlimiti too low for contact check''',
                        5069: '''Autorange locked for HighC mode'''}
        # reset
        if reset:
            self.reset()
        else:
            self.get_all()
    
    def _write(self, cmd):
        """
        Sends a visa command <cmd>, waits until "operation complete" and raises eventual errors of the Device.
        
        Parameters
        ----------
        cmd: str
            Command that is send to the instrument via pyvisa and NI-VISA backend.
        
        Returns
        -------
        None
        """
        self._visainstrument.write(cmd)
        while not bool(int(self._visainstrument.query('*OPC?'))):
            time.sleep(1e-6)
        self._raise_error()
        return
    
    def _ask(self, cmd):
        """
        Sends a visa command <cmd>, waits until "operation complete", raises eventual errors of the Device and returns the read answer <ans>.
        
        Parameters
        ----------
        cmd: str
            Command that is send to the instrument via pyvisa and NI-VISA backend.
        
        Returns
        -------
        answer: str
            Answer that is returned at query after the sent <cmd>.
        """
        ans = self._visainstrument.query('print({:s})'.format(cmd)).strip()
        while not bool(int(self._visainstrument.query('*OPC?'))):
            time.sleep(1e-6)
        self._raise_error()
        return ans
    
    def set_digio(self, line, status):
        """
        Sets digital Input/Output line <line> to status <status>. 0 (Off) is 0V and 1 (On) is 5V.
        
        Parameters
        ----------
        line: int
            Number of digital I/O line of interest. Must be in [1,14]
        status: bool
            Output status of selected digital I/O line.
        
        Returns
        -------
        None
        """
        # Corresponding Command: digio.writebit(N, data)
        try:
            logging.debug('{!s}: Set digital I/O of line {:d} to {:d}'.format(__name__, line, status))
            self._write('digio.writebit({:d}, {:d})'.format(line, status))
        except Exception as e:
            logging.error('{!s}: Cannot set digital I/O of line {!s} to {!s}'.format(__name__, line, status))
            raise type(e)('{!s}: Cannot set digital I/O of line {!s} to {!s}\n{!s}'.format(__name__, line, status, e))
        return
    
    def get_digio(self, line):
        """
        Gets digital Input/Output status of line <line>. 0 (Off) is 0V and 1 (On) is 5V.
        
        Parameters
        ----------
        line: int
            Number of digital I/O line of interest. Must be in [1,14]
        
        Returns
        -------
        status: bool
            Output status of selected digital I/O line.
        """
        # Corresponding Command: data = digio.readbit(N)
        try:
            logging.debug('{:s}: Get digital I/O of line {:d}'.format(__name__, line))
            return bool(int(float(self._ask('digio.readbit({:d})'.format(line)))))
        except Exception as e:
            logging.error('{!s}: Cannot get digital I/O of line {!s}'.format(__name__, line))
            raise type(e)('{!s}: Cannot get digital I/O of line {!s}\n{!s}'.format(__name__, line, e))
    
    def set_measurement_mode(self, mode, channel=1):
        """
        Sets measurement mode (wiring system) of channel <channel> to <val>.
        
        Parameters
        ----------
        mode: int
            State of the measurement sense mode. Must be 0 (2-wire), 1 (4-wire) or 3 (calibration).
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        
        Returns
        -------
        None
        """
        # Corresponding Command: smuX.sense = senseMode
        try:
            logging.debug('{!s}: Set measurement mode of channel {:s} to {:d}'.format(__name__, chr(64+channel), mode))
            self._write('smu{:s}.sense = {:d}'.format(chr(96+channel), mode))
        except Exception as e:
            logging.error('{!s}: Cannot set measurement mode of channel {!s} to {!s}'.format(__name__, chr(64+channel), mode))
            raise type(e)('{!s}: Cannot set measurement mode of channel {!s} to {!s}\n{!s}'.format(__name__, chr(64+channel), mode, e))
        return
    
    def get_measurement_mode(self, channel=1):
        """
        Gets measurement mode (wiring system) <mode> of channel <channel>.
        
        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        
        Returns
        -------
        mode: int
            State of the measurement sense mode. Meanings are 0 (2-wire), 1 (4-wire) and 3 (calibration).
        """
        # Corresponding Command: senseMode= smuX.sense
        try:
            logging.debug('{!s}: Get measurement mode of channel {:s}'.format(__name__, chr(64+channel)))
            return int(float(self._ask('smu{:s}.sense'.format(chr(96+channel)))))
        except Exception as e:
            logging.error('{!s}: Cannot get measurement mode of channel {!s}'.format(__name__, chr(64+channel)))
            raise type(e)('{!s}: Cannot get measurement mode of channel {!s}\n{!s}'.format(__name__, chr(64+channel), e))
    
    def set_bias_mode(self, mode, channel=1):
        """
        Sets bias mode of channel <channel> to mode <mode>.
        
        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        mode: int
            Bias mode. Must be 0 (current) or 1 (voltage).
        
        Returns
        -------
        None
        """
        # Corresponding Command: smuX.source.func = 0|1|smuX.OUTPUT_DCAMPS|smuX.OUTPUT_DCVOLTS
        try:
            logging.debug('{:s}: Set bias mode of channel {:s} to {:d}'.format(__name__, chr(64+channel), mode))
            self._write('smu{:s}.source.func = {:d}'.format(chr(96+channel), mode))
        except Exception as e:
            logging.error('{!s}: Cannot set bias mode of channel {!s} to {!s}'.format(__name__, chr(64+channel), mode))
            raise type(e)('{!s}: Cannot set bias mode of channel {!s} to {!s}\n{!s}'.format(__name__, chr(64+channel), mode, e))
        return
    
    def get_bias_mode(self, channel=1):
        """
        Gets bias mode <mode> of channel <channel>.
        
        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        
        Returns
        -------
        mode: int
            Bias mode. Meanings are 0 (current) and 1 (voltage).
        """
        # Corresponding Command: 0|1|smuX.OUTPUT_DCAMPS|smuX.OUTPUT_DCVOLTS = smuX.source.func
        try:
            logging.debug('{:s}: Get bias mode of channel {:s}'.format(__name__, chr(64+channel)))
            return int(float(self._ask('smu{:s}.source.func'.format(chr(96+channel)))))
        except Exception as e:
            logging.error('{!s}: Cannot get bias mode of channel {!s}'.format(__name__, chr(64+channel)))
            raise type(e)('{!s}: Cannot get bias mode of channel {!s}\n{!s}'.format(__name__, chr(64+channel), e))
    
    def set_sense_mode(self, mode, channel=1):
        """
        Sets sense mode of channel <channel> to mode <mode>.
        
        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        mode: int
            Sense mode. Must be 0 (current), 1 (voltage), 2 (resistance) or 3 (power).
        
        Returns
        -------
        None
        """
        # Corresponding Command: display.smuX.measure.func = 0|1|2|3|display.MEASURE_DCAMPS|display.MEASURE_DCVOLTS|display.MEASURE_OHMS|display.MEASURE_WATTS
        try:
            logging.debug('{:s}: Set sense mode of channel {:s} to {:d}'.format(__name__, chr(64+channel), mode))
            self._write('display.smu{:s}.measure.func = {:d}'.format(chr(96+channel), mode))
        except Exception as e:
            logging.error('{!s}: Cannot set sense mode of channel {!s} to {!s}'.format(__name__, chr(64+channel), mode))
            raise type(e)('{!s}: Cannot set sense mode of channel {!s} to {!s}\n{!s}'.format(__name__, chr(64+channel), mode, e))
        return
    
    def get_sense_mode(self, channel=1):
        """
        Gets sense mode <mode> of channel <channel>.
        
        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        
        Returns
        -------
        mode: int
            Sense mode. Meanings are 0 (current), 1 (voltage), 2 (resistance) and 3 (power).
        """
        # Corresponding Command: 0|1|2|3|display.MEASURE_DCAMPS|display.MEASURE_DCVOLTS|display.MEASURE_OHMS|display.MEASURE_WATTS = display.smuX.measure.func
        try:
            logging.debug('{:s}: Get sense mode of channel {:s}'.format(__name__, chr(64+channel)))
            return int(float(self._ask('display.smu{:s}.measure.func'.format(chr(96+channel)))))
        except Exception as e:
            logging.error('{!s}: Cannot get sense mode of channel {!s}'.format(__name__, chr(64+channel)))
            raise type(e)('{!s}: Cannot get sense mode of channel {!s}\n{!s}'.format(__name__, chr(64+channel), e))
    
    def set_bias_range(self, val, channel=1):
        """
        Sets bias range of channel <channel> to <val>.
        
        Parameters
        ----------
        val: float
            Bias range. Possible values are -1 (auto), for currents 100pA, 1nA, 10nA, 100nA, 1uA, 10uA, 100uA, 1mA, 10mA, 100mA, 1 A, 1.5A and for voltages 200mV, 2V, 20V, 200V.
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        
        Returns
        -------
        None
        """
        # Corresponding Command: smuX.source.rangeY = rangeValue
        # Corresponding Command: smuX.source.autorangeY = 0|1|smuX.AUTORANGE_OFF|smuX.AUTORANGE_ON
        try:
            logging.debug('{:s}: Set bias range of channel {:s} to {:f}'.format(__name__, chr(64+channel), val))
            if val == -1:
                self._write('smu{:s}.source.autorange{:s} = 1'.format(chr(96+channel), self._smu_command[self.get_bias_mode(channel=channel)]))
            else:
                self._write('smu{:s}.source.autorange{:s} = 0'.format(chr(96+channel), self._smu_command[self.get_bias_mode(channel=channel)]))
                self._write('smu{:s}.source.range{:s} = {:f}'.format(chr(96+channel), self._smu_command[self.get_bias_mode(channel=channel)], val))
        except Exception as e:
            logging.error('{!s}: Cannot set bias range of channel {!s} to {!s}'.format(__name__, chr(64+channel), val))
            raise type(e)('{!s}: Cannot set bias range of channel {!s} to {!s}\n{!s}'.format(__name__, chr(64+channel), val, e))
        return
    
    def get_bias_range(self, channel=1):
        """
        Gets bias mode <val> of channel <channel>.
        
        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        
        Returns
        -------
        val: float
            Bias range.
        """
        # Corresponding Command: rangeValue = smuX.source.rangeY
        try:
            logging.debug('{:s}: Get bias range of channel {:s}'.format(__name__, chr(64+channel)))
            return float(self._ask('smu{:s}.source.range{:s}'.format(chr(96+channel), self._smu_command[self.get_bias_mode(channel=channel)])))
        except Exception as e:
            logging.error('{!s}: Cannot get bias range of channel {!s}'.format(__name__, chr(64+channel)))
            raise type(e)('{!s}: Cannot get bias range of channel {!s}\n{!s}'.format(__name__, chr(64+channel), e))
    
    def set_bias_limit(self, val, channel=1):
        """
        Sets bias limit of channel <channel> to <val>.
        Note that the 200V range requires the interlock to be enabled: pull high pin 24 (e.g. by shorting with pin 23) of the digital I/O port.
        
        Parameters
        ----------
        val: float
            Compliance limits. Possible values for currents are 0 < <val> < 1.5A and for voltages are 0 < <val> < 200V.
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        
        Returns
        -------
        None
        """
        # Corresponding Command: smuX.source.limitY = limit
        try:
            logging.debug('{:s}: Set bias limit of channel {:s} to {:f}'.format(__name__, chr(64+channel), val))
            self._write('smu{:s}.source.limit{:s} = {:f}'.format(chr(96+channel), self._smu_command[self.get_bias_mode(channel=channel)], val))
        except Exception as e:
            logging.error('{!s}: Cannot set bias limit of channel {!s} to {!s}'.format(__name__, chr(64+channel), val))
            raise type(e)('{!s}: Cannot set bias limit of channel {!s} to {!s}\n{!s}'.format(__name__, chr(64+channel), val, e))
        return
    
    def get_bias_limit(self, channel=1):
        """
        Gets bias limit <val> of channel <channel>.
        
        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        
        Returns
        -------
        val: float
            Compliance limits.
        """
        # Corresponding Command: limit = smuX.source.limitY
        try:
            logging.debug('{:s}: Get bias limit of channel {:s}'.format(__name__, chr(64+channel)))
            return float(self._ask('smu{:s}.source.limit{:s}'.format(chr(96+channel), self._smu_command[self.get_bias_mode(channel=channel)])))
        except Exception as e:
            logging.error('{!s}: Cannot get bias limit of channel {!s}'.format(__name__, chr(64+channel)))
            raise type(e)('{!s}: Cannot get bias limit of channel {!s}\n{!s}'.format(__name__, chr(64+channel), e))
    
    def set_sense_range(self, val, channel=1):
        """
        Sets sense range of channel <channel> to <val>.
        
        Parameters
        ----------
        val: float
            Sense range. Possible values are -1 (auto), for currents 100pA, 1nA, 10nA |100nA, 1uA, 10uA, 100uA, 1mA, 10mA, 100mA, 1 A, 1.5A and for voltages 200mV, 2V, 20V, 200V.
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        
        Returns
        -------
        None
        """
        # Corresponding Command: smuX.measure.rangeY = rangeValue
        # Corresponding Command: smuX.measure.autorangeY = 0|1|2|smuX.AUTORANGE_OFF|smuX.AUTORANGE_ON|smuX.AUTORANGE_FOLLOW_LIMIT
        try:
            logging.debug('{:s}: Set sense range of channel {:s} to {:f}'.format(__name__, chr(64+channel), val))
            if val == -1:
                self._write('smu{:s}.measure.autorange{:s} = 1'.format(chr(96+channel), self._smu_command[self.get_sense_mode(channel=channel)]))
            else:
                self._write('smu{:s}.measure.autorange{:s} = 0'.format(chr(96+channel), self._smu_command[self.get_sense_mode(channel=channel)]))
                self._write('smu{:s}.measure.range{:s} = {:f}'.format(chr(96+channel), self._smu_command[self.get_sense_mode(channel=channel)], val))
        except Exception as e:
            logging.error('{!s}: Cannot set sense range of channel {!s} to {!s}'.format(__name__, chr(64+channel), val))
            raise type(e)('{!s}: Cannot set sense range of channel {!s} to {!s}\n{!s}'.format(__name__, chr(64+channel), val, e))
        return
    
    def get_sense_range(self, channel=1):
        """
        Gets sense mode <val> of channel <channel>.
        
        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        
        Returns
        -------
        val: float
            Sense range.
        """
        # Corresponding Command: rangeValue = smuX.measure.rangeY
        try:
            logging.debug('{:s}: Get sense range of channel {:s}'.format(__name__, chr(64+channel)))
            return float(self._ask('smu{:s}.measure.range{:s}'.format(chr(96+channel), self._smu_command[self.get_sense_mode(channel=channel)])))
        except Exception as e:
            logging.error('{!s}: Cannot get sense range of channel {!s}'.format(__name__, chr(64+channel)))
            raise type(e)('{!s}: Cannot get sense range of channel {!s}\n{!s}'.format(__name__, chr(64+channel), e))
    
    def set_bias_delay(self, val, channel=1):
        """
        Sets bias delay of channel <channel> to <val>.
        
        Parameters
        ----------
        val: float
            Bias delay with respect to the bias trigger. Possible values are -1 (auto), 0 (off) or positive numbers.
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        
        Returns
        -------
        None
        """
        # Corresponding Command: smuX.source.delay = 0|1|smuX.DELAY_OFF|muX.DELAY_AUTO|sDelay
        try:
            logging.debug('{:s}: Set bias delay of channel {:s} to {:f}'.format(__name__, chr(64+channel), val))
            self._write('smu{:s}.source.delay = {:f}'.format(chr(96+channel), val))
        except Exception as e:
            logging.error('{!s}: Cannot set bias delay of channel {!s} to {!s}'.format(__name__, chr(64+channel), val))
            raise type(e)('{!s}: Cannot set bias delay of channel {!s} to {!s}\n{!s}'.format(__name__, chr(64+channel), val, e))
        return
    
    def get_bias_delay(self, channel=1):
        """
        Gets bias delay <val> of channel <channel>.
        
        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        
        Returns
        -------
        val: float
            Bias delay with respect to the bias trigger.
        """
        # Corresponding Command: 0|1|smuX.DELAY_OFF|muX.DELAY_AUTO|sDelay = smuX.source.delay
        try:
            logging.debug('{:s}: Get bias delay of channel {:s}'.format(__name__, chr(64+channel)))
            return float(self._ask('smu{:s}.source.delay'.format(chr(96+channel))))
        except Exception as e:
            logging.error('{!s}: Cannot get bias delay of channel {!s}'.format(__name__, chr(64+channel)))
            raise type(e)('{!s}: Cannot get bias delay of channel {!s}\n{!s}'.format(__name__, chr(64+channel), e))
    
    def set_sense_delay(self, val, channel=1, **kwargs):
        """
        Sets sense delay of channel <channel> to <val>.
        
        Parameters
        ----------
        val: float
            Sense delay with respect to the sense trigger. Possible values are -1 (auto), 0 (off) or positive numbers.
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        factor: float, optional
            Multiplier to the delays if auto delay is used. Default is 1.
        
        Returns
        -------
        None
        """
        # Corresponding Command: smuX.measure.delay = 0|1|smuX.DELAY_OFF|muX.DELAY_AUTO|mDelay
        # Corresponding Command: smuX.measure.delayfactor = delayFactor
        try:
            logging.debug('{:s}: Set sense delay of channel {:s} to {:f}'.format(__name__, chr(64+channel), val))
            self._write('smu{:s}.measure.delay = {:f}'.format(chr(96+channel), val))
            if val == -1:
                self._write('smu{:s}.measure.delayfactor = {:f}'.format(chr(96+channel), kwargs.get('factor', 1)))
        except Exception as e:
            logging.error('{!s}: Cannot set sense delay of channel {!s} to {!s}'.format(__name__, chr(64+channel), val))
            raise type(e)('{!s}: Cannot set sense delay of channel {!s} to {!s}\n{!s}'.format(__name__, chr(64+channel), val, e))
        return
    
    def get_sense_delay(self, channel=1):
        """
        Gets sense delay <val> of channel <channel>.
        
        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        
        Returns
        -------
        val: float
            Sense delay with respect to the sense trigger.
        """
        # Corresponding Command: 0|1|smuX.DELAY_OFF|muX.DELAY_AUTO|mDelay= smuX.measure.delay
        try:
            logging.debug('{:s}: Get sense delay of channel {:s}'.format(__name__, chr(64+channel)))
            return float(self._ask('smu{:s}.measure.delay'.format(chr(96+channel))))
        except Exception as e:
            logging.error('{!s}: Cannot get sense delay of channel {!s}'.format(__name__, chr(64+channel)))
            raise type(e)('{!s}: Cannot get sense delay of channel {!s}\n{!s}'.format(__name__, chr(64+channel), e))
    
    def set_sense_average(self, val, channel=1, **kwargs):
        """
        Sets sense average of channel <channel> to <val>.
        
        Parameters
        ----------
        val: int
            Number of measured readings that are required to yield one filtered measurement. Must be in [1, 100].
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        mode: str
            Type of filter used for measurements when the measurement filter is enabled. Possible values are 0 (moving average) | 1 (repeat average) | 2 (median). Default is 1.
        
        Returns
        -------
        None
        """
        # Corresponding Command: smuX.measure.filter.count = filterCount
        # Corresponding Command: smuX.measure.filter.enable = 0|1|smuX.FILTER_OFF|smuX.FILTER_ON
        # Corresponding Command: smuX.measure.filter.type = 0|1|2|smuX.FILTER_MOVING_AVG|smuX.FILTER_REPEAT_AVG|smuX.FILTER_MEDIAN
        try:
            mode = kwargs.get('mode', 1)
            logging.debug('{:s}: Set sense average of channel {:s} to {:d} and mode {:s}'.format(__name__, chr(64+channel), val, self._avg_types[mode]))
            status = not(.5*(1-np.sign(val-1)))  # equals Heaviside(1-<val>) --> turns on for <val> >= 2
            self._write('smu{:s}.measure.filter.enable = {:d}'.format(chr(96+channel), status))
            if status:
                self._write('smu{:s}.measure.filter.count = {:d}'.format(chr(96+channel), val))
                self._write('smu{:s}.measure.filter.type = {:d}'.format(chr(96+channel), mode))
        except Exception as e:
            logging.error('{!s}: Cannot set sense average of channel {!s} to {!s}'.format(__name__, chr(64+channel), val))
            raise type(e)('{!s}: Cannot set sense average of channel {!s} to {!s}\n{!s}'.format(__name__, chr(64+channel), val, e))
        return
    
    def get_sense_average(self, channel=1):
        """
        Gets sense average status <status>, value <val> and mode <mode> of channel <channel>.
        
        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        
        Returns
        -------
        status: bool
            Status if the measurement filter is enabled.
        val: int
            Number of measured readings that are required to yield one filtered measurement.
        mode: str
            Type of filter used for measurements when the measurement filter is enabled. Meanings are 0 (moving average) | 1 (repeat average) | 2 (median).
        """
        # Corresponding Command: filterCount = smuX.measure.filter.count
        # Corresponding Command: 0|1|smuX.FILTER_OFF|smuX.FILTER_ON = smuX.measure.filter.enable
        # Corresponding Command: 0|1|2|smuX.FILTER_MOVING_AVG|smuX.FILTER_REPEAT_AVG|smuX.FILTER_MEDIAN = smuX.measure.filter.type
        try:
            logging.debug('{:s}: Get sense average of channel {:s}'.format(__name__, chr(64+channel)))
            status = bool(int(float(self._ask('smu{:s}.measure.filter.enable'.format(chr(96+channel))))))
            val = int(float(self._ask('smu{:s}.measure.filter.count'.format(chr(96+channel)))))
            mode = int(float(self._ask('smu{:s}.measure.filter.type'.format(chr(96+channel)))))
            return status, val, mode
        except Exception as e:
            logging.error('{!s}: Cannot get sense average of channel {!s}'.format(__name__, chr(64+channel)))
            raise type(e)('{!s}: Cannot get sense average of channel {!s}\n{!s}'.format(__name__, chr(64+channel), e))
    
    def set_plc(self, val):
        """
        Sets power line cycle (PLC) to <val>.
        
        Parameters
        ----------
        plc: int
            Power line frequency setting used for NPLC calculations. Possible values are -1 (auto) | 50 | 60.
        
        Returns
        -------
        None
        """
        # Corresponding Command: localnode.linefreq = frequency
        # Corresponding Command: localnode.autolinefreq = flag
        try:
            logging.debug('{:s}: Set PLC to {:s}'.format(__name__, str(val)))
            cmd = {-1: 'autolinefreq = true', 50: 'linefreq = 50', 60: 'linefreq = 60'}
            self._write('localnode.{:s}'.format(cmd[int(val)]))
        except Exception as e:
            logging.error('{!s}: Cannot set PLC to {!s}'.format(__name__, val))
            raise type(e)('{!s}: Cannot set PLC to {!s}\n{!s}'.format(__name__, val, e))
        return
    
    def get_plc(self):
        """
        Gets power line cycle (PLC) <val>.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        plc: int
            Power line frequency setting used for NPLC calculations.
        """
        # Corresponding Command: frequency = localnode.linefreq
        # Corresponding Command: flag = localnode.autolinefreq
        try:
            logging.debug('{:s}: Get PLC')
            return float(self._ask('localnode.linefreq'))
        except Exception as e:
            logging.error('{!s}: Cannot get PLC'.format(__name__))
            raise type(e)('{!s}: Cannot get PLC\n{!s}'.format(__name__, e))
    
    def set_sense_nplc(self, val, channel=1):
        """
        Sets sense nplc (number of power line cycle) of channel <channel> with the <val>-fold of one power line cycle.
        
        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        val: float
            Integration aperture for measurements. Must be in [0.001, 25].
        
        Returns
        -------
        None
        """
        # Corresponding Command: smuX.measure.nplc = nplc
        try:
            logging.debug('{:s}: Set sense nplc of channel {:s} to {:f} PLC'.format(__name__, chr(64+channel), val))
            self._write('smu{:s}.measure.nplc = {:f}'.format(chr(96+channel), val))
        except Exception as e:
            logging.error('{!s}: Cannot set sense nplc of channel {!s} to {!s}'.format(__name__, chr(64+channel), val))
            raise type(e)('{!s}: Cannot set sense nplc of channel {!s} to {!s}\n{!s}'.format(__name__, chr(64+channel), val, e))
        return
    
    def get_sense_nplc(self, channel=1):
        """
        Gets sense nplc (number of power line cycle) <val> of channel <channel>.
        
        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        
        Returns
        -------
        val: float
            Integration aperture for measurements.
        """
        # Corresponding Command: nplc = smuX.measure.nplc
        try:
            logging.debug('{:s}: Get sense nplc of channel {:s}'.format(__name__, chr(64+channel)))
            return float(self._ask('smu{:s}.measure.nplc'.format(chr(96+channel))))
        except Exception as e:
            logging.error('{!s}: Cannot get sense nplc of channel {!s}'.format(__name__, chr(64+channel)))
            raise type(e)('{!s}: Cannot get sense nplc of channel {!s}\n{!s}'.format(__name__, chr(64+channel), e))
    
    def set_sense_autozero(self, val, channel=1):
        """
        Sets autozero of channel <channel> to <val>. Note that "on" means that the internal zero point is measured for each measurement, wherefore the measurement takes approximately twice as long as when the auto zero function is "off"
        
        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        val: int
            Status of the internal reference measurements (autozero) of the source-measure unit. Possible values are 0 (off), 1 (on) or 2 (once).
        
        Returns
        -------
        None
        """
        # Corresponding Command: smuX.measure.autozero = azMode
        #                        azMode: 0 (off) | 1 (once) | 2 (at each measurement)
        val = 3*int(bool(val))-val  # swap 1 and 2
        try:
            logging.debug('{:s}: Set sense autozero of channel {:s} to {:d}'.format(__name__, chr(64+channel), val))
            self._write('smu{:s}.measure.autozero = {:d}'.format(chr(96+channel), val))
        except Exception as e:
            logging.error('{!s}: Cannot set sense autozero of channel {!s} to {!s}'.format(__name__, chr(64+channel), val))
            raise type(e)('{!s}: Cannot set sense autozero of channel {!s} to {!s}\n{!s}'.format(__name__, chr(64+channel), val, e))
        return
    
    def get_sense_autozero(self, channel=1):
        """
        Gets sense autozero <val> of channel <channel>.
        
        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        
        Returns
        -------
        val: int
            Status of the internal reference measurements (autozero) of the source-measure unit. Meanings are 0 (off), 1 (on) and 2 (once).
        """
        # Corresponding Command: azMode = smuX.measure.autozero
        #                        azMode: 0 (off) | 1 (once) | 2 (at each measurement)
        try:
            logging.debug('{:s}: Get sense autozero of channel {:s}'.format(__name__, chr(64+channel)))
            val = int(float(self._ask('smu{:s}.measure.autozero'.format(chr(96+channel)))))
            return 3*int(bool(val))-val  # swap 1 and 2
        except Exception as e:
            logging.error('{!s}: Cannot get sense autozero of channel {!s}'.format(__name__, chr(64+channel)))
            raise type(e)('{!s}: Cannot get sense autozero of channel {!s}\n{!s}'.format(__name__, chr(64+channel), e))
    
    def set_status(self, status, channel=1):
        """
        Sets output status of channel <channel> to <status>.
        
        Parameters
        ----------
        status: int
            Output status. Possible values are 0 (off), 1 (on) or 2 (high Z).
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        
        Returns
        -------
        None
        """
        # Corresponding Command: smuX.source.output = 0|1|2|smuX.OUTPUT_OFF|smuX.OUTPUT_ON|smuX.OUTPUT_HIGH_Z
        try:
            logging.debug('{:s}: Set output status of channel {:s} to {:d}'.format(__name__, chr(64+channel), status))
            self._write('smu{:s}.source.output = {:d}'.format(chr(96+channel), status))
        except Exception as e:
            logging.error('{!s}: Cannot set output status of channel {!s} to {!s}'.format(__name__, chr(64+channel), status))
            raise type(e)('{!s}: Cannot set output status of channel {!s} to {!s}\n{!s}'.format(__name__, chr(64+channel), status, e))
        return
    
    def get_status(self, channel=1):
        """
        Gets output status <status> of channel <channel>.
        
        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        
        Returns
        -------
        status: int
            Output status. Meanings are 0 (off), 1 (on) and 2 (high Z).
        """
        # Corresponding Command: 0|1|2|smuX.OUTPUT_OFF|smuX.OUTPUT_ON|smuX.OUTPUT_HIGH_Z = smuX.source.output
        try:
            logging.debug('{:s}: Get output status of channel {:s}'.format(__name__, chr(64+channel)))
            return int(float(self._ask('smu{:s}.source.output'.format(chr(96+channel)))))
        except Exception as e:
            logging.error('{!s}: Cannot get output status of channel {!s}'.format(__name__, chr(64+channel)))
            raise type(e)('{!s}: Cannot get output status of channel {!s}\n{!s}'.format(__name__, chr(64+channel), e))
    
    def set_bias_value(self, val, channel=1):
        """
        Sets bias value of channel <channel> to value <val>.
        
        Parameters
        ----------
        val: float
            Bias value.
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        
        Returns
        -------
        None
        """
        # Corresponding Command: smuX.source.levelY = sourceLevel
        try:
            logging.debug('{:s}: Set bias value of channel {:s} to {:f}'.format(__name__, chr(64+channel), val))
            self._write('smu{:s}.source.level{:s} = {:f}'.format(chr(96+channel), self._smu_command[self.get_bias_mode(channel=channel)], val))
        except Exception as e:
            logging.error('{!s}: Cannot set bias value of channel {!s} to {!s}'.format(__name__, chr(64+channel), val))
            raise type(e)('{!s}: Cannot set bias value of channel {!s} to {!s}\n{!s}'.format(__name__, chr(64+channel), val, e))
        return
    
    def get_bias_value(self, channel=1):
        """
        Gets bias value <val> of channel <channel>.
        
        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        
        Returns
        -------
        val: float
            Bias value.
        """
        # Corresponding Command: sourceLevel = smuX.source.levelY
        try:
            logging.debug('{:s}: Get bias value of channel {:s}'.format(__name__, chr(64+channel)))
            return float(self._ask('smu{:s}.source.level{:s}'.format(chr(96+channel), self._smu_command[self.get_bias_mode(channel=channel)])))
        except Exception as e:
            logging.error('{!s}: Cannot get bias value of channel {!s}'.format(__name__, chr(64+channel)))
            raise type(e)('{!s}: Cannot get bias value of channel {!s}\n{!s}'.format(__name__, chr(64+channel), e))
        return
    
    def get_sense_value(self, channel=1, readingbuffer=None):
        """
        Gets sense value of channel <channel>.
        
        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        readingbuffer: str
            Reading buffer object where all readings will be stored
        
        Returns
        -------
        val: float
            Sense value.
        """
        # Corresponding Command: reading= smuX.measure.Y()
        # Corresponding Command: reading = smuX.measure.Y(readingbuffer)
        try:
            logging.debug('{:s}: Get sense value of channel {:s}'.format(__name__, chr(64+channel)))
            return float(self._ask('smu{:s}.measure.{:s}({:s})'.format(chr(96+channel), self._smu_command[self.get_sense_mode(channel=channel)], readingbuffer if readingbuffer is not None else '')))
        except Exception as e:
            logging.error('{!s}: Cannot get sense value of channel {!s}'.format(__name__, chr(64+channel)))
            raise type(e)('{!s}: Cannot get sense value of channel {!s}\n{!s}'.format(__name__, chr(64+channel), e))
    
    def set_voltage(self, val, channel=1):
        """
        Sets voltage value of channel <channel> to <val>.
        
        Parameters
        ----------
        val: float
            Bias voltage value.
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        
        Returns
        -------
        None
        """
        # Corresponding Command: smuX.source.levelY = sourceLevel
        try:
            logging.debug('{:s}: Set voltage value of channel {:s} to {:f}'.format(__name__, chr(64+channel), val))
            self._write('smu{:s}.source.levelv = {:f}'.format(chr(96+channel), val))
        except Exception as e:
            logging.error('{!s}: Cannot set voltage value of channel {!s} to {!s}'.format(__name__, chr(64+channel), val))
            raise type(e)('{!s}: Cannot set voltage value of channel {!s} to {!s}\n{!s}'.format(__name__, chr(64+channel), val, e))
        return
    
    def get_voltage(self, channel=1, readingbuffer=None):
        """
        Gets voltage value <val> of channel <channel>.
        
        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        readingbuffer: str
            Reading buffer object where all readings will be stored
        
        Returns
        -------
        val: float
            Sense voltage value.
        """
        # Corresponding Command: reading = smuX.measure.Y()
        # Corresponding Command: reading = smuX.measure.Y(readingbuffer)
        try:
            logging.debug('{:s}: Get voltage value of channel {:s}'.format(__name__, chr(64+channel)))
            return float(self._ask('smu{:s}.measure.v({:s})'.format(chr(96+channel), readingbuffer if readingbuffer is not None else '')))
        except Exception as e:
            logging.error('{!s}: Cannot get voltage value of channel {!s}'.format(__name__, chr(64+channel)))
            raise type(e)('{!s}: Cannot get voltage value of channel {!s}\n{!s}'.format(__name__, chr(64+channel), e))
    
    def set_current(self, val, channel=1):
        """
        Sets current value of channel <channel> to <val>.
        
        Parameters
        ----------
        val: float
            Bias current value.
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        
        Returns
        -------
        None
        """
        # Corresponding Command: smuX.source.levelY = sourceLevel
        try:
            logging.debug('{:s}: Set current value of channel {:s} to {:f}'.format(__name__, chr(64+channel), val))
            self._write('smu{:s}.source.leveli = {:f}'.format(chr(96+channel), val))
        except Exception as e:
            logging.error('{!s}: Cannot set current value of channel {!s} to {!s}'.format(__name__, chr(64+channel), val))
            raise type(e)('{!s}: Cannot set current value of channel {!s} to {!s}\n{!s}'.format(__name__, chr(64+channel), val, e))
        return
    
    def get_current(self, channel=1, readingbuffer=None):
        """
        Gets current value <val> of channel <channel>.
        
        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        readingbuffer: str
            Reading buffer object where all readings will be stored
        
        Returns
        -------
        val: float
            Sense current value.
        """
        # Corresponding Command: reading = smuX.measure.Y()
        # Corresponding Command: reading = smuX.measure.Y(readingbuffer)
        try:
            logging.debug('{:s}: Get current value of channel {:s}'.format(__name__, chr(64+channel)))
            return float(self._ask('smu{:s}.measure.i({:s})'.format(chr(96+channel), readingbuffer if readingbuffer is not None else '')))
        except Exception as e:
            logging.error('{!s}: Cannot get current value of channel {!s}'.format(__name__, chr(64+channel)))
            raise type(e)('{!s}: Cannot get current value of channel {!s}\n{!s}'.format(__name__, chr(64+channel), e))
        return
    
    def get_IV(self, channel=1, *readingbuffer):
        """
        Gets both current value <I_val> and voltage value <V_val> of channel <channel>.
        
        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        readingbuffer: str
            Reading buffer object where current (1st entry) and voltage (2nd entry) readings will be stored.
        
        Returns
        -------
        I_val: float
            Sense current value.
        V_val: float
            Sense voltage value.
        """
        # Corresponding Command: iReading, vReading= smuX.measure.iv()
        # Corresponding Command: iReading, vReading = smuX.measure.iv(ireadingbuffer)
        # Corresponding Command: iReading, vReading = smuX.measure.iv(ireadingbuffer, vreadingbuffer)
        try:
            logging.debug('{:s}: Get current and voltage sense value of channel {:s}'.format(__name__, chr(64+channel)))
            return np.array([float(val) for val in self._ask('smu{:s}.measure.iv{:s}'.format(chr(96+channel), readingbuffer).replace(',)', ')')).split('\t')])
        except Exception as e:
            logging.error('{!s}: Cannot get current and voltage sense value of channel {!s}'.format(__name__, chr(64+channel)))
            raise type(e)('{!s}: Cannot get current and voltage sense value of channel {!s}\n{!s}'.format(__name__, chr(64+channel), e))
    
    def ramp_bias(self, stop, step, step_time=0.1, channel=2):
        """
        Ramps bias value of channel <channel> from recent value to stop value <stop> with step size <step> and step time <step_time>.
        
        Parameters
        ----------
        stop: float
            Stop value
        step: float
            Step size.
        step_time: float
            Sleep time between staircase ramp.
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1. (default)
        
        Returns
        -------
        None
        """
        start = self.get_bias_value(channel=channel)
        if stop < start:
            step = -step
        for val in np.arange(start, stop, step)+step:
            self.set_bias_value(val, channel=channel)
            print('{:f}{:s}'.format(val, self._IV_units[self.get_bias_mode()]), end='\r')
            time.sleep(step_time)
    
    def ramp_voltage(self, stop, step, step_time=0.1, channel=1):
        """
        Ramps voltage of channel <channel> from recent value to stop value <stop> with step size <step> and step time <step_time> according to bias_mode.
        
        Parameters
        ----------
        stop: float
            Stop voltage value
        step: float
            Step voltage size.
        step_time: float
            Sleep time between voltage staircase ramp.
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1. (default)
        
        Returns
        -------
        None
        """
        if self.get_bias_mode(channel=channel):  # 1 (voltage bias)
            return self.ramp_bias(stop=stop, step=step, step_time=step_time, channel=channel)
        elif not self.get_bias_mode(channel=channel):  # 0 (current bias)
            logging.error(__name__ + ': Cannot set voltage value of channel {!s}: in the current bias'.format(channel))
            return
    
    def ramp_current(self, stop, step, step_time=0.1, channel=1):
        """
        Ramps current of channel <channel> from recent value to stop value <stop> with step size <step> and step time <step_time> according to bias_mode.
        
        Parameters
        ----------
        stop: float
            Stop current value
        step: float
            Step current size.
        step_time: float
            Sleep time between current staircase ramp.
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1. (default)
        
        Returns
        -------
        None
        """
        if not self.get_bias_mode(channel=channel):  # 0 (current bias)
            return self.ramp_bias(stop=stop, step=step, step_time=step_time, channel=channel)
        elif self.get_bias_mode(channel=channel):  # 1 (voltage bias)
            logging.error(__name__ + ': Cannot ramp current value of channel {!s}: in the voltage bias'.format(channel))
    
    def set_sweep_mode(self, mode=1, *channels):
        """
        Sets an variable to decide weather
         * voltage is both applied and measured (VV-mode),
         * current is applied and voltage is measured (IV-mode) or
         * voltage is applied and current is measured (VI-mode)
        and channels <channels> that are used during sweeps.
        
        Parameters
        ----------
        mode: int
            Sweep mode denoting bias and sense modes. Possible values are 0 (VV-mode), 1 (IV-mode) or 2 (VI-mode). Default is 1
        channels: int or tuple(int)
            Number of channel of usage. Must be 1 or 2 for IV-mode and VI-mode or a tuple containing both channels for VV-mode (1st argument as bias channel and 2nd argument as sense channel).
            
        
        Returns
        -------
        None
        """
        default_channels = {0: (1, 2), 1: (1,), 2: (1,)}
        if mode in [0, 1, 2]:
            if len(channels) == int(not mode)+1:
                logging.debug('{!s}: Set sweep channels to {!s}'.format(__name__, channels))
                self._sweep_channels = channels
            elif len(channels) == 0:
                logging.debug('{!s}: Set sweep channels to {!s}'.format(__name__, default_channels[mode]))
                self._sweep_channels = default_channels[mode]
            else:
                logging.error('{!s}: Cannot set sweep channels to {!s}'.format(__name__, channels))
                raise ValueError('{!s}: Cannot set sweep channels to {!s}'.format(__name__, channels))
            logging.debug('{!s}: Set sweep mode to {:d}'.format(__name__, mode))
            self._sweep_mode = mode
            self.__set_defaults_docstring()
        else:
            logging.error('{!s}: Cannot set sweep mode to {!s}'.format(__name__, mode))
            raise ValueError('{!s}: Cannot set sweep mode to {!s}'.format(__name__, mode))
        return
    
    def get_sweep_mode(self):
        """
        Gets an internal variable <mode> to decide weather
         * voltage is both applied and measured (VV-mode),
         * current is applied and voltage is measured (IV-mode) or
         * voltage is applied and current is measured (VI-mode).
        
        Parameters
        ----------
        None
        
        Returns
        -------
        mode: int
            Sweep mode denoting bias and sense modes. Meanings are 0 (VV-mode), 1 (IV-mode) or 2 (VI-mode).
        """
        return self._sweep_mode
    
    def get_sweep_channels(self):
        """
        Gets channels <channels> that are used during sweeps. In the IV and VI sweep mode one channel requires for biasing and sensing, whereas two channels are returned in the VV sweep mode (1st as bias and 2nd as sense channel).
        
        Parameters
        ----------
        None
        
        Returns
        -------
        channels: int or tuple(int)
            Number of channel of usage. Meanings are 1 or 2 for IV-mode and VI-mode or a tuple containing both channels for VV-mode (1st argument as bias channel and 2nd argument as sense channel).
        """
        return self._sweep_channels
    
    def get_sweep_bias(self):
        """
        Calls get_bias_mode of channel <channel>. This method is needed for qkit.measure.transport.transport.py in case of no virtual tunnel electronic.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        mode: int
            Bias mode. Meanings are 0 (current) and 1 (voltage).
        """
        return self.get_bias_mode(self._sweep_channels[0])
    
    def create_readingbuffer(self, name, size, timestamps=None, channel=1):
        """
        Creates a new reading buffer with name <name> and maximal size <size>.
        
        Parameters
        ----------
        name: str
            Name of the created reading buffer.
        size: int
            Maximum number of readings that can be stored. Maximal value is for default reading buffers is 60 000, when the timestamps and source values options are enabled or over 140 000, when the timestamps and source values options are disabled.
        timestamps: bool
            Status if timestamp values are stored with the readings in the buffer. Default is None.
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        
        Returns
        -------
        """
        # Corresponding Command: bufferVar = smuX.makebuffer(bufferSize)
        # Corresponding Command: bufferVar.collecttimestamps = state
        try:
            logging.debug('{:s}: create reading buffer {:s} for channel {:s} with size {:d}'.format(__name__, name, chr(64+channel), size))
            self._write('{:s} = smu{:s}.makebuffer({:d})'.format(name, chr(96+channel), size))
        except Exception as e:
            logging.error('{:s}: Cannot create reading buffer {:s} for channel {:s} with size {:d}'.format(__name__, name, chr(64+channel), size))
            raise type(e)('{:s}: Cannot create reading buffer {:s} for channel {:s} with size {:d}'.format(__name__, name, chr(64+channel), size, e))
        if timestamps is not None:
            try:
                logging.debug('{:s}: Set timestamps of reading buffer {:s} to {!r}'.format(__name__, name, timestamps))
                self._write('{:s}.collecttimestamps = {!d}'.format(name, timestamps))
            except Exception as e:
                logging.error('{:s}: Cannot set timestamps of reading buffer {:s} to {!r}'.format(__name__, name, timestamps))
                raise type(e)('{:s}: Cannot set timestamps of reading buffer {:s} to {!r}'.format(__name__, name, timestamps, e))
        return
    
    def set_sweep_readingbuffer(self, readingbuffer_bias, readingbuffer_sense):
        """
        Sets reading buffer that is used during sweeps.
        
        Parameters
        ----------
         readingbuffer_bias: str
             Reading buffer object where all bias readings will be stored.
         readingbuffer_sense: str
             Reading buffer object where all sense readings will be stored.
        
        Returns
        -------
        None
        """
        self._readingbuffer_bias = readingbuffer_bias
        self._readingbuffer_sense = readingbuffer_sense
        return
    
    def set_sweep_parameters(self, sweep):
        """
        Sets sweep parameters <sweep> and prepares instrument for the set sweep mode.
        
        Parameters
        ----------
        sweep: array_likes of floats
            Sweep range containing start, stop and step size (e.g. sweep object using qkit.measure.transport.transport.sweep class)
        
        Returns
        -------
        None
        """
        # Corresponding Command: format.data = value
        # Corresponding Command: format.asciiprecision = precision
        # Corresponding Command: smuX.trigger.source.linearY(startValue, endValue, points)
        # Corresponding Command: smuX.trigger.source.action = action
        # Corresponding Command: smuX.trigger.measure.action = action
        # Corresponding Command: bufferVar.clear()
        # Corresponding Command: smuX.trigger.measure.iv(ibuffer, vbuffer)
        # Corresponding Command: smuX.trigger.count = triggerCount
        # Corresponding Command: smuX.trigger.arm.count = triggerArmCount
        try:
            self._write('format.data = format.ASCII')
            self._write('format.asciiprecision = 6')
            self._start, self._stop, self._step = np.array(sweep[:3], dtype=float)
            if not self._sweep_mode:  # 0 (VV-mode)
                channel_bias, channel_sense = self._sweep_channels
                readingbuffer_bias = 'smu{:s}.nvbuffer1'.format(chr(96+channel_bias)) if self._readingbuffer_bias is None else self._readingbuffer_bias
                readingbuffer_sense = 'smu{:s}.nvbuffer1'.format(chr(96+channel_sense)) if self._readingbuffer_sense is None else self._readingbuffer_sense
                self._step_signed = np.sign(self._stop-self._start)*np.abs(self._step)
                self.set_bias_value(val=self._start, channel=channel_bias)
                cmd =  '{:s}.clear()'.format(readingbuffer_bias)
                cmd += '{:s}.appendmode = 1'.format(readingbuffer_bias)
                cmd += '{:s}.clear()'.format(readingbuffer_sense)
                cmd += '{:s}.appendmode = 1'.format(readingbuffer_sense)
            elif self._sweep_mode in [1, 2]:  # 1 (IV-mode) | 2 (VI-mode)
                channel, = self._sweep_channels
                readingbuffer_bias = 'smu{:s}.nvbuffer1'.format(chr(96+channel)) if self._readingbuffer_bias is None else self._readingbuffer_bias
                readingbuffer_sense = 'smu{:s}.nvbuffer2'.format(chr(96+channel)) if self._readingbuffer_sense is None else self._readingbuffer_sense
                self._nop = int(np.abs((self._stop-self._start)/self._step)+1)
                cmd =  'smu{:s}.trigger.source.linear{:s}({:f}, {:f}, {:d})'.format(chr(96+channel), self._smu_command[self.get_bias_mode(channel=channel)], self._start, self._stop, self._nop)
                cmd += 'smu{:s}.trigger.source.action = 1'.format(chr(96+channel))
                cmd += 'smu{:s}.trigger.measure.action = 1'.format(chr(96+channel))
                cmd += '{:s}.clear()'.format(readingbuffer_bias)
                cmd += '{:s}.clear()'.format(readingbuffer_sense)
                cmd += 'smu{:s}.trigger.measure.iv({:s}, {:s})'.format(chr(96+channel), *[readingbuffer_bias, readingbuffer_sense][::int(2*(1.5-self._sweep_mode))])
                cmd += 'smu{:s}.trigger.count = {:d}'.format(chr(96+channel), self._nop)
                cmd += 'smu{:s}.trigger.arm.count = 1'.format(chr(96+channel))
            else:
                logging.error('{:s}: Cannot set sweep parameters in sweep mode {!s}'.format(__name__, self._sweep_mode))
                raise AttributeError('{:s}: Cannot set sweep parameters in sweep mode {!s}'.format(__name__, self._sweep_mode))
            self._visainstrument.write(cmd)
            self._prepare_stb('status.OSB')
            time.sleep(1e-3)
        except Exception as e:
            logging.error('{!s}: Cannot set sweep parameters of channel {:s} to {!s}'.format(__name__, self._sweep_channels, sweep))
            raise type(e)('{!s}: Cannot set sweep parameters of channel {:s} to {!s}\n{!s}'.format(__name__, self._sweep_channels, sweep, e))
        return
    
    def get_tracedata(self):
        """
        Starts bias sweep with already set parameters and gets trace data of bias <bias_values> and sense <sense_values> in the set sweep mode.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        bias_values: numpy.array(float)
            Measured bias values.
        sense_values: numpy.array(float)
            Measured sense values.
        """
        # Corresponding Command: bufferVar.clear()
        # Corresponding Command: bufferVar.appendmode = state
        # Corresponding Command: smuX.source.levelY = sourceLevel
        # Corresponding Command: reading = smuX.measure.Y(readingbuffer)
        # Corresponding Command: numberOfReadings = bufferVar.n
        # Corresponding Command: smuX.trigger.initiate()
        # Corresponding Command: waitcomplete()
        try:
            if not self._sweep_mode:  # 0 (VV-mode)
                channel_bias, channel_sense = self._sweep_channels
                readingbuffer_bias = 'smu{:s}.nvbuffer1'.format(chr(96+channel_bias)) if self._readingbuffer_bias is None else self._readingbuffer_bias
                readingbuffer_sense = 'smu{:s}.nvbuffer1'.format(chr(96+channel_sense)) if self._readingbuffer_sense is None else self._readingbuffer_sense
                # sweep channel_bias and measure channel_sense
                cmd = 'for i = {:f}, {:f}, {:f} do'.format(self._start, self._stop+self._step_signed/2., self._step_signed)
                cmd += '\tsmu{:s}.source.levelv = i'.format(chr(96+channel_bias))
                cmd += '\tsmu{:s}.measure.v({:s})'.format(chr(96+channel_bias), readingbuffer_bias)
                cmd += '\tsmu{:s}.measure.v({:s})'.format(chr(96+channel_sense), readingbuffer_sense)
                cmd += 'end\n'
                self._visainstrument.write(cmd)
            elif self._sweep_mode in [1, 2]:  # 1 (IV-mode) | 2 (VI-mode)
                channel, = self._sweep_channels
                readingbuffer_bias = 'smu{:s}.nvbuffer1'.format(chr(96+channel)) if self._readingbuffer_bias is None else self._readingbuffer_bias
                readingbuffer_sense = 'smu{:s}.nvbuffer2'.format(chr(96+channel)) if self._readingbuffer_sense is None else self._readingbuffer_sense
                # sweep and measure channel
                self._visainstrument.write('smu{:s}.trigger.initiate()'.format(chr(96+channel)))
                self._visainstrument.write('waitcomplete()')
            self._wait_for_stb()
            time.sleep(0.1)
            # read data
            self._visainstrument.write('*CLS')
            self._prepare_stb('status.MAV')
            self._visainstrument.write('printbuffer(1, {:s}.n, {:s}, {:s})'.format(readingbuffer_bias, readingbuffer_bias, readingbuffer_sense))
            self._wait_for_stb()
            data = np.fromstring(string=self._visainstrument.read(), dtype=float, count=-1, sep=',')
            return data[0::2], data[1::2]
        except Exception as e:
            logging.error('{!s}: Cannot take sweep data of channel {:s}'.format(__name__, self._sweep_channels))
            raise type(e)('{!s}: Cannot take sweep data of channel {:s}\n{!s}'.format(__name__, self._sweep_channels, e))
    
    def take_IV(self, sweep):
        """
        Takes IV curve with sweep parameters <sweep> in set sweep mode.
        
        Parameters
        ----------
        sweep: array_likes of floats
            Sweep range containing start, stop and step size (e.g. sweep object using qkit.measure.transport.transport.sweep class)
        
        Returns
        -------
        bias_values: numpy.array(float)
            Measured bias values.
        sense_values: numpy.array(float)
            Measured sense values.
        """
        self.set_sweep_parameters(sweep=sweep)
        return self.get_tracedata()
    
    def _prepare_stb(self, stb):
        """
        Prepares status bit <stb> for high level query.
        
        Parameters
        ----------
        stb: str
            Status bit. Possible values are status.MSB (measurement summary bit), status.SSB (system summary bit), status.EAV (error available), status.QSB (questionable summary bit), status.MAV (meassage available), status.ESB (event summary bit), status.MSS (master summary bit), status.OSB (operation summary bit)
        
        Returns
        -------
        None
        """
        # Corresponding Command: status.reset()
        # Corresponding Command: status.operation.user.condition = operationRegister
        # Corresponding Command: status.operation.user.enable = operationRegister
        # Corresponding Command: status.operation.user.ptr = operationRegister
        # Corresponding Command: status.operation.enable = operationRegister
        # Corresponding Command: status.request_enable = requestSRQEnableRegister
        cmd = '''status.reset()
                 status.operation.user.condition = 0
                 status.operation.user.enable = status.operation.user.BIT0
                 status.operation.user.ptr = status.operation.user.BIT0
                 status.operation.enable = status.operation.USER
                 status.request_enable = {:s}'''.format(stb)
        return self._visainstrument.write(cmd)
    
    def _wait_for_stb(self, wait_time=1e-1):
        """
        Waits until the status bit occurs.
        
        Parameters
        ----------
        wait_time: float
            Sleep time between status bit queries.
        
        Returns
        -------
        None
        """
        # Corresponding Command: status.operation.user.condition = operationRegister
        self._visainstrument.write('status.operation.user.condition = status.operation.user.BIT0')
        self._read_stb()
        time.sleep(wait_time)
        while self._read_stb() == 0:
            time.sleep(wait_time)
        return
    
    def get_OPC(self):
        """
        Gets condition of standard event register entry "Operation complete" <val>.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        val: bool
            Operation complete of standard event register.
        """
        # Corresponding Command: *OPC
        try:
            logging.debug('''{!s}: Get ccr event "Operation complete"'''.format(__name__))
            return bool(int(self._ask('*OPC')))
        except Exception as e:
            logging.error('{!s}: Cannot get ccr condition "Operation complete"'.format(__name__))
            raise type(e)('{!s}: Cannot get ccr condition "Operation complete"\n{!s}'.format(__name__, e))
    
    def _wait_for_OPC(self):
        """
        Waits until the condition of standard event register entry "Operation complete" is fulfilled.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        """
        while not (self.get_OPC()):
            time.sleep(1e-3)
        return
    
    def set_defaults(self, sweep_mode=None):
        """
        Sets default settings that are:
        default parameters
        
        Parameters
        ----------
        mode: int
            Sweep mode denoting bias and sense modes. Possible values are 0 (VV-mode), 1 (IV-mode) or 2 (VI-mode). Default is 1
        
        Returns
        -------
        None
        """
        self.reset()
        # beeper off
        self._write('beeper.enable = 0')
        # distiguish different sweep modes
        if sweep_mode is not None:
            self.set_sweep_mode(sweep_mode)
        # set values
        for i, channel in enumerate(self._sweep_channels):
            for func, param in self._defaults[self._sweep_mode][i].items():
                func(param, channel=channel)
        return
    
    def __set_defaults_docstring(self):
        '''
        Sets docstring of "set_defaults" method with actual default settings.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        '''
        new = 'sweep mode: {:d}:\n'.format(self._sweep_mode) + ''.join(['\t    channel: {:d}\n'.format(channel) + ''.join(['\t\t{:s}: {!s}\n'.format(key_parameter, val_parameter) for key_parameter, val_parameter in self._defaults[self._sweep_mode][i].items()]) for i, channel in enumerate(self._sweep_channels)])
        self.set_defaults.__func__.__doc__ = self.set_defaults.__func__.__doc__.replace(self._default_str, new)
        self._default_str = new
        return
    
    def get_all(self, channel=1):
        """
        Prints all settings of channel <channel>.
        
        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        
        Returns
        -------
        None
        """
        logging.debug('{:s}: Get all'.format(__name__))
        print('measurement mode   = {:s}'.format(self._measurement_modes[self.get_measurement_mode(channel=channel)]))
        print('bias mode          = {:d}'.format(self.get_bias_mode(channel=channel)))
        print('sense mode         = {:d}'.format(self.get_sense_mode(channel=channel)))
        print('bias range         = {:1.0e}{:s}'.format(self.get_bias_range(channel=channel), self._IV_units[self.get_bias_mode(channel=channel)]))
        print('sense range        = {:1.0e}{:s}'.format(self.get_sense_range(channel=channel), self._IV_units[self.get_sense_mode(channel=channel)]))
        print('bias delay         = {:1.3e}s'.format(self.get_bias_delay(channel=channel)))
        print('sense delay        = {:1.3e}s'.format(self.get_sense_delay(channel=channel)))
        print('sense average      = {:f}'.format(self.get_sense_average(channel=channel)[1]))
        print('sense average type = {:s}'.format(self._avg_types[self.get_sense_average(channel=channel)[2]]))
        print('plc                = {:f}Hz'.format(self.get_plc()))
        print('sense nplc         = {:f}'.format(self.get_sense_nplc(channel=channel)))
        print('sense autozero     = {:f}'.format(self.get_sense_autozero(channel=channel)))
        print('status             = {!r}'.format(self.get_status(channel=channel)))
        print('bias value         = {:f}{:s}'.format(self.get_bias_value(channel=channel), self._IV_units[self.get_bias_mode(channel=channel)]))
        print('sense value        = {:f}{:s}'.format(self.get_sense_value(channel=channel), self._IV_units[self.get_sense_mode(channel=channel)]))
        for err in self.get_error():
            print('error\t\t   = {:d}\n\t\t     {:s}\n\t\t     {:d}'.format(err[0], err[1], err[2]))
        return
    
    def reset(self, channel=None):
        """
        Resets the instrument or a single channel to default conditions.
        
        Parameters
        ----------
        channel: int
            Number of channel to be set. Must be None, 1 or 2. Default is 1.
        
        Returns
        -------
        None
        """
        # Corresponding Command: reset()
        # Corresponding Command: smuX.reset()
        if channel is None:
            try:
                logging.debug('{!s}: Reset instrument to factory settings'.format(__name__))
                self._write('reset()')
                self._write('status.reset()')
            except Exception as e:
                logging.error('{!s}: Cannot reset instrument to factory settings'.format(__name__))
                raise type(e)('{!s}: Cannot reset instrument to factory settings\n{!s}'.format(__name__, e))
        else:
            try:
                logging.debug('{!s}: Reset channel {:s} to factory settings'.format(__name__, chr(64+channel)))
                self._write('smu{:s}.reset()'.format(chr(96+channel)))
            except Exception as e:
                logging.error('{!s}: Cannot reset channel {:s} to factory settings'.format(__name__, chr(64+channel)))
                raise type(e)('{!s}: Cannot reset channel {:s} to factory settings\n{!s}'.format(__name__, chr(64+channel), e))
        return
    
    def abort(self, channel=1):
        """
        Aborts the running command of channel <channel>.
        
        Parameters
        ----------
        channel: int
            Number of channel to be set. Must be None, 1 or 2. Default is 1.
        
        Returns
        -------
        None
        """
        # Corresponding Command: smuX.abort()
        try:
            logging.debug('{:s}: Abort running command of channel {:s}'.format(__name__, chr(64+channel)))
            return self._write('smu{:s}.abort()'.format(chr(96+channel)))
        except Exception as e:
            logging.error('{!s}: Cannot abort running command of channel {:s}'.format(__name__, chr(64+channel)))
            raise type(e)('{!s}: Cannot abort running command of channel {:s}\n{!s}'.format(__name__, chr(64+channel), e))
    
    def get_error(self):
        """
        Gets errors of instrument and removes them from the error queue.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        err: array of str
            Entries from the error queue
        """
        # Corresponding Command: errorCount = errorqueue.count
        # Corresponding Command: errorCode, message, severity, errorNode = errorqueue.next() 
        try:
            logging.debug('{!s}: Get errors of instrument'.format(__name__))
            err = [self._visainstrument.query('print(errorqueue.next())').split('\t') for i in range(int(float(self._visainstrument.query('print(errorqueue.count)'))))]
            err = [[int(float(e[0])), str(e[1]), int(float(e[2]))] for e in err]
            if not err:
                err = [[0, 'no error', 0]]
            return err
        except Exception as e:
            logging.error('{!s}: Cannot get errors of instrument'.format(__name__))
            raise type(e)('{!s}: Cannot get errors of instrument\n{!s}'.format(__name__, e))
    
    def _raise_error(self):
        """
        Gets errors of instrument and as the case may be raises a python error.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        """
        errors = self.get_error()
        if len(errors) == 1 and errors[0][0] is 0:  # no error
            return
        else:
            msg = __name__ + ' raises the following errors:'
            for err in errors:
                msg += '\n{:s} ({:s})'.format(self.err_msg[err[0]], err[1])
            raise ValueError(msg)
    
    def clear_error(self):
        """
        Clears error of instrument.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        """
        # Corresponding Command: errorqueue.clear()
        try:
            logging.debug('{:s}: Clear error'.format(__name__))
            self._write('errorqueue.clear()')
        except AttributeError as e:
            logging.error('{!s}: Cannot clear errors'.format(__name__))
            raise type(e)('{!s}: Cannot clear errors\n{!s}'.format(__name__, e))
        return
    
    def close(self):
        """
        Closes the VISA-instrument to disconnect the instrument.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        """
        try:
            logging.debug('{!s}: Close VISA-instrument'.format(__name__))
            self._visainstrument.close()
        except Exception as e:
            logging.error('{!s}: Cannot close VISA-instrument'.format(__name__))
            raise type(e)('{!s}: Cannot close VISA-instrument\n{!s}'.format(__name__, e))
        return
    
    def get_parameters(self):
        """
        Gets a parameter list <parlist> of measurement specific setting parameters.
        Needed for .set-file in 'write_additional_files', if qt parameters are not used.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        parlist: dict
            Parameter names as keys, corresponding channels of interest as values.
        """
        parlist = {'measurement_mode': {'channels': [1, 2]},
                   'bias_mode': {'channels': [1, 2]},
                   'sense_mode': {'channels': [1, 2]},
                   'bias_range': {'channels': [1, 2]},
                   'sense_range': {'channels': [1, 2]},
                   'bias_delay': {'channels': [1, 2]},
                   'sense_delay': {'channels': [1, 2]},
                   'sense_average': {'channels': [1, 2]},
                   'bias_value': {'channels': [1, 2]},
                   'plc': {'channels': [None]},
                   'sense_nplc': {'channels': [1, 2]},
                   'sense_autozero': {'channels': [1, 2]},
                   'status': {'channels': [1, 2]}}
        return parlist

    def get(self, param, **kwargs):
        """
        Gets the current parameter <param> by evaluation 'get_'+<param> and corresponding channel if needed
        In combination with <self.get_parameters> above.

        Parameters
        ----------
        param: str
            Parameter of interest.
        channels: array_likes
            Number of channels of interest. Must be in {1, 2} for channel specific parameters or None for channel independent (global) parameters.

        Returns
        -------
        parlist: dict
            Parameter names as keys, values of corresponding channels as values.
        """
        channels = kwargs.get('channels').get('channels')
        if channels == [None]:
            return getattr(self, 'get_{!s}'.format(param))()
        else:
            return tuple([getattr(self, 'get_{!s}'.format(param))(channel=channel) for channel in channels])
