# -*- coding: utf-8 -*-

# Keithley.py driver for Keithley 2636A multi channel source measure unit
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

import qkit
from qkit.core.instrument_base import Instrument
import logging
import numpy as np


class virtual_tunnel_electronic(Instrument):
    """
    This is the virtual driver for the home made tunnel electronic combined with a Multi Channel Source Measure Unit <SMU>. I.a. it allows the external usage of voltage controlled current sources or transimpedance amplifiers

    Usage:
    Initialize with
    <name> = qkit.instruments.create('<name>', 'virtual_tunnel_electronic', SMU=<SMU>)
    """

    def __init__(self, name, SMU):
        """
        Initializes VISA communication with the instrument Yokogawa GS820.

        Parameters
        ----------
        name: string
            Name of the instrument (driver).
        SMU: qkit.instrument
            Multi channel source measure unit.
        reset: bool, optional
            Resets the instrument to default conditions.. Default is False.

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

        >>> SMU = qkit.instruments.create('SMU', 'Keithley', address='TCPIP0::00.00.000.00::INSTR', reset=True)
        >>> IVD = qkit.instruments.create('IVD', 'virtual_tunnel_electronic', SMU=SMU)
        Initialized the file info database (qkit.fid) in 0.000 seconds.
        """
        self.__name__ = __name__
        # create instrument
        logging.info(__name__ + ': Initializing instrument virtual tunnel electronic')
        Instrument.__init__(self, name, tags=['virtual'])
        self._instruments = qkit.instruments.get_instruments()
        # Source Measure Unit (SMU)
        self._SMU = SMU
        # external measurement setup
        self._BW = None  # bandwidth of prefilter (only for get_all and setting file)
        self._dAdV = 2e-6  # for external current bias
        self._amp = 1e3  # for external voltage amplifier
        self._tau_amp = 100e-3  # time constant of amplifier (only for get_all and setting file)
        self._dVdA = 1e8  # for external voltage bias
        self._Vdiv = 1e3  # for external voltage divider
        # internal variables
        self._sweep_mode = 0  # VV-mode
        self._sweep_channels = (1, 2)
        self._sweep_modes = {0: 'VV-mode', 1: 'IV-mode', 2: 'VI-mode'}
        self._pseudo_bias_mode = 0  # current bias
        self._pseudo_bias_modes = {0: 'current bias', 1: 'voltage bias'}
        # dict of defaults values: defaults[<pseudo_bias_mode>][<parameter>][<value>]
        self._defaults = {0: {'dAdV': 2e-6,
                              'amp': 1e3},
                          1: {'dVdA': 1e8,
                              'Vdiv': 1e3}}
        self._default_str = 'default parameters'
        self.__set_defaults_docstring()

    def set_BW(self, val=None):
        """
        Sets the internal variable for the bandwidth of an external filter to <val>.

        Parameters
        ----------
        val: float
            Bandwidth of external filter (in Hz). Default is None.

        Returns
        -------
        None
        """
        self._BW = val
        return

    def get_BW(self):
        """
        Gets the internal variable for the bandwidth of an external filter.

        Parameters
        ----------
        None

        Returns
        -------
        val: float
            Bandwidth of external filter (in Hz). Default is None.
        """
        return self._BW

    def set_dAdV(self, val=1):
        """
        Sets the internal variable for the voltage-current conversion factor to <val>.
        This is used for the current bias if the currents to apply are generated by means of an external voltage controlled current source.

        Parameters
        ----------
        val: float
            Voltage-current conversion factor (in A/V). Default is 1.

        Returns
        -------
        None
        """
        self._dAdV = val
        return

    def get_dAdV(self):
        """
        Gets the internal variable for the voltage-current conversion factor.
        This is used for the current bias if the currents to apply are generated by means of an external voltage controlled current source.

        Parameters
        ----------
        None

        Returns
        -------
        val: float
            Voltage-current conversion factor (in A/V).
        """
        return self._dAdV

    def set_amp(self, val=1):
        """
        Sets the internal variable for the pre-amplification factor to <val>.
        This is used in the current bias if the measured voltages are amplified by means of an external pre-amplifier.

        Parameters
        ----------
        val: float
            Pre-amplification factor. Default is 1.

        Returns
        -------
        None
        """
        self._amp = val
        return

    def get_amp(self):
        """
        Gets the internal variable for the pre-amplification factor.
        This is used in the current bias if the measured voltages are amplified by means of an external pre-amplifier.

        Parameters
        ----------
        None

        Returns
        -------
        val: float
            Pre-amplification factor.
        """
        return self._amp

    def set_tau_amp(self, val=100e-3):
        """
        Sets the internal variable for the pre-amplifiers lowpass filters time constant to <val>.
        This is used in the current bias if the measured voltages are amplified by means of an external pre-amplifier whose feedback includes a RC element to lowpass filter the signal.

        Parameters
        ----------
        val: float
            Pre-amplifiers time constant (τ=2πRC in s). Default is 100e-3.

        Returns
        -------
        None
        """
        self._tau_amp = val
        return

    def get_tau_amp(self):
        """
        Gets the internal variable for the pre-amplifiers lowpass filters time constant.
        This is used in the current bias if the measured voltages are amplified by means of an external pre-amplifier whose feedback includes a RC element to lowpass filter the signal.

        Parameters
        ----------
        None

        Returns
        -------
        val: float
            Pre-amplifiers time constant (τ=2πRC in s).
        """
        return self._tau_amp

    def set_dVdA(self, val=1):
        """
        Sets the internal variable for the current-voltage conversion to <val>.
        This is used for the voltage bias if the measured currents are converted to voltages by means of an external transimpedance amplifier.

        Parameters
        ----------
        val: float
            Current-voltage conversion factor (in V/A). Default is 1.

        Returns
        -------
        None
        """
        self._dVdA = val

    def get_dVdA(self):
        """
        Gets the internal variable for the current-voltage conversion.
        This is used for the voltage bias if the measured currents are converted to voltages by means of an external transimpedance amplifier.

        Parameters
        ----------
        None

        Returns
        -------
        val: float
            Current-voltage conversion factor (in V/A).
        """
        return self._dVdA

    def set_Vdiv(self, val=1):
        """
        Sets the internal variable for the voltage division factor to <val>.
        This is used for the voltage bias if the input voltage is divided by means of an external voltage divider.

        Parameters
        ----------
        val: float
            Voltage division factor. Default is 1.

        Returns
        -------
        None
        """
        self._Vdiv = val

    def get_Vdiv(self):
        """
        Gets the internal variable for the voltage division factor.
        This is used for the voltage bias if the input voltage is divided by means of an external voltage divider.

        Parameters
        ----------
        None

        Returns
        -------
        val: float
            Voltage division factor.
        """
        return self._Vdiv

    def set_measurement_mode(self, mode, channel=1):
        """
        Sets measurement mode (wiring system) of channel <channel> to <mode>.

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
        return self._SMU.set_measurement_mode(mode=mode, channel=channel)

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
        return self._SMU.get_measurement_mode(channel=channel)

    def set_bias_mode(self, mode, channel=1):
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
        return self._SMU.set_bias_mode(mode=mode, channel=channel)

    def get_bias_mode(self, channel=1):
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
        return self._SMU.get_bias_mode(channel=channel)

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
        return self._SMU.set_sense_mode(mode=mode, channel=channel)

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
        return self._SMU.get_sense_mode(channel=channel)

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
        return self._SMU.set_bias_range(val=val, channel=channel)

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
            Bias range. Possible values for currents are 100pA, 1nA, 10nA, 100nA, 1uA, 10uA, 100uA, 1mA, 10mA, 100mA, 1 A, 1.5A and for voltages 200mV, 2V, 20V, 200V.
        """
        return self._SMU.get_bias_range(channel=channel)

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
        return self._SMU.set_sense_range(val=val, channel=channel)

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
            Sense range. Possible values are -1 (auto), for currents 100pA, 1nA, 10nA |100nA, 1uA, 10uA, 100uA, 1mA, 10mA, 100mA, 1 A, 1.5A and for voltages 200mV, 2V, 20V, 200V.
        """
        return self._SMU.get_sense_range(channel=channel)

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
        return self._SMU.set_bias_delay(val=val, channel=channel)

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
        return self._SMU.get_bias_delay(channel=channel)

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
            Multiplier to the delays if auto delay is used (for Keithley 2636A only). Default is 1.

        Returns
        -------
        None
        """
        return self._SMU.set_sense_delay(val=val, channel=channel, **kwargs)

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
        return self._SMU.get_sense_delay(channel=channel)

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
            Type of filter used for measurements when the measurement filter is enabled (for Keithley 2636A only). Possible values are 0 (moving average) | 1 (repeat average) | 2 (median). Default is 1.

        Returns
        -------
        None
        """
        return self._SMU.set_sense_average(val=val, channel=channel, **kwargs)

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
        mode: str, optional
            Type of filter used for measurements when the measurement filter is enabled. Measnings are 0 (moving average) | 1 (repeat average) | 2 (median).
        """
        return self._SMU.get_sense_average(channel=channel)

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
        return self._SMU.set_plc(val=val)

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
        return self._SMU.get_plc()

    def set_sense_nplc(self, val, channel=1):
        """
        Sets sense nplc (number of power line cycle) of channel <channel> with the <val>-fold of one power line cycle.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.
        val: float
            Integration aperture for measurements. Possible values depend on the used SMU.

        Returns
        -------
        None
        """
        return self._SMU.set_sense_nplc(val=val, channel=channel)

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
        return self._SMU.get_sense_nplc(channel=channel)

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
        return self._SMU.set_sense_autozero(val=val, channel=channel)

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
        return self._SMU.get_sense_autozero(channel=channel)

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
        return self._SMU.set_status(status=status, channel=channel)

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
        return self._SMU.get_status(channel=channel)

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
            if len(channels) == 0:
                logging.debug('{!s}: Set sweep channels to {!s}'.format(__name__, default_channels[mode]))
                self._sweep_channels = default_channels[mode]
                self._SMU._sweep_channels = default_channels[mode]
            else:
                logging.debug('{!s}: Set sweep channels to {!s}'.format(__name__, channels))
                self._sweep_channels = channels
                self._SMU._sweep_channels = channels
            logging.debug('{!s}: Set sweep mode to {:d}'.format(__name__, mode))
            self._sweep_mode = mode
            self._SMU.set_sweep_mode(mode=mode)
        else:
            logging.error('{!s}: Cannot set sweep mode to {!s}'.format(__name__, mode))
            raise ValueError('{!s}: Cannot set sweep mode to {!s}'.format(__name__, mode))

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
        if self._sweep_channels != self._SMU.get_sweep_channels():
            logging.error(
                '{!s}: sweep channels of {:s} and {:s} do not coincide: {:s} and {:s}'.format(__name__, self.__name__,
                                                                                              self._SMU.__name__,
                                                                                              self._sweep_channels,
                                                                                              self._SMU.get_sweep_channels()))
            raise ValueError(
                '{!s}: sweep channels of {:s} and {:s} do not coincide: {:s} and {:s}'.format(__name__, self.__name__,
                                                                                              self._SMU.__name__,
                                                                                              self._sweep_channels,
                                                                                              self._SMU.get_sweep_channels()))
        else:
            return self._sweep_channels

    def set_pseudo_bias_mode(self, mode):
        """
        Sets an internal variable according to the external measurement setup that proviedes an effective bias to <mode>.
         * For the current bias the exernal setup includes
            * a voltage-controlled current source to generate the bias currents and
            * a voltage pre-amplifier to amplify the measured voltages.
         * For the voltage bias the exernal setup includes
            * a voltage divider to reduce the bias voltages and
            * a transimpedance amplifier that converts the measured currents to voltages.

        Parameters
        ----------
        mode: int
            Pseudo bias mode denoting current and voltage bias. Possible values are 0 (current bias) and 1 (voltage bias).

        Returns
        -------
        None
        """
        if mode in [0, 1, 2]:
            logging.debug('{!s}: Set pseudo bias mode to {:d}'.format(__name__, mode))
            self._pseudo_bias_mode = mode
            self.__set_defaults_docstring()
        else:
            logging.error('{!s}: Cannot set pseudo bias mode to {!s}'.format(__name__, mode))
            raise ValueError('{!s}: Cannot set pseudo bias mode to {!s}'.format(__name__, mode))

    def get_pseudo_bias_mode(self):
        """
        Gets an internal variable according to the external measurement setup that proviedes an effective bias.
         * For the current bias the exernal setup includes
            * a voltage-controlled current source to generate the bias currents and
            * a voltage pre-amplifier to amplify the measured voltages.
         * For the voltage bias the exernal setup includes
            * a voltage divider to reduce the bias voltages and
            * a transimpedance amplifier that converts the measured currents to voltages.

        Parameters
        ----------
        None

        Returns
        -------
        mode: int
            Pseudo bias mode denoting current and voltage bias. Possible values are 0 (current bias) and 1 (voltage bias).
        """
        return self._pseudo_bias_mode

    def get_sweep_bias(self):
        """
        Gets the real bias mode as combination of <self._sweep_mode> and <self._pseudo_bias_mode>.

        Parameters
        ----------
        None

        Returns
        -------
        mode: int
            Bias mode. Meanings are 0 (current) and 1 (voltage).
        """
        # attribute **kwargs needed for identical call as in SMUs (which need channels)
        if self._sweep_mode != self._SMU.get_sweep_mode():
            logging.error(
                '{!s}: sweep mode of {:s} and {:s} do not coincide: {:s} and {:s}'.format(__name__, self.__name__,
                                                                                          self._SMU.__name__,
                                                                                          self._sweep_modes[
                                                                                              self._sweep_mode],
                                                                                          self._sweep_modes[
                                                                                              self._SMU.get_sweep_mode()]))
            raise ValueError(
                '{!s}: sweep mode of {:s} and {:s} do not coincide: {:s} and {:s}'.format(__name__, self.__name__,
                                                                                          self._SMU.__name__,
                                                                                          self._sweep_modes[
                                                                                              self._sweep_mode],
                                                                                          self._sweep_modes[
                                                                                              self._SMU.get_sweep_mode()]))
        else:
            return int(not bool(self._sweep_mode)) * self._pseudo_bias_mode + int(bool(self._sweep_mode)) * (
                        self._sweep_mode - 1)  # 0 (current bias) | 1 (voltage bias)

    def set_voltage(self, val, channel=1):
        """
        Sets bias voltage value of channel <channel> to <val>.
        This can only be set in the effective voltage bias mode, defined by <self.sweep_mode> and <self.pseudo_bias_mode>, and considers an external voltage divider <self._Vdiv>.

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
        if self._sweep_mode == 0:  # 0 (VV mode)
            if not self._pseudo_bias_mode:  # 0 (current bias)
                logging.error(
                    '{!s}: Cannot set voltage value of channel {!s} in the current bias'.format(__name__, channel))
                raise SystemError(
                    '{!s}: Cannot set voltage value of channel {!s} in the current bias'.format(__name__, channel))
            elif self._pseudo_bias_mode:  # 1 (voltage bias)
                return self._SMU.set_bias_value(val=val * self._Vdiv, channel=channel)
        elif self._sweep_mode == 1:  # 1 (IV mode)
            logging.error(
                '{!s}: Cannot set voltage value of channel {!s} in the current bias'.format(__name__, channel))
            raise SystemError(
                '{!s}: Cannot set voltage value of channel {!s} in the current bias'.format(__name__, channel))
        elif self._sweep_mode == 2:  # 2 (VI-mode)
            return self._SMU.set_bias_value(val=val, channel=channel)

    def get_voltage(self, channel=1):
        """
        Gets voltage value of channel <channel> taking tunnel settings of the electronic into account (<sweep_mode>, <pseudo_bias_mode>)

        Gets bias or sense voltage value of channel <channel>.
        This depends on the effective bias mode, defined by <self.sweep_mode> and <self.pseudo_bias_mode>, and considers the external pre-amplifier <self._amp> (current bias) and the external voltage divider <self._Vdiv> (voltage bias).

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.

        Returns
        -------
        val: float
            Bias or sense voltage value.
        """
        if self._sweep_mode == 0:  # 0 (VV mode)
            if not self._pseudo_bias_mode:  # 0 (current bias)
                return self._SMU.get_sense_value(channel=channel) / self._amp
            elif self._pseudo_bias_mode:  # 1 (voltage bias)
                return self._SMU.get_bias_value(channel=channel) / self._Vdiv
        elif self._sweep_mode == 1:  # 1 (IV mode)
            return self._SMU.get_sense_value(channel=channel)
        elif self._sweep_mode == 2:  # 2 (VI-mode)
            return self._SMU.get_bias_value(channel=channel)

    def set_current(self, val, channel=1):
        """
        Sets bias current value of channel <channel> to <val>.
        This can only be set in the effective current bias mode, defined by <self.sweep_mode> and <self.pseudo_bias_mode>, and considers an external voltage-controlled current source <self._dAdV>.

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
        if self._sweep_mode == 0:  # 0 (VV mode)
            if not self._pseudo_bias_mode:  # 0 (current bias)
                return self._SMU.set_bias_value(val=val / self._dAdV, channel=channel)
            elif self._pseudo_bias_mode:  # 1 (voltage bias)
                logging.error(
                    '{!s}: Cannot set current value of channel {!s} in the voltage bias'.format(__name__, channel))
                raise SystemError(
                    '{!s}: Cannot set current value of channel {!s} in the voltage bias'.format(__name__, channel))
        elif self._sweep_mode == 1:  # 1 (IV mode)
            return self._SMU.set_bias_value(val=val, channel=channel)
        elif self._sweep_mode == 2:  # 2 (VI-mode)
            logging.error(
                '{!s}: Cannot set current value of channel {!s} in the voltage bias'.format(__name__, channel))
            raise SystemError(
                '{!s}: Cannot set current value of channel {!s} in the voltage bias'.format(__name__, channel))

    def get_current(self, channel=1):
        """
        Gets current value of channel <channel> taking tunnel settings of the electronic into account (<sweep_mode>, <pseudo_bias_mode>)

        Gets bias or sense current value of channel <channel>.
        This depends on the effective bias mode, defined by <self.sweep_mode> and <self.pseudo_bias_mode>, and considers the external voltage-controlled current source <self._dAdV> (current bias) and the external transimpedance amplifier <self._dVdA> (voltage bias).

        Parameters
        ----------
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.

        Returns
        -------
        val: float
            Bias or sense current value.
        """
        if self._sweep_mode == 0:  # 0 (VV mode)
            if not self._pseudo_bias_mode:  # 0 (current bias)
                return self._SMU.get_bias_value(channel=channel) * self._dAdV
            elif self._pseudo_bias_mode:  # 1 (voltage bias)
                return self._SMU.get_sense_value(channel=channel) / self._dVdA
        elif self._sweep_mode == 1:  # 1 (IV mode)
            return self._SMU.get_bias_value(channel=channel)
        elif self._sweep_mode == 2:  # 2 (VI-mode)
            return self._SMU.get_sense_value(channel=channel)

    def ramp_voltage(self, stop, step, step_time=0.1, channel=1):
        """
        Ramps voltage of channel <channel> from recent value to stop value <stop> with step size <step> and step time <step_time> according to bias_mode.
        This can only be set in the effective voltage bias mode, defined by <self.sweep_mode> and <self.pseudo_bias_mode>, and considers an external voltage divider <self._Vdiv>.

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
        if self._sweep_mode == 0:  # 0 (VV mode)
            if not self._pseudo_bias_mode:  # 0 (current bias)
                logging.error(
                    '{!s}: Cannot set voltage value of channel {!s} in the current bias'.format(__name__, channel))
                raise SystemError(
                    '{!s}: Cannot set voltage value of channel {!s} in the current bias'.format(__name__, channel))
            elif self._pseudo_bias_mode:  # 1 (voltage bias)
                return self._SMU.ramp_bias(stop=stop * self._Vdiv, step=step * self._Vdiv, step_time=step_time,
                                           channel=channel)
        elif self._sweep_mode == 1:  # 1 (IV mode)
            logging.error(
                '{!s}: Cannot set voltage value of channel {!s} in the current bias'.format(__name__, channel))
            raise SystemError(
                '{!s}: Cannot set voltage value of channel {!s} in the current bias'.format(__name__, channel))
        elif self._sweep_mode == 2:  # 2 (VI-mode)
            return self._SMU.ramp_bias(stop=stop, step=step, step_time=step_time, channel=channel)

    def ramp_current(self, stop, step, step_time=0.1, channel=1):
        """
        Ramps current of channel <channel> from recent value to stop value <stop> with step size <step> and step time <step_time> according to bias_mode.
        This can only be set in the effective current bias mode, defined by <self.sweep_mode> and <self.pseudo_bias_mode>, and considers an external voltage-controlled current source <self._dAdV>.

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
        if self._sweep_mode == 0:  # 0 (VV mode)
            if not self._pseudo_bias_mode:  # 0 (current bias)
                return self._SMU.ramp_bias(stop=stop / self._dAdV, step=step / self._dAdV, step_time=step_time,
                                           channel=channel)
            elif self._pseudo_bias_mode:  # 1 (voltage bias)
                logging.error(
                    '{!s}: Cannot set current value of channel {!s} in the voltage bias'.format(__name__, channel))
                raise SystemError(
                    '{!s}: Cannot set current value of channel {!s} in the voltage bias'.format(__name__, channel))
        elif self._sweep_mode == 1:  # 1 (IV mode)
            return self._SMU.ramp_bias(stop=stop, step=step, step_time=step_time, channel=channel)
        elif self._sweep_mode == 2:  # 2 (VI-mode)
            logging.error(
                '{!s}: Cannot set current value of channel {!s} in the voltage bias'.format(__name__, channel))
            raise SystemError(
                '{!s}: Cannot set current value of channel {!s} in the voltage bias'.format(__name__, channel))

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
        if not self._sweep_mode:  # 0 (VV-mode)
            if not self._pseudo_bias_mode:  # 0 (current bias)
                sweep = np.array(sweep).astype(float) / self._dAdV
                sweep[2] = np.abs(sweep[2])
                # alternative: self._sweep = np.array((lambda a: [a[0], a[1], np.abs(a[-1])])(sweep)).astype(float)/self._dAdV
            elif self._pseudo_bias_mode:  # 0 (voltage bias)
                sweep = np.array(sweep).astype(float) * self._Vdiv
                sweep[2] = np.abs(sweep[2])
        return self._SMU.set_sweep_parameters(sweep)

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
        bias_values, sense_values = self._SMU.get_tracedata()
        if self._sweep_mode == 0:  # IV-mode
            if not self._pseudo_bias_mode:  # 0 (current bias)
                I_values = bias_values * self._dAdV
                V_values = sense_values / self._amp
            elif self._pseudo_bias_mode:  # 1 (voltage bias)
                V_values = bias_values / self._Vdiv
                I_values = sense_values / self._dVdA
        elif self._sweep_mode == 1:  # IV-mode
            I_values = bias_values
            V_values = sense_values
        elif self._sweep_mode == 2:  # VI-mode
            V_values = bias_values
            I_values = sense_values
        return I_values, V_values

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

    def set_defaults(self, pseudo_bias_mode=None, SMU=True, sweep_mode=None):
        """
        Sets default settings for different pseudo bias modes <pseudo_bias_mode> and optional of the used source measure unit <SMU> of channel <channel>, too. Actual settings are:
        default parameters

        Parameters
        ----------
        pseudo_bias_mode: int
            Pseudo bias mode denoting current and voltage bias. Possible values are None (before used <self._sweep_mode>), 0 (current bias) and 1 (voltage bias). Default is None.
        SMU: bool
            Source measure unit. Default is True.
        sweep_mode: int
            Sweep mode denoting bias and sense modes. Possible values are None (before used <self._sweep_mode>), 0 (VV-mode), 1 (IV-mode) or 2 (VI-mode). Default is 1

        Returns
        -------
        None
        """
        # distinguish different pseudo bias modes
        if pseudo_bias_mode is not None:
            self.set_pseudo_bias_mode(pseudo_bias_mode)
        # set values
        for key_parameter, val_parameter in self._defaults[self._pseudo_bias_mode].items():
            eval('self.set_{:s}(val={!s})'.format(key_parameter, val_parameter))
        # set defaults of SMU according to sweep_mode
        if SMU:
            if sweep_mode is not None:
                self.set_sweep_mode(sweep_mode)
            self._SMU.set_defaults(sweep_mode=sweep_mode)

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
        new = 'pseudo bias mode: {:d}:\n'.format(self._pseudo_bias_mode) + ''.join(
            ['\t\t{:s}: {:1.2e}\n'.format(key_parameter, val_parameter) for key_parameter, val_parameter in
             self._defaults[self._pseudo_bias_mode].items()])
        self.set_defaults.__func__.__doc__ = self.set_defaults.__func__.__doc__.replace(self._default_str, new)
        self._default_str = new
        return

    def get_all(self, SMU=True, channel=1):
        """
        Prints all settings of channel <channel> and optional of the used source measure unit <SMU>, too.

        Parameters
        ----------
        SMU: bool
            Source measure unit. Default is True.
        channel: int
            Number of channel of interest. Must be 1 or 2. Default is 1.

        Returns
        -------
        None
        """
        logging.info(__name__ + ': Get all')
        if self.get_BW() is not None:
            print('bandwidth          = {:1.0e}Hz'.format(self.get_BW()))
        print('dAdV               = {:1.0e}A/V'.format(self.get_dAdV()))
        print('amp factor         = {:1.0e}'.format(self.get_amp()))
        print('amp time constant  = {:1.0e}s'.format(self.get_tau_amp()))
        print('dVdA               = {:1.0e}V/A'.format(self.get_dVdA()))
        print('voltage divider    = {:1.0e}'.format(self.get_Vdiv()))
        print('sweep mode         = {:d} ({:s})'.format(self._sweep_mode, self._sweep_modes[self._sweep_mode]))
        print('pseudo bias mode   = {:d} ({:s})'.format(self._pseudo_bias_mode,
                                                        self._pseudo_bias_modes[self._pseudo_bias_mode]))
        if SMU:
            self._SMU.get_all(channel=channel)
        return

    def reset(self, SMU=True):
        """
        Resets internal variables for external tunnel electronic to default conditions and optional of the used source measure unit <SMU>, too.
        Resets the instrument or a single channel to .

        Parameters
        ----------
        SMU: bool
            Source measure unit. Default is True.

        Returns
        -------
        None
        """
        self.set_BW()
        self.set_dAdV()
        self.set_amp()
        self.set_tau_amp()
        self.set_dVdA()
        self.set_Vdiv()
        if SMU:
            self._SMU.reset()

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
        parlist = {# 'measurement_mode': self._sweep_channels,
                   # 'bias_mode': self._sweep_channels,
                   # 'sense_mode': self._sweep_channels,
                   # 'bias_range': self._sweep_channels,
                   # 'sense_range': self._sweep_channels,
                   # 'bias_delay': self._sweep_channels,
                   # 'sense_delay': self._sweep_channels,
                   # 'sense_average': self._sweep_channels,
                   # 'plc': [None],
                   # 'sense_nplc': self._sweep_channels,
                   'sweep_mode': [None],
                   'pseudo_bias_mode': [None],
                   'BW': [None]
                   }
        if not self._pseudo_bias_mode:  # 0 (current bias)
            parlist['dAdV'] = [None]
            parlist['amp'] = [None]
            # parlist['current'] = self._sweep_channels
        elif self._pseudo_bias_mode:  # 1 (voltage bias)
            parlist['dVdA'] = [None]
            parlist['Vdiv'] = [None]
            # parlist['voltage'] = self._sweep_channels
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
            Number of channels of interest. Must be in {1, 2} for channel specific parameters or None for channel independant (global) parameters.

        Returns
        -------
        parlist: dict
            Parameter names as keys, values of corresponding channels as values.
        """
        channels = kwargs.get('channels')
        if channels != [None]:
            return tuple(eval('map(lambda channel, self=self: self.get_{:s}(channel=channel), [{:s}])'.format(param, ', '.join(map(str, channels)))))
            #return tuple([eval('self.get_{:s}(channel={!s})'.format(param, channel)) for channel in channels])
        else:
            return tuple(eval('map(lambda channel, self=self: self.get_{:s}(), [None])'.format(param)))
            #return eval('self.get_{:s}()'.format(param))
