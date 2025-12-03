# MG@KIT 04/2022
"""
qkit instrument driver for qdevil QDAC-II.
 +- 24 channel low noise voltage source.
"""

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

import logging

import qkit
from qkit.core.instrument_base import Instrument
from qkit import visa
import numpy as np
import time

class qdevil_qdacII(Instrument):
    """
    Instrument class for QDevil QDAC-II.


    """

    # SENSe[:CURRent]: RANGe(Defines the current sensing range, HIGH(default) or LOW.
    # SENS:CURR:RANG?
    # SENS:CURR:RANG HIGH / LOW  # +/-10V / +/-2V
    #
    # READ[:CURRent]?
    # READ:CURR < 1 >?
    #
    # SOURce[n][:VOLTage]: RANGe[?] {LOW | HIGH}[, channel_list]
    # SOURce[n][:VOLTage]: RANGe:LOW: {MINimum | MAXimum}[?] [, channel_list]
    # SOURce[n][:VOLTage]: RANGe:HIGH: {MINimum | MAXimum}[?] [, channel_list]
    # SOURce[n][:VOLTage]: FILTer[:LOWPass][?] {DC | MEDium | HIGH}[, channel_list]
    # SOURce[n]: DC[:VOLTage]:MODE[?] FIXed | SWEep | LIST[, channel_list]
    # SOURce[n][:DC]: VOLTage[:LEVel[:IMMediate[:AMPLitude]]]:LAST? [, channel_list]

    def __init__(self, name, address, port=5025):
        """
        Initialize qkit paramters and connect to the device.
        """

        logging.info(__name__ + " : Initializing Instrument")
        Instrument.__init__(self, name, tags=["physical"])

        self._address = address
        self._port = port
        try:
            self._visainstrument = visa.instrument("TCPIP::{:s}::{:d}::SOCKET".format(self._address, self._port))
        except Exception as detail:
            logging.error("Connection to QDvil Instrument not possible. Original error: {:s}".format(detail))
        self._visainstrument.read_termination = "\n"
        self._visainstrument.write_termination = "\n"
        self._visainstrument.query_delay = 0.01  # Documentation says it can take 10ms for the packets to be processed.

        identity = str(self._visainstrument.query("*IDN?")).strip()
        logging.info(f"Connected to {identity}")
        if "QDevil, QDAC-II" not in identity:
            logging.warning(f"Suspicious identity of QDevil Device: '{identity}'")

        # initial variables
        self._channels = 24

        # new parameter for initialization
        self._current_channel_offsets = np.zeros(24, dtype=float)

    def remove(self):
        self._visainstrument.close()
        super().remove()

    def write(self, cmd, await_end=True):
        """
        Sends a visa command <cmd>, waits until "operation complete" and raises eventual errors of the device.

        Parameters
        ----------
        cmd: str
            Command that is send to the instrument via pyvisa and NI-VISA backend.

        Returns
        -------
        None
        """
        assert not cmd.strip().endswith("?"), "Attempting to write Query!"
        logging.debug("VISA Write, PC -> %s : %s", self.get_name(), cmd)
        with self._visainstrument.lock_context():
            self._visainstrument.write(cmd)
            if await_end:
                # According to the manual, section 6.3.1, the QDevil executes all command in sequence.
                # To check if it has finished, executing a small query, such as the status byte, is recommended.
                # The assertion here does two things: Ensure the system is in a sane state, and second, synchronization.
                self.assert_status(cmd_ref=cmd)
        return

    def execute(self, *commands, await_end=True, individual_wait=False):
        """
        Executes a sequency of commands and synchronizes in the end. Allows for faster operation.

        Each command is sent individually. This is done to use consistent checking logic.
        :param individual_wait: For debug purposes. Check status after each command.
        :param commands: A single command or list of commands. Strings.
        :param await_end: Wait for the excution to end, if True.
        :return:
        """
        for command in commands:
            self.write(command, await_end=individual_wait)
        if await_end:
            self.assert_status(cmd_ref=commands[-1])

    def query(self, cmd):
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
        # Sanitize cmd string
        cmd = cmd.strip()  # Remove spaces
        cmd = cmd if "?" in cmd and ";" not in cmd else cmd + "?"  # Ensure CMD ends with '?'

        # Send query and log everything.
        logging.debug("VISA Query, PC -> %s : %s", self.get_name(), cmd)
        with self._visainstrument.lock_context():
            ans = self._visainstrument.query(cmd).rstrip()
        logging.debug("VISA Query, PC <- %s : %s", self.get_name(), ans)

        # Return data.
        return ans

    def get_status(self) -> int:
        """
        Queries the status byte register using '*STB?'

        :return: A byte representing the device status. 0 Means everything is ok.
        """
        return int(self.query("*STB?"))

    def assert_status(self, cmd_ref="None"):
        """
        Assert the status is ok.
        :return: None, if everything is ok.
        :raises: AssertionError, if status is not ok.
        """
        reported_status = self.get_status()
        assert reported_status & 4 == 0, \
            f"Status:{reported_status} Error! After: {cmd_ref}, Message:\n{self.query('SYST:ERR:ALL')}"

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
        try:
            logging.debug("{!s}: Clears error of instrument".format(__name__))
            self.write("*CLS")
        except Exception as e:
            logging.error("{!s}: Cannot clears error of instrument".format(__name__))
            raise type(e)("{!s}: Cannot clears error of instrument\n{!s}".format(__name__, e))
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
        try:
            logging.debug("{!s}: Reset instrument to factory settings".format(__name__))
            self.write("*RST", await_end=False)  # We don't wail till we're done, because we will time out.
        except Exception as e:
            logging.error("{!s}: Cannot reset instrument to factory settings".format(__name__))
            raise type(e)("{!s}: Cannot reset instrument to factory settings\n{!s}".format(__name__, e))
        return

    def restart(self):
        """
        Restart the QDevil. This will cause delays and execution is not awaited. The connection will be closed.
        A new connection must be established, because the Ethernet interface will be restarted.
        :return: None
        """
        self.write("SYST:REST", await_end=False)  # Don't wait for execution, we will time out.
        self.close_connection()

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
            msg = __name__ + " raises the following errors:"
            for err in errors:
                msg += "\n{:s}: ({:s})".format(err[0], err[1])
            raise ValueError(msg)

    def close_connection(self):
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
            logging.info(__name__ + " : Closing connection to QDAC-II server {:s}".format(self._address))
            self._visainstrument.close()
        except Exception as e:
            logging.error("{!s}: Cannot close VISA-instrument".format(__name__))
            raise type(e)("{!s}: Cannot close VISA-instrument\n{!s}".format(__name__, e))
        return

    def set_voltage(self, channel, value):
        self.execute(
            f'sour{channel}:volt:MODE fix',
            f'sour{channel}:volt {value}'
        )

    def set_voltages(self, voltages):
        """
        Return measured voltages at the output.
        :param voltages:
        :return: An array of the voltages on the output. These differ from the set voltages.
        """
        assert len(voltages) == 24, "One voltage per channel (24 in total) required!"
        self.execute(
            f"SOURCE:VOLT:MODE fix,(@1:24)",
            *[f'SOUR{channel + 1}:VOLT {value}' for (channel, value) in enumerate(voltages)]
        )

    def get_voltages(self):
        return np.array(self.query("SOURCE:VOLT? (@1:24)").split(',')).astype(float)

    def get_voltage(self, channel):
        """
        Gets the last command send to the channel.
        :param channel:
        :return:
        """
        self.query(f'sour{channel}:volt:last?')

    def set_voltage_trace(self, channel: int, trace: np.ndarray, duration: int, trigger: str):
        """
        Set a AWG sequence of voltages for a channel.

        Internally, we normalize the trace to be between -1 and 1, and configure scaling appropriately.
        :param channel: The channel to be affected
        :param trace: The voltages to be set in sequence
        :param duration: Sequence duration in µs
        :param trigger: Trigger to be used. Must be one of 'int#', 'ext#', 'bus' or 'imm'
        """
        scale = np.max(np.abs(trace))
        trace = (trace / scale).astype(np.float32)
        name = f"trace_{channel}"
        # Define the trace with its temporal length
        self.write(f"TRACE:DEFINE \"{name}\", {duration}")

        # Manually write data to use binary data syntax
        data_upload_command = f"TRACE:DATA \"{name}\","
        self._visainstrument.write_binary_value(data_upload_command, trace)
        self.assert_status(cmd_ref=data_upload_command)

        # Assign trace to channel
        self.write(f"SOUR{channel}:AWG:DEFINE \"{name}\"")
        self.write(f"SOUR{channel}:AWG:SCALE {scale}; OFFSET 0")

        # Configure trigger source and arm sequence
        self.write(f"SOUR{channel}:AWG:TRIG:SOUR {trigger}")
        self.write(f"SOUR{channel}:AWG:INIT")

    def set_square_pulse(self, channel: int, period: int, ptp_amplitude: float, offset: float, repetitions: int, delay: int, trigger_on: str):
        """
        Configure a square pulse on a pin.

        After a delay (delay) a pulse of duration (duration) and amplitude (amplitude) is sent.

        This pulse is triggered as configured by trigger_on.
        """
        self.write(f"SOUR{channel}:SQU:PERIOD {period}")
        self.write(f"SOUR{channel}:SQU:COUNT {repetitions}")
        self.write(f"SOUR{channel}:SQU:VOLT:SPAN {ptp_amplitude}")
        self.write(f"SOUR{channel}:SQU:VOLT:OFFSET {offset}")
        self.write(f"SOUR{channel}:SQU:DELAY {delay}")
        self.write(f"SOUR{channel}:SQU:TRIG:SOUR {trigger_on}")
        # Allow continuous retriggering
        self.write(f"SOUR{channel}:SQU:INIT:CONT ON")


    def fire_internal_trigger(self, internal_trigger: int):
        assert internal_trigger in range(1, 15), "Internal trigger must be in [1, 14]"
        self.write(f"TINT {internal_trigger}")


    def set_output_filter(self, channel, value):
        assert value in ("dc", 'med', 'high')
        self.write(f"sour{channel}:filt {value}")

    def get_output_filter(self, channel):
        self.query(f"sour{channel}:filt?")


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
        # Corresponding Command: voltage = SOURce[n][:DC]:VOLTage[:LEVel[:IMMediate[:AMPLitude]]]:LAST? [,channel_list]
        try:
            logging.debug('{:s}: Get voltage value{!s}'.format(__name__, channel))
            return float(self.query(f'sour{channel}:volt:last?'))
        except Exception as e:
            logging.error('{!s}: Cannot get voltage value{!s}'.format(__name__, channel))
            raise type(e)('{!s}: Cannot get voltage value{!s}\n{!s}'.format(__name__, channel, e))


    def get_currents(self):
        """
        Triggers an immediate measurement of the current on all ports, terminating all scheduled triggers.
        :return: The current on the ports.
        """
        # CMD: READ[n][:CURRent]? [channel_list]
        return np.array(self.query("READ? (@1:24)").split(',')).astype(float)

    def get_current(self, channel):
        return self.get_currents()[channel - 1]

    def get_corrected_current(self, channel):
        return self.get_current(channel) - self._current_channel_offsets[channel - 1]

    def update_current_offset(self, channel):
        """
        updates the current offset for the specified channel, by setting the voltage
        on the channel to 0 and measuring the current.
        """
        self.set_voltage(channel=channel, value=0)
        offset = np.mean(self.get_current(channel=channel))

        self._current_channel_offsets[channel - 1] = offset

    def update_all_current_offsets(self):

        '''
        this is quite badly written, needs some more effort with modes of currents sensings
        '''
        for m in range(24):
            self.set_voltage(channel=m + 1, value=0)
            self._current_channel_offsets[m] = np.mean(self.get_current(channel=m + 1))

    #######################################################

    # def take_IV(self, sweep):
    #     """
    #     Takes IV curve with sweep parameters <sweep> in set sweep mode.
    #
    #     Parameters
    #     ----------
    #     sweep: array_likes of floats
    #         Sweep range containing start, stop and step size (e.g. sweep object using
    #         qkit.measure.transport.transport.sweep class)
    #
    #     Returns
    #     -------
    #     bias_values: numpy.array(float)
    #         Measured bias values.
    #     sense_values: numpy.array(float)
    #         Measured sense values.
    #     """
    #     self.set_sweep_parameters(sweep=sweep)
    #     return self.get_tracedata()
    #
    # def set_sweep_paramters(self, sweep, dwell=1e-6, **par):
    #     """
    #     Sets sweep parameters <sweep> and prepares instrument for the set sweep mode.
    #
    #     Parameters
    #     ----------
    #     sweep: array_likes of floats
    #         Sweep range containing start, stop and step size (e.g. sweep object using
    #         qkit.measure.transport.transport.sweep class)
    #
    #     dwell: float.
    #         Duration of each level of the sweep in s. Must be beween 1e-6 (one sample at each level)
    #         and 3600s (10h). Default is 1e-6.
    #     **par: dict type. optional
    #         Dict of parameters that will be passed to set_DC_value. Containing settings for the
    #         voltage generator. Including lowpass_filter and volt_range.
    #
    #     Returns
    #     -------
    #             None
    #     """
    #
    #     if self._sweep_mode == 2:
    #         channel_bias, channel_sense = self._sweep_channels
    #     else:
    #         logging.error(
    #             "Mode {:d} not supported. This device only supports mode 2 (VI-mode).".format(
    #                 mode
    #             )
    #         )
    #         raise ValueError(
    #             "Mode {:d} not supported. This device only supports mode 2 (VI-mode).".format(
    #                 mode
    #             )
    #         )
    #     try:
    #         logging.debug(
    #             "{!s}: Set sweep parameters of channel {:d} and {:d} to {!s}".format(
    #                 __name__, channel_bias, channel_sense, sweep
    #             )
    #         )
    #         self._set_sweep_start(val=float(sweep[0]), channel=channel_bias)
    #         self._set_sweep_stop(val=float(sweep[1]), channel=channel_bias)
    #         self._set_sweep_step(val=np.abs(float(sweep[2])), channel=channel_bias)
    #         self._set_sweep_dwell(val=dwell, channel=channel_bias)
    #         # setup triggers
    #         self.set_trigger("int1", channel=channel_bias)
    #         # set int2 trigger to trigger on every step of the voltage sweep
    #         self.write("sour{:d}:dc:sst:tnum 2".format(channel_bias))
    #         self.set_sensor_trigger("int2", channel=channel_sense)
    #
    #         self._set_DC_voltage_par(channel, value=sweep[1], **par)
    #         self._write("sour{:d}:mode swe".format(channel_bias))
    #     except Exception as e:
    #         logging.error(
    #             "{!s}: Cannot set sweep parameters of channel {:d} and {:d} to {!s}".format(
    #                 __name__, channel_bias, channel_sense, sweep
    #             )
    #         )
    #         raise type(e)(
    #             "{!s}: Cannot set sweep parameters of channel {:d} and {:d} to {!s}\n{!s}".format(
    #                 __name__, channel_bias, channel_sense, sweep, e
    #             )
    #         )
    #     return
    #
    # def get_tracedata(self, sweep):
    #     """
    #     Starts bias sweep with already set parameters and gets trace data of bias <bias_values> and sense <sense_values> in the set sweep mode.
    #
    #     Parameters
    #     ----------
    #             None
    #
    #     Returns
    #     -------
    #     bias_values: numpy.array(float)
    #         Measured bias values.
    #     sense_values: numpy.array(float)
    #         Measured sense values.
    #     """
    #     if self._sweep_mode == 2:
    #         channel_bias, channel_sense = self._sweep_channels
    #     else:
    #         logging.error(
    #             "Mode {:d} not supported. This device only supports mode 2 (VI-mode).".format(
    #                 mode
    #             )
    #         )
    #         raise ValueError(
    #             "Mode {:d} not supported. This device only supports mode 2 (VI-mode).".format(
    #                 mode
    #             )
    #         )
    #     try:
    #         logging.debug(
    #             "{!s}: Take sweep data of bias channel {:d} and measurement channel{:d}".format(
    #                 __name__, channel_bias, channel_sense
    #             )
    #         )
    #         duration = self.query("sour{:d}:dc:swe:time?".format(channel_bias))
    #         self.write("sens{:d}:init:cont ON".format(channel_sense))
    #         self._wait_for_OPC()
    #         time.sleep(100e-6)
    #         self.write("tint1")
    #         time.sleep(duration)
    #         sense_values = np.fromstring(
    #             string=self.query("read? (@{:d})".format(channel_sense)),
    #             dtype=float,
    #             sep=",",
    #         )
    #         bias_values = get_sweep_bias_values(channel_bias)
    #         if len(bias_value) != len(sense_values):
    #             logging.error(
    #                 "Length of bias values ({:d}) does not match length of sensor values ({:d})".format(
    #                     len(bias_values), len(sense_values)
    #                 )
    #             )
    #             raise ValueError(
    #                 "Length of bias values ({:d}) does not match length of sensor values ({:d})".format(
    #                     len(bias_values), len(sense_values)
    #                 )
    #             )
    #         return bias_values, sense_values
    #     except Exception as e:
    #         logging.error(
    #             "{!s}: Cannot take sweep data of channel {!s} and {!s}".format(
    #                 __name__, channel_bias, channel_sense
    #             )
    #         )
    #         raise type(e)(
    #             "{!s}: Cannot take sweep data of channel {!s} and {!s}\n{!s}".format(
    #                 __name__, channel_bias, channel_sense, e
    #             )
    #         )
    #
    # def get_sweep_bias_values(self, channel):
    #     """
    #     Read out bias values of a sweep for a given channel.
    #
    #     Parameters
    #     ----------
    #     channel: int
    #         Bias channel. Must be between 1 and 24.
    #
    #     Returns
    #     -------
    #     values: list of float
    #         List of bias values
    #     """
    #     try:
    #         start = float(self.query("sour{:d}:swe:star?".format(channel)))
    #         stop = float(self.query("sour{:d}:swe:stop?".format(channel)))
    #         step = float(self.query("sour{:d}:swe:step?".foramt(channel)))
    #         return list(range(start, stop + step, step))
    #     except Exception as e:
    #         logging.error(
    #             "{:s}: Cannot get bias values of sweep of channels {:s}. Start, Stop or Stepsize not specified.".format(
    #                 __name__, channel
    #             )
    #         )
    #         raise type(e)(
    #             "{:s}: Cannot get bias values of sweep of channels {:s}. Start, Stop or Stepsize not specified.\n{:s}".format(
    #                 __name__, channel, e
    #             )
    #         )
    #
    # def set_trigger(self, trigger, channel=1):
    #     """
    #     Sets trigger of channel <channel> to <trigger>.
    #
    #     Parameters
    #     ----------
    #     trigger: str
    #         Trigger to use. For example IMM, INT1 or EXT1.
    #     channel: int
    #         Number of channel of interest. Must be between 1 and 24. Default is 1.
    #
    #     Returns
    #     -------
    #             None
    #     """
    #     try:
    #         logging.debug(
    #             "{!s}: Set trigger of channel {:d} to {:s}".format(
    #                 __name__, channel, trigger
    #             )
    #         )
    #         self._write("sour{:d}:trig:sour {:s}".format(channel, trigger))
    #     except Exception as e:
    #         logging.error(
    #             "{!s}: Cannot set trigger of channel {!s} to {!s}".format(
    #                 __name__, channel, trigger
    #             )
    #         )
    #         raise type(e)(
    #             "{!s}: Cannot set trigger of channel {!s} to {!s}\n{!s}".format(
    #                 __name__, channel, trigger, e
    #             )
    #         )
    #     return
    #
    # def get_trigger(self, channel=1):
    #     """
    #     Gets trigger of channel <channel>.
    #
    #     Parameters
    #     ----------
    #     channel: int
    #         Number of channel of interest. Must be between 1 and 24. Default is 1.
    #
    #     Returns
    #     -------
    #     trigger: str
    #         Trigger of given channel. For example INT1.
    #     """
    #     try:
    #         logging.debug("{!s}: Get trigger of channel {:d}".format(__name__, channel))
    #         trigger = str(self.query("sour{:d}:trig:sourc?".format(channel)).lower())
    #         return trigger
    #     except Exception as e:
    #         logging.error(
    #             "{!s}: Cannot get trigger of channel {!s}".format(__name__, channel)
    #         )
    #         raise type(e)(
    #             "{!s}: Cannot get trigger of channel {!s}\n{!s}".format(
    #                 __name__, channel, e
    #             )
    #         )
    #
    # def set_sensor_trigger(self, trigger, channel=1):
    #     """
    #     Sets trigger for the current sensor of channel <channel> to <trigger>.
    #
    #     Parameters
    #     ----------
    #     trigger: str
    #         Trigger to use. For example IMM, INT1 or EXT1.
    #     channel: int
    #         Number of channel of interest. Must be between 1 and 24. Default is 1.
    #
    #     Returns
    #     -------
    #             None
    #     """
    #     try:
    #         logging.debug(
    #             "{!s}: Set sensor trigger of channel {:d} to {:s}".format(
    #                 __name__, channel, trigger
    #             )
    #         )
    #         self._write("sens{:d}:trig:sour {:s}".format(channel, trigger))
    #     except Exception as e:
    #         logging.error(
    #             "{!s}: Cannot set sensor trigger of channel {!s} to {!s}".format(
    #                 __name__, channel, trigger
    #             )
    #         )
    #         raise type(e)(
    #             "{!s}: Cannot set sensor trigger of channel {!s} to {!s}\n{!s}".format(
    #                 __name__, channel, trigger, e
    #             )
    #         )
    #     return
    #
    # def get_sensor_trigger(self, channel=1):
    #     """
    #     Gets trigger for the current sensor of channel <channel>.
    #
    #     Parameters
    #     ----------
    #     channel: int
    #         Number of channel of interest. Must be between 1 and 24. Default is 1.
    #
    #     Returns
    #     -------
    #     trigger: str
    #         Trigger of given channel. For example INT1.
    #     """
    #     try:
    #         logging.debug(
    #             "{!s}: Get sensor trigger of channel {:d}".format(__name__, channel)
    #         )
    #         trigger = str(self.query("sens{:d}:trig:sourc?".format(channel)).lower())
    #         return trigger
    #     except Exception as e:
    #         logging.error(
    #             "{!s}: Cannot get sensor trigger of channel {!s}".format(
    #                 __name__, channel
    #             )
    #         )
    #         raise type(e)(
    #             "{!s}: Cannot get sensor trigger of channel {!s}\n{!s}".format(
    #                 __name__, channel, e
    #             )
    #         )
    #
    # def _set_sweep_start(self, val, channel):
    #     """
    #     Sets sweep start value of channel <channel> to <val>.
    #
    #     Parameters
    #     ----------
    #     val: float
    #         Start value of sweep.
    #     channel: int
    #         Number of channel of interest. Must be between 1 and 24. Default is 1.
    #
    #     Returns
    #     -------
    #             None
    #     """
    #     try:
    #         logging.debug(
    #             "{!s}: Set sweep start of channel {:d} to {:f}".format(
    #                 __name__, channel, val
    #             )
    #         )
    #         self.write("sour{:d}:swe:star {:f}".format(channel, val))
    #     except Exception as e:
    #         logging.error(
    #             "{!s}: Cannot set sweep start of channel {!s} to {!s}".format(
    #                 __name__, channel, val
    #             )
    #         )
    #         raise type(e)(
    #             "{!s}: Cannot set sweep start of channel {!s} to {!s}\n{!s}".format(
    #                 __name__, channel, val, e
    #             )
    #         )
    #     return
    #
    # def _get_sweep_start(self, channel=1):
    #     """
    #     Gets sweep start value of channel <channel>.
    #
    #     Parameters
    #     ----------
    #     channel: int
    #         Number of channel of interest. Must be between 1 and 24. Default is 1.
    #
    #     Returns
    #     -------
    #     val: float
    #         Start value of sweep.
    #     """
    #     try:
    #         logging.debug(
    #             "{!s}: Get sweep start of channel {:d}".format(__name__, channel)
    #         )
    #         return float(self.query(":sour{:d}:swe:star".format(channel)))
    #     except Exception as e:
    #         logging.error(
    #             "{!s}: Cannot get sweep start of channel {!s}".format(__name__, channel)
    #         )
    #         raise type(e)(
    #             "{!s}: Cannot get sweep start of channel {!s}\n{!s}".format(
    #                 __name__, channel, e
    #             )
    #         )
    #
    # def set_sweep_dwell(self, val, channel):
    #     """
    #     Sets sweep dwell value of channel <channel> to <val>.
    #
    #     Parameters
    #     ----------
    #     val: float
    #         Dwell value of sweep. The duration of each level in the sweep. Must be between
    #         1e-6 (1 sample) and 3600s (10h).
    #     channel: int
    #         Number of channel of interest. Must be between 1 and 24. Default is 1.
    #
    #     Returns
    #     -------
    #             None
    #     """
    #     try:
    #         logging.debug(
    #             "{!s}: Set sweep dwell of channel {:d} to {:f}".format(
    #                 __name__, channel, val
    #             )
    #         )
    #         self.write("sour{:d}:swe:dweli {:f}".format(channel, val))
    #     except Exception as e:
    #         logging.error(
    #             "{!s}: Cannot set sweep dwell of channel {!s} to {!s}".format(
    #                 __name__, channel, val
    #             )
    #         )
    #         raise type(e)(
    #             "{!s}: Cannot set sweep dwell of channel {!s} to {!s}\n{!s}".format(
    #                 __name__, channel, val, e
    #             )
    #         )
    #     return
    #
    # def get_sweep_dwell(self, channel=1):
    #     """
    #     Gets sweep dwell value of channel <channel>.
    #
    #     Parameters
    #     ----------
    #     channel: int
    #         Number of channel of interest. Must be between 1 and 24. Default is 1.
    #
    #     Returns
    #     -------
    #     val: float
    #         Dwell value of sweep. The duration of each level in the sweep in seconds.
    #     """
    #     try:
    #         logging.debug(
    #             "{!s}: Get sweep dwell of channel {:d}".format(__name__, channel)
    #         )
    #         return float(self.query(":sour{:d}:swe:dweli".format(channel)))
    #     except Exception as e:
    #         logging.error(
    #             "{!s}: Cannot get sweep dwell of channel {!s}".format(__name__, channel)
    #         )
    #         raise type(e)(
    #             "{!s}: Cannot get sweep dwell of channel {!s}\n{!s}".format(
    #                 __name__, channel, e
    #             )
    #         )
    #
    # def _set_sweep_stop(self, val, channel):
    #     """
    #     Sets sweep stop value of channel <channel> to <val>.
    #
    #     Parameters
    #     ----------
    #     val: float
    #         Stop value of sweep.
    #     channel: int
    #         Number of channel of interest. Must be between 1 and 24. Default is 1.
    #
    #     Returns
    #     -------
    #             None
    #     """
    #     try:
    #         logging.debug(
    #             "{!s}: Set sweep stop of channel {:d} to {:f}".format(
    #                 __name__, channel, val
    #             )
    #         )
    #         self.write("sour{:d}:swe:stop {:f}".format(channel, val))
    #     except Exception as e:
    #         logging.error(
    #             "{!s}: Cannot set sweep stop of channel {!s} to {!s}".format(
    #                 __name__, channel, val
    #             )
    #         )
    #         raise type(e)(
    #             "{!s}: Cannot set sweep stop of channel {!s} to {!s}\n{!s}".format(
    #                 __name__, channel, val, e
    #             )
    #         )
    #     return
    #
    # def _get_sweep_stop(self, channel=1):
    #     """
    #     Gets sweep stop value of channel <channel>.
    #
    #     Parameters
    #     ----------
    #     channel: int
    #         Number of channel of interest. Must be between 1 and 24. Default is 1.
    #
    #     Returns
    #     -------
    #     val: float
    #         Stop value of sweep.
    #     """
    #     try:
    #         logging.debug(
    #             "{!s}: Get sweep stop of channel {:d}".format(__name__, channel)
    #         )
    #         return float(self.query(":sour{:d}:swe:stop".format(channel)))
    #     except Exception as e:
    #         logging.error(
    #             "{!s}: Cannot get sweep stop of channel {!s}".format(__name__, channel)
    #         )
    #         raise type(e)(
    #             "{!s}: Cannot get sweep stop of channel {!s}\n{!s}".format(
    #                 __name__, channel, e
    #             )
    #         )
    #
    # def _set_sweep_step(self, val, channel=1):
    #     """
    #     Sets sweep step value of channel <channel> to <val>.
    #
    #     Parameters
    #     ----------
    #     val: float
    #         Step value of sweep.
    #     channel: int
    #         Number of channel of interest. Must be between 1 and 24. Default is 1.
    #
    #     Returns
    #     -------
    #             None
    #     """
    #     try:
    #         logging.debug(
    #             "{!s}: Set sweep step of channel {:d} to {:f}".format(
    #                 __name__, channel, val
    #             )
    #         )
    #         self.write("sour{:d}:swe:step {:f}".format(channel, val))
    #     except Exception as e:
    #         logging.error(
    #             "{!s}: Cannot set sweep step of channel {!s} to {!s}".format(
    #                 __name__, channel, val
    #             )
    #         )
    #         raise type(e)(
    #             "{!s}: Cannot set sweep step of channel {!s} to {!s}\n{!s}".format(
    #                 __name__, channel, val, e
    #             )
    #         )
    #     return
    #
    # def _get_sweep_step(self, channel=1):
    #     """
    #     Gets sweep step value of channel <channel>.
    #
    #     Parameters
    #     ----------
    #     channel: int
    #         Number of channel of interest. Must be between 1 and 24. Default is 1.
    #
    #     Returns
    #     -------
    #     val:
    #         Step value of sweep.
    #     """
    #     try:
    #         logging.debug(
    #             "{!s}: Get sweep step of channel {:d}".format(__name__, channel)
    #         )
    #         return float(self.query("sour{:d}:swe:step?".format(channel)))
    #     except Exception as e:
    #         logging.error(
    #             "{!s}: Cannot get sweep step of channel {!s}".format(__name__, channel)
    #         )
    #         raise type(e)(
    #             "{!s}: Cannot get sweep step of channel {!s}\n{!s}".format(
    #                 __name__, channel, e
    #             )
    #         )
    #
    # def _get_sweep_nop(self, channel=1):
    #     """
    #     Gets sweeps number of points (nop) of channel <channel>.
    #
    #     Parameters
    #     ----------
    #     channel: int
    #         Number of channel of interest. Must be between 1 and 24. Default is 1.
    #
    #     Returns
    #     -------
    #     val:
    #         Number of points of sweep.
    #     """
    #     try:
    #         logging.debug(
    #             "{!s}: Get sweep nop of channel {:d}".format(__name__, channel)
    #         )
    #         return int(
    #             (
    #                 self._get_sweep_stop(channel=channel)
    #                 - self._get_sweep_start(channel=channel)
    #             )
    #             / self._get_sweep_step(channel=channel)
    #             + 1
    #         )
    #     except Exception as e:
    #         logging.error(
    #             "{!s}: Cannot get sweep nop of channel {!s}".format(__name__, channel)
    #         )
    #         raise type(e)(
    #             "{!s}: Cannot get sweep nop of channel {!s}\n{!s}".format(
    #                 __name__, channel, e
    #             )
    #         )
    #
    # def set_sweep_mode(self, mode=1, *channels):
    #     """
    #     Setterfunction for the internal variable _sweep_mode.
    #
    #     Sets an variable to indicate that
    #      * voltage is applied and current is measured (VI-mode)
    #     and channels <channels> that are used during sweeps.
    #
    #     This function is necessary for the transport mode, however this device only
    #     supports this one mode.
    #
    #     Parameters
    #     ----------
    #     mode: int. {1}
    #         Sweep mode denoting bias and sense modes. Possible values are 1 (VI-mode).
    #         Default is 1.
    #     channels: int or tuple(int).
    #         Number of channel of usage. Must be between 1 and 24 or a tuple containing
    #         two channels (1st argument as bias channel and 2nd argument as sense channel).
    #
    #
    #     Returns
    #     -------
    #     None
    #     """
    #     default_channels = (1, 1)
    #     if mode == 2:
    #         if len(channels) == 2:
    #             logging.debug(
    #                 "{!s}: Set sweep channels to {!s}".format(__name__, channels)
    #             )
    #             self._sweep_channels = channels
    #         elif len(channels) == 1:
    #             logging.debug(
    #                 "{!s}: Set sweep channels to {!s}".format(__name__, channels)
    #             )
    #             self._sweep_channels = (channels, channels)
    #         elif len(channels) == 0:
    #             logging.debug(
    #                 "{!s}: Set sweep channels to {!s}".format(
    #                     __name__, default_channels
    #                 )
    #             )
    #             self._sweep_channels = default_channels
    #         else:
    #             logging.error(
    #                 "{!s}: Cannot set sweep channels to {!s}".format(__name__, channels)
    #             )
    #             raise ValueError(
    #                 "{!s}: Cannot set sweep channels to {!s}".format(__name__, channels)
    #             )
    #         logging.debug("{!s}: Set sweep mode to {:d}".format(__name__, mode))
    #         self._sweep_mode = mode
    #     else:
    #         logging.error(
    #             "{!s}: Cannot set sweep mode to {!s}. Only mode 2 (VI-mode) is supported.".format(
    #                 __name__, mode
    #             )
    #         )
    #         raise ValueError(
    #             "{!s}: Cannot set sweep mode to {!s}".format(__name__, mode)
    #         )
    #     return
    #
    # def get_sweep_mode(self):
    #     """
    #     Getterfunction for internal variable _sweep_mode.
    #
    #     Gets an internal variable <mode> to decide weather
    #      * 0: voltage is both applied and measured (VV-mode),
    #      * 1: current is applied and voltage is measured (IV-mode) or
    #      * 2: voltage is applied and current is measured (VI-mode).
    #
    #     This device only supports mode 2 (VI-mode).
    #
    #     Parameters
    #     ----------
    #     None
    #
    #     Returns
    #     -------
    #     mode: int
    #         Sweep mode denoting bias and sense modes. Meanings are 0 (VV-mode), 1 (IV-mode) or 2 (VI-mode).
    #     """
    #     return self._sweep_mode
    #
    # def get_sweep_channels(self):
    #     """
    #     Gets channels <channels> that are used during sweeps.
    #     In the IV sweep mode one channel requires for biasing and sensing, whereas two channels are returned in the VV sweep mode (1st as bias and 2nd as sense channel).
    #
    #     Parameters
    #     ----------
    #     None
    #
    #     Returns
    #     -------
    #     channels: int or tuple(int)
    #         Number of channel of usage. Meanings are 1 or 2 for IV-mode and VI-mode or a tuple containing both channels for VV-mode (1st argument as bias channel and 2nd argument as sense channel).
    #     """
    #     return self._sweep_channels
    #
    # def get_sweep_bias(self):
    #     """
    #     Calls get_bias_mode of channel <channel>.
    #     This method is needed for qkit.measure.transport.transport.py in case of no virtual tunnel electronic.
    #
    #     Parameters
    #     ----------
    #     None
    #
    #     Returns
    #     -------
    #     mode: int
    #         Bias mode. Meanings are 0 (current) and 1 (voltage).
    #     """
    #     return self.get_bias_mode(self._sweep_channels[0])
    #
    # def set_status(self, status, channel=1):
    #     """
    #     Sets output DC status of channel <channel> to <status>.
    #
    #     Parameters
    #     ----------
    #     status: int
    #         Output status. Possible values are 0 (off) or 1 (on).
    #     channel: int
    #         Number of channel of interest. Must be between 1 and 24. Default is 1.
    #
    #     Returns
    #     -------
    #             None
    #     """
    #     try:
    #         logging.debug(
    #             "{!s}: Set output status of channel {:d} to {!r}".format(
    #                 __name__, channel, status
    #             )
    #         )
    #         if status == 1:
    #             self._write(":sour{:d}:dc:init".format(channel))
    #         elif status == 0:
    #             self._write("sour{:d}:all:abor".format(channel))
    #             self._write("sour{:d}:volt 0".format(channel))
    #         else:
    #             raise TypeError("Status not valid, only 0 (off) and 1 (on) possible.")
    #     except Exception as e:
    #         logging.error(
    #             "{!s}: Cannot set output status of channel {!s} to {!s}".format(
    #                 __name__, channel, status
    #             )
    #         )
    #         raise type(e)(
    #             "{!s}: Cannot set output status of channel {!s} to {!s}\n{!s}".format(
    #                 __name__, channel, status, e
    #             )
    #         )
    #     return
    #
    # def get_end_of_sweep(self, channel=1):
    #     """
    #     Gets event of bias condition code register (ccr) entry "End for Sweep" <val> of channel <channel>.
    #
    #     Parameters
    #     ----------
    #     channel: int
    #         Number of channel of interest. Must be between 1 and 24. Default is 1.
    #
    #     Returns
    #     -------
    #     val: bool
    #         End of sweep entry of bias condition code register.
    #     """
    #     try:
    #         logging.debug(
    #             """{!s}: Get bias ccr event "End of Sweep" of channel {:d}""".format(
    #                 __name__, channel
    #             )
    #         )
    #         return bool(
    #             (int(self._ask(":stat:sour:even")) >> (0 + 8 * (channel - 1))) % 2
    #         )
    #     except Exception as e:
    #         logging.error(
    #             '{!s}: Cannot get bias ccr event "End of Sweep" of channel {!s}'.format(
    #                 __name__, channel
    #             )
    #         )
    #         raise type(e)(
    #             '{!s}: Cannot get bias ccr event "End of Sweep" of channel {!s}\n{!s}'.format(
    #                 __name__, channel, e
    #             )
    #         )
    #
    # def _wait_for_end_of_sweep(self, channel=1):
    #     """
    #     Waits until the event of bias condition code register (ccr) entry "End for Sweep" of channel <channel> occurs.
    #
    #     Parameters
    #     ----------
    #     channel: int
    #         Number of channel of interest. Must be 1 or 2. Default is 1.
    #
    #     Returns
    #     -------
    #     None
    #     """
    #     while not (self.get_end_of_sweep(channel=channel)):
    #         time.sleep(100e-3)
    #     return
    #
    # def get_end_of_measure(self, channel=1):
    #     """
    #     Gets condition of sense condition code register (ccr) entry "End of Measure" <val> of channel <channel>.
    #
    #     Parameters
    #     ----------
    #     channel: int
    #         Number of channel of interest. Must be 1 or 2. Default is 1.
    #
    #     Returns
    #     -------
    #     val: bool
    #         End of sweep entry of bias condition code register.
    #     """
    #     # Corresponding Command: :STATus:SENSe:CONDition?
    #     try:
    #         logging.debug(
    #             """{!s}: Get sense ccr event "End of Measure" of channel {:d}""".format(
    #                 __name__, channel
    #             )
    #         )
    #         return bool(
    #             (int(self._ask(":stat:sens:cond")) >> (0 + 8 * (channel - 1))) % 2
    #         )
    #     except Exception as e:
    #         logging.error(
    #             '{!s}: Cannot get sense ccr event "End of Measure" of channel {!s}'.format(
    #                 __name__, channel
    #             )
    #         )
    #         raise type(e)(
    #             '{!s}: Cannot get sense ccr event "End of Measure" of channel {!s}\n{!s}'.format(
    #                 __name__, channel, e
    #             )
    #         )

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
        parlist = {'voltage': {'channels': range(1, self._channels + 1)},
                   'current': {'channels': range(1, self._channels + 1)},
                   'corrected_current': {'channels': range(1, self._channels + 1)},
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
