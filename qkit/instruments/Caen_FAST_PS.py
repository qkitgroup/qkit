# Caen Fast-PS class, to perform the communication between the Wrapper and the device
# Marco Pfirrmann, marco.pfirrmann@kit.edu 2017
#
# based on the work on the Keithley_2636A driver by
# Pieter de Groot <pieterdegroot@gmail.com>, 2008
# Martijn Schaafsma <qtlab@mcschaafsma.nl>, 2008
# Hannes Rotzinger, hannes.rotzinger@kit.edu 2010
#
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

from instrument import Instrument
import visa
import types
import time
import logging
import numpy as np

class Caen_fast_ps(Instrument):
    '''
    This is the driver for the Caen Fast-PS Power Supply

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Caen_fast_ps', address='<GPIB address>', reset=<bool>')
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the Caen_fast_ps, and communicates with the wrapper.

        Input:
          name (string)    : name of the instrument
          address (string) : GPIB address
          reset (bool)     : resets to default values, default=False
        '''
        logging.info(__name__ + ' : Initializing instrument Caen_fast_ps')
        Instrument.__init__(self, name, tags=['physical'])

        # Add some global constants
        self._address = address
        self._visainstrument = visa.instrument(self._address)
        self._name = name
        
        self.add_parameter('voltage',
            flags=Instrument.FLAG_GET, units='V', minval=-20, maxval=20, type=types.FloatType)
            
        self.add_parameter('setvoltage',
            flags=Instrument.FLAG_GETSET, units='V', minval=-20, maxval=20, type=types.FloatType)
 
        self.add_parameter('current',
            flags=Instrument.FLAG_GET, units='A', minval=-10, maxval=10, type=types.FloatType)
            
        self.add_parameter('setcurrent',
            flags=Instrument.FLAG_GETSET, units='A', minval=-10, maxval=10, type=types.FloatType)

        self.add_parameter('status',
            flags=Instrument.FLAG_GETSET, type=types.BooleanType)
        
        self.add_parameter('current_ramp_rate',
            flags=Instrument.FLAG_GETSET, units='A/s', minval=-10, maxval=10, type=types.FloatType)

        self.add_parameter('voltage_ramp_rate',
            flags=Instrument.FLAG_GETSET, units='A/s', minval=-10, maxval=10, type=types.FloatType)
        
        self.add_function('reset')
        self.add_function('ramp_current')
        self.add_function('ramp_voltage')
        self.add_function('on')
        self.add_function('off')
 

        if (reset):
            self.reset()
        else:
            self.get_all()

    def reset(self):
        '''
        Resets the instrument to default values

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : resetting instrument')
        self._visainstrument.write("*RST")
        self.get_all()

    def get_all(self):
        '''
        Reads all implemented parameters from the instrument,
        and updates the wrapper.

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : get all')
        self.get('voltage')
        self.get('current')
        self.get('status')
        self.get('setcurrent')
        self.get('setvoltage')
    
 
    def do_get_voltage(self):
        '''
        Reads the voltage signal from the instrument

        Input:
            None

        Output:
            volt (float) : Voltage in Volts
        '''
        logging.debug(__name__ + ' : get voltage')
        return float(self._visainstrument.ask('MEAS:VOLT?'))

    def do_get_setvoltage(self):
        '''
        Reads the setvoltage signal from the instrument

        Input:
            None

        Output:
            setvolt (float) : Voltage in Volts
        '''
        logging.debug(__name__ + ' : get setvoltage')
        return float(self._visainstrument.ask('MWV:?\r\n'))

    def do_set_setvoltage(self, setvoltage):
        '''
        Reads the setvoltage signal from the instrument

        Input:
            setvoltage (float) : setvoltage in volts

        Output:
            None
        '''
        logging.debug(__name__ + ' : set setvoltage to %s' % setvoltage)
        return float(self._visainstrument.ask('MWV:%s\r\n' %setvoltage))        
        
    def do_get_current(self):
        '''
        Reads the current signal from the instrument

        Input:
            None

        Output:
            current (float) : current in amps
        '''
        logging.debug(__name__ + ' : get current')
        return float(self._visainstrument.ask('MEAS:CURR?'))

    def do_get_setcurrent(self):
        '''
        Reads the setcurrent signal from the instrument

        Input:
            None

        Output:
            setcurrent (float) : setcurrent in amps
        '''
        logging.debug(__name__ + ' : get setcurrent')
        return float(self._visainstrument.ask('MWI:?\r\n'))
    
    def do_set_setcurrent(self, setcurrent):
        '''
        Reads the setcurrent signal from the instrument

        Input:
            setcurrent (float) : setcurrent in amps

        Output:
            None
        '''
        logging.debug(__name__ + ' : set setcurrent to %s' % setcurrent)
        return float(self._visainstrument.ask('MWI:%s\r\n' %setcurrent))

    def do_get_status(self):
        '''
        Reads the output status from the instrument

        Input:
            None

        Output:
            status (boolean) 
        '''
        logging.debug(__name__ + ' : get status')
        return bool(int(self._visainstrument.ask('OUTPUT?')))


    def do_set_status(self, status):
        '''
        Sets the output status of the instrument

        Input:
            status (boolean)

        Output:
            None
        '''
        logging.debug(__name__ + ' : set status to %d' % status)
        self._visainstrument.write('OUTPUT %d' %status)

    def do_get_current_ramp_rate(self):
        '''
        Reads the setcurrent signal from the instrument

        Input:
            None

        Output:
            rate (float) : current_ramp_rate in A/s
        '''
        logging.debug(__name__ + ' : get setcurrent')
        return float(self._visainstrument.ask('MSRI:?\r\n'))
    
    def do_set_current_ramp_rate(self, rate):
        '''
        Reads the setcurrent signal from the instrument

        Input:
            rate (float) : current_ramp_rate in A/s

        Output:
            None
        '''
        logging.debug(__name__ + ' : set setcurrent to %s' %rate)
        return float(self._visainstrument.ask('MSRI:%s\r\n' %rate))

    def do_get_voltage_ramp_rate(self):
        '''
        Reads the setcurrent signal from the instrument

        Input:
            None

        Output:
            rate (float) : voltage_ramp_rate in V/s
        '''
        logging.debug(__name__ + ' : get setcurrent')
        return float(self._visainstrument.ask('MSRV:?\r\n'))
    
    def do_set_voltage_ramp_rate(self, rate):
        '''
        Reads the setcurrent signal from the instrument

        Input:
            rate (float) : voltage_ramp_rate in V/s

        Output:
            None
        '''
        logging.debug(__name__ + ' : set setcurrent to %s' %rate)
        return float(self._visainstrument.ask('MSRV:%s\r\n' %rate))
        
    # shortcuts
    def off(self):
        '''
        Sets status to False

        Input:
            None

        Output:
            None
        '''
        self.set_status(False)

    def on(self):
        '''
        Sets status to True

        Input:
            None

        Output:
            None
        '''
        self.set_status(True)
    
    def ramp_current(self, current, ramp_rate = False):
        '''
        Ramps current with given rate
        
        Input:
            current (float) : destination value in A
            ramp_rate (float) : ramp rate in A/s (optional)
        
        Output:
            None
        '''
        if ramp_rate: self.do_set_current_ramp_rate(ramp_rate)
        logging.debug(__name__ + ' : ramp current to %s' %current)
        return float(self._visainstrument.ask('MWIR:%s\r\n' %current))
    
    def ramp_voltage(self, voltage, ramp_rate = False):
        '''
        Ramps voltage with given rate
        
        Input:
            voltage (float) : destination value in V
            ramp_rate (float) : ramp rate in V/s (optional)
        
        Output:
            None
        '''
        if ramp_rate: self.do_set_voltage_ramp_rate(ramp_rate)
        logging.debug(__name__ + ' : ramp current to %s' %voltage)
        return float(self._visainstrument.ask('MWVR:%s\r\n' %voltage))
        
error_msg = {1:"Unknown command",
             2:"Unknown Parameter",
             3:"Index out of range",
             4:"Not Enough Arguments",
             5:"Privilege Level Requirement not met",
             6:"Saving Error on device",
             7:"Invalid password",
             8:"Power supply in fault",
             9:"Power supply already ON",
             10:"Setpoint is out of model limits",
             11:"Setpoint is out of software limits",
             12:"Setpoint is not a number",
             13:"Module is OFF",
             14:"Slew Rate out of limits",
             15:"Device is set in local mode",
             16:"Module is not in waveform mode",
             17:"Module is in waveform mode",
             18:"Device is set in remote mode",
             19:"Module is already in the selected loop mode",
             20:"Module is not in the selected loop mode",
             99:"Unknown error"}