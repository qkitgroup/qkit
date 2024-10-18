# -*- coding: utf-8 -*-

# Keysight_B2900.py driver for Keysight B2900 series source measure unit
# Micha Wildermuth, micha.wildermuth@kit.edu 2019
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


class Keysight_B2900(Instrument):
    """
    This is the driver for the Keysight B2900 series source measure unit.
    """

    def __init__(self, name, address, reset=False):
        """
        Initializes VISA communication with the instrument Keysight B2900.

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

        >>> IVD = qkit.instruments.create('IVD', 'Keysight_B2900', address='TCPIP0::00.00.000.00::INSTR', reset=True)
        Initialized the file info database (qkit.fid) in 0.000 seconds.
        """
        # Corresponding Command: :SYSTem:BEEPer:STATe mode
        self.__name__ = __name__
        # Start VISA communication
        logging.info(__name__ + ': Initializing instrument Keysight B29000')
        Instrument.__init__(self, name, tags=['physical'])
        self._address = address
        self._visainstrument = visa.instrument(self._address)
        # different versions for 1 or 2 channels
        self._IDN = self._ask('*IDN?')
        self._channels = int(self._IDN.split(',')[1][4])
        self._cmd_chans = {1: {1: ''}, 2: {1: '1', 2: '2'}}
        self._log_chans = {1: {1: ''}, 2: {1: ' of channel 1', 2: ' of channel 2'}}
        # initial variables
        self._sweep_mode = 2 - self._channels  # 1 (IV-mode) for single channel SMU and 0 (VV-mode) for two channel SMU
        self._sweep_channels = (1,)
        self._measurement_modes = {0: '2-wire', 1: '4-wire'}
        self._IV_modes = {0: 'curr', 1: 'volt', 2: 'res'}
        self._IV_units = {0: 'A', 1: 'V', 2: 'Ohm'}
        self._sense_mode = {i + 1: 0 for i in range(self._channels)}
        # dict of defaults values: defaults[<sweep_mode>][<channel>][<parameter>][<value>]
        self._defaults = {0: [{self.set_measurement_mode: 0,
                               self.set_bias_mode: 1,
                               self.set_sense_mode: 1,
                               self.set_bias_range: -1,
                               self.set_sense_range: -1,
                               self.set_bias_delay: 15e-6,
                               self.set_sense_delay: 15e-6,
                               self.set_sense_nplc: 1},
                              {self.set_measurement_mode: 1,
                               self.set_bias_mode: 0,
                               self.set_sense_mode: 1,
                               self.set_bias_range: -1,
                               self.set_sense_range: -1,
                               self.set_bias_delay: 15e-6,
                               self.set_sense_delay: 15e-6,
                               self.set_sense_nplc: 1}],
                          1: [{self.set_measurement_mode: 1,
                               self.set_bias_mode: 0,
                               self.set_sense_mode: 1,
                               self.set_bias_range: -1,
                               self.set_sense_range: -1,
                               self.set_bias_delay: 15e-6,
                               self.set_sense_delay: 15e-6,
                               self.set_sense_nplc: 1}],
                          2: [{self.set_measurement_mode: 1,
                               self.set_bias_mode: 1,
                               self.set_sense_mode: 0,
                               self.set_bias_range: -1,
                               self.set_sense_range: -1,
                               self.set_bias_delay: 15e-6,
                               self.set_sense_delay: 15e-6,
                               self.set_sense_nplc: 1}]}
        self._default_str = 'default parameters'
        self._set_defaults_docstring()
        # condition code registers
        self.measurement_ccr = [('Ch1 Limit Test Summary', 'Channel 1 failed one or more limit tests.'),
                                ('Ch1 Reading Available', 'Reading of channel 1 was taken normally.'),
                                (
                                'Ch1 Reading Overflow', 'Reading of channel 1 exceeds the selected measurement range.'),
                                ('Ch1 Buffer Available', 'Trace buffer for channel 1 has data.'),
                                ('Ch1 Buffer Full', 'Trace buffer for channel 1 is full.'),
                                ('Not used', '0 is returned.'),
                                ('Ch2 Limit Test Summary', 'Channel 2 failed one or more limit tests.'),
                                ('Ch2 Reading Available', 'Reading of channel 2 was taken normally.'),
                                (
                                'Ch2 Reading Overflow', 'Reading of channel 2 exceeds the selected measurement range.'),
                                ('Ch2 Buffer Available', 'Trace buffer for channel 2 has data.'),
                                ('Ch2 Buffer Full', 'Trace buffer for channel 2 is full.'),
                                ('Not used', '0 is returned.'),
                                ('Not used', '0 is returned.'),
                                ('Not used', '0 is returned.'),
                                ('Not used', '0 is returned.'),
                                ('Not used', '0 is returned.')]
        self.operation_ccr = [('Calibration/Self-test Running', 'Self-calibration or Self-test is in progress.'),
                              ('Ch1 Transition Idle', 'Channel 1 is in the transition idle state.'),
                              (
                              'Ch1 Waiting for Transition Trigger', 'Channel 1 is waiting for the transition trigger.'),
                              ('Ch1 Waiting for Transition Arm', 'Channel 1 is waiting for the transition arm.'),
                              ('Ch1 Acquire Idle', 'Channel 1 is in the acquire idle state.'),
                              ('Ch1 Waiting for Acquire Trigger', 'Channel 1 is waiting for the acquire trigger.'),
                              ('Ch1 Waiting for Acquire Arm', 'Channel 1 is waiting for the acquire arm.'),
                              ('Ch2 Transition Idle', 'Channel 2 is in the transition idle state.'),
                              (
                              'Ch2 Waiting for Transition Trigger', 'Channel 2 is waiting for the transition trigger.'),
                              ('Ch2 Waiting for Transition Arm', 'Channel 2 is waiting for the transition arm.'),
                              ('Ch2 Acquire Idle', 'Channel 2 is in the acquire idle state.'),
                              ('Ch2 Waiting for Acquire Trigger', 'Channel 2 is waiting for the acquire trigger.'),
                              ('Ch2 Waiting for Acquire Arm', 'Channel 2 is waiting for the acquire arm.'),
                              ('Instrument Locked',
                               'If a remote interface (GPIB, USB, or LAN) has a lock (see :SYSTem:LOCK:OWNer? command), this bit will be set. When a remote interface releases the lock (see :SYSTem:LOCK:NAME? command), this bit will be cleared.'),
                              ('Program Running',
                               'Program is running. 0 is set during the program memory execution is stopped.'),
                              ('Not used', '0 is returned.')]
        self.questionable_ccr = [('Voltage Summary', 'Over voltage in channel 1, and/or 2.'),
                                 ('Current Summary', 'Over current in channel 1, and/or 2.'),
                                 ('Ch1 Output Protection',
                                  'Output relay of the specified channel is opened by the automatic output off at compliance function.'),
                                 ('Ch2 Output Protection',
                                  'Output relay of the specified channel is opened by the automatic output off at compliance function.'),
                                 ('Temperature Summary', 'Over temperature in channel 1, and/or 2.'),
                                 ('Not used', '0 is returned.'),
                                 ('Not used', '0 is returned.'),
                                 ('Not used', '0 is returned.'),
                                 ('Calibration', 'Channel 1 and/or 2 failed calibration.'),
                                 ('Self-test', 'Channel 1 and/or 2 failed self-test.'),
                                 ('Interlock', 'Interlock circuit is open.'),
                                 ('Ch1 Transition Event Lost', 'Lost arm or trigger transition event on channel 1'),
                                 ('Ch1 Acquire Event Lost', 'Lost arm or trigger acquire event on channel 1'),
                                 ('Ch2 Transition Event Lost', 'Lost arm or trigger transition event on channel 2'),
                                 ('Ch2 Acquire Event Lost', 'Lost arm or trigger acquire event on channel 2'),
                                 ('Not used', '0 is returned.')]
        # error messages
        self.err_msg = {-100: '''Command error: Generic syntax error that cannot be determined more specifically.''',
                        -101: '''Invalid character: An invalid character for the type of a syntax element was received; for example, a header containing an ampersand.''',
                        -102: '''Syntax error: An unrecognized command or data type was received; for example, a string was received when B2901A does not accept strings.''',
                        -103: '''Invalid separator: An illegal character was received when a separator was expected; for example, the semicolon was omitted after a program message unit.''',
                        -104: '''Data type error: An improper data type was received; for example, numeric data was expected but string data was received.''',
                        -105: '''GET not allowed: A group execute trigger was received within a program message.''',
                        -108: '''Parameter not allowed: Too many parameters for the command were received.''',
                        -109: '''Missing parameter: Fewer parameters were received than required for the command.''',
                        -110: '''Command header error: An error was detected in the header. This error message is reported if B2901A cannot determine the more specific header errors -111 through -114.''',
                        -111: '''Header separator error: An illegal character for a header separator was received; for example, no white space between the header and parameter.''',
                        -112: '''Program mnemonic too long: A keyword in the command header contains more than twelve characters.''',
                        -113: '''Undefined header: An undefined command header was received; for example, *XYZ.''',
                        -114: '''Header suffix out of range: The value of a numeric suffix attached to a program mnemonic is out of range; for example, :OUTP3:FILT:AUTO specifies illegal channel number 3.''',
                        -120: '''Numeric data error: Numeric (including the non-decimal numeric types) data error. This error message is reported when B2901A cannot determine the more specific errors -121 through -128.''',
                        -121: '''Invalid character in number: An invalid character for the data type was received; for example, an alpha-character was received when the type was decimal numeric.''',
                        -123: '''Exponent too large: The magnitude of the exponent was larger than 32000.''',
                        -124: '''Too many digits: The mantissa of a decimal numeric data contained more than 255 digits excluding leading zeros.''',
                        -128: '''Numeric data not allowed: Numeric data is not allowed in this position for this command.''',
                        -130: '''Suffix error: An error was detected in the suffix. This error message is reported if B2901A cannot determine the more specific suffix errors -131 through -138.''',
                        -131: '''Invalid suffix: The suffix does not follow the correct syntax or the suffix is inappropriate.''',
                        -134: '''Suffix too long: The suffix contains more than 12 characters.''',
                        -138: '''Suffix not allowed: A suffix was received after a numeric parameter that does not allow suffixes.''',
                        -140: '''Character data error: An error was detected in a character parameter. This error message is reported if B2901A cannot determine the more specific errors -141 through -148.''',
                        -141: '''Invalid character data: Either the character parameter contains an invalid character or the particular element received is not valid for the command header.''',
                        -144: '''Character data too long: The character parameter contains more than 12 characters.''',
                        -148: '''Character data not allowed: A character parameter is not allowed for this position.''',
                        -150: '''String data error: An error was detected in a string parameter. This error is reported if B2901A cannot determine a more specific error -151 and -158.''',
                        -151: '''Invalid string data: An invalid string parameter data was received; for example, an END message was received before the terminal quote character.''',
                        -158: '''String data not allowed: A string parameter data was received but was not allowed at this point.''',
                        -160: '''Block data error: An error was detected in a block data. This error is reported if B2901A cannot determine more specific errors -161 and -168.''',
                        -161: '''Invalid block data: An invalid block data was received; for example, an END message was received before the length was satisfied.''',
                        -168: '''Block data not allowed: A legal block data was received but was not allowed at this point.''',
                        -170: '''Expression error: An error was detected in an expression. This error is reported if B2901A cannot determine more specific errors -171 and -178.''',
                        -171: '''Invalid expression: The expression was invalid; for example, unmatched parentheses or an illegal character.''',
                        -178: '''Expression data not allowed: An expression was received but was not allowed at this point.''',
                        -200: '''Execution error: Generic execution error for B2901A that cannot be determined more specifically.''',
                        -220: '''Parameter error; Invalid channel list | Parameter error; Invalid group definition: Invalid channel list or group definition was specified. Set appropriate value.''',
                        -221: '''Settings conflict; message; channel n: A specified parameter setting could not be executed due to the present device state. Check the settings specified by message and channel n, and set appropriate value.''',
                        -222: '''Data out of range; message; channel n: Interpreted value of the program was out of range as defined by B2900. Check the B2901A settings specified by message and channel n, and set appropriate value.''',
                        -223: '''Too much data: Too many parameters were sent. Reduce number of list data.''',
                        -224: '''Illegal parameter value: Illegal parameter value was sent. Set appropriate parameter value.''',
                        -230: '''Data corrupt or stale: Possibly invalid data; new reading started but not completed since last access.''',
                        -231: '''Data questionable: Measurement accuracy is suspect.''',
                        -232: '''Invalid format: The data format or structure is inappropriate.''',
                        -233: '''Invalid version: The version of the data format is incorrect to the instrument.''',
                        -240: '''Hardware error: A hardware problem in B2900. This error message is reported if B2901A cannot detect the more specific error -241.''',
                        -241: '''Hardware missing; To recover channel, execute *TST?. A program command or query could not be executed because of missing hardware; for example, an option was not installed. Execute the *TST? command to recover or unlock channel.''',
                        -300: '''Device-specific error: Generic device-dependent error for B2901A that cannot be determined more specifically.''',
                        -310: '''System error: Some error, termed “system error” by B2900, has occurred.''',
                        -311: '''Memory error: An error was detected in B2900’s memory.''',
                        -313: '''Calibration memory lost; Calibration data has been lost, Calibration data is initialized; Channel n, Calibration memory lost; Nonvolatile data saved by the *CAL? command has been lost; Channel n: Non-volatile data related to the *CAL? command has been lost.''',
                        -315: '''Configuration memory lost: Non-volatile configuration data saved by B2901A has been lost.''',
                        -321: '''Out of memory: Too many data was sent at a time.''',
                        -350: '''Queue overflow: This code is entered into the queue instead of the code that caused the error. This code indicates that there is no room in the queue and an error occurred but was not recorded.''',
                        -400: '''Query error: Generic query error for B2901A that cannot be determined more specifically.''',
                        -410: '''Query INTERRUPTED: A condition causing an INTERRUPTED query error occurred; for example, a query followed by DAB or GET before a response was completely sent.''',
                        -420: '''Query UNTERMINATED: A condition causing an UNTERMINATED query error occurred; for example, B2901A was addressed to talk and an incomplete program message was received.''',
                        -430: '''Query DEADLOCKED: A condition causing a DEADLOCKED query error occurred; for example, both input buffer and output buffer are full and B2901A cannot continue.''',
                        -440: '''Query UNTERMINATED after indefinite response: A query was received in the same program message after a query requesting an indefinite length response was executed.''',
                        101: '''Wrong password''',
                        102: '''Enter password for calibration''',
                        103: '''Data load failed''',
                        104: '''Data save failed''',
                        111: '''Self-calibration failed; Voltage offset: Failed the voltage offset self-calibration specified by item and channel n.''',
                        112: '''Self-calibration failed; Current offset, item; channel n: Failed the current offset self-calibration specified by item and channel n.''',
                        113: '''Self-calibration failed; Voltage gain, item; channel n: Failed the voltage gain self-calibration specified by item and channel n.''',
                        114: '''Self-calibration failed; Current gain, item; channel n: Failed the current gain self-calibration specified by item and channel n.''',
                        115: '''Self-calibration failed; CMR DAC, item; channel n: Failed the CMR DAC self-calibration specified by item and channel n.''',
                        121: '''Self-test failed; CPU communication, item; channel n: Failed the CPU communication test specified by item and channel n.''',
                        122: '''Self-test failed; Fan status, item; channel n: Failed the fan status test specified by item and channel n.''',
                        131: '''Self-test failed; SMU communication, item; channel n: Failed the SMU communication test specified by item and channel n.''',
                        132: '''Self-test failed; CPLD access, item; channel n: Failed the CPLD access test specified by item and channel n.''',
                        133: '''Self-test failed; Trigger count, item; channel n: Failed the trigger count test specified by item and channel n.''',
                        134: '''Self-test failed; DAC/ADC, item; channel n: Failed the DAC/ADC test specified by item and channel n.''',
                        135: '''Self-test failed; Loop control, item; channel n: Failed the loop control test specified by item and channel n.''',
                        136: '''Self-test failed; I sense, item; channel n: Failed the current sense test specified by item and channel n.''',
                        137: '''Self-test failed; V sense, item; channel n: Failed the voltage sense test specified by item and channel n.''',
                        138: '''Self-test failed; F-COM comparison, item; channel n: Failed the F-COM comparison test specified by item and channel n.''',
                        139: '''Self-test failed; V switch, item; channel n: Failed the voltage switch test specified by item and channel n.''',
                        140: '''Self-test failed; Temperature sensor, item; channel n: Failed the temperature sensor test specified by item and channel n.''',
                        141: '''Self-test skipped; To recover channel, execute *TST?: 201 Not able to perform requested operation''',
                        202: '''Not allowed; Instrument locked by another I/O session: The requested operation is not allowed because the instrument is locked by another I/O session. The instrument must be unlocked.''',
                        203: '''Not able to execute while instrument is measuring''',
                        210: '''Operation is not completed: Operation is still in progress. Wait for operation complete.''',
                        211: '''Cannot switch low sense terminal with output on: Output relay must be off to switch low sense terminal.''',
                        212: '''Output relay must be on: Output relay must be on to perform the requested operation.''',
                        213: '''Output relay must be off: Output relay must be off to perform the requested operation.''',
                        214: '''Display must be enabled: Display is currently disabled. Set remote display on.''',
                        215: '''Remote sensing must be on: Remote sensing must be on to perform the requested operation.''',
                        216: '''Auto resistance measurement must be off: Automatic resistance measurement must be off to perform the requested operation.''',
                        290: '''Not able to recall state: it is empty: 291 State file size error''',
                        292: '''State file corrupt''',
                        301: '''Emergency; Overvoltage status detected; Channel n: Overvoltage status was detected in channel n. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        302: '''Emergency; Overcurrent status(245 V) detected; Channel n: overcurrent status (245 V) was detected in channel n. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        303: '''Emergency; Overcurrent status(35 'V) detected; Channel n: overcurrent status (35 V) was detected in channel n. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        304: '''Emergency; Over range current status detected; Channel n: Over range current status was detected in channel n. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        305: '''Emergency; High temperature1 status detected; Channel n: High temperature 1 status was detected in channel n. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        306: '''Emergency; High temperature2 status detected; Channel n: High temperature 2 status was detected in channel n. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        307: '''Emergency; High temperature3 status detected; Channel n: High temperature 3 status was detected in channel n. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        308: '''Emergency; High temperature4 status detected; Channel n: High temperature 4 status was detected in channel n. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        311: '''Emergency; Abuse detected; Channel n: Abuse status was detected in channel n. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        312: '''Emergency; F-COM(minus) abuse detected; Channel n: F-COM (minus) status was detected in channel n. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        313: '''Emergency; F-COM(plus) abuse detected; Channel n: F-COM (plus) abuse status was detected in channel n. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        314: '''Emergency; Low sense(minus) abuse detected; Channel n: Low sense (minus) abuse status was detected in channel n. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        315: '''Emergency; Low sense(plus) abuse detected; Channel n: Low sense (plus) abuse status was detected in channel n. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        321: '''Emergency; SMU main power supply failure detected; Channel n: SMU main power supply failure was detected in channel n. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        322: '''Emergency; SMU positive power supply failure detected; Channel n: SMU positive power supply failure was detected in channel n. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        323: '''Emergency; SMU negative power supply failure detected; Channel n: SMU negative power supply failure was detected in channel n. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        324: '''Emergency; SMU power supply was turned off; Channel n: SMU power supply was turned off because emergency status was detected in channel n. All channels were disabled. Execute the *TST? command.''',
                        331: '''Emergency; Interlock open detected: Interlock open was detected. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command. Do not open interlock circuit while SMU is in high voltage state.''',
                        341: '''Emergency; Fan speed is too slow: Too slow fan speed status was detected. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        342: '''Emergency; Fan speed is too fast: Too fast fan speed status was detected. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        351: '''Emergency; Internal communication failure detected by SMU; Channel n: Internal communication failure was detected in channel n. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        352: '''Emergency; Watchdog timer expired; Channel n: Watchdog timer expired status was detected in channel n. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        353: '''Emergency; F-COM CPLD reset detected; Channel n: F-COM CPLD reset status was detected in channel n. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        354: '''Emergency; VADC data was lost; Channel n: Channel n voltage ADC data was lost. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        355: '''Emergency; IADC data was lost; Channel n: Channel n current ADC data was lost. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        356: '''Emergency; Sense data FIFO overflow detected; Channel n: Sense data FIFO overflow was detected in channel n. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        361: '''Emergency; Internal communication failure detected by CPU; Channel n: Channel n internal communication failure was detected by CPU. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        362: '''Emergency; Internal command queue overflow detected; Channel n: Internal command queue overflow was detected in channel n. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        363: '''Emergency; Sense data was not received for acquire: trigger; Channel n: Channel n sense data was not received for acquire trigger. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        364: '''Emergency; Unexpected sense data was received; Channel n: Unexpected sense data was received. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        365: '''Emergency; Sense data was not received in Timer period; Channel n: Data communication failure. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        366: '''Emergency; Timestamp FIFO overflow detected; Channel n: Data communication failure. All channel output is changed to 0 V and the all output switch is opened. Execute the *TST? command.''',
                        600: '''Some or all licenses from license file(s) could not be installed''',
                        700: '''ProgramMemory; Program size overflow: Program memory cannot save the program. Reduce program size.''',
                        701: '''ProgramMemory; Invalid variable: Appropriate variable name must be specified.''',
                        702: '''ProgramMemory; Invalid variable number: Appropriate variable name must be specified.''',
                        703: '''ProgramMemory; Query command is not supported: Memory program cannot contain query command.''',
                        704: '''ProgramMemory; Program is not selected: Appropriate program name must be specified.''',
                        705: '''ProgramMemory; Cannot execute program while another program is running: Another program is running. Execute the program after it is stopped.''',
                        706: '''ProgramMemory; Cannot execute program while this program is running: This program is running. Execute the program after it is stopped.''',
                        707: '''ProgramMemory; Cannot step program while program is running: Program is running. Step execution is effective when program is paused or stopped.''',
                        708: '''ProgramMemory; Cannot continue program while program is running: Program is running. Program continue is effective when program is paused.''',
                        709: '''ProgramMemory; Cannot continue program while program is stopped: Program is stopped. Program continue is effective when program is paused.''',
                        710: '''ProgramMemory; Program line is too long: Program memory cannot save the program. Reduce program line.''',
                        711: '''ProgramMemory; Variable length is too long: Variable contains too many data. Reduce variable length.''',
                        712: '''ProgramMemory; Unsupported command is used in program: Memory program cannot contain the specified command.''',
                        713: '''ProgramMemory; Cannot set multiple INIT commands in program line: A program line cannot contain multiple INIT commands.''',
                        714: '''ProgramMemory; Invalid character in program line: Program line contains invalid character. Use appropriate characters.''',
                        715: '''ProgramMemory; Invalid character in program name: Appropriate program name must be specified.''',
                        716: '''ProgramMemory; Program count overflow: Program memory cannot save the program. Delete dispensable program.''',
                        801: '''Calculate; Expression list full: Cannot save the expression. Delete dispensable expression.''',
                        802: '''Calculate; Expression cannot be deleted: Cannot delete the specified expression. Specify erasable expression.''',
                        803: '''Calculate; Missmatched parenthesis: Number of open and close parentheses must be the same.''',
                        804: '''Calculate; Not a number of data handle: Expression contains invalid floating point number or symbol. Enter appropriate expression. Available symbols are VOLT, CURR, RES, TIME, and SOUR.''',
                        805: '''Calculate; Mismatched brackets: Number of open and close brackets must be the same.''',
                        806: '''Calculate; Entire expression not parsed: Expression is not correct. Enter appropriate expression.''',
                        807: '''Calculate; Not an operator or number: Expression contains not an operator or not a number. Enter appropriate expression.''',
                        811: '''Calculate; parsing value: Expression contains invalid floating point number. Enter appropriate expression.''',
                        812: '''Calculate; Invalid data handle index: Vector expression contains invalid index value of an array. Enter appropriate expression.''',
                        813: '''Calculate; Divided by zero: Denominator must not be zero. Enter appropriate expression.''',
                        814: '''Calculate; Log of zero: Expression cannot contain log 0. Enter appropriate expression.''',
                        815: '''Calculate; Invalid binary format string is used: Data contains invalid binary format string. Enter appropriate expression.''',
                        816: '''Calculate; Invalid hex format string is used: Data contains invalid hex format string. Enter appropriate expression.''',
                        817: '''Calculate; Invalid channel number is used: Expression contains invalid channel number. Enter appropriate expression.''',
                        818: '''Calculate; Null expression: Expression is not defined. Enter appropriate expression.''',
                        819: '''Calculate; Null expression in parentheses: Expression contains empty parentheses. Enter appropriate expression.''',
                        820: '''Calculate; Null expression in brackets: Expression contains empty brackets. Enter appropriate expression.''',
                        821: '''Calculate; Fed disabled MATH for limit test: Limit test tried to feed the math result currently disabled. Enable the math expression.''',
                        822: '''Calculate; Missmatched trigger counts: Trigger count of grouped channels must be the same.''',
                        823: '''Calculate; Missmatched vector lengths: Vector length of grouped channels must be the same.''',
                        824: '''Calculate; Invalid character in math name: Appropriate math expression name must be specified.''',
                        861: '''Trace; Illegal with storage active: Storage device must be idle to perform the requested operation.''',
                        862: '''Trace; No trace data: Trace buffer must contain data to perform the requested operation.''',
                        870: '''Macro file size error: Macro file size error. Reduce file size.''',
                        871: '''Cannot create state data on non-volatile memory: 900 Internal system error''',
                        950: '''Unsupported parameter: Conventional command set error. Specified parameter is not supported by B2900.''',
                        951: '''Unsupported command: Conventional command set error. Specified command is not supported by B2900.'''}
        # reset
        if reset:
            self.reset()
            [self.set_sense_mode(channel=channel, mode=0) for channel in np.arange(self._channels) + 1]
        else:
            self.get_all()
        self._write(':syst:beep:stat 0')  # disable beeper

    def _write(self, cmd):
        """
        sends a visa command <cmd>, waits until "operation complete" and raises eventual errors of the device.

        parameters
        ----------
        cmd: str
            command that is send to the instrument via pyvisa and ni-visa backend.

        returns
        -------
        none
        """
        self._visainstrument.write(cmd)
        while not bool(int(self._visainstrument.query('*OPC?'))):
            time.sleep(1e-6)
        self._raise_error()
        return

    def _ask(self, cmd):
        """
        sends a visa command <cmd>, waits until "operation complete", raises eventual errors of the device and returns the read answer <ans>.

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
        while not bool(int(self._visainstrument.query('*opc?'))):
            time.sleep(1e-6)
        self._raise_error()
        return ans

    def set_gpio_mode(self, val, channel=-1):
        """
        Assigns the input/output function to the specified GPIO pin <channel> to <val>.

        Parameters
        ----------
        val: str
            GPIO specification. possible values are DINPut(default for the EXT1 to EXT13 pins) | DIO | HVOL(default for the EXT14 pin) | TINPut | TOUT
        channel: int
            Number of GPIO pin of interest. -1 means channel 1 to 14.
        """
        # Corresponding Command: [:SOURce]:DIGital:EXTernal[n][:FUNCtion] function
        try:
            logging.debug('{!s}: Set the GPIO mode of pin {!s} to {!s}'.format(__name__, channel, val))
            if channel == -1:
                for j in range(14):
                    self._write('sour:dig:ext{:d}:func {:s}'.format(j + 1, val))
            else:
                self._write('sour:dig:ext{:d}:func {:s}'.format(channel, val))
            self._write('SOUR:DIG:DATA 16383')
            self.ccr = bin(16383)
        except Exception as e:
            logging.error('{!s}: Cannot set the GPIO mode of pin {!s} to {!s}'.format(__name__, channel, val))
            raise type(e)('{!s}: Cannot set the GPIO mode of pin {!s} to {!s}\n{!s}'.format(__name__, channel, val, e))
        return

    def get_gpio_mode(self, channel):
        """
        Gets the assigned input/output function to the specified GPIO pin <channel>.

        Parameters
        ----------
        channel: int
            Number of GPIO pin of interest. -1 means channel 1 to 14.

        Returns
        -------
        val: str
            GPIO specification. possible values are DINPut(default for the EXT1 to EXT13 pins) | DIO | HVOL(default for the EXT14 pin) | TINPut | TOUT
        """
        # Corresponding Command: [:SOURce]:DIGital:EXTernal[n][:FUNCtion]?
        try:
            logging.debug('{!s}: Get the GPIO mode of pin {!s}'.format(__name__, channel))
            return self._ask('SOUR:DIG:EXT{:d}:FUNC'.format(channel))
        except Exception as e:
            logging.error('{!s}: Cannot get the GPIO mode of pin {!s}'.format(__name__, channel))
            raise type(e)('{!s}: Cannot get the GPIO mode of pin {!s}\n{!s}'.format(__name__, channel, e))

    def set_digio(self, status, channel):
        """
        Sets the output data to GPIO pin (digital control port) <channel> to <status>.

        Parameters
        ----------
        status: bool, int
            Digital Output status.
        channel: int
            Number of GPIO pin of interest.
        """
        # Corresponding Command: [:SOURce]:DIGital:DATA data
        try:
            logging.debug('{!s}: Set the digital output of pin {!s} to {!s}'.format(__name__, channel, status))
            self.ccr = (self.ccr[:-channel] + str(int(not (status))) + self.ccr[-channel + 1:])[:16]
            self._write('sour:dig:data {:d}'.format(int(self.ccr, 2)))
        except Exception as e:
            logging.error('{!s}: Cannot set the digital output of pin {!s} to {!s}'.format(__name__, channel, status))
            raise type(e)(
                '{!s}: Cannot set the digital output of pin {!s} to {!s}\n{!s}'.format(__name__, channel, status, e))
        return

    def get_digio(self, channel):
        """
        Sets the output data to GPIO pin (digital control port) <channel> to <status>.

        Parameters
        ----------
        status: bool, int
            Digital Output status.
        channel: int
            Number of GPIO pin of interest.
        """
        # Corresponding Command: [:SOURce]:DIGital:DATA?
        try:
            logging.debug('{!s}: Get the digital output of pin {!s}'.format(__name__, channel))
            return not (int(bin(int(self._ask('sour:dig:data?')))[-channel:][0]))
        except Exception as e:
            logging.error('{!s}: Cannot get the digital output of pin {!s}'.format(__name__, channel))
            raise type(e)('{!s}: Cannot get the digital output of pin {!s}\n{!s}'.format(__name__, channel, e))

    def set_measurement_mode(self, mode, channel=1):
        """
        Sets measurement mode (wiring system) of channel <channel> to <mode>.

        Parameters
        ----------
        mode: int
            State of the measurement sense mode. Must be 0 (2-wire) or 1 (4-wire).
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        None
        """
        # Corresponding Command: :SENSe[c]:REMote 1|0|ON|OFF
        try:
            logging.debug('{!s}: Set measurement mode{:s} to {:d}'.format(__name__, self._log_chans[self._channels][channel], mode))
            self._write(':sens{:s}:rem {:d}'.format(self._cmd_chans[self._channels][channel], mode))
        except Exception as e:
            logging.error('{!s}: Cannot set measurement mode{:s} to {!s}'.format(__name__, self._log_chans[self._channels][ channel], mode))
            raise type(e)('{!s}: Cannot set measurement mode{:s} to {!s}\n{!s}'.format(__name__, self._log_chans[self._channels][ channel], mode, e))
        return

    def set_sync(self, status):
        """
        Sets the interchannel synchronization to <val>.

        Parameters
        ----------
        status: bool
            Inter-channel synchronization mode specifies whether two channels are to be operated in sync.

        Returns
        -------
        None
        """
        # Corresponding Command: :SYSTem: GROup[:DEFine]
        # Corresponding Command: :SYSTem: GROup:RESet
        try:
            logging.debug('{!s}: Set interchannel synchronization to {!r}'.format(__name__, status))
            if status:
                self._write(':syst:gro:def (@1,2)'.format(status))
            else:
                self._write(':syst:gro:res')
        except Exception as e:
            logging.error('{!s}: Cannot set interchannel synchronization to {!s}'.format(__name__, status))
            raise type(e)('{!s}: Cannot set interchannel synchronization to {!s}\n{!s}'.format(__name__, status, e))
        return

    def get_sync(self):
        """
        Gets the interchannel synchronization.

        Parameters
        ----------
        None

        Returns
        -------
        val: bool
			Inter-channel synchronization mode specifies whether two channels are to be operated in sync.
        """
        # Corresponding Command: :SYSTem: GROup[:DEFine]?
        try:
            logging.debug('{!s}: Get interchannel synchronization'.format(__name__))
            return bool(int(self._ask(':syst:gro:def?')))
        except Exception as e:
            logging.error('{!s}: Cannot get interchannel synchronization'.format(__name__))
            raise type(e)('{!s}: Cannot get interchannel synchronization\n{!s}'.format(__name__, e))

    def get_measurement_mode(self, channel=1):
        """
        Gets measurement mode (wiring system) <mode> of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        mode: int
            State of the measurement sense mode. Meanings are 0 (2-wire) and 1 (4-wire).
        """
        # Corresponding Command: :SENSe[c]:REMote?
        try:
            logging.debug('{!s}: Get measurement mode{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            return int(self._ask(':sens{:s}:rem'.format(self._cmd_chans[self._channels][channel])))
        except Exception as e:
            logging.error(
                '{!s}: Cannot get measurement mode{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            raise type(e)(
                '{!s}: Cannot get measurement mode{:s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel],
                                                                     e))

    def set_bias_mode(self, mode, channel=1):
        """
        Sets bias mode of channel <channel> to mode <mode>.

        Parameters
        ----------
        mode: int
            Bias mode. Must be 0 (current) or 1 (voltage).
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        None
        """
        # Corresponding Command: [:SOURce[c]]:FUNCtion:MODE VOLTage|CURRent
        try:
            logging.debug('{!s}: Set bias mode{:s} to {:d}'.format(__name__, self._log_chans[self._channels][channel], mode))
            self._write(':sour{:s}:func:mode {:s}'.format(self._cmd_chans[self._channels][channel], self._IV_modes[mode]))
            self.set_bias_range(val=-1)  # set bias range to "auto"
            self._write(''':sens{:s}:func:on "{:s}"'''.format(self._cmd_chans[self._channels][channel], self._IV_modes[mode]))  # enables same sense function to measure bias value
        except Exception as e:
            logging.error('{!s}: Cannot set bias mode{:s} to {!s}'.format(__name__, self._log_chans[self._channels][channel], mode))
            raise type(e)('{!s}: Cannot set bias mode{:s} to {!s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], mode, e))
        return

    def get_bias_mode(self, channel=1):
        """
        Gets bias mode <mode> of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        mode: int
            Bias mode. Meanings are 0 (current) and 1 (voltage).
        """
        # Corresponding Command: [:SOURce[c]]:FUNCtion:MODE?
        try:
            logging.debug('{!s}: Get bias mode{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            return int(list(self._IV_modes.keys())[list(self._IV_modes.values()).index(self._ask(':sour{:s}:func:mode'.format(self._cmd_chans[self._channels][channel])).lower())])
        except Exception as e:
            logging.error('{!s}: Cannot get bias mode{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            raise type(e)('{!s}: Cannot get bias mode{:s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], e))

    def set_sense_mode(self, mode, channel=1):
        """
        Sets sense mode of channel <channel> to mode <mode>.

        Parameters
        ----------
        mode: int
            Sense mode. Must be 0 (current), 1 (voltage) or or 2 (resistance).
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        None
        """
        # Corresponding Command: :SENSe[c]:FUNCtion[:ON] function[, function[, function]]
        try:
            logging.debug('{!s}: Set sense mode{:s} to {:d}'.format(__name__, self._log_chans[self._channels][channel], mode))
            self._write(':sens{:s}:func:on:all'.format(self._cmd_chans[self._channels][channel]))
            self._write(''':sens{:s}:func:on "{:s}"'''.format(self._cmd_chans[self._channels][channel], self._ask(':sour:func:mode').lower()))  # turn on bias mode in order to measure bias values
            self._write(''':sens{:s}:func:on "{:s}"'''.format(self._cmd_chans[self._channels][channel], self._IV_modes[mode]))  # turn on sense mode
            self._sense_mode[channel] = mode
            self.set_sense_range(val=-1, channel=channel)
        except Exception as e:
            logging.error('{!s}: Cannot set sense mode{:s} to {!s}'.format(__name__, self._log_chans[self._channels][channel], mode))
            raise type(e)('{!s}: Cannot set sense mode{:s} to {!s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], mode, e))
        return

    def get_sense_mode(self, channel=1):
        """
        Gets sense mode <mode> of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        mode: int
            Sense mode. Meanings are 0 (current) and 1 (voltage).
        """
        return self._sense_mode[channel]

    def get_sense_modes(self, channel=1):
        """
        Gets all active sense modes <mode> of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        mode: int
            Sense mode. Meanings are 0 (current), 1 (voltage) and 2 (resistance).
        """
        # Corresponding Command: [:SOURce[c]]:<CURRent|VOLTage>:RANGe:AUTO?
        try:
            logging.debug('{!s}: Get sense mode{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            # return str(self._ask(':sens:func:on?').replace('''"''', '')).lower().split(',')
            return [key for key, val in self._IV_modes.items() if val in str(self._ask(":sens{:s}:func:on?".format(self._cmd_chans[self._channels][channel])).replace('''"''', '')).lower().split(
                ',')]
        except Exception as e:
            logging.error('{!s}: Cannot get sense mode{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            raise type(e)('{!s}: Cannot get sense mode{:s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], e))

    def set_bias_range(self, val, channel=1):
        """
        Sets bias range of channel <channel> to <val>.

        Parameters
        ----------
        val: float
            Bias range. Possible values are -1 (auto), for currents 200nA, 2uA, 20uA, 200uA, 2mA, 20mA, 200mA, 1 A, 3A and for voltages 200mV, 2V, 7V, 18V.
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        None
        """
        # Corresponding Command: [:SOURce[c]]:<CURRent|VOLTage>:RANGe range
        # Corresponding Command: [:SOURce[c]]:<CURRent|VOLTage>:RANGe:AUTO mode
        try:
            logging.debug('{!s}: Set bias range{:s} to {:g}'.format(__name__, self._log_chans[self._channels][channel], val))
            if val == -1:
                self._write(':sour{:s}:{:s}:rang:auto 1'.format(self._cmd_chans[self._channels][channel], self._IV_modes[self.get_bias_mode()]))
            else:
                self._write(':sour{:s}:{:s}:rang {:g}'.format(self._cmd_chans[self._channels][channel], self._IV_modes[self.get_bias_mode()], val))
        except Exception as e:
            logging.error(
                '{!s}: Cannot set bias range{:s} to {!s}'.format(__name__, self._log_chans[self._channels][channel], val))
            raise type(e)('{!s}: Cannot set bias range{:s} to {!s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], val, e))
        return

    def get_bias_range(self, channel=1):
        """
        Gets bias mode <val> of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        val: float
            Bias range.
        """
        # Corresponding Command: [:SOURce[c]]:<CURRent|VOLTage>:RANGe?
        # Corresponding Command: [:SOURce[c]]:<CURRent|VOLTage>:RANGe:AUTO?
        try:
            logging.debug('{!s}: Get bias range{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            return float(self._ask(':sour{:s}:{:s}:rang'.format(self._cmd_chans[self._channels][channel], self._IV_modes[self.get_bias_mode()])))
        except Exception as e:
            logging.error('{!s}: Cannot get bias range{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            raise type(e)('{!s}: Cannot get bias range{:s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], e))

    def set_sense_range(self, val, channel=1):
        """
        Sets sense range of channel <channel> to <val>.

        Parameters
        ----------
        val: float
           Sense range. Possible values are -1 (auto), for currents 200nA, 2uA, 20uA, 200uA, 2mA, 20mA, 200mA, 1 A, 3A and for voltages 200mV, 2V, 7V, 18V.
        channel: int
           Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        None
        """
        # Corresponding Command: :SENSe[c]:<CURRent[:DC]|RESistance|VOLTage[:DC]>:RANGe:UPPer range
        # Corresponding Command: :SENSe[c]:<CURRent[:DC]|RESistance|VOLTage[:DC]>:RANGe:AUTO mode
        try:
            logging.debug('{!s}: Set sense range{:s} to {:g}'.format(__name__, self._log_chans[self._channels][channel], val))
            if val == -1:
                self._write(':sens{:s}:{:s}:rang:auto 1'.format(self._cmd_chans[self._channels][channel], self._IV_modes[self._sense_mode[channel]]))
            else:
                self._write(':sens{:s}:{:s}:rang:upp {:g}'.format(self._cmd_chans[self._channels][channel], self._IV_modes[self._sense_mode[channel]], val))
        except Exception as e:
            logging.error(
                '{!s}: Cannot set sense range{:s} to {!s}'.format(__name__, self._log_chans[self._channels][channel], val))
            raise type(e)('{!s}: Cannot set sense range{:s} to {!s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], val, e))

    def get_sense_range(self, channel=1):
        """
        Gets sense range <val> of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        val: float
            Sense range.
        """
        # Corresponding Command: :SENSe[c]:<CURRent[:DC]|RESistance|VOLTage[:DC]>:RANGe:UPPer? [range]
        # Corresponding Command: :SENSe[c]:<CURRent[:DC]|RESistance|VOLTage[:DC]>:RANGe:AUTO?
        try:
            logging.debug('{!s}: Get sense range{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            return float(self._ask(':sens{:s}:{:s}:rang:upp?'.format(self._cmd_chans[self._channels][channel], self._IV_modes[self._sense_mode[channel]])))
        except Exception as e:
            logging.error('{!s}: Cannot get sense range{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            raise type(e)('{!s}: Cannot get sense range{:s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], e))

    def set_sense_limit(self, val, channel=1):
        """
        Sets sense compliance limit of channel <channel> to <val>.

        Parameters
        ----------
        val: float
           Sense compliance limit.
        channel: int
           Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        None
        """
        # Corresponding Command: :SENS[c]:CURR[:DC]:PROT[:LEV][:BOTH] comp
        # Corresponding Command: :SENS[c]:VOLT[:DC]:PROT[:LEV] comp
        try:
            logging.debug('{!s}: Set sense compliance limit{:s} to {:g}'.format(__name__, self._log_chans[self._channels][channel], val))
            self._write(':sens{:s}:{:s}:prot {:g}'.format(self._cmd_chans[self._channels][channel], self._IV_modes[self._sense_mode[channel]], val))
        except Exception as e:
            logging.error('{!s}: Cannot set sense compliance limit{:s} to {!s}'.format(__name__, self._log_chans[self._channels][channel], val))
            raise type(e)('{!s}: Cannot set sense compliance limit{:s} to {!s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], val, e))

    def get_sense_limit(self, channel=1):
        """
        Gets sense compliance limit <val> of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        val: float
            Sense compliance limit.
        """
        # Corresponding Command: :SENS[c]:CURR[:DC]:PROT[:LEV]? [DEFault | MINimum | MAXimum]
        # Corresponding Command: :SENS[c]:VOLT[:DC]:PROT[:LEV]? [DEFault | MINimum | MAXimum]
        try:
            logging.debug('{!s}: Get sense compliance limit{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            return float(self._ask(':sens{:s}:{:s}:prot?'.format(self._cmd_chans[self._channels][channel], self._IV_modes[self._sense_mode[channel]])))
        except Exception as e:
            logging.error('{!s}: Cannot get sense compliance limit{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            raise type(e)('{!s}: Cannot get sense compliance limit{:s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], e))

    def set_bias_trigger(self, mode, channel=1, **val):
        """
        Sets bias trigger mode of channel <channel> to <mode> and optional value <val>.

        Parameters
        ----------
        mode: str
            Bias trigger mode. Must be 'ext' (external), 'aux' (auxiliary), 'tim' (timer) or 'sens' (sense).
            AINT (default)|BUS|TIMer|INT1|INT2|LAN|EXT1|EXT2|EXT3|EXT4|EXT5|EXT6|EXT7|EXT8|EXT9|EXT10|EXT11|EXT12|EXT13|EXT14
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.
        time: float, optional
            Time trigger period if <mode> is 'timer'. Must be in [100µs, 3600s].
        pol: int, optional
            Polarity of auxiliary trigger if <mode> is 'aux'. Must be 0 (falling edge) or 1 (rising edge).

        Returns
        -------
        None
        """
        # Corresponding Command: :TRIGger<:ACQuire|:TRANsient|[:ALL]>:SOURce[:SIGNal] AINT (default)|BUS|TIMer|INT1|INT2|LAN|EXT1|EXT2|EXT3|EXT4|EXT5|EXT6|EXT7|EXT8|EXT9|EXT10|EXT11|EXT12|EXT13|EXT14
        # Corresponding Command: :TRIGger<:ACQuire|:TRANsient|[:ALL]>:TIMer
        try:
            logging.debug('{!s}: Set bias trigger{:s} to {:s}'.format(__name__, self._log_chans[self._channels][channel], mode))
            self._write(':trig:tran:sour: {:s}'.format(mode))
            if 'time' in val:
                logging.debug('{!s}: Set bias trigger timer{:s} to {:s}s'.format(__name__, self._log_chans[self._channels][channel], val.get('time', 50e-3)))
                self._write(':trig:tran:{:s} {:g}'.format(mode, val.get('time', 50e-3)))
        except Exception as e:
            logging.error('{!s}: Cannot set bias trigger{:s} to {!s}{!s}'.format(__name__, self._log_chans[self._channels][channel], mode, val))
            raise type(e)('{!s}: Cannot set bias trigger{:s} to {!s}{!s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], mode, val, e))
        return

    def get_bias_trigger(self, channel=1):
        """
        Gets bias trigger of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        mode: str
            Bias trigger mode. Meanings are 'ext' (external), 'aux' (auxiliary), 'tim1' (timer1), 'tim2' (timer2) and 'sens' (sense).
        time: float, optional
            Time trigger period if <mode> is 'timer'.
        pol: int, optional
            Polarity of auxiliary trigger if <mode> is 'aux'. Meanings are 0 (falling edge) and 1 (rising edge).
        """
        # Corresponding Command: :TRIGger<:ACQuire|:TRANsient|[:ALL]>:SOURce[:SIGNal] AINT (default)|BUS|TIMer|INT1|INT2|LAN|EXT1|EXT2|EXT3|EXT4|EXT5|EXT6|EXT7|EXT8|EXT9|EXT10|EXT11|EXT12|EXT13|EXT14
        # Corresponding Command: :TRIGger<:ACQuire|:TRANsient|[:ALL]>:TIMer
        try:
            logging.debug('{!s}: Get bias trigger{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            mode = str(self._ask(':trig:tran:sour').lower())
            if mode == 'tim':
                logging.debug('{!s}: Get bias trigger timer{:s}'.format(__name__, self._log_chans[self._channels][channel]))
                val = float(self._ask(':trig:tran:{:s}'.format(mode)))
                return mode, val
            else:
                return mode
        except Exception as e:
            logging.error('{!s}: Cannot get bias trigger{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            raise type(e)('{!s}: Cannot get bias trigger{:s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], e))

    def set_sense_trigger(self, mode, channel=1, **val):
        """
        Sets sense trigger mode of channel <channel> to <mode> and optional value <val>.

        Parameters
        ----------
        mode: str
            Bias trigger mode. Must be 'ext' (external), 'aux' (auxiliary), 'tim' (timer) or 'sens' (sense).
            AINT (default)|BUS|TIMer|INT1|INT2|LAN|EXT1|EXT2|EXT3|EXT4|EXT5|EXT6|EXT7|EXT8|EXT9|EXT10|EXT11|EXT12|EXT13|EXT14
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.
        time: float, optional
            Time trigger period if <mode> is 'timer'. Must be in [100µs, 3600s].
        pol: int, optional
            Polarity of auxiliary trigger if <mode> is 'aux'. Must be 0 (falling edge) or 1 (rising edge).

        Returns
        -------
        None
        """
        # Corresponding Command: :TRIGger<:ACQuire|:TRANsient|[:ALL]>:SOURce[:SIGNal] AINT (default)|BUS|TIMer|INT1|INT2|LAN|EXT1|EXT2|EXT3|EXT4|EXT5|EXT6|EXT7|EXT8|EXT9|EXT10|EXT11|EXT12|EXT13|EXT14
        # Corresponding Command: :TRIGger<:ACQuire|:TRANsient|[:ALL]>:TIMer
        ### TODO: set counter
        ### TODO: continuous measurement (same as "Auto" key)
        try:
            logging.debug('{!s}: Set sense trigger{:s} to {:s}'.format(__name__, self._log_chans[self._channels][channel], mode))
            self._write(':trig:acq:sour: {:s}'.format(mode))
            if 'time' in val:
                logging.debug('{!s}: Set sense trigger timer{:s} to {:s}s'.format(__name__, self._log_chans[self._channels][channel], val.get('time', 50e-3)))
                self._write(':trig:acq:{:s} {:g}'.format(mode, val.get('time', 50e-3)))
        except Exception as e:
            logging.error('{!s}: Cannot set sense trigger{:s} to {!s}{!s}'.format(__name__, self._log_chans[self._channels][channel], mode, val))
            raise type(e)('{!s}: Cannot set sense trigger{:s} to {!s}{!s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], mode, val, e))
        return

    def get_sense_trigger(self, channel=1):
        """
        Gets sense trigger of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        mode: str
            Bias trigger mode. Meanings are 'ext' (external), 'aux' (auxiliary), 'tim1' (timer1), 'tim2' (timer2) and 'sens' (sense).
        time: float, optional
            Time trigger period if <mode> is 'timer'.
        pol: int, optional
            Polarity of auxiliary trigger if <mode> is 'aux'. Meanings are 0 (falling edge) and 1 (rising edge).
        """
        # Corresponding Command: :TRIGger<:ACQuire|:TRANsient|[:ALL]>:SOURce[:SIGNal] AINT (default)|BUS|TIMer|INT1|INT2|LAN|EXT1|EXT2|EXT3|EXT4|EXT5|EXT6|EXT7|EXT8|EXT9|EXT10|EXT11|EXT12|EXT13|EXT14
        # Corresponding Command: :TRIGger<:ACQuire|:TRANsient|[:ALL]>:TIMer
        try:
            logging.debug('{!s}: Get sense trigger{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            mode = str(self._ask(':trig:acq:sour'.format(channel)).lower())
            if mode == 'tim':
                logging.debug('{!s}: Get sense trigger timer{:s}'.format(__name__, self._log_chans[self._channels][channel]))
                val = float(self._ask(':trig:tran:{:s}'.format(mode)))
                return mode, val
            else:
                return mode
        except Exception as e:
            logging.error('{!s}: Cannot get sense trigger{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            raise type(e)('{!s}: Cannot get sense trigger{:s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], e))

    def set_bias_delay(self, offset, status=True, channel=1, **kwargs):
        """
        Sets bias delay with respect to the bias trigger to the value <val> that is calculated internally by
            if status is True:
                if auto = True:
                    val = gain*initial_wait_time + offset
                else:
                    val = offset
            else:
                val = 0

        Parameters
        ----------
        offset: float
            Offset value used for calculating the source wait time for the specified channel. Can be between 0 and 1 seconds, MINimum, MAXimum or DEFault. Default is 0.
        status: bool
        auto: bool
            Initial wait time used for calculating the source wait time for the specified channel.
        gain: float
            Gain value used for calculating the source wait time for the specified channel. Can be between 0 and 100, MINimum, MAXimum or DEFault. Default is 1.
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        None
        """
        # Corresponding Command: [:SOURce[c]]:WAIT:AUTO 0|OFF|1|ON
        # Corresponding Command: [:SOURce[c]]:WAIT:GAIN gain
        # Corresponding Command: [:SOURce[c]]:WAIT:OFFSet offset
        # Corresponding Command: [:SOURce[c]]:WAIT[:STATe] 0|OFF|1|ON
        try:
            logging.debug('{!s}: Set bias delay status{:s} to {:g}'.format(__name__, self._log_chans[self._channels][channel], status))
            self._write(':sour{:s}:wait:stat {:d}'.format(self._cmd_chans[self._channels][channel], int(status)))
        except Exception as e:
            logging.error('{!s}: Cannot set bias delay status{:s} to {!s}'.format(__name__, self._log_chans[self._channels][channel], status))
            raise type(e)('{!s}: Cannot set bias delay status{:s} to {!s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], status, e))
        try:
            logging.debug('{!s}: Set bias delay{:s} to {:g}'.format(__name__, self._log_chans[self._channels][channel], offset))
            self._write(':sour{:s}:wait:offs {:g}'.format(self._cmd_chans[self._channels][channel], offset))
        except Exception as e:
            logging.error('{!s}: Cannot set bias delay{:s} to {!s}'.format(__name__, self._log_chans[self._channels][channel], offset))
            raise type(e)('{!s}: Cannot set bias delay{:s} to {!s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], offset, e))
        if 'auto' in kwargs:
            auto = kwargs.get('auto')
            try:
                logging.debug('{!s}: Set auto bias delay{:s} to {!r}'.format(__name__, self._log_chans[self._channels][channel], auto))
                self._write(':sour{:s}:wait:auto {:d}'.format(self._cmd_chans[self._channels][channel], int(auto)))
            except Exception as e:
                logging.error('{!s}: Cannot set auto bias delay{:s} to {!s}'.format(__name__, self._log_chans[self._channels][channel], auto))
                raise type(e)('{!s}: Cannot set auto bias delay{:s} to {!s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], auto, e))
        if 'gain' in kwargs:
            gain = kwargs.get('gain')
            try:
                logging.debug('{!s}: Set gain bias delay{:s} to {!r}'.format(__name__, self._log_chans[self._channels][channel], gain))
                self._write(':sour{:s}:wait:gain {:d}'.format(self._cmd_chans[self._channels][channel], int(gain)))
            except Exception as e:
                logging.error('{!s}: Cannot set gain bias delay{:s} to {!s}'.format(__name__, self._log_chans[self._channels][channel], gain))
                raise type(e)('{!s}: Cannot set gain bias delay{:s} to {!s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], gain, e))
        return

    def get_bias_delay(self, channel=1):
        """
        Gets bias delay <val> of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        val: dict
            Sense delay with respect to the bias trigger.
        """
        # Corresponding Command: [:SOURce[c]]:WAIT:AUTO?
        # Corresponding Command: [:SOURce[c]]:WAIT:GAIN? [gain]
        # Corresponding Command: [:SOURce[c]]:WAIT:OFFSet? [offset]
        # Corresponding Command: [:SOURce[c]]:WAIT[:STATe]?
        try:
            logging.debug('{!s}: Get bias delay{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            return {
                'status': bool(int(self._ask(':sour{:s}:wait:stat?'.format(self._cmd_chans[self._channels][channel])))),
                'offset': float(self._ask(':sour{:s}:wait:offs?'.format(self._cmd_chans[self._channels][channel]))),
                'auto': bool(int(self._ask(':sour{:s}:wait:auto?'.format(self._cmd_chans[self._channels][channel])))),
                'gain': float(self._ask(':sour{:s}:wait:gain?'.format(self._cmd_chans[self._channels][channel])))}
        except Exception as e:
            logging.error('{!s}: Cannot get bias delay{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            raise type(e)('{!s}: Cannot get bias delay{:s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], e))

    def set_sense_delay(self, offset, status=True, channel=1, **kwargs):
        """
        Sets sense delay with respect to the sense trigger to the value <val> that is calculated internally by
            if status is True:
                if auto = True:
                    val = gain*initial_wait_time + offset
                else:
                    val = offset
            else:
                val = 0

        Parameters
        ----------
        offset: float
            Offset value used for calculating the sense wait time for the specified channel. Can be between 0 and 1 seconds, MINimum, MAXimum or DEFault. Default is 0.
        status: bool
        auto: bool
            Initial wait time used for calculating the sense wait time for the specified channel.
        gain: float
            Gain value used for calculating the sense wait time for the specified channel. Can be between 0 and 100, MINimum, MAXimum or DEFault. Default is 1.
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        None
        """
        # Corresponding Command: [:SENSe[c]]:WAIT:AUTO 0|OFF|1|ON
        # Corresponding Command: [:SENSe[c]]:WAIT:GAIN gain
        # Corresponding Command: [:SENSe[c]]:WAIT:OFFSet offset
        # Corresponding Command: [:SENSe[c]]:WAIT[:STATe] 0|OFF|1|ON
        try:
            logging.debug('{!s}: Set sense delay status{:s} to {:g}'.format(__name__, self._log_chans[self._channels][channel], status))
            self._write(':sens{:s}:wait:stat {:d}'.format(self._cmd_chans[self._channels][channel], int(status)))
        except Exception as e:
            logging.error('{!s}: Cannot set sense delay status{:s} to {!s}'.format(__name__, self._log_chans[self._channels][channel], status))
            raise type(e)('{!s}: Cannot set sense delay status{:s} to {!s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], status, e))
        try:
            logging.debug('{!s}: Set sense delay{:s} to {:g}'.format(__name__, self._log_chans[self._channels][channel], offset))
            self._write(':sens{:s}:wait:offs {:g}'.format(self._cmd_chans[self._channels][channel], offset))
        except Exception as e:
            logging.error('{!s}: Cannot set sense delay{:s} to {!s}'.format(__name__, self._log_chans[self._channels][channel], offset))
            raise type(e)('{!s}: Cannot set sense delay{:s} to {!s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], offset, e))
        if 'auto' in kwargs:
            auto = kwargs.get('auto')
            try:
                logging.debug(
                    '{!s}: Set auto sense delay{:s} to {!r}'.format(__name__, self._log_chans[self._channels][channel], auto))
                self._write(':sens{:s}:wait:auto {:d}'.format(self._cmd_chans[self._channels][channel], int(auto)))
            except Exception as e:
                logging.error('{!s}: Cannot set auto sense delay{:s} to {!s}'.format(__name__, self._log_chans[self._channels][channel], auto))
                raise type(e)('{!s}: Cannot set auto sense delay{:s} to {!s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], auto, e))
        if 'gain' in kwargs:
            gain = kwargs.get('gain')
            try:
                logging.debug('{!s}: Set gain sense delay{:s} to {!r}'.format(__name__, self._log_chans[self._channels][channel], gain))
                self._write(':sens{:s}:wait:gain {:d}'.format(self._cmd_chans[self._channels][channel], int(gain)))
            except Exception as e:
                logging.error('{!s}: Cannot set gain sense delay{:s} to {!s}'.format(__name__, self._log_chans[self._channels][channel], gain))
                raise type(e)('{!s}: Cannot set gain sense delay{:s} to {!s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], gain, e))
        return

    def get_sense_delay(self, channel=1):
        """
        Gets sense delay <val> of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        val: dict
            Sense delay with respect to the bias trigger.
        """
        # Corresponding Command: [:SENSe[c]]:WAIT:AUTO?
        # Corresponding Command: [:SENSe[c]]:WAIT:GAIN? [gain]
        # Corresponding Command: [:SENSe[c]]:WAIT:OFFSet? [offset]
        # Corresponding Command: [:SENSe[c]]:WAIT[:STATe]?
        try:
            logging.debug('{!s}: Get sense delay{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            return {
                'status': bool(int(self._ask(':sens{:s}:wait:stat?'.format(self._cmd_chans[self._channels][channel])))),
                'offset': float(self._ask(':sens{:s}:wait:offs?'.format(self._cmd_chans[self._channels][channel]))),
                'auto': bool(int(self._ask(':sens{:s}:wait:auto?'.format(self._cmd_chans[self._channels][channel])))),
                'gain': float(self._ask(':sens{:s}:wait:gain?'.format(self._cmd_chans[self._channels][channel])))}
        except Exception as e:
            logging.error('{!s}: Cannot get sense delay{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            raise type(e)('{!s}: Cannot get sense delay{:s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], e))

    def set_plc(self, plc):
        """
        Sets power line cycle (PLC) to <val>.

        Parameters
        ----------
        plc: int
            Power line frequency setting used for NPLC calculations. Possible values are 50 or 60.

        Returns
        -------
        None
        """
        # Corresponding Command: :SYSTem:LFRequency
        try:
            logging.debug('{!s}: Set PLC to {!s}'.format(__name__, plc))
            self._write('syst:lfr {:d}'.format(plc))
        except Exception as e:
            logging.error('{!s}: Cannot set PLC to {!s}'.format(__name__, plc))
            raise type(e)('{!s}: Cannot set PLC to {!s}\n{!s}'.format(__name__, plc, e))
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
        # Corresponding Command: :SYSTem:LFRequency?
        try:
            logging.debug('{!s}: Get PLC'.format(__name__))
            return int(self._ask('syst:lfr'))
        except Exception as e:
            logging.error('{!s}: Cannot get PLC'.format(__name__))
            raise type(e)('{!s}: Cannot get PLC\n{!s}'.format(__name__, e))

    def set_sense_nplc(self, val, channel=1):
        """
        Sets sense nplc (number of power line cycle) of channel <channel> with the <val>-fold of one power line cycle.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.
        val: float
            Integration aperture for measurements. Must be 'min' (minimum), 'max' (maximum), 'def' (default) or in [4e-4 to 100], [4.8e-4 to 120] for 50 Hz, 60 Hz, respectively.


        Returns
        -------
        None
        """
        # Corresponding Command: :SENSe[c]:<CURRent[:DC]|RESistance|VOLTage[:DC]>:NPLCycles nplc
        # Corresponding Command: :SENSe[c]:<CURRent[:DC]|RESistance|VOLTage[:DC]>:NPLCycles:AUTO mode
        try:
            logging.debug('{!s}: Set sense nplc{:s} to {!s}'.format(__name__, self._log_chans[self._channels][channel],
                                                                    *['auto' if val == -1 else val]))
            self._write(':sens{:s}:{:s}:nplc{!s}'.format(self._cmd_chans[self._channels][channel],
                                                         self._IV_modes[self._sense_mode[channel]],
                                                         *[':auto 1' if val == -1 else ' {!s}'.format(val)]))
        except Exception as e:
            logging.error(
                '{!s}: Cannot set sense nplc{:s} to {!s}'.format(__name__, self._log_chans[self._channels][channel],
                                                                 val))
            raise type(e)('{!s}: Cannot set sense nplc{:s} to {!s}\n{!s}'.format(__name__,
                                                                                 self._log_chans[self._channels][
                                                                                     channel], val, e))
        return

    def get_sense_nplc(self, channel=1):
        """
        Gets sense nplc (number of power line cycle) <val> of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        val: float
            Integration aperture for measurements.
        """
        # Corresponding Command: :SENSe[c]:<CURRent[:DC]|RESistance|VOLTage[:DC]>:NPLCycles? [nplc]
        try:
            logging.debug('{!s}: Get sense nplc{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            return float(self._ask(':sens{:s}:{:s}:nplc'.format(self._cmd_chans[self._channels][channel], self._IV_modes[self._sense_mode[channel]])))
        except Exception as e:
            logging.error('{!s}: Cannot get sense nplc{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            raise type(e)('{!s}: Cannot get sense nplc{:s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], e))

    def get_sense_average(self, channel=1):
        return None

    def set_status(self, status, channel=1):
        """
        Sets output status of channel <channel> to <status>.

        Parameters
        ----------
        status: int
            Output status. Possible values are 0 (off) or 1 (on).
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        None
        """
        # Corresponding Command: :OUTPut[c][:STATe] 1|ON|0|OFF
        try:
            logging.debug('{!s}: Set output status{:s} to {!r}'.format(__name__, self._log_chans[self._channels][channel], status))
            self._write(':outp{:s}:stat {:d}'.format(self._cmd_chans[self._channels][channel], status))
        except Exception as e:
            logging.error('{!s}: Cannot set output status{:s} to {!s}'.format(__name__, self._log_chans[self._channels][channel], status))
            raise type(e)('{!s}: Cannot set output status{:s} to {!s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], status, e))
        return

    def get_status(self, channel=1):
        """
        Gets output status <status> of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        status: int
            Output status. Meanings are 0 (off) and 1 (on).
        """
        # Corresponding Command: :OUTPut[c][:STATe]?
        try:
            logging.debug('{!s}: Get output status{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            return bool(int(self._ask(':outp{:s}:stat'.format(self._cmd_chans[self._channels][channel]))))
        except Exception as e:
            logging.error('{!s}: Cannot get output status{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            raise type(e)('{!s}: Cannot get output status{:s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], e))

    def set_bias_value(self, val, channel=1):
        """"
        Sets bias value of channel <channel> to value <val>.

        Parameters
        ----------
        val: float
            Bias value.
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        None
        """
        # Corresponding Command: [:SOUR[c]]:VOLT: voltage
        # Corresponding Command: :DISPlay:VIEW mode
        try:
            logging.debug('{!s}: Set bias value{:s} to {:g}'.format(__name__, self._log_chans[self._channels][channel], val))
            self._write(':sour{:s}:{:s}:lev {:g}'.format(self._cmd_chans[self._channels][channel], self._IV_modes[self.get_bias_mode(channel=channel)], val))  # necessary to cast as scientific float! (otherwise only >= 1e-6 possible)
            #self._write(':disp:view sing{:d}'.format(channel))
        except Exception as e:
            logging.error(
                '{!s}: Cannot set bias value{:s} to {!s}'.format(__name__, self._log_chans[self._channels][channel], val))
            raise type(e)('{!s}: Cannot set bias value{:s} to {!s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], val, e))
        return

    def get_bias_value(self, channel=1):
        """
        Gets bias value <val> of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        val: float
            Bias value.
        """
        # Corresponding Command: voltage = [:SOUR[c]]:VOLT?
        # Corresponding Command: :MEASure: < CURRent[:DC] | RESistance | VOLTage[:DC] >? [chanlist]
        try:
            logging.debug('{!s}: Get bias value{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            # return float(self._ask(':sour{:s}:{:s}?'.format(self._cmd_chans[self._channels][channel], self._IV_modes[self.get_bias_mode(channel=channel)])))
            #self._write(':disp:view sing{:d}'.format(channel))
            if self.get_status(channel):
                return float(self._ask(':meas:{:s}? (@{})'.format(self._IV_modes[self.get_bias_mode(channel=channel)], channel)).replace('+9.910000E+37', 'nan').replace('9.900000E+37', 'inf'))
            else:
                return float(self._ask(':sour{:s}:{:s}:lev'.format(self._cmd_chans[self._channels][channel], self._IV_modes[self.get_bias_mode(channel=channel)])))
        except Exception as e:
            logging.error('{!s}: Cannot get bias value{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            raise type(e)('{!s}: Cannot get bias value{:s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], e))

    def get_sense_value(self, channel=1):
        """
        Gets sense value of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        val: float
            Sense value.
        """
        # Corresponding Command: [:CHANnel<n>]:MEASure?
        try:
            logging.debug('{!s}: Get sense value{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            # self._write(':disp:view sing{:d}'.format(channel))
            return float(self._ask(':meas:{:s}? (@{})'.format(self._IV_modes[self._sense_mode[channel]], channel)).replace('+9.910000E+37', 'nan').replace('9.900000E+37', 'inf'))
        except Exception as e:
            logging.error('{!s}: Cannot get sense value{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            raise type(e)('{!s}: Cannot get sense value{:s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], e))

    def get_sense_values(self, channel=1):
        """
        Gets sense values of all active sense modes of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        val: numpy.array
            Sense values.
        """
        # Corresponding Command: :MEAS? [chanlist]
        try:
            logging.debug('{!s}: Get sense values of all active sense modes{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            #self._write(':disp:view sing{:d}'.format(channel))
            return np.fromstring(self._ask(':meas? (@{})'.format(channel)).replace('+9.910000E+37', 'nan').replace('9.900000E+37', 'inf'), sep=',', dtype=float)
        except Exception as e:
            logging.error('{!s}: Cannot get sense values of all active sense modes{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            raise type(e)('{!s}: Cannot get sense values of all active sense modes{:s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], e))

    def set_voltage(self, val, channel=1):
        """
        Sets voltage value of channel <channel> to <val>.

        Parameters
        ----------
        val: float
            Bias voltage value.
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        None
        """
        # Corresponding Command: [:SOUR[c]]:VOLT: voltage
        try:
            logging.debug('{:s}: Set voltage value{:s} to {:g}'.format(__name__, self._log_chans[self._channels][channel], val))
            self._write(':sour{:s}:volt {:g}'.format(self._cmd_chans[self._channels][channel], val))
            #self._write(':disp:view sing{:d}'.format(channel))
        except Exception as e:
            logging.error('{!s}: Cannot set voltage value{:s} to {!s}'.format(__name__, self._log_chans[self._channels][channel], val))
            raise type(e)('{!s}: Cannot set voltage value{:s} to {!s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], val, e))
        return

    def get_voltage(self, channel=1):
        """
        Gets voltage value <val> of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        val: float
            Sense voltage value.
        """
        # Corresponding Command: voltage = [:SOUR[c]]:VOLT?
        # Corresponding Command: :MEASure: < CURRent[:DC] | RESistance | VOLTage[:DC] >? [chanlist]
        try:
            logging.debug('{:s}: Get voltage value{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            #self._write(':disp:view sing{:d}'.format(channel))
            # return float(self._ask(':sour{:s}:volt?'.format(self._cmd_chans[self._channels][channel])))
            return float(self._ask(':meas:volt?').replace('+9.910000E+37', 'nan').replace('9.900000E+37', 'inf'))
        except Exception as e:
            logging.error('{!s}: Cannot get voltage value{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            raise type(e)('{!s}: Cannot get voltage value{:s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], e))

    def set_current(self, val, channel=1):
        """
        Sets current value of channel <channel> to <val>.

        Parameters
        ----------
        val: float
            Bias current value.
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        None
        """
        # Corresponding Command: [:SOUR[c]]:CURR: current
        try:
            logging.debug('{:s}: Set current value{:s} to {:g}'.format(__name__, self._log_chans[self._channels][channel], val))
            self._write(':sour{:s}:curr {:g}'.format(self._cmd_chans[self._channels][channel], val))
            #self._write(':disp:view sing{:d}'.format(channel))
        except Exception as e:
            logging.error('{!s}: Cannot set current value{:s} to {!s}'.format(__name__, self._log_chans[self._channels][channel], val))
            raise type(e)('{!s}: Cannot set current value{:s} to {!s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], val, e))
        return

    def get_current(self, channel=1):
        """
        Gets current value <val> of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        val: float
            Sense current value.
        """
        # Corresponding Command: voltage = [:SOUR[c]]:VOLT?
        # Corresponding Command: :READ[:SCALar]: <CURRent|RESistance|SOURce|STATus|TIME|VOLTage>? [chanlist]
        try:
            logging.debug('{:s}: Get current value{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            #self._write(':disp:view sing{:d}'.format(channel))
            # return float(self._ask(':sour{:s}:curr?'.format(self._cmd_chans[self._channels][channel])))
            return float(self._ask(':meas:curr?').replace('+9.910000E+37', 'nan').replace('9.900000E+37', 'inf'))
        except Exception as e:
            logging.error('{!s}: Cannot get current value{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            raise type(e)('{!s}: Cannot get current value{:s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], e))

    def get_resistance(self, channel=1):
        """
        Gets resistance value <val> of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        val: float
            Sense resistance value.
        """
        # Corresponding Command: voltage = [:SOUR[c]]:VOLT?
        # Corresponding Command: :READ[:SCALar]: <CURRent|RESistance|SOURce|STATus|TIME|VOLTage>? [chanlist]
        # Corresponding Command: :MEASure:<CURRent[:DC]|RESistance|VOLTage[:DC]>? [chanlist]
        try:
            logging.debug('{:s}: Get resistance value{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            #self._write(':disp:view sing{:d}'.format(channel))
            # return float(self._ask(':sour{:s}:res?'.format(self._cmd_chans[self._channels][channel])))
            return float(self._ask(':meas:res?').replace('+9.910000E+37', 'nan').replace('9.900000E+37', 'inf'))
        except Exception as e:
            logging.error('{!s}: Cannot get resistance value{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            raise type(e)('{!s}: Cannot get resistance value{:s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], e))

    def get_IV(self, channel=1):
        """
        Gets both current value <I_val> and voltage value <V_val> of channel <channel>.

        Parameters
        ----------
        channel: int
           Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        I_val: float
            Sense current value.
        V_val: float
            Sense voltage value.
        """
        # Corresponding Command: :MEASure? [chanlist]
        try:
            logging.debug('{:s}: Get current and voltage value{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            #self._write(':disp:view sing{:d}'.format(channel))
            return np.fromstring(self._ask(':meas? (@{})'.format(channel)).replace('+9.910000E+37', 'nan').replace('9.900000E+37', 'inf'), sep=',', dtype=float)[:2][::-1]
        except Exception as e:
            logging.error('{!s}: Cannot get current and voltage value{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            raise type(e)('{!s}: Cannot get current and voltage value{:s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], e))

    def ramp_bias(self, stop, step, step_time=0.1, channel=1):
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
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1. (default)

        Returns
        -------
        None
        """
        start = self.get_bias_value(channel=channel)
        if stop < start:
            step = -step
        for val in np.arange(start, stop, step) + step:
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
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1. (default)

        Returns
        -------
        None
        """
        if self.get_bias_mode(channel=channel):  # 1 (voltage bias)
            return self.ramp_bias(stop=stop, step=step, step_time=step_time, channel=channel)
        elif not self.get_bias_mode(channel=channel):  # 0 (current bias)
            logging.error(__name__ + ': Cannot ramp voltage{:s} in the current bias'.format(self._log_chans[self._channels][channel]))
            raise ValueError(__name__ + ': Cannot ramp voltage{:s} in the current bias'.format(self._log_chans[self._channels][channel]))

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
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1. (default)

        Returns
        -------
        None
        """
        if not self.get_bias_mode(channel=channel):  # 0 (current bias)
            return self.ramp_bias(stop=stop, step=step, step_time=step_time, channel=channel)
        elif self.get_bias_mode(channel=channel):  # 1 (voltage bias)
            logging.error(__name__ + ': Cannot ramp current{:s} in the voltage bias'.format(self._log_chans[self._channels][channel]))
            raise ValueError(__name__ + ': Cannot ramp current{:s} in the voltage bias'.format(self._log_chans[self._channels][channel]))

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
            if len(channels) == int(not mode) + 1:
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
            self._set_defaults_docstring()
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

    def _set_sweep_start(self, val, channel=1):
        """
        Sets sweep start value of channel <channel> to <val>.

        Parameters
        ----------
        val: float
            Start value of sweep.
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        None
        """
        # Corresponding Command: [:SOURce[c]]:<CURRent|VOLTage>:<STARt|STOP> data
        try:
            logging.debug('{!s}: Set sweep start{:s} to {:g}'.format(__name__, self._log_chans[self._channels][channel], val))
            self._write(':sour{:s}:{:s}:star {:g}'.format(self._cmd_chans[self._channels][channel], self._IV_modes[self.get_bias_mode(channel)], val))
        except Exception as e:
            logging.error('{!s}: Cannot set sweep start{:s} to {!s}'.format(__name__, self._log_chans[self._channels][channel], val))
            raise type(e)('{!s}: Cannot set sweep start{:s} to {!s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], val, e))
        return

    def _get_sweep_start(self, channel=1):
        """
        Gets sweep start value of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        val: float
            Start value of sweep.
        """
        # Corresponding Command: [:SOURce[c]]:<CURRent|VOLTage>:<STARt|STOP>? [data]
        try:
            logging.debug('{!s}: Get sweep start{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            return float(self._ask(':sour{:s}:{:s}:star'.format(self._cmd_chans[self._channels][channel], self._IV_modes[self.get_bias_mode(channel)])))
        except Exception as e:
            logging.error('{!s}: Cannot get sweep start{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            raise type(e)('{!s}: Cannot get sweep start{:s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], e))

    def _set_sweep_stop(self, val, channel=1):
        """
        Sets sweep stop value of channel <channel> to <val>.

        Parameters
        ----------
        val: float
            Stop value of sweep.
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        None
        """
        # Corresponding Command: [:SOURce[c]]:<CURRent|VOLTage>:<STARt|STOP> data
        try:
            logging.debug('{!s}: Set sweep stop{:s} to {:g}'.format(__name__, self._log_chans[self._channels][channel], val))
            self._write(':sour{:s}:{:s}:stop {:g}'.format(self._cmd_chans[self._channels][channel], self._IV_modes[self.get_bias_mode(channel)], val))
        except Exception as e:
            logging.error('{!s}: Cannot set sweep stop{:s} to {!s}'.format(__name__, self._log_chans[self._channels][channel], val))
            raise type(e)('{!s}: Cannot set sweep stop{:s} to {!s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], val, e))
        return

    def _get_sweep_stop(self, channel=1):
        """
        Gets sweep stop value of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        val: float
            Stop value of sweep.
        """
        # Corresponding Command: [:SOURce[c]]:<CURRent|VOLTage>:<STARt|STOP>? [data]
        try:
            logging.debug('{!s}: Get sweep stop{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            return float(self._ask(':sour{:s}:{:s}:stop'.format(self._cmd_chans[self._channels][channel], self._IV_modes[self.get_bias_mode(channel)])))
        except Exception as e:
            logging.error('{!s}: Cannot get sweep stop{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            raise type(e)('{!s}: Cannot get sweep stop{:s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], e))

    def _set_sweep_step(self, val, channel=1):
        """
        Sets sweep step value of channel <channel> to <val>.

        Parameters
        ----------
        val: float
            Step value of sweep.
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        None
        """
        # Corresponding Command: [:SOURce[c]]:<CURRent|VOLTage>:STEP step
        try:
            logging.debug('{!s}: Set sweep step{:s} to {:g}'.format(__name__, self._log_chans[self._channels][channel], val))
            self._write(':sour{:s}:{:s}:step {:g}'.format(self._cmd_chans[self._channels][channel], self._IV_modes[self.get_bias_mode(channel)], val))
        except Exception as e:
            logging.error('{!s}: Cannot set sweep step{:s} to {!s}'.format(__name__, self._log_chans[self._channels][channel], val))
            raise type(e)('{!s}: Cannot set sweep step{:s} to {!s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], val, e))
        return

    def _get_sweep_step(self, channel=1):
        """
        Gets sweep step value of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        val:
            Step value of sweep.
        """
        # Corresponding Command: [:SOURce[c]]:<CURRent|VOLTage>:STEP? [step]
        try:
            logging.debug('{!s}: Get sweep step{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            return float(self._ask(':sour{:s}:{:s}:step'.format(self._cmd_chans[self._channels][channel], self._IV_modes[self.get_bias_mode(channel)])))
        except Exception as e:
            logging.error('{!s}: Cannot get sweep step{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            raise type(e)('{!s}: Cannot get sweep step{:s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], e))

    def _get_sweep_nop(self, channel=1):
        """
        Gets sweeps number of points (nop) of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        val:
            Number of points of sweep.
        """
        # Corresponding Command: [:SOURce[c]]:<CURRent|VOLTage>:POINts? [points])
        try:
            logging.debug('{!s}: Get sweep nop{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            return int(self._ask(':sour{:s}:{:s}:poin'.format(self._cmd_chans[self._channels][channel],
                                                              self._IV_modes[self.get_bias_mode(channel)])))
        except Exception as e:
            logging.error('{!s}: Cannot get sweep nop{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            raise type(e)('{!s}: Cannot get sweep nop{:s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], e))

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
        # Corresponding Command: [:SOURce[c]]:<CURRent|VOLTage>:MODE mode
        # Corresponding Command: [:SOUR[c]]:SWE:RANG mode
        # Corresponding Command: [:SOURce[c]]:SWEep:SPACing LOGarithmic|LINear (default)
        # Corresponding Command: [:SOURce[c]]:SWEep:STAir SINGle (default)|DOUBle
        # Corresponding Command: [:SOURce[c]]:SWEep:DIRection DOWN|UP (default)
        # Corresponding Command: :TRIGger[c]<:ACQuire|:TRANsient|[:ALL]>:SOURce[:SIGNal] source
        # Corresponding Command: :TRIGger[c]<:ACQuire|:TRANsient|[:ALL]>:SOURce[:SIGNal] source
        # Corresponding Command: :TRIGger<:ACQuire|:TRANsient|[:ALL]>:COUNt
        # Corresponding Command: :DISPlay:VIEW mode
        if not self._sweep_mode:  # 0 (VV-mode)
            channel_bias, channel_sense = self._sweep_channels
            try:
                # bias channel
                self._write(':sour{:s}:{:s}:mode swe'.format(self._cmd_chans[self._channels][channel_bias], self._IV_modes[self.get_bias_mode(channel_bias)]))
                self._write(':sour{:s}:swe:rang best'.format(self._cmd_chans[self._channels][channel_bias]))
                self._write(':sour{:s}:swe:spac lin'.format(self._cmd_chans[self._channels][channel_bias]))
                self._write(':sour{:s}:swe:sta sing'.format(self._cmd_chans[self._channels][channel_bias]))
                self._write(':sour{:s}:swe:dir up'.format(self._cmd_chans[self._channels][channel_bias]))
                self._set_sweep_start(val=float(sweep[0]), channel=channel_bias)
                self._set_sweep_stop(val=float(sweep[1]), channel=channel_bias)
                self._set_sweep_step(val=float(sweep[2] * np.sign(float(sweep[1]) - float(sweep[0]))), channel=channel_bias)
                self.set_bias_value(val=self._get_sweep_start(channel=channel_bias), channel=channel_bias)
                self._write(':trig{:d}:acq:sour aint'.format(channel_bias))
                self._write(':trig{:d}:tran:sour aint'.format(channel_bias))
                self._write(':trig{:d}:all:count {:d}'.format(channel_bias, self._get_sweep_nop(channel=channel_bias)))
                # sense channel
                self._write(':sour{:s}:{:s}:mode swe'.format(self._cmd_chans[self._channels][channel_sense], self._IV_modes[self.get_bias_mode(channel_sense)]))
                self._write(':sour{:s}:swe:rang best'.format(self._cmd_chans[self._channels][channel_sense]))
                self._write(':sour{:s}:swe:spac lin'.format(self._cmd_chans[self._channels][channel_sense]))
                self._write(':sour{:s}:swe:sta sing'.format(self._cmd_chans[self._channels][channel_sense]))
                self._write(':sour{:s}:swe:dir up'.format(self._cmd_chans[self._channels][channel_sense]))
                self._set_sweep_start(val=0, channel=channel_sense)
                self._set_sweep_stop(val=0, channel=channel_sense)
                self._write('sour{:d}:curr:poin {:d}'.format(channel_sense, self._get_sweep_nop()))
                self._write(':trig{:d}:acq:sour aint'.format(channel_sense))
                self._write(':trig{:d}:tran:sour aint'.format(channel_sense))
                self._write(':trig{:d}:all:count {:d}'.format(channel_sense, self._get_sweep_nop(channel=channel_sense)))
                # general
                self.set_sync(True)
                self.set_display('dual')
            except Exception as e:
                logging.error('{!s}: Cannot set sweep parameters of channels {!s} to {!s}'.format(__name__, self._sweep_channels, sweep))
                raise type(e)('{!s}: Cannot set sweep parameters of channels {!s} to {!s}\n{!s}'.format(__name__, self._sweep_channels, sweep, e))
        elif self._sweep_mode in [1, 2]:  # 1 (IV-mode) | 2 (VI-mode)
            channel_bias, channel_sense = self._sweep_channels * 2
            try:
                logging.debug('{!s}: Set sweep parameters of channel {!s} to {!s}'.format(__name__, self._sweep_channels, sweep))
                self._write(':sour{:s}:{:s}:mode swe'.format(self._cmd_chans[self._channels][channel_bias], self._IV_modes[self.get_bias_mode(channel_bias)]))
                self._write(':sour{:s}:swe:rang best'.format(self._cmd_chans[self._channels][channel_bias]))
                self._write(':sour{:s}:swe:spac lin'.format(self._cmd_chans[self._channels][channel_bias]))
                self._write(':sour{:s}:swe:sta sing'.format(self._cmd_chans[self._channels][channel_bias]))
                self._write(':sour{:s}:swe:dir up'.format(self._cmd_chans[self._channels][channel_bias]))
                self._set_sweep_start(val=float(sweep[0]), channel=channel_bias)
                self._set_sweep_stop(val=float(sweep[1]), channel=channel_bias)
                self._set_sweep_step(val=float(sweep[2] * np.sign(float(sweep[1]) - float(sweep[0]))), channel=channel_bias)
                self.set_bias_value(val=self._get_sweep_start(channel=channel_bias), channel=channel_bias)
                self._write(':trig:acq:sour aint')
                self._write(':trig:tran:sour aint')
                self._write(':trig:all:count {:d}'.format(self._get_sweep_nop(channel=channel_bias)))
                self.set_display('grap')
                ### TODO: auto scale display
            except Exception as e:
                logging.error('{!s}: Cannot set sweep parameters of channel {!s} to {!s}'.format(__name__, self._sweep_channels, sweep))
                raise type(e)('{!s}: Cannot set sweep parameters of channel {!s} to {!s}\n{!s}'.format(__name__, self._sweep_channels, sweep, e))
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
        # Corresponding Command: :INITiate[:IMMediate]<:ACQuire|:TRANsient|[:ALL]> [chanlist]
        # Corresponding Command: :FETCh:ARRay:<CURRent|RESistance|SOURce|STATus|TIME|VOLTage>? [chanlist]
        try:
            if not self._sweep_mode:  # 0 (VV-mode)
                channel_bias, channel_sense = self._sweep_channels
                logging.debug('{!s}: Take sweep data of channels {!s}'.format(__name__, self._sweep_channels))
                self._visainstrument.write(':init (@1,2)')
                self._wait_for_transition_idle(channel=channel_bias)
                bias_values = np.fromstring(self._ask(':fetc:arr:volt? (@{:d})'.format(channel_bias)).replace('+9.910000E+37', 'nan').replace('9.900000E+37', 'inf'), sep=',', dtype=float)
                sense_values = np.fromstring(self._ask(':fetc:arr:volt? (@{:d})'.format(channel_sense)).replace('+9.910000E+37', 'nan').replace('9.900000E+37', 'inf'), sep=',', dtype=float)
                return bias_values, sense_values
            elif self._sweep_mode in [1, 2]:  # 1 (IV-mode) | 2 (VI-mode)
                channel_bias, channel_sense = self._sweep_channels * 2
                logging.debug('{!s}: Take sweep data of channel {!s}'.format(__name__, self._sweep_channels))
                self._visainstrument.write(':init')
                self._wait_for_transition_idle(channel=channel_bias)
                I_values = np.fromstring(self._ask(':fetc:arr:curr?').replace('+9.910000E+37', 'nan').replace('9.900000E+37', 'inf'), sep=',', dtype=float)
                V_values = np.fromstring(self._ask(':fetc:arr:volt?').replace('+9.910000E+37', 'nan').replace('9.900000E+37', 'inf'), sep=',', dtype=float)
                return (I_values, V_values)[::int(np.sign(.5 - self.get_sweep_bias()))]
        except Exception as e:
            logging.error('{!s}: Cannot take sweep data of channel {!s}'.format(__name__, self._sweep_channels))
            raise type(e)('{!s}: Cannot take sweep data of channel {!s}\n{!s}'.format(__name__, self._sweep_channels, e))

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

    def get_measurement_ccr(self):
        """
        Gets the entire measurement condition code register (ccr)

        Parameters
        ----------
        None

        Returns
        -------
        ccr: list of booleans
            Operation measurement code register. Entries are
                0: Ch1 Limit Summary
                1: Ch1 Reading Available
                2: Ch1 Reading Overflow
                3: Ch1 Buffer Available
                4: Ch1 Buffer Full
                5:
                6: Ch2 Limit Summary
                7: Ch2 Reading Available
                8: Ch2 Reading Overflow
                9: Ch2 Buffer Available
                10: Ch2 Buffer Full
                11:
                12:
                13:
                14:
                15:
        """
        # Corresponding Command: :STATus:<MEASurement|OPERation|QUEStionable>:ENABle mask
        # Corresponding Command: :STATus:<MEASurement|OPERation|QUEStionable>:CONDition?
        try:
            logging.debug('{!s}: Get measurement ccr'.format(__name__))
            self._write(':stat:meas:enab 1')
            ccr = int(self._ask(':stat:meas:cond'))
            ans = []
            for i in range(16):
                ans.append(bool((ccr >> i) % 2))
            return ans
        except Exception as e:
            logging.error('{!s}: Cannot get measurement ccr'.format(__name__))
            raise type(e)('{!s}: Cannot get measurement ccr\n{!s}'.format(__name__, e))

    def print_measurement_ccr(self):
        """
        Prints the entire measurement condition code register (ccr) including explanation.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        ccr = self.get_measurement_ccr()
        msg = [('\n\t{:36s}:{!r}\t({:s})'.format(sb[0], ccr[i], sb[1])) for i, sb in enumerate(self.measurement_ccr) if sb != ('', '')]
        print('Measurement ccr :{:s}'.format(''.join(msg)))
        return

    def get_operation_ccr(self):
        """
        Gets the entire operation condition code register (ccr)

        Parameters
        ----------
        None

        Returns
        -------
        ccr: list of booleans
            Operation condition code register. Entries are
                0: Calibration/Self-Test Running
                1: Ch1 Transition Idle
                2: Ch1 Waiting for Transition Trigger
                3: Program Running
                4: Ch1 Waiting for Transition Arm
                5: Ch1 Acquire Idle
                6: Ch1 Waiting for Acquire Trigger
                7: Ch1 Waiting for Acquire Arm
                8: Ch2 Transition Idle
                9: Ch2 Waiting for Transition Trigger
                10: Ch2 Waiting for Transition Arm
                11: Ch2 Acquire Idle
                12: Ch2 Waiting for Acquire Trigger
                13: Ch2 Waiting for Acquire Arm
                14: Instrument Locked
                15: Program Running
        """
        # Corresponding Command: :STATus:<MEASurement|OPERation|QUEStionable>:ENABle mask
        # Corresponding Command: :STATus:<MEASurement|OPERation|QUEStionable>:CONDition?
        try:
            logging.debug('{!s}: Get operation ccr'.format(__name__))
            self._write(':stat:oper:enab 1')
            ccr = int(self._ask(':stat:oper:cond'))
            ans = []
            for i in range(16):
                ans.append(bool((ccr >> i) % 2))
            return ans
        except Exception as e:
            logging.error('{!s}: Cannot get operation ccr'.format(__name__))
            raise type(e)('{!s}: Cannot get operation ccr\n{!s}'.format(__name__, e))

    def print_operation_ccr(self):
        """
        Prints the entire operation condition code register (ccr) including explanation.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        ccr = self.get_operation_ccr()
        msg = [('\n\t{:36s}:{!r}\t({:s})'.format(sb[0], ccr[i], sb[1])) for i, sb in enumerate(self.operation_ccr) if sb != ('', '')]
        print('Operation ccr :{:s}'.format(''.join(msg)))
        return

    def get_questionable_ccr(self):
        """
        Gets the entire questionable condition code register (ccr)

        Parameters
        ----------
        None

        Returns
        -------
        ccr: list of booleans
            Questionable condition code register. Entries are
                0: Voltage Summary
                1: Current Summary
                2: Ch1 Output Protection
                3: Ch2 Output Protection
                4: Temp. Summary
                5:
                6:
                7:
                8: Calibration Summary
                9: Self-Test Summary
                10: Interlock
                11: Ch1 Transient Event Lost
                12: Ch2 Transient Event Lost
                13: Ch1 Acquire Event Lost
                14: Ch2 Acquire Event Lost
                15:
        """
        # Corresponding Command: :STATus:<MEASurement|OPERation|QUEStionable>:ENABle mask
        # Corresponding Command: :STATus:<MEASurement|OPERation|QUEStionable>:CONDition?
        try:
            logging.debug('{!s}: Get questionable ccr'.format(__name__))
            self._write(':stat:ques:enab 1')
            ccr = int(self._ask(':stat:ques:cond'))
            ans = []
            for i in range(16):
                ans.append(bool((ccr >> i) % 2))
            return ans
        except Exception as e:
            logging.error('{!s}: Cannot get questionable ccr'.format(__name__))
            raise type(e)('{!s}: Cannot get questionable ccr\n{!s}'.format(__name__, e))

    def print_questionable_ccr(self):
        """
        Prints the entire questionable condition code register (ccr) including explanation.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        ccr = self.get_questionable_ccr()
        msg = [('\n\t{:36s}:{!r}\t({:s})'.format(sb[0], ccr[i], sb[1])) for i, sb in enumerate(self.questionable_ccr) if sb != ('', '')]
        print('Questionable ccr :{:s}'.format(''.join(msg)))
        return

    def get_transition_idle(self, channel=1):
        """
        Gets event of operation condition code register (ccr) entry "Transition idle" <val> of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        val: bool
            "Transition idle" entry of operation condition code register.
        """
        # Corresponding Command: :STATus:<MEASurement|OPERation|QUEStionable>:ENABle mask
        # Corresponding Command: :STATus:<MEASurement|OPERation|QUEStionable>:CONDition?
        try:
            logging.debug('''{!s}: Get operation ccr condition "Transition idle"{:s}'''.format(__name__, self._log_chans[self._channels][channel]))
            self._visainstrument.write(':stat:oper:enab 1')
            return bool((int(self._visainstrument.query(':stat:oper:cond?')) >> (1 + 6 * (channel - 1))) % 2)
        except Exception as e:
            logging.error('{!s}: Cannot get operation ccr condition "Transition idle"{:s}'.format(__name__, self._log_chans[self._channels][channel]))
            raise type(e)('{!s}: Cannot get operation ccr condition "Transition idle"{:s}\n{!s}'.format(__name__, self._log_chans[self._channels][channel], e))

    def _wait_for_transition_idle(self, channel=1):
        """
        Waits until the event of operation condition code register (ccr) entry "Transition idle" of channel <channel> occurs.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels. Default is 1.

        Returns
        -------
        None
        """
        while not (self.get_transition_idle(channel=channel)):
            time.sleep(100e-3)
        return

    def set_display(self, mode):
        """
        Sets the display mode to <mode>.

        Parameters
        ----------
        mode: str
            Bias trigger mode. Must be 'SINGle1' (channel 1), 'SINGle2' (channel 2), 'DUAL' (channel 1 & 2), 'GRAPh' (xy-graph of sweeps).

        Returns
        -------
        None
        """
        # Corresponding Command: :DISPlay:VIEW
        if mode.lower() in ('sing1', 'single1', 'sing2', 'single2', 'dual', 'grap', 'graph'):
            logging.debug('{!s}: Set display to {:s}'.format(__name__, mode))
            self._write(':disp:view {:s}'.format(mode))
        else:
            logging.error('{:s}: Cannot set display to {!s}'.format(__name__, mode))
            raise ValueError('{:s}: Cannot set display to {!s}'.format(__name__, mode))

    def set_defaults(self, sweep_mode=None):
        """
        Sets default settings. Actual settings are:
        default parameters
        Parameters
        ----------
        sweep_mode: int
            Sweep mode denoting bias and sense modes. Possible values are 0 (VV-mode), 1 (IV-mode) or 2 (VI-mode). Default is 1

        Returns
        -------
        None
        """
        # Corresponding Command: :SYSTem:BEEPer:STATe
        self.reset()
        # beeper off
        self._write(':syst:beep:stat 0')
        self._write(':sens:func:on:all')  # enable all sense functions (voltage, current, resistance)
        self._write(''':sens:func:off "res"''')  # disable resistance
        # distinguish different sweep modes
        if sweep_mode is not None:
            self.set_sweep_mode(sweep_mode)
        # set values
        for i, channel in enumerate(self._sweep_channels[:self._channels]):
            for func, param in self._defaults[self._sweep_mode][i].items():
                func(param, channel=channel)
                # eval('map(lambda channel, self=self: self.set_{:s}({!s}, channel=channel), [{:d}])'.format(key_parameter, val_parameter, channel))
                # eval('self.set_{:s}({!s}, channel={:d})'.format(key_parameter, val_parameter, channel))
        return

    def _set_defaults_docstring(self):
        '''
        Sets docstring of "set_defaults" method with actual default settings.

        Parameters
        ----------
        None

        Returns
        -------
        None
        '''
        pass
        new = 'sweep mode: {:d}:\n'.format(self._sweep_mode) + ''.join(['\t    channel: {:d}\n'.format(channel) + ''.join(['\t\t{:s}: {!s}\n'.format(func.__name__.replace('set_', ''), param) for func, param in self._defaults[self._sweep_mode][i].items()]) for i, channel in enumerate(self._sweep_channels)])
        self.set_defaults.__func__.__doc__ = self.set_defaults.__func__.__doc__.replace(self._default_str, new)
        self._default_str = new
        return

    def get_all(self, channel=None):
        """
        Prints all settings of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one channel and 1 or 2 for SMUs with two channels or None for both channels. Default is None.

        Returns
        -------
        None
        """
        logging.debug('{:s}: Get all'.format(__name__))
        for chan in np.arange(self._channels) + 1 if channel == None else [channel]:
            print('channel: {:d}'.format(chan))
            print('\tmeasurement mode   = {:s}'.format(self._measurement_modes[self.get_measurement_mode(channel=chan)]))
            print('\tbias mode          = {:s}'.format(self._IV_modes[self.get_bias_mode(channel=chan)]))
            print('\tsense mode         = {:s}'.format(self._IV_modes[self.get_sense_mode(channel=chan)]))
            print('\tbias range         = {:1.0e}{:s}'.format(self.get_bias_range(), self._IV_units[self.get_bias_mode(channel=chan)]))
            print('\tsense range        = {:1.0e}{:s}'.format(self.get_sense_range(), self._IV_units[self.get_sense_mode(channel=chan)]))
            print('\tbias delay         = {!s}'.format(self.get_bias_delay(channel=chan)))
            print('\tsense delay        = {!s}'.format(self.get_sense_delay(channel=chan)))
            print('\tsense nplc         = {:f}'.format(self.get_sense_nplc(channel=chan)))
            print('\tstatus             = {!r}'.format(self.get_status(channel=chan)))
            if self.get_status(channel=chan):
                print('\tbias value         = {:g}{:s}'.format(self.get_bias_value(channel=chan), self._IV_units[self.get_bias_mode(channel=chan)]))
                print('\tsense value        = {:g}{:s}'.format(self.get_sense_value(channel=chan), self._IV_units[self.get_sense_mode(channel=chan)]))
            print('\tsweep start        = {:g}{:s}'.format(self._get_sweep_start(channel=chan), self._IV_units[self.get_bias_mode(channel=chan)]))
            print('\tsweep stop         = {:g}{:s}'.format(self._get_sweep_stop(channel=chan), self._IV_units[self.get_bias_mode(channel=chan)]))
            print('\tsweep step         = {:g}{:s}'.format(self._get_sweep_step(channel=chan), self._IV_units[self.get_bias_mode(channel=chan)]))
            print('\tsweep nop          = {:d}'.format(self._get_sweep_nop(channel=self._sweep_channels[0])))
        print('plc                = {:f}Hz'.format(self.get_plc()))
        for err in self.get_error():
            print('error              = {:d}\t{:s}'.format(err[0], err[1]))
        self.print_measurement_ccr()
        self.print_operation_ccr()
        self.print_questionable_ccr()
        return

    def reset(self):
        """
        Resets the instrument or a single channel to default conditions.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        # Corresponding Command: *RST
        try:
            logging.debug('{!s}: Reset instrument to factory settings'.format(__name__))
            self._write('*RST')
        except Exception as e:
            logging.error('{!s}: Cannot reset instrument to factory settings'.format(__name__))
            raise type(e)('{!s}: Cannot reset instrument to factory settings\n{!s}'.format(__name__, e))
        return

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
        # Corresponding Command: :SYSTem:ERRor:ALL?
        # :SYSTem:ERRor:CODE:ALL?
        # :SYSTem:ERRor:CODE[:NEXT]?
        # :SYSTem:ERRor:COUNt?
        # :SYSTem:ERRor[:NEXT]?
        try:
            logging.debug('{!s}: Get errors of instrument'.format(__name__))
            err = [self._visainstrument.query(':syst:err:all?').rstrip().split(',', 1)]
            err = [[int(float(e[0])), str(e[1])] for e in err]
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
        if len(errors) == 1 and errors[0][0] == 0:  # no error
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
        # Corresponding Command: *CLS
        try:
            logging.debug('{!s}: Clears error of instrument'.format(__name__))
            self._write('*CLS')
        except Exception as e:
            logging.error('{!s}: Cannot clears error of instrument'.format(__name__))
            raise type(e)('{!s}: Cannot clears error of instrument\n{!s}'.format(__name__, e))
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
        parlist = {'measurement_mode': {'channels': range(1, self._channels + 1)},
                   'bias_mode': {'channels': range(1, self._channels + 1)},
                   'sense_mode': {'channels': range(1, self._channels + 1)},
                   'bias_range': {'channels': range(1, self._channels + 1)},
                   'sense_range': {'channels': range(1, self._channels + 1)},
                   'bias_trigger': {'channels': range(1, self._channels + 1)},
                   'sense_trigger': {'channels': range(1, self._channels + 1)},
                   'bias_delay': {'channels': range(1, self._channels + 1)},
                   'sense_delay': {'channels': range(1, self._channels + 1)},
                   'bias_value': {'channels': range(1, self._channels + 1)},
                   'plc': {'channels': [None]},
                   'sense_nplc': {'channels': range(1, self._channels + 1)},
                   'status': {'channels': range(1, self._channels + 1)},
                   }
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
