# -*- coding: utf-8 -*-

# Oxford_ITC503.py driver for Oxford ITC503 temperature controller connected 
# via a Prologix GPIB ethernet controller
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
import re
import logging
        

class Oxford_ITC503(Instrument):
    """
    This is the driver for the Oxford ITC503 temperature controller
    """
    
    def __init__(self, name, address):
        """
        Initializes VISA communication with the instrument Keithley 2636A.
        
        Parameters
        ----------
        name: string
            Name of the instrument (driver).
        address: string
            IP address for the communication with the instrument.
        
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
        
        >>> ITC503 = qkit.instruments.create('ITC503', 'Oxford_ITC503', address='ASRL1::INSTR')
        """
        self.__name__ = __name__
        # Start VISA communication
        logging.info(__name__ + ': Initializing instrument Oxford ITC 503 temperature control')
        Instrument.__init__(self, name, tags=['physical'])
        self._address = address
        self._visainstrument = visa.instrument(self._address)
        self._visainstrument.read_termination = '\r'
    
    def write(self, cmd):
        """
        Sends a visa command <cmd> to the Device.
        
        Parameters
        ----------
        cmd: str
            Command that is send to the instrument via pyvisa and NI-VISA backend.
        
        Returns
        -------
        None
        """
        #if cmd == '*CLS': cmd = 'Q0'
        ans = self._visainstrument.query(cmd)  # Use query, since it returns first letter of <cmd>, e.g. u'O'
        return ans
    
    def query(self, cmd):
        """
        Clears the communication buffer, sends a visa command <cmd> and returns the read answer <ans>.
        
        Parameters
        ----------
        cmd: str
            Command that is send to the instrument via pyvisa and NI-VISA backend.
        
        Returns
        -------
        ans: str
            Answer that is returned at query after the sent <cmd>.
        """
        self._visainstrument.write('Q0')  # usually defines the communication protocol, but can be used to clear the the communications buffer
        return self._visainstrument.query(cmd)
    
    def get_IDN(self):
        """
        Gets the identification query of the device.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        IDN: (str)
            Identification query.
        """
        try:
            logging.debug('{:s}: Get IDN'.format(__name__))
            return str(self.query('V'))
        except Exception as e:
            logging.error('{!s}: Cannot get IDN'.format(__name__))
            raise type(e)('{!s}: Cannot get IDN\n{!s}'.format(__name__, e))
    
    def get_status(self, *args):
        """
        Gets status entries.
        
        Meanings are:
            X: SYSTEM STATUS (Always zero currently)
            A: AUTO/MAN STATUS (n as for A COMMAND but see below)
            C: LOC/REM/LOCK STATUS (n as for C COMMAND)
            S: SWEEP STATUS (nn=0-32 as follows)
                nn=0 SWEEP NOT RUNNING
                nn=2P-1 SWEEPING to step P
                nn=2P HOLDING at step P
            H: CONTROL SENSOR (n as for H COMMAND)
            L: AUTO-PID STATUS (n as for L COMMAND)
        
        Parameters
        ----------
        *args: (str)
            variables of interest
        
        Returns
        -------
        status: (dict)
            All or selected entries of status query.
        """
        # Corresponding Command: XnAnCnSnnHnLn = X
        try:
            logging.debug('{:s}: Get status'.format(__name__))
            ans = self.query('X')
            status = {str(key): str(val) for key, val in zip(re.findall(r'[A-Za-z]+', ans), re.findall(r'\d+', ans))}
            if args:
                return {var: status[var] for var in args}
            else:
                return status
        except Exception as e:
            logging.error('{!s}: Cannot get status'.format(__name__))
            raise type(e)('{!s}: Cannot get status{!s}'.format(__name__, e))
        
    def set_control(self, remote=1, unlocked=1):
        """
        Sets the device into LOCAL or REMOTE and determines whether the LOC/REM button is LOCKED or active.
        
        Parameters
        ----------
        remote: (int)
            0 for local, 1 for remote
        unlocked: (int)
            0 to lock, 1 to unlock
        
        Returns
        -------
        None
        """
        # Corresponding Command: Cn
        try:
            logging.debug('{:s}: Set control to {:r}, {:r}'.format(__name__, remote, unlocked))
            self.write("C{:d}".format(int(str(remote) + str(unlocked), 2)))
        except Exception as e:
            logging.error('{!s}: Cannot set control to {!r}, {!r}'.format(__name__, remote, unlocked))
            raise type(e)('{!s}: Cannot set control o {!r}, {!r}\n{!s}'.format(__name__, remote, unlocked, e))
        return
    
    def set_display(self, channel):
        """
        Sets the front panel display to channel <channel>.
        
        Parameters
        ----------
        channel: (int)
            Channel to read. Possible channels are:
                0: SET TEMPERATURE
                1: SENSOR 1 TEMPERATURE
                2: SENSOR 2 TEMPERATURE
                3: SENSOR 3 TEMPERATURE
                4: TEMPERATURE ERROR
                5: HEATER O/P (as %)
                6: HEATER O/P (as V)
                7: GAS FLOW O/P (a.u.)
                8: PROPORTIONAL BAND
                9: INTEGRAL ACTION TIME
                10: DERIVATIVE ACTION TIME
        
        Returns
        -------
        None
        """
        # Corresponding Command: Fnn
        assert type(channel) == int, 'Argument must be an integer.'
        assert channel in range(0,11), 'Argument is not a valid number.'
        try:
            logging.debug('{:s}: Get value of channel {:d}'.format(__name__, channel))
            self.write('F{:d}'.format(channel))
        except Exception as e:
            logging.error('{!s}: Cannot set front pannel to channel {!s}'.format(__name__, channel))
            raise type(e)('{!s}: Cannot set front pannel to channel {!s}\n{!s}'.format(__name__, channel, e))
    
    def get_value(self, channel, display=False):
        """
        Gets the current value of channel <channel>.
        
        Parameters
        ----------
        channel: (int)
            Channel to read. Possible channels are:
                0: SET TEMPERATURE
                1: SENSOR 1 TEMPERATURE
                2: SENSOR 2 TEMPERATURE
                3: SENSOR 3 TEMPERATURE
                4: TEMPERATURE ERROR
                5: HEATER O/P (as %)
                6: HEATER O/P (as V)
                7: GAS FLOW O/P (a.u.)
                8: PROPORTIONAL BAND
                9: INTEGRAL ACTION TIME
                10: DERIVATIVE ACTION TIME
        
        Returns
        -------
        val: (float)
            answer of queried variable.
        """
        # Corresponding Command: Rn
        assert type(channel) == int, 'Argument must be an integer.'
        assert channel in range(0,11), 'Argument is not a valid number.'
        try:
            logging.debug('{:s}: Get value of channel {:d}'.format(__name__, channel))
            if display: self.set_display(channel=channel)
            return float(self.query('R{:d}'.format(channel)).strip('R+'))
        except Exception as e:
            logging.error('{!s}: Cannot get value of channel  {!s}'.format(__name__, channel))
            raise type(e)('{!s}: Cannot get value of channel  {!s}\n{!s}'.format(__name__, channel, e))
    
    def get_Temp(self, sensor=2):
        """
        Gets temperature of thermometer channel <channel>.
        
        Parameters
        ----------
        sensor: int
            Number of sensor of interest. Must be 1 (Sorb), 2 (RuOx) or 3 (Cernox). Default is 2.
        
        Returns
        -------
        temp: float
            Temperature in K.
        """
        # Corresponding Command: Rn
        assert type(sensor) == int, 'Argument must be an integer.'
        assert sensor in range(1, 4), 'Argument is not a valid number.'
        try:
            logging.debug('{:s}: Get temperature of sensor {:d}'.format(__name__, sensor))
            return float(self.query('R{:d}'.format(sensor)).strip('R+'))
        except Exception as e:
            logging.error('{!s}: Cannot get temperature of sensor {!s}'.format(__name__, sensor))
            raise type(e)('{!s}: Cannot get temperature of sensor {!s}\n{!s}'.format(__name__, sensor, e))
        
    def set_proportional(self, proportional=0):
        """
        Sets the proportional band.
        
        Parameters
        ----------
        proportional: (float)
            Proportional band, in steps of 0.0001K.
        
        Returns
        -------
        None
        """
        # Corresponding Command: Pnnnn
        try:
            logging.debug('{:s}: Set proportional band to {:f}'.format(__name__, proportional))
            self.write('P{}'.format(proportional))
        except Exception as e:
            logging.error('{!s}: Cannot set proportional band to {!s}'.format(__name__, proportional))
            raise type(e)('{!s}: Cannot set proportional band to {!s}\n{!s}'.format(__name__, proportional, e))
        return
        
    def set_integral(self, integral=0):
        """
        Sets the integral action time.
        
        Parameters
        ----------
        integral: (float)
            Integral action time, in steps of 0.1 minute. Ranges from 0 to 140 minutes.
        
        Returns
        -------
        None
        """
        # Corresponding Command: Innnn
        try:
            logging.debug('{:s}: Set integral action time to {:f}'.format(__name__, integral))
            self.write('I{}'.format(integral))
        except Exception as e:
            logging.error('{!s}: Cannot set integral action time to {!s}'.format(__name__, integral))
            raise type(e)('{!s}: Cannot set integral action time to {!s}\n{!s}'.format(__name__, integral, e))
        return
        
    def set_derivative(self, derivative=0):
        """
        Sets the derivative action time.
        
        Parameters
        ----------
        derivative: (float)
            Derivative action time. Ranges from 0 to 273 minutes.
        
        Returns
        -------
        None
        """
        # Corresponding Command: Dnnnn
        try:
            logging.debug('{:s}: Set derivative action time to {:f}'.format(__name__, derivative))
            self.write('D{}'.format(derivative))
        except Exception as e:
            logging.error('{!s}: Cannot set derivative action time to {!s}'.format(__name__, derivative))
            raise type(e)('{!s}: Cannot set derivative action time to {!s}\n{!s}'.format(__name__, derivative, e))
        return

    def set_temperature(self, temperature=0.010):
        """
        Change the temperature set point.
        
        Parameters
        ----------
        temperature: (float)
            Temperature set point in Kelvin. Default is 0.010
        
        Returns
        -------
        None
        """
        # Corresponding Command: Tnnnnn
        assert type(temperature) in [int, float], 'argument must be a number'
        try:
            logging.debug('{:s}: Set temperature set point to {:f}'.format(__name__, temperature))
            self.write('T{:d}'.format(int(1000*temperature)))
        except Exception as e:
            logging.error('{!s}: Cannot set temperature set point to {!s}'.format(__name__, temperature))
            raise type(e)('{!s}: Cannot set temperature set point to {!s}\n{!s}'.format(__name__, temperature, e))
        return
        
    def set_heater_sensor(self, sensor=1):
        """
        Selects the heater sensor.
        
        Parameters
        ----------
        sensor: (int)
            Heater sensor corresponding to the three input channels. Should be 1, 2, or 3, corresponding to the heater on the front panel.
        
        Returns
        -------
        None
        """
        # Corresponding Command: Hn
        assert sensor in [1,2,3], 'Heater not on list.'
        try:
            logging.debug('{:s}: Set heater sensor. to {:f}'.format(__name__, sensor))
            self.write('H{}'.format(sensor))
        except Exception as e:
            logging.error('{!s}: Cannot set heater sensor. to {!s}'.format(__name__, sensor))
            raise type(e)('{!s}: Cannot set heater sensor. to {!s}\n{!s}'.format(__name__, sensor, e))
        return
            
    def set_heater_maximum(self, val):
        """
        Sets the maximum heater voltage that ITC503 may deliver
        
        Parameters
        ----------
        val: float
            The maximum heater voltage is specified as a decimal number with a resolution of 0.1 volt, and is approximate. 0 may be used to specify a dynamically varying limit.
        
        Returns
        -------
        None
        """
        # Corresponding Command: Mnnn
        try:
            logging.debug('{:s}: Set maximum heater voltage to {:f}'.format(__name__, val))
            self.write('M{:04.1F}'.format(val))
        except Exception as e:
            logging.error('{!s}: Cannot set maximum heater voltage to {!s}'.format(__name__, val))
            raise type(e)('{!s}: Cannot set maximum heater voltage to {!s}\n{!s}'.format(__name__, val, e))
        return
    
    def set_heater_output(self, val):
        """
        Sets the heater output level <val>.
        
        Parameters
        ----------
        val: float
            Sets the percent of the maximum heater output in units of 0.1%. Ranges from 0 to 99.9.
        
        Returns
        -------
        None
        """
        # Corresponding Command: Onnn
        try:
            logging.debug('{:s}: Set heater output to {:f}'.format(__name__, val))
            self.query('O{:04.1F}'.format(val))
        except Exception as e:
            logging.error('{!s}: Cannot set heater output to {!s}'.format(__name__, val))
            raise type(e)('{!s}: Cannot set heater output to {!s}\n{!s}'.format(__name__, val, e))
        return
    
    def set_gas_output(self, val=0):
        """
        Sets the gas (needle valve) output level <gas_output>.
        
        Parameters
        ----------
        val: (float)
            Sets the percent of the maximum gas output in units of 0.1%. Ranges from 0 to 99.9.
        
        Returns
        -------
        None
        """
        # Corresponding Command: Gnnn
        try:
            logging.debug('{:s}: Set gas output to {:f}'.format(__name__, val))
            self.query('G{:04.1F}'.format(val))
        except Exception as e:
            logging.error('{!s}: Cannot set gas output to {!s}'.format(__name__, val))
            raise type(e)('{!s}: Cannot set gas output to {!s}\n{!s}'.format(__name__, val, e))
        return
    
    def set_auto_control(self, heater_auto=0, gas_auto=0):
        """
        Sets automatic control for heater and gas flow (needle valve).
        
        Parameters
        ----------
        heater_auto: (bool)
            Status of heater function.
        gas_auto: (bool)
            Status of gas flow control function.
        
        Returns
        -------
        None
        """
        # Corresponding Command: An
        try:
            logging.debug('{:s}: Set automatic control for heater to {:d} and gas flow to {:d}'.format(__name__, heater_auto, gas_auto))
            self.write('A{}'.format(int(str(int(gas_auto))+str(int(heater_auto)), 2)))
        except Exception as e:
            logging.error('{!s}: Cannot set automatic control for heater to {!s} and gas flow to {!s}'.format(__name__, heater_auto, gas_auto))
            raise type(e)('{!s}: Cannot set automatic control for heater to {!s} and gas flow to {!s}\n{!s}'.format(__name__, heater_auto, gas_auto, e))
        return
    
    def set_sweeps(self, sweep_parameters):
        """
        Sets the parameters for all sweeps.

        This fills up a dictionary with all the possible steps in a sweep. If a step number is not found in the sweep_parametersdictionary, then it will create the sweep step with all parameters set to 0.
        
        Parameters
        ----------
        sweep_parameters: (dict)
            Keys are the step numbers and range fron 1 to 16. The value of each key is a dictionary whose keys are the parameters in the sweep table (see _setSweepStep).
        
        Returns
        -------
        None
        """
        for step in range(1,17):
            if step in sweep_parameters.keys():
                self._set_sweep_step(step, sweep_parameters[step])
            else:
                self._set_sweep_step(step, {'set_point': 0, 'sweep_time': 0, 'hold_time': 0 })  # default is 0
    
    def _set_sweep_step(self, sweep_step, sweep_table):
        """
        Sets the parameters for a sweep step by setting the step pointer (x) to the proper step, the step parameters (y1, y2, y3) to the values dictated by the sweep_table and resetting the x and y pointers to 0.
        
        Parameters
        ----------
        sweep_step: (int)
            The sweep step to be modified. Ranges from 1 to 16
        sweep_table: (int)
            A dictionary of parameters describing the sweep. Keys are set_point, sweep_time and hold_time.
        
        Returns
        -------
        None
        """
        self.write('x{}'.format(sweep_step))

        self.write('y1')
        self.write('s{}'.format(sweep_table['set_point']))

        self.write('y2')
        self.write('s{}'.format(sweep_table['sweep_time']))

        self.write('y3')
        self.write('s{}'.format(sweep_table['hold_time']))

        self._reset_sweep_table_pointers()

    def _reset_sweep_table_pointers(self):
        """
        Resets the table pointers to x=0 and y=0 to prevent accidental sweep table changes.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        """
        self.write('x0')
        self.write('y0')
    