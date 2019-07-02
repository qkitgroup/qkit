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
    
    def get_value(self, ind):
        """
        Read the variable defined by the index.

        The possible inputs are:
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
        
        Parameters
        ----------
        ind: (int)
            Index of variable to read.
        
        Returns
        -------
        val: (float)
            answer of queried variable.
        """
        # Corresponding Command: Rn
        assert type(ind) == int, 'Argument must be an integer.'
        assert ind in range(0,11), 'Argument is not a valid number.'
        try:
            logging.debug('{:s}: Get value of variable {:d}'.format(__name__, ind))
            return float(self.query('R{:d}'.format(ind)).strip('R+'))
        except Exception as e:
            logging.error('{!s}: Cannot value of variable  {!s}'.format(__name__, ind))
            raise type(e)('{!s}: Cannot value of variable  {!s}\n{!s}'.format(__name__, ind, e))
    
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
            logging.error('{!s}: Cannot temperature of sensor {!s}'.format(__name__, sensor))
            raise type(e)('{!s}: Cannot temperature of sensor {!s}\n{!s}'.format(__name__, sensor, e))
        
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
            logging.error('{!s}: Cannot proportional band to {!s}'.format(__name__, proportional))
            raise type(e)('{!s}: Cannot proportional band to {!s}\n{!s}'.format(__name__, proportional, e))
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
            logging.error('{!s}: Cannot integral action time to {!s}'.format(__name__, integral))
            raise type(e)('{!s}: Cannot integral action time to {!s}\n{!s}'.format(__name__, integral, e))
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
            logging.error('{!s}: Cannot derivative action time to {!s}'.format(__name__, derivative))
            raise type(e)('{!s}: Cannot derivative action time to {!s}\n{!s}'.format(__name__, derivative, e))
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
            logging.error('{!s}: Cannot temperature set point to {!s}'.format(__name__, temperature))
            raise type(e)('{!s}: Cannot temperature set point to {!s}\n{!s}'.format(__name__, temperature, e))
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
            logging.error('{!s}: Cannot heater sensor. to {!s}'.format(__name__, sensor))
            raise type(e)('{!s}: Cannot heater sensor. to {!s}\n{!s}'.format(__name__, sensor, e))
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
            logging.error('{!s}: Cannot maximum heater voltage to {!s}'.format(__name__, val))
            raise type(e)('{!s}: Cannot maximum heater voltage to {!s}\n{!s}'.format(__name__, val, e))
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
            logging.error('{!s}: Cannot heater output to {!s}'.format(__name__, val))
            raise type(e)('{!s}: Cannot heater output to {!s}\n{!s}'.format(__name__, val, e))
        return
        

##########################################################################################
### https://labdrivers.readthedocs.io/en/latest/_modules/labdrivers/oxford/itc503.html ### 
########################################################################################## 


    def setGasOutput(self, gas_output=0):
        """
        Sets the gas (needle valve) output level.
        
        Args:
            gas_output: Sets the percent of the maximum gas
                    output in units of 0.1%.
                    Min: 0. Max: 999.
        """
        self.write('G{}'.format(gas_output))
        return None      

        
    def setAutoControl(self, auto_manual=0):
        """
        Sets automatic control for heater/gas(needle valve).
        
        Value: Status map
            0: heater manual, gas manual
            1: heater auto  , gas manual
            2: heater manual, gas auto
            3: heater auto  , gas auto
        
        Args:
            auto_manual: Index for gas/manual.
        """
        self.write('A{}'.format(auto_manual))


    def setSweeps(self, sweep_parameters):
        """
        Sets the parameters for all sweeps.

        This fills up a dictionary with all the possible steps in
        a sweep. If a step number is not found in the sweep_parameters
        dictionary, then it will create the sweep step with all
        parameters set to 0.

        Args:
            sweep_parameters: A dictionary whose keys are the step
                numbers (keys: 1-16). The value of each key is a
                dictionary whose keys are the parameters in the
                sweep table (see _setSweepStep).
        """
        steps = range(1,17)
        parameters_keys = sweep_parameters.keys()
        null_parameter = {  'set_point' : 0,
                            'sweep_time': 0,
                            'hold_time' : 0  }

        for step in steps:
            if step in parameters_keys:
                self._setSweepStep(step, sweep_parameters[step])
            else:
                self._setSweepStep(step, null_parameter)


    def _setSweepStep(self, sweep_step, sweep_table):
        """
        Sets the parameters for a sweep step.

        This sets the step pointer (x) to the proper step.
        Then this sets the step parameters (y1, y2, y3) to
        the values dictated by the sweep_table. Finally, this
        resets the x and y pointers to 0.

        Args:
            sweep_step: The sweep step to be modified (values: 1-16)
            sweep_table: A dictionary of parameters describing the
                sweep. Keys: set_point, sweep_time, hold_time.
        """
        step_setting = 'x{}'.format(sweep_step)
        self.write(step_setting)

        setpoint_setting = 's{}'.format(
                            sweep_table['set_point'])
        sweeptime_setting = 's{}'.format(
                            sweep_table['sweep_time'])
        holdtime_setting = 's{}'.format(
                            sweep_table['hold_time'])

        self.write('y1')
        self.write(setpoint_setting)

        self.write('y2')
        self.write(sweeptime_setting)

        self.write('y3')
        self.write(holdtime_setting)

        self._resetSweepTablePointers()

    def _resetSweepTablePointers(self):
        """
        Resets the table pointers to x=0 and y=0 to prevent accidental sweep table changes.
        """
        self.write('x0')
        self.write('y0')