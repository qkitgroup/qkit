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


class QDAC_II(Instrument):
    """
    Instrument class for QDevil QDAC-II.


    """

    def __init__(self, name, address, port=5025):
        """
        Initialize qkit paramters and connect to the device.
        """

        logging.info(__name__ + " : Initializing Instrument")
        Instrument.__init__(self, name, tags=["physical"])

        self._address = address
        self._port = port
        try:
            self._visainstrument = visa.instrument(
                "TCPIP::{:s}::{:i}::SOCKET".format(self._address, self._port)
            )
        except Exception as detail:
            logging.error(
                "Connection to QDvil Instrument not possible. Original error: {:s}".format(
                    detail
                )
            )
        self._visainstrument.read_termination = "\n"
        self._visainstrument.write_termination = "\n"

        # initial variables
        self._sweep_mode = 1  # IV-mode
        self._sweep_channels = (1,)
        self._measurement_modes = {0: "2-wire", 1: "4-wire"}
        self._IV_modes = {0: "curr", 1: "volt"}
        self._IV_units = {0: "A", 1: "V"}

    def write(self, cmd):
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
        self._visainstrument.write(cmd)
        while not bool(int(self._visainstrument.query("*OPC?"))):
            time.sleep(1e-6)
        self._raise_error()
        return

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
        if "?" in cmd:
            ans = self._visainstrument.query(cmd).rstrip()
        else:
            ans = self._visainstrument.query("{:s}?".format(cmd)).rstrip()
        while not bool(int(self._visainstrument.query("*opc?"))):
            time.sleep(1e-6)
        self._raise_error()
        return ans

    def get_OPC(self):
        """
        Waits until the condition of standard event register entry "Operation complete" is fulfilled.

        Parameters
        ----------
                None

        Returns
        -------
                None
        """
        try:
            logging.debug(
                '''{!s}: Get ccr event "Operation complete"'''.format(__name__)
            )
            return bool(int(self.query("*OPC")))
        except Exception as e:
            logging.error(
                '{!s}: Cannot get ccr condition "Operation complete"'.format(__name__)
            )
            raise type(e)(
                '{!s}: Cannot get ccr condition "Operation complete"\n{!s}'.format(
                    __name__, e
                )
            )

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
            raise type(e)(
                "{!s}: Cannot clears error of instrument\n{!s}".format(__name__, e)
            )
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
            self.write("*RST")
        except Exception as e:
            logging.error(
                "{!s}: Cannot reset instrument to factory settings".format(__name__)
            )
            raise type(e)(
                "{!s}: Cannot reset instrument to factory settings\n{!s}".format(
                    __name__, e
                )
            )
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
        try:
            logging.debug("{!s}: Get errors of instrument".format(__name__))
            err = [self._visainstrument.query("syst:err?").rstrip().split(",", 1)]
            while err[-1] != ["0", '"No error"']:
                err.append(
                    self._visainstrument.query("syst:err?").rstrip().split(",", 1)
                )
            if len(err) > 1:
                err = err[:-1]
            err = [[int(e[0]), str(e[1][1:-1])] for e in err]
            return err
        except Exception as e:
            logging.error("{!s}: Cannot get errors of instrument".format(__name__))
            raise type(e)(
                "{!s}: Cannot get errors of instrument\n{!s}".format(__name__, e)
            )

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
            msg = __name__ + " raises the following errors:"
            for err in errors:
                msg += "\n{:s}: ({:s})".format(err[0], err[1])
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
        try:
            logging.debug("{!s}: Clears error of instrument".format(__name__))
            self._write("*CLS")
        except Exception as e:
            logging.error("{!s}: Cannot clears error of instrument".format(__name__))
            raise type(e)(
                "{!s}: Cannot clears error of instrument\n{!s}".format(__name__, e)
            )
        return

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
            logging.info(
                __name__
                + " : Closing connection to QDAC-II server {:s}".format(self._address)
            )
            self._visainstrument.close()
        except Exception as e:
            logging.error("{!s}: Cannot close VISA-instrument".format(__name__))
            raise type(e)(
                "{!s}: Cannot close VISA-instrument\n{!s}".format(__name__, e)
            )
        return

    def set_DC_voltage(channel, value, slew=2e7, **par):
        """
        Setter function for voltage in a channel.

        Parameter
        ---------
        channel: int or list of int.
            Channel(s) for which the voltage should be set.
        value: float.
            Voltage value in volts (V) that should be set in each channel.
        slew: float, default 2e7.
            Maximum voltage change rate in volts per second (V/s). Minimal value is 20
            and maximum is 2e7 (default).

        **par: dict type. optional.
            Including volt_range and lowpass_filter.
            volt_range: {None, 'LOW','HIGH'}
                Voltage range 'LOW' is up to 2 V and 'HIGH' up to 10 V. If not specified it
                will be calculated from the <value> parameter.
            lowpass_filter: {'DC', 'MED', 'HIGH'}
                'DC' filters out everything below ~10 Hz, 'MED' at 10 kHz and 'HIGH' at 100kHz.
                Default is 'DC'.

        Example
        -------
        q = QDAC_II("QDevil QDAC-II", 10.22.197.176)
        q.set_DC_voltage([1,2,6],0.2)
        """

        channel_str = ""
        for ch in channel:
            channel_str = channel_str + str(int(ch)) + ","

        try:
            logging.debug(
                "{!s}: Set voltage of channel(s) {:s} to {:d} with slew {:d}".format(
                    __name__, channel_str, value, slew
                )
            )
            self.write("sour:volt {:d}, (@{:s}) ".format(value, channel_str))
            self._set_DC_voltage_par(channel, value, slew, *par)
        except Exception as e:
            logging.error(
                "{!s}: Cannot set voltage of channel(s) {!s}".format(
                    __name__, channel_str
                )
            )
            raise type(e)(
                "{!s}: Cannot set voltage of channel(s) {!s}\n{!s}".format(
                    __name__, channel_str, e
                )
            )
        return

    def _set_DC_voltage_par(channel, value, slew=2e7, **par):
        """
        Private function for setting additional parameters for the DC voltage.

        Parameters
        ----------
        channel: int or list of int.
            Channel(s) for which the voltage should be set.
        value: float
            Voltage value you want to set. Used for computing voltage range, if no range
            is specified in par.
        slew: float, default 2e7.
            Maximum voltage change rate in volts per second (V/s). Minimal value is 20
            and maximum is 2e7 (default).

        **par: dict type. optional.
            Including volt_range and lowpass_filter.
            volt_range: {None, 'LOW','HIGH'}
                Voltage range 'LOW' is up to 2 V and 'HIGH' up to 10 V. If not specified it
                will be calculated from the <value> parameter.
            lowpass_filter: {'DC', 'MED', 'HIGH'}
                'DC' filters out everything below ~10 Hz, 'MED' at 10 kHz and 'HIGH' at 100kHz.
                Default is 'DC'.

        Returns
        -------
        None
        """

        channel_str = ""
        for ch in channel:
            channel_str = channel_str + str(int(ch)) + ","
        try:
            self.write("sour:volt:slew {:d}, (@{:s})".format(slew, channel_str))

            if volt_range not in par:
                if value < 2:
                    volt_range = "LOW"
                else:
                    volt_range = "HIGH"
            self.write("sour:volt:range {:s}, (@{:s})".format(volt_range, channel_str))
            if lowpass_filter in par:
                self.write(
                    "sour:volt:filter {:s}, (@{:s})".format(lowpass_filter, channel_str)
                )
            else:
                self.write("sour:volt:filter DC, (@{:s})".format(channel_str))
        except Exception as e:
            logging.error(
                "{!s}: Cannot set voltage parameters of channel(s) {!s}".format(
                    __name__, channel_str
                )
            )
            raise type(e)(
                "{!s}: Cannot set voltage parameters of channel(s) {!s}\n{!s}".format(
                    __name__, channel_str, e
                )
            )
        return

    def get_current(channel):
        """
        Reads current from the device for given channels and returns result as a dict.

        Parameters
        ----------
        channel: int of list of int.
            Channel(s) for which the current should be read.

        Returns
        -------
        current: dict of floats.
            A dict containing the current in ampere (A) for each measured channel.

        Example
        -------
        q = QDAC_II("QDevil QDAC-II", 10.22.197.176)
        q.get_current([1,2,6])
        """
        self.query()  # TODO

    def take_IV(self, sweep):
        """
        Takes IV curve with sweep parameters <sweep> in set sweep mode.

        Parameters
        ----------
        sweep: array_likes of floats
            Sweep range containing start, stop and step size (e.g. sweep object using
            qkit.measure.transport.transport.sweep class)

        Returns
        -------
        bias_values: numpy.array(float)
            Measured bias values.
        sense_values: numpy.array(float)
            Measured sense values.
        """
        self.set_sweep_parameters(sweep=sweep)
        return self.get_tracedata()

    def set_sweep_paramters(self, sweep, dwell=1e-6, **par):
        """
        Sets sweep parameters <sweep> and prepares instrument for the set sweep mode.

        Parameters
        ----------
        sweep: array_likes of floats
            Sweep range containing start, stop and step size (e.g. sweep object using
            qkit.measure.transport.transport.sweep class)

        dwell: float.
            Duration of each level of the sweep in s. Must be beween 1e-6 (one sample at each level)
            and 3600s (10h). Default is 1e-6.
        **par: dict type. optional
            Dict of parameters that will be passed to set_DC_value. Containing settings for the
            voltage generator. Including lowpass_filter and volt_range.

        Returns
        -------
                None
        """

        if self._sweep_mode == 2:
            channel_bias, channel_sense = self._sweep_channels
        else:
            logging.error(
                "Mode {:d} not supported. This device only supports mode 2 (VI-mode).".format(
                    mode
                )
            )
            raise ValueError(
                "Mode {:d} not supported. This device only supports mode 2 (VI-mode).".format(
                    mode
                )
            )
        try:
            logging.debug(
                "{!s}: Set sweep parameters of channel {:d} and {:d} to {!s}".format(
                    __name__, channel_bias, channel_sense, sweep
                )
            )
            self._set_sweep_start(val=float(sweep[0]), channel=channel_bias)
            self._set_sweep_stop(val=float(sweep[1]), channel=channel_bias)
            self._set_sweep_step(val=np.abs(float(sweep[2])), channel=channel_bias)
            self._set_sweep_dwell(val=dwell, channel=channel_bias)
            # setup triggers
            self.set_trigger("int1", channel=channel_bias)
            # set int2 trigger to trigger on every step of the voltage sweep
            self.write("sour{:d}:dc:sst:tnum 2".format(channel_bias))
            self.set_sensor_trigger("int2", channel=channel_sense)

            self._set_DC_voltage_par(channel, value=sweep[1], **par)
            self._write("sour{:d}:mode swe".format(channel_bias))
        except Exception as e:
            logging.error(
                "{!s}: Cannot set sweep parameters of channel {:d} and {:d} to {!s}".format(
                    __name__, channel_bias, channel_sense, sweep
                )
            )
            raise type(e)(
                "{!s}: Cannot set sweep parameters of channel {:d} and {:d} to {!s}\n{!s}".format(
                    __name__, channel_bias, channel_sense, sweep, e
                )
            )
        return

    def get_tracedata(self, sweep):
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
        if self._sweep_mode == 2:
            channel_bias, channel_sense = self._sweep_channels
        else:
            logging.error(
                "Mode {:d} not supported. This device only supports mode 2 (VI-mode).".format(
                    mode
                )
            )
            raise ValueError(
                "Mode {:d} not supported. This device only supports mode 2 (VI-mode).".format(
                    mode
                )
            )
        try:
            logging.debug(
                "{!s}: Take sweep data of bias channel {:d} and measurement channel{:d}".format(
                    __name__, channel_bias, channel_sense
                )
            )
            duration = self.query("sour{:d}:dc:swe:time?".format(channel_bias))
            self.write("sens{:d}:init:cont ON".format(channel_sense))
            self._wait_for_OPC()
            time.sleep(100e-6)
            self.write("tint1")
            time.sleep(duration)
            sense_values = np.fromstring(
                string=self.query("read? (@{:d})".format(channel_sense)),
                dtype=float,
                sep=",",
            )
            bias_values = get_sweep_bias_values(channel_bias)
            if len(bias_value) != len(sense_values):
                logging.error(
                    "Length of bias values ({:d}) does not match length of sensor values ({:d})".format(
                        len(bias_values), len(sense_values)
                    )
                )
                raise ValueError(
                    "Length of bias values ({:d}) does not match length of sensor values ({:d})".format(
                        len(bias_values), len(sense_values)
                    )
                )
            return bias_values, sense_values
        except Exception as e:
            logging.error(
                "{!s}: Cannot take sweep data of channel {!s} and {!s}".format(
                    __name__, channel_bias, channel_sense
                )
            )
            raise type(e)(
                "{!s}: Cannot take sweep data of channel {!s} and {!s}\n{!s}".format(
                    __name__, channel_bias, channel_sense, e
                )
            )

    def get_sweep_bias_values(self, channel):
        """
        Read out bias values of a sweep for a given channel.

        Parameters
        ----------
        channel: int
            Bias channel. Must be between 1 and 24.

        Returns
        -------
        values: list of float
            List of bias values
        """
        try:
            start = float(self.query("sour{:d}:swe:star?".format(channel)))
            stop = float(self.query("sour{:d}:swe:stop?".format(channel)))
            step = float(self.query("sour{:d}:swe:step?".foramt(channel)))
            return list(range(start, stop + step, step))
        except Exception as e:
            logging.error(
                "{:s}: Cannot get bias values of sweep of channels {:s}. Start, Stop or Stepsize not specified.".format(
                    __name__, channel
                )
            )
            raise type(e)(
                "{:s}: Cannot get bias values of sweep of channels {:s}. Start, Stop or Stepsize not specified.\n{:s}".format(
                    __name__, channel, e
                )
            )

    def set_trigger(self, trigger, channel=1):
        """
        Sets trigger of channel <channel> to <trigger>.

        Parameters
        ----------
        trigger: str
            Trigger to use. For example IMM, INT1 or EXT1.
        channel: int
            Number of channel of interest. Must be between 1 and 24. Default is 1.

        Returns
        -------
                None
        """
        try:
            logging.debug(
                "{!s}: Set trigger of channel {:d} to {:s}".format(
                    __name__, channel, trigger
                )
            )
            self._write("sour{:d}:trig:sour {:s}".format(channel, trigger))
        except Exception as e:
            logging.error(
                "{!s}: Cannot set trigger of channel {!s} to {!s}".format(
                    __name__, channel, trigger
                )
            )
            raise type(e)(
                "{!s}: Cannot set trigger of channel {!s} to {!s}\n{!s}".format(
                    __name__, channel, trigger, e
                )
            )
        return

    def get_trigger(self, channel=1):
        """
        Gets trigger of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be between 1 and 24. Default is 1.

        Returns
        -------
        trigger: str
            Trigger of given channel. For example INT1.
        """
        try:
            logging.debug("{!s}: Get trigger of channel {:d}".format(__name__, channel))
            trigger = str(self.query("sour{:d}:trig:sourc?".format(channel)).lower())
            return trigger
        except Exception as e:
            logging.error(
                "{!s}: Cannot get trigger of channel {!s}".format(__name__, channel)
            )
            raise type(e)(
                "{!s}: Cannot get trigger of channel {!s}\n{!s}".format(
                    __name__, channel, e
                )
            )

    def set_sensor_trigger(self, trigger, channel=1):
        """
        Sets trigger for the current sensor of channel <channel> to <trigger>.

        Parameters
        ----------
        trigger: str
            Trigger to use. For example IMM, INT1 or EXT1.
        channel: int
            Number of channel of interest. Must be between 1 and 24. Default is 1.

        Returns
        -------
                None
        """
        try:
            logging.debug(
                "{!s}: Set sensor trigger of channel {:d} to {:s}".format(
                    __name__, channel, trigger
                )
            )
            self._write("sens{:d}:trig:sour {:s}".format(channel, trigger))
        except Exception as e:
            logging.error(
                "{!s}: Cannot set sensor trigger of channel {!s} to {!s}".format(
                    __name__, channel, trigger
                )
            )
            raise type(e)(
                "{!s}: Cannot set sensor trigger of channel {!s} to {!s}\n{!s}".format(
                    __name__, channel, trigger, e
                )
            )
        return

    def get_sensor_trigger(self, channel=1):
        """
        Gets trigger for the current sensor of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be between 1 and 24. Default is 1.

        Returns
        -------
        trigger: str
            Trigger of given channel. For example INT1.
        """
        try:
            logging.debug(
                "{!s}: Get sensor trigger of channel {:d}".format(__name__, channel)
            )
            trigger = str(self.query("sens{:d}:trig:sourc?".format(channel)).lower())
            return trigger
        except Exception as e:
            logging.error(
                "{!s}: Cannot get sensor trigger of channel {!s}".format(
                    __name__, channel
                )
            )
            raise type(e)(
                "{!s}: Cannot get sensor trigger of channel {!s}\n{!s}".format(
                    __name__, channel, e
                )
            )

    def _set_sweep_start(self, val, channel):
        """
        Sets sweep start value of channel <channel> to <val>.

        Parameters
        ----------
        val: float
            Start value of sweep.
        channel: int
            Number of channel of interest. Must be between 1 and 24. Default is 1.

        Returns
        -------
                None
        """
        try:
            logging.debug(
                "{!s}: Set sweep start of channel {:d} to {:f}".format(
                    __name__, channel, val
                )
            )
            self.write("sour{:d}:swe:star {:f}".format(channel, val))
        except Exception as e:
            logging.error(
                "{!s}: Cannot set sweep start of channel {!s} to {!s}".format(
                    __name__, channel, val
                )
            )
            raise type(e)(
                "{!s}: Cannot set sweep start of channel {!s} to {!s}\n{!s}".format(
                    __name__, channel, val, e
                )
            )
        return

    def _get_sweep_start(self, channel=1):
        """
        Gets sweep start value of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be between 1 and 24. Default is 1.

        Returns
        -------
        val: float
            Start value of sweep.
        """
        try:
            logging.debug(
                "{!s}: Get sweep start of channel {:d}".format(__name__, channel)
            )
            return float(self.query(":sour{:d}:swe:star".format(channel)))
        except Exception as e:
            logging.error(
                "{!s}: Cannot get sweep start of channel {!s}".format(__name__, channel)
            )
            raise type(e)(
                "{!s}: Cannot get sweep start of channel {!s}\n{!s}".format(
                    __name__, channel, e
                )
            )

    def set_sweep_dwell(self, val, channel):
        """
        Sets sweep dwell value of channel <channel> to <val>.

        Parameters
        ----------
        val: float
            Dwell value of sweep. The duration of each level in the sweep. Must be between
            1e-6 (1 sample) and 3600s (10h).
        channel: int
            Number of channel of interest. Must be between 1 and 24. Default is 1.

        Returns
        -------
                None
        """
        try:
            logging.debug(
                "{!s}: Set sweep dwell of channel {:d} to {:f}".format(
                    __name__, channel, val
                )
            )
            self.write("sour{:d}:swe:dweli {:f}".format(channel, val))
        except Exception as e:
            logging.error(
                "{!s}: Cannot set sweep dwell of channel {!s} to {!s}".format(
                    __name__, channel, val
                )
            )
            raise type(e)(
                "{!s}: Cannot set sweep dwell of channel {!s} to {!s}\n{!s}".format(
                    __name__, channel, val, e
                )
            )
        return

    def get_sweep_dwell(self, channel=1):
        """
        Gets sweep dwell value of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be between 1 and 24. Default is 1.

        Returns
        -------
        val: float
            Dwell value of sweep. The duration of each level in the sweep in seconds.
        """
        try:
            logging.debug(
                "{!s}: Get sweep dwell of channel {:d}".format(__name__, channel)
            )
            return float(self.query(":sour{:d}:swe:dweli".format(channel)))
        except Exception as e:
            logging.error(
                "{!s}: Cannot get sweep dwell of channel {!s}".format(__name__, channel)
            )
            raise type(e)(
                "{!s}: Cannot get sweep dwell of channel {!s}\n{!s}".format(
                    __name__, channel, e
                )
            )

    def _set_sweep_stop(self, val, channel):
        """
        Sets sweep stop value of channel <channel> to <val>.

        Parameters
        ----------
        val: float
            Stop value of sweep.
        channel: int
            Number of channel of interest. Must be between 1 and 24. Default is 1.

        Returns
        -------
                None
        """
        try:
            logging.debug(
                "{!s}: Set sweep stop of channel {:d} to {:f}".format(
                    __name__, channel, val
                )
            )
            self.write("sour{:d}:swe:stop {:f}".format(channel, val))
        except Exception as e:
            logging.error(
                "{!s}: Cannot set sweep stop of channel {!s} to {!s}".format(
                    __name__, channel, val
                )
            )
            raise type(e)(
                "{!s}: Cannot set sweep stop of channel {!s} to {!s}\n{!s}".format(
                    __name__, channel, val, e
                )
            )
        return

    def _get_sweep_stop(self, channel=1):
        """
        Gets sweep stop value of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be between 1 and 24. Default is 1.

        Returns
        -------
        val: float
            Stop value of sweep.
        """
        try:
            logging.debug(
                "{!s}: Get sweep stop of channel {:d}".format(__name__, channel)
            )
            return float(self.query(":sour{:d}:swe:stop".format(channel)))
        except Exception as e:
            logging.error(
                "{!s}: Cannot get sweep stop of channel {!s}".format(__name__, channel)
            )
            raise type(e)(
                "{!s}: Cannot get sweep stop of channel {!s}\n{!s}".format(
                    __name__, channel, e
                )
            )

    def _set_sweep_step(self, val, channel=1):
        """
        Sets sweep step value of channel <channel> to <val>.

        Parameters
        ----------
        val: float
            Step value of sweep.
        channel: int
            Number of channel of interest. Must be between 1 and 24. Default is 1.

        Returns
        -------
                None
        """
        try:
            logging.debug(
                "{!s}: Set sweep step of channel {:d} to {:f}".format(
                    __name__, channel, val
                )
            )
            self.write("sour{:d}:swe:step {:f}".format(channel, val))
        except Exception as e:
            logging.error(
                "{!s}: Cannot set sweep step of channel {!s} to {!s}".format(
                    __name__, channel, val
                )
            )
            raise type(e)(
                "{!s}: Cannot set sweep step of channel {!s} to {!s}\n{!s}".format(
                    __name__, channel, val, e
                )
            )
        return

    def _get_sweep_step(self, channel=1):
        """
        Gets sweep step value of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be between 1 and 24. Default is 1.

        Returns
        -------
        val:
            Step value of sweep.
        """
        try:
            logging.debug(
                "{!s}: Get sweep step of channel {:d}".format(__name__, channel)
            )
            return float(self.query("sour{:d}:swe:step?".format(channel)))
        except Exception as e:
            logging.error(
                "{!s}: Cannot get sweep step of channel {!s}".format(__name__, channel)
            )
            raise type(e)(
                "{!s}: Cannot get sweep step of channel {!s}\n{!s}".format(
                    __name__, channel, e
                )
            )

    def _get_sweep_nop(self, channel=1):
        """
        Gets sweeps number of points (nop) of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be between 1 and 24. Default is 1.

        Returns
        -------
        val:
            Number of points of sweep.
        """
        try:
            logging.debug(
                "{!s}: Get sweep nop of channel {:d}".format(__name__, channel)
            )
            return int(
                (
                    self._get_sweep_stop(channel=channel)
                    - self._get_sweep_start(channel=channel)
                )
                / self._get_sweep_step(channel=channel)
                + 1
            )
        except Exception as e:
            logging.error(
                "{!s}: Cannot get sweep nop of channel {!s}".format(__name__, channel)
            )
            raise type(e)(
                "{!s}: Cannot get sweep nop of channel {!s}\n{!s}".format(
                    __name__, channel, e
                )
            )

    def set_sweep_mode(self, mode=1, *channels):
        """
        Setterfunction for the internal variable _sweep_mode.

        Sets an variable to indicate that
         * voltage is applied and current is measured (VI-mode)
        and channels <channels> that are used during sweeps.

        This function is necessary for the transport mode, however this device only
        supports this one mode.

        Parameters
        ----------
        mode: int. {1}
            Sweep mode denoting bias and sense modes. Possible values are 1 (VI-mode).
            Default is 1.
        channels: int or tuple(int).
            Number of channel of usage. Must be between 1 and 24 or a tuple containing
            two channels (1st argument as bias channel and 2nd argument as sense channel).


        Returns
        -------
        None
        """
        default_channels = (1, 1)
        if mode == 2:
            if len(channels) == 2:
                logging.debug(
                    "{!s}: Set sweep channels to {!s}".format(__name__, channels)
                )
                self._sweep_channels = channels
            elif len(channels) == 1:
                logging.debug(
                    "{!s}: Set sweep channels to {!s}".format(__name__, channels)
                )
                self._sweep_channels = (channels, channels)
            elif len(channels) == 0:
                logging.debug(
                    "{!s}: Set sweep channels to {!s}".format(
                        __name__, default_channels
                    )
                )
                self._sweep_channels = default_channels
            else:
                logging.error(
                    "{!s}: Cannot set sweep channels to {!s}".format(__name__, channels)
                )
                raise ValueError(
                    "{!s}: Cannot set sweep channels to {!s}".format(__name__, channels)
                )
            logging.debug("{!s}: Set sweep mode to {:d}".format(__name__, mode))
            self._sweep_mode = mode
        else:
            logging.error(
                "{!s}: Cannot set sweep mode to {!s}. Only mode 2 (VI-mode) is supported.".format(
                    __name__, mode
                )
            )
            raise ValueError(
                "{!s}: Cannot set sweep mode to {!s}".format(__name__, mode)
            )
        return

    def get_sweep_mode(self):
        """
        Getterfunction for internal variable _sweep_mode.

        Gets an internal variable <mode> to decide weather
         * 0: voltage is both applied and measured (VV-mode),
         * 1: current is applied and voltage is measured (IV-mode) or
         * 2: voltage is applied and current is measured (VI-mode).

        This device only supports mode 2 (VI-mode).

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
        Gets channels <channels> that are used during sweeps.
        In the IV sweep mode one channel requires for biasing and sensing, whereas two channels are returned in the VV sweep mode (1st as bias and 2nd as sense channel).

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
        Calls get_bias_mode of channel <channel>.
        This method is needed for qkit.measure.transport.transport.py in case of no virtual tunnel electronic.

        Parameters
        ----------
        None

        Returns
        -------
        mode: int
            Bias mode. Meanings are 0 (current) and 1 (voltage).
        """
        return self.get_bias_mode(self._sweep_channels[0])

    def set_status(self, status, channel=1):
        """
        Sets output DC status of channel <channel> to <status>.

        Parameters
        ----------
        status: int
            Output status. Possible values are 0 (off) or 1 (on).
        channel: int
            Number of channel of interest. Must be between 1 and 24. Default is 1.

        Returns
        -------
                None
        """
        try:
            logging.debug(
                "{!s}: Set output status of channel {:d} to {!r}".format(
                    __name__, channel, status
                )
            )
            if status == 1:
                self._write(":sour{:d}:dc:init".format(channel))
            elif status == 0:
                self._write("sour{:d}:all:abor".format(channel))
                self._write("sour{:d}:volt 0".format(channel))
            else:
                raise TypeError("Status not valid, only 0 (off) and 1 (on) possible.")
        except Exception as e:
            logging.error(
                "{!s}: Cannot set output status of channel {!s} to {!s}".format(
                    __name__, channel, status
                )
            )
            raise type(e)(
                "{!s}: Cannot set output status of channel {!s} to {!s}\n{!s}".format(
                    __name__, channel, status, e
                )
            )
        return

    def get_end_of_sweep(self, channel=1):
        """
        Gets event of bias condition code register (ccr) entry "End for Sweep" <val> of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be between 1 and 24. Default is 1.

        Returns
        -------
        val: bool
            End of sweep entry of bias condition code register.
        """
        try:
            logging.debug(
                """{!s}: Get bias ccr event "End of Sweep" of channel {:d}""".format(
                    __name__, channel
                )
            )
            return bool(
                (int(self._ask(":stat:sour:even")) >> (0 + 8 * (channel - 1))) % 2
            )
        except Exception as e:
            logging.error(
                '{!s}: Cannot get bias ccr event "End of Sweep" of channel {!s}'.format(
                    __name__, channel
                )
            )
            raise type(e)(
                '{!s}: Cannot get bias ccr event "End of Sweep" of channel {!s}\n{!s}'.format(
                    __name__, channel, e
                )
            )

    def _wait_for_end_of_sweep(self, channel=1):
        """
        Waits until the event of bias condition code register (ccr) entry "End for Sweep" of channel <channel> occurs.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.

        Returns
        -------
        None
        """
        while not (self.get_end_of_sweep(channel=channel)):
            time.sleep(100e-3)
        return

    def get_end_of_measure(self, channel=1):
        """
        Gets condition of sense condition code register (ccr) entry "End of Measure" <val> of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.

        Returns
        -------
        val: bool
            End of sweep entry of bias condition code register.
        """
        # Corresponding Command: :STATus:SENSe:CONDition?
        try:
            logging.debug(
                """{!s}: Get sense ccr event "End of Measure" of channel {:d}""".format(
                    __name__, channel
                )
            )
            return bool(
                (int(self._ask(":stat:sens:cond")) >> (0 + 8 * (channel - 1))) % 2
            )
        except Exception as e:
            logging.error(
                '{!s}: Cannot get sense ccr event "End of Measure" of channel {!s}'.format(
                    __name__, channel
                )
            )
            raise type(e)(
                '{!s}: Cannot get sense ccr event "End of Measure" of channel {!s}\n{!s}'.format(
                    __name__, channel, e
                )
            )
