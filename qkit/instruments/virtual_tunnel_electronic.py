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
        self.set_sweep_mode(0, 1, 2)  # 0 (VV-mode) with channels 1 (bias) and 2 (sense)
        self._sweep_modes = {0: 'VV-mode', 1: 'IV-mode', 2: 'VI-mode'}
        self.set_pseudo_bias_mode(mode=0)  # current bias
        self._pseudo_bias_modes = {0: 'current bias', 1: 'voltage bias'}

    def set_BW(self, val=None):
        """
        Sets the internal variable for the bandwidth of an external filter to <val> (in Hz)
        
        Input:
            val (float): None (default)
        Output:
            None
        """
        self._BW = val

    def get_BW(self):
        """
        Gets the internal variable for the bandwidth of an external filter (in Hz)
        
        Input:
            None
        Output:
            val (float)
        """
        return self._BW

    def set_dAdV(self, val=1):
        """
        Sets the internal variable for the voltage-current conversion factor of an external voltage controlled current source used for the current bias to <val> (in A/V)
        
        Input:
            val (float): 1 (default)
        Output:
            None
        """
        self._dAdV = val

    def get_dAdV(self):
        """
        Gets the internal variable for the voltage-current conversion factor of an external voltage controlled current source used for the current bias (in A/V)
        
        Input:
            None
        Output:
            val (float)
        """
        return self._dAdV

    def set_amp(self, val=1):
        """
        Sets the internal variable for the amplification factor of an external amplifier to <val>
        
        Input:
            val (float): 1 (default)
        Output:
            None
        """
        self._amp = val

    def get_amp(self):
        """
        Gets the internal variable for the amplification factor of an external amplifier
        
        Input:
            None
        Output:
            val (float)
        """
        return self._amp

    def set_tau_amp(self, val=100e-3):
        """
        Sets the internal variable for the time constant of an external amplifier to <val> (τ=2πRC in s)
        
        Input:
            val (float): 100e-3 (default)
        Output:
            None
        """
        self._tau_amp = val

    def get_tau_amp(self):
        """
        Gets the internal variable for the time constant of an external amplifier (τ=2πRC in s)
        
        Input:
            None
        Output:
            val (float)
        """
        return self._tau_amp

    def set_dVdA(self, val=1):
        """
        Sets the internal variable for the current-voltage conversion of an external transimpedance amplifier used for the voltage bias to <val> (in V/A)
        
        Input:
            val (float): 1 (default)
        Output:
            None
        """
        self._dVdA = val

    def get_dVdA(self):
        """
        Gets the internal variable for the current-voltage conversion of an external transimpedance amplifier used for the voltage bias (in V/A)
        
        Input:
            None
        Output:
            val (float)
        """
        return self._dVdA

    def set_Vdiv(self, val=1):
        """
        Sets the internal variable for the voltage divider factor of an external voltage divider to <val>
        
        Input:
            val (float): 1 (default)
        Output:
            None
        """
        self._Vdiv = val

    def get_Vdiv(self):
        """
        Gets the internal variable for the voltage divider factor of an external voltage divider
        
        Input:
            None
        Output:
            val (float)
        """
        return self._Vdiv

    def set_measurement_mode(self, val, channel=1):
        """
        Sets measurement mode (wiring system) of channel <channel> to <val>

        Input:
            channel (int): 1 (default) | 2
            val (int): 0 (2-wire) | 1 (4-wire)
        Output:
            None
        """
        return self._SMU.set_measurement_mode(val=val, channel=channel)

    def get_measurement_mode(self, channel=1):
        """
        Gets measurement mode (wiring system) of channel <channel>

        Input:
            channel (int): 1 (default) | 2
        Output:
            val (int): 0 (2-wire) | 1 (4-wire)
        """
        return self._SMU.get_measurement_mode(channel=channel)

    def set_bias_mode(self, mode, channel=1):
        """
        Sets bias mode of channel <channel> to <mode> regime.

        Input:
            mode (int): 0 (current) | 1 (voltage)
            channel (int): 1 (default) | 2
        Output:
            None
        """
        return self._SMU.set_bias_mode(mode=mode, channel=channel)

    def get_bias_mode(self, channel=1):
        """
        Gets bias mode <output> of channel <channel>

        Input:
            channel (int): 1 (default) | 2
        Output:
            mode (int): 0 (current) | 1 (voltage)
        """
        return self._SMU.get_bias_mode(channel=channel)

    def set_sense_mode(self, mode, channel=1):
        """
        Sets sense mode of channel <channel> to <mode> regime.

        Input:
            mode (str): 0 (current) | 1 (voltage)
            channel (int): 1 (default) | 2
        Output:
            None
        """
        return self._SMU.set_sense_mode(mode=mode, channel=channel)

    def get_sense_mode(self, channel=1):
        """
        Gets sense mode <output> of channel <channel>

        Input:
            channel (int): 1 (default) | 2
        Output:
            mode (str): 0 (current) | 1 (voltage)
        """
        return self._SMU.get_sense_mode(channel=channel)

    def set_bias_range(self, val, channel=1):
        """
        Sets bias range of channel <channel> to <val>

        Input:
            val (float): -1 (auto) | possible ranges of the used SMU
            channel (int): 1 (default) | 2
        Output:
            None
        """
        return self._SMU.set_bias_range(val=val, channel=channel)

    def get_bias_range(self, channel=1):
        """
        Gets bias mode <output> of channel <channel>

        Input:
            channel (int): 1 (default) | 2
        Output:
            val (float): -1 (auto) | possible ranges of the used SMU
        """
        return self._SMU.get_bias_range(channel=channel)
    
    def set_sense_range(self, val, channel=1):
        """
        Sets sense range of channel <channel> to <val>

        Input:
            val (float): -1 (auto) | possible ranges of the used SMU
            channel (int): 1 (default) | 2
        Output:
            None
        """
        return self._SMU.set_sense_range(val=val, channel=channel)

    def get_sense_range(self, channel=1):
        """
        Gets sense mode <output> of channel <channel>
        
        Input:
            channel (int): 1 (default) | 2
        Output:
            val (float): -1 (auto) | possible ranges of the used SMU
        """
        return self._SMU.get_sense_range(channel=channel)

    def set_bias_delay(self, val, channel=1):
        """
        Sets bias delay of channel <channel> to <val>
        
        Input:
            val (float): -1 (auto) | 0 (off) | positive number
            channel (int): 1 (default) | 2
        Output:
            None
        """
        return self._SMU.set_bias_delay(val=val, channel=channel)

    def get_bias_delay(self, channel=1):
        """
        Gets bias delay of channel <channel>
        
        Input:
            channel (int): 1 (default) | 2
        Output:
            val (float)
        """
        return self._SMU.get_bias_delay(channel=channel)

    def set_sense_delay(self, val, factor=1, channel=1):
        """
        Sets sense delay of channel <channel> to <val>
        
        Input:
            val (float): -1 (auto) | 0 (off) | positive number
            factor (float): 1 (default) | multiplier to the delays if auto delay is used (for Keithley 2636A only)
            channel (int): 1 (default) | 2
        Output:
            None
        """
        return self._SMU.set_sense_delay(val=val, factor=factor, channel=channel)

    def get_sense_delay(self, channel=1):
        """
        Gets sense delay of channel <channel>
        
        Input:
            channel (int): 1 (default) | 2
        Output:
            val (float)
        """
        return self._SMU.get_sense_delay(channel=channel)

    def set_sense_average(self, val, mode=1, channel=1):
        """
        Sets sense average of channel <channel> to <val>
        
        Input:
            val (int): possible values of the used SMU
            mode (str): 0 (moving average) | 1 (repeat average) (default) | 2 (median)
            channel (int): 1 (default) | 2
        Output:
            None
        """
        return self._SMU.set_sense_average(val=val, mode=mode, channel=channel)

    def get_sense_average(self, channel=1):
        """
        Gets sense average of channel <channel>
        
        Input:
            channel (int): 1 (default) | 2
        Output:
            status (bool)
            val (int)
            mode (int)
        """
        return self._SMU.get_sense_average(channel=channel)

    def set_plc(self, val):
        """
        Sets power line cycle (PLC) to <val>
        
        Input:
            plc (int): -1 (auto) | 50 | 60
        Output:
            None
        """
        return self._SMU.set_plc(val=val)

    def get_plc(self):
        """
        Gets power line cycle (PLC)
        
        Input:
            None
        Output:
            val (float): 50 | 60
        """
        return self._SMU.get_plc()

    def set_sense_nplc(self, val, channel=1):
        """
        Sets sense nplc (number of power line cycle) of channel <channel> with the <val>-fold of one power line cycle
        
        Input:
            channel (int): 1 (default) | 2
            val (float): possible values of the used SMU
        Output:
            None
        """
        return self._SMU.set_sense_nplc(val=val, channel=channel)

    def get_sense_nplc(self, channel=1):
        """
        Gets sense nplc (number of power line cycle) of channel <channel>
        
        Input:
            channel (int): 1 (default) | 2
        Output:
            val (int): possible values of the used SMU
        """
        return self._SMU.get_sense_nplc(channel=channel)

    def set_sense_autozero(self, val, channel=1):
        """
        Sets autozero of channel <channel> to <val>.
        
        Input:
            val (int): 0 (off) | 1 (on) | 2 (once)
        Output:
            None
        """
        return self._SMU.set_sense_autozero(val=val, channel=channel)

    def get_sense_autozero(self, channel=1):
        """
        Gets autozero of channel <channel>
        
        Input:
            channel (int): 1 (default) | 2
        Output:
            val (int)
        """
        return self._SMU.get_sense_autozero(channel=channel)

    def set_status(self, status, channel=1):
        """
        Sets output status of channel <channel> to <status>
        
        Input:
            status (int): 0 (off) | 1 (on)
            channel (int): 1 (default) | 2
        Output:
            None
        """
        return self._SMU.set_status(status=status, channel=channel)

    def get_status(self, channel=1):
        """
        Gets output status of channel <channel>
        
        Input:
            channel (int): 1 (default) | 2
        Output:
            status (int): 0 (off) | 1 (on)
        """
        return self._SMU.get_status(channel=channel)

    def set_sweep_mode(self, mode=1, *channels):
        """
        Sets an variable to decide weather
         * voltage is both applied and measured (VV-mode),
         * current is applied and voltage is measured (IV-mode) or
         * voltage is applied and current is measured (VI-mode)
        and channels <channels> that are used during sweeps. Give
         * two different channels in case of VV sweep mode (1st argument as bias channel and 2nd argument as sense channel)
         * one channel in case of IV or VI sweep mode

        Input:
            mode (int): 0 (VV-mode) | 1 (IV-mode) (default) | 2 (VI-mode)
            channels tuple(int): 1 | 2
        Output:
            None
        """
        default_channels = {0: (1, 2), 1: (1,), 2: (1,)}
        if mode in [0, 1, 2]:
            if len(channels) == int(not mode) + 1:
                logging.debug('{!s}: Set sweep channels to {:s}'.format(__name__, channels))
                self._sweep_channels = channels
                self._SMU._sweep_channels = channels
            elif len(channels) == 0:
                logging.debug('{!s}: Set sweep channels to {:s}'.format(__name__, default_channels[mode]))
                self._sweep_channels = default_channels[mode]
                self._SMU._sweep_channels = default_channels[mode]
            else:
                logging.error('{!s}: Cannot set sweep channels to {!s}'.format(__name__, channels))
                raise ValueError('{!s}: Cannot set sweep channels to {!s}'.format(__name__, channels))
            logging.debug('{!s}: Set sweep mode to {:d}'.format(__name__, mode))
            self._sweep_mode = mode
            self._SMU.set_sweep_mode(mode=mode)
        else:
            logging.error('{!s}: Cannot set sweep mode to {!s}'.format(__name__, mode))
            raise ValueError('{!s}: Cannot set sweep mode to {!s}'.format(__name__, mode))

    def get_sweep_mode(self):
        """
        Gets an internal variable to decide weather voltage is both applied and measured (VV-mode), current is applied and voltage is measured (IV-mode) or voltage is applied and current is measured (VI-mode).

        Input:
            None
        Output:
            mode (int): 0 (VV mode) | 1 (IV mode) | 2 (VI-mode)
        """
        if self._sweep_mode != self._SMU.get_sweep_mode():
            logging.error('{!s}: sweep mode of {:s} and {:s} do not coincide: {:s} and {:s}'.format(__name__, self.__name__, self._SMU.__name__, self._sweep_modes[self._sweep_mode], self._sweep_modes[self._SMU.get_sweep_mode()]))
            raise ValueError('{!s}: sweep mode of {:s} and {:s} do not coincide: {:s} and {:s}'.format(__name__, self.__name__, self._SMU.__name__, self._sweep_modes[self._sweep_mode], self._sweep_modes[self._SMU.get_sweep_mode()]))
        else:
            return self._sweep_mode

    def get_sweep_channels(self):
        """
        Gets channels <channels> that are used during sweeps. In the IV and VI sweep mode one channel requires for biasing and sensing, whereas two channels are returned in the VV sweep mode (1st as bias and 2nd as sense channel).

        Input:
            None
        Output:
            channels (tuple): 1 | 2
        """
        if self._sweep_channels != self._SMU.get_sweep_channels():
            logging.error('{!s}: sweep channels of {:s} and {:s} do not coincide: {:s} and {:s}'.format(__name__, self.__name__, self._SMU.__name__, self._sweep_channels, self._SMU.get_sweep_channels()))
            raise ValueError('{!s}: sweep channels of {:s} and {:s} do not coincide: {:s} and {:s}'.format(__name__, self.__name__, self._SMU.__name__, self._sweep_channels, self._SMU.get_sweep_channels()))
        else:
            return self._sweep_channels

    def set_pseudo_bias_mode(self, mode):
        """
        Sets an internal variable according to the external measurement setup that proviedes an effective bias <mode>

        Input:
            mode (int): 0 (current bias) | 1 (voltage bias)
        Output:
            None
        """
        if mode in [0, 1, 2]:
            logging.debug('{!s}: Set pseudo bias mode to {:d}'.format(__name__, mode))
            self._pseudo_bias_mode = mode
        else:
            logging.error('{!s}: Cannot set pseudo bias mode to {!s}'.format(__name__, mode))
            raise ValueError('{!s}: Cannot set pseudo bias mode to {!s}'.format(__name__, mode))

    def get_pseudo_bias_mode(self):
        """
        Gets an internal variable according to the external measurement setup that proviedes an effective bias <mode>

        Input:
            None
        Output:
            mode (int): 0 (current bias) | 1 (voltage bias)
        """
        return self._pseudo_bias_mode

    def get_sweep_bias(self):
        """
        Gets the real bias mode as combination of <self._sweep_mode> and <self._pseudo_bias_mode>

        Input:
            None
        Output:
            mode (int): 0 (current bias) | 1 (voltage bias)
        """
        # attribute **kwargs needed for identical call as in SMUs (which need channels)
        if self._sweep_mode != self._SMU.get_sweep_mode():
            logging.error('{!s}: sweep mode of {:s} and {:s} do not coincide: {:s} and {:s}'.format(__name__, self.__name__, self._SMU.__name__, self._sweep_modes[self._sweep_mode], self._sweep_modes[self._SMU.get_sweep_mode()]))
            raise ValueError('{!s}: sweep mode of {:s} and {:s} do not coincide: {:s} and {:s}'.format(__name__, self.__name__, self._SMU.__name__, self._sweep_modes[self._sweep_mode], self._sweep_modes[self._SMU.get_sweep_mode()]))
        else:
            return int(not bool(self._sweep_mode)) * self._pseudo_bias_mode + int(bool(self._sweep_mode)) * (self._sweep_mode - 1)  # 0 (current bias) | 1 (voltage bias)

    def set_voltage(self, val, channel=1):
        """
        Sets voltage value of channel <channel> to <val> taking tunnel settings of the electronic into account (<sweep_mode>, <pseudo_bias_mode>)
        
        Input:
            val (float)
            channel (int): 1 (default) | 2
        Output:
            None
        """
        if self._sweep_mode == 0:  # 0 (VV mode)
            if not self._pseudo_bias_mode:  # 0 (current bias)
                logging.error('{!s}: Cannot set voltage value of channel {!s} in the current bias'.format(__name__, channel))
                raise SystemError('{!s}: Cannot set voltage value of channel {!s} in the current bias'.format(__name__, channel))
            elif self._pseudo_bias_mode:  # 1 (voltage bias)
                return self._SMU.set_bias_value(val=val*self._Vdiv, channel=channel)
        elif self._sweep_mode == 1:  # 1 (IV mode)
            logging.error('{!s}: Cannot set voltage value of channel {!s} in the current bias'.format(__name__, channel))
            raise SystemError('{!s}: Cannot set voltage value of channel {!s} in the current bias'.format(__name__, channel))
        elif self._sweep_mode == 2:  # 2 (VI-mode)
            return self._SMU.set_bias_value(val=val, channel=channel)

    def get_voltage(self, channel=1):
        """
        Gets voltage value of channel <channel> taking tunnel settings of the electronic into account (<sweep_mode>, <pseudo_bias_mode>)
        
        Input:
            channel (int): 1 (default) | 2
        Output:
            val (float)
        """
        if self._sweep_mode == 0:  # 0 (VV mode)
            if not self._pseudo_bias_mode:  # 0 (current bias)
                return self._SMU.get_sense_value(channel=channel)/self._amp
            elif self._pseudo_bias_mode:  # 1 (voltage bias)
                return self._SMU.get_bias_value(channel=channel)/self._Vdiv
        elif self._sweep_mode == 1:  # 1 (IV mode)
            return self._SMU.set_sense_value(channel=channel)
        elif self._sweep_mode == 2:  # 2 (VI-mode)
            return self._SMU.set_bias_value(channel=channel)

    def set_current(self, val, channel=1):
        """
        Sets current value of channel <channel> to <val> taking tunnel settings of the electronic into account (<sweep_mode>, <pseudo_bias_mode>)
        
        Input:
            val (float): arb.
            channel (int): 1 (default) | 2
        Output:
            None
        """
        if self._sweep_mode == 0:  # 0 (VV mode)
            if not self._pseudo_bias_mode:  # 0 (current bias)
                return self._SMU.set_bias_value(val=val/self._dAdV, channel=channel)
            elif self._pseudo_bias_mode:  # 1 (voltage bias)
                logging.error('{!s}: Cannot set current value of channel {!s} in the voltage bias'.format(__name__, channel))
                raise SystemError('{!s}: Cannot set current value of channel {!s} in the voltage bias'.format(__name__, channel))
        elif self._sweep_mode == 1:  # 1 (IV mode)
            return self._SMU.set_bias_value(val=val, channel=channel)
        elif self._sweep_mode == 2:  # 2 (VI-mode)
            logging.error('{!s}: Cannot set current value of channel {!s} in the voltage bias'.format(__name__, channel))
            raise SystemError('{!s}: Cannot set current value of channel {!s} in the voltage bias'.format(__name__, channel))

    def get_current(self, channel=1):
        """
        Gets current value of channel <channel> taking tunnel settings of the electronic into account (<sweep_mode>, <pseudo_bias_mode>)
        
        Input:
            channel (int): 1 (default) | 2
        Output:
            val (float)
        """
        if self._sweep_mode == 0:  # 0 (VV mode)
            if not self._pseudo_bias_mode:  # 0 (current bias)
                return self._SMU.get_bias_value(channel=channel)*self._dAdV
            elif self._pseudo_bias_mode:  # 1 (voltage bias)
                return self._SMU.get_sense_value(channel=channel)/self._dVdA
        elif self._sweep_mode == 1:  # 1 (IV mode)
            return self._SMU.set_bias_value(channel=channel)
        elif self._sweep_mode == 2:  # 2 (VI-mode)
            return self._SMU.set_sense_value(channel=channel)

    def set_sweep_parameters(self, sweep):
        """
        Sets sweep parameters <sweep> and prepares instrument for the set sweep mode

        Input:
            sweep (list(float)): start, stop, step
        Output:
            None
        """
        if not self._sweep_mode:  # 0 (VV-mode)
            if not self._pseudo_bias_mode:  # 0 (current bias)
                sweep = np.array(sweep).astype(float)/self._dAdV
                sweep[2] = np.abs(sweep[2])
                # alternative: self._sweep = np.array((lambda a: [a[0], a[1], np.abs(a[-1])])(sweep)).astype(float)/self._dAdV
            elif self._pseudo_bias_mode:  # 0 (voltage bias)
                sweep = np.array(sweep).astype(float)*self._Vdiv
                sweep[2] = np.abs(sweep[2])
        return self._SMU.set_sweep_parameters(sweep)

    def get_tracedata(self):
        """
        Starts bias sweep and gets trace data in the set sweep mode.

        Input:
            None
        Output:
            bias_values (numpy.array(float))
            sense_values (numpy.array(float))
        """
        bias_values, sense_values = self._SMU.get_tracedata()
        if self._sweep_mode == 0:  # IV-mode
            if not self._pseudo_bias_mode:  # 0 (current bias)
                I_values = bias_values*self._dAdV
                V_values = sense_values/self._amp
            elif self._pseudo_bias_mode:  # 1 (voltage bias)
                V_values = bias_values/self._Vdiv
                I_values = sense_values/self._dVdA
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

        Input:
            sweep (list(float)): start, stop, step
        Output:
            bias_values (numpy.array(float))
            sense_values (numpy.array(float))
        """
        self.set_sweep_parameters(sweep=sweep)
        return self.get_tracedata()

    def set_defaults(self, sweep_mode=None, pseudo_bias_mode=None, SMU=True):
        """
        Sets default settings for different pseudo bias modes <pseudo_bias_mode> and optional of the used source measure unit <SMU> of channel <channel>, too, if <SMU>.
        
        Input:
            sweep_mode (int): None <self._sweep_mode> (default) | 0 (VV-mode) | 1 (IV-mode) | 2 (VI-mode)
            pseudo_bias_modes (int): None <self._sweep_mode> (default) | 0 (VV-mode) | 1 (IV-mode) | 2 (VI-mode)
            SMU (bool): False | True
        Output:
            None
        """
        # dict of defaults values: defaults[<pseudo_bias_mode>][<parameter>][<value>]
        defaults = {0: {'dAdV': 2e-6,
                        'amp': 1e3},
                    1: {'dVdA': 1e8,
                        'Vdiv': 1e3}}
        # distinguish different pseudo bias modes
        if sweep_mode is not None:
            self.set_sweep_mode(sweep_mode)
        if pseudo_bias_mode is not None:
            self.set_pseudo_bias_mode(pseudo_bias_mode)
        # set values
        for key_parameter, val_parameter in defaults[self._pseudo_bias_mode].items():
            eval('self.set_{:s}(val={!s})'.format(key_parameter, val_parameter))
        if SMU:
            self._SMU.set_defaults(sweep_mode=sweep_mode)

    def get_all(self, SMU=True, channel=1):
        """
        Prints all settings and optional of the used source measure unit <SMU> of channel <channel>, too.
        
        Input:
            SMU (bool): True | False
            channel (int): 1 (default) | 2
        Output:
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
        print('pseudo bias mode   = {:d} ({:s})'.format(self._pseudo_bias_mode, self._pseudo_bias_modes[self._pseudo_bias_mode]))
        if SMU:
            self._SMU.get_all(channel=channel)
        return

    def reset(self, SMU=True):
        """
        Resets internal variables for external bias and optional the instrument to factory settings, if source measure unit <SMU>.
        
        Input:
            SMU (bool): True | False
        Output:
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
        
        Input:
            None
        Output:
            parlist (dict): Parameter as key, corresponding channels as value
        """
        parlist = {'measurement_mode': [1, 2],
                   'bias_mode': [1, 2],
                   'sense_mode': [1, 2],
                   'bias_range': [1, 2],
                   'sense_range': [1, 2],
                   'bias_delay': [1, 2],
                   'sense_delay': [1, 2],
                   'sense_average': [1, 2],
                   'plc': [None],
                   'sense_nplc': [1, 2],
                   'sweep_mode': [None],
                   'pseudo_bias_mode': [None],
                   'BW': [None]}
        if not self._pseudo_bias_mode:  # 0 (current bias)
            parlist['dAdV'] = [None]
            parlist['amp'] = [None]
        elif self._pseudo_bias_mode:  # 1 (voltage bias)
            parlist['dVdA'] = [None]
            parlist['Vdiv'] = [None]
        return parlist

    def get(self, param, **kwargs):
        """
        Gets the current parameter <param> by evaluation 'get_'+<param> and corresponding channel if needed
        In combination with <self.get_parameters> above.
        
        Input:
            param (str): parameter to be got
            **kwargs: channels (list[int]): certain channel {1, 2} for channel specific parameter or None if no channel (global parameter)
        Output:
            parlist (dict): Parameter as key, corresponding channels as value
        """
        channels = kwargs.get('channels')
        if channels != [None]:
            return tuple([eval('self.get_{:s}(channel={!s})'.format(param, channel)) for channel in channels])
        else:
            return eval('self.get_{:s}()'.format(param))
