# Keithley 2636A class, to perform the communication between the Wrapper and the device
# Hannes Rotzinger, hannes.rotzinger@kit.edu 2010
#
# based on the work by
# Pieter de Groot <pieterdegroot@gmail.com>, 2008
# Martijn Schaafsma <qtlab@mcschaafsma.nl>, 2008
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

from qkit.core.instrument_base import Instrument
from qkit import visa
import types
import time
import logging
import numpy

class Keithley_2636A(Instrument):
    '''
    This is the driver for the Keithley 2636A Source Meter

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Keithley_2636A', address='<GBIP address>, reset=<bool>')
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the Keithley_2636A, and communicates with the wrapper.

        Input:
          name (string)    : name of the instrument
          address (string) : GPIB address
          reset (bool)     : resets to default values, default=False
        '''
        logging.info(__name__ + ' : Initializing instrument Keithley_2636A')
        Instrument.__init__(self, name, tags=['physical'])

        # Add some global constants
        self._address = address
        self._visainstrument = visa.instrument(self._address)
        
        self.add_parameter('voltageA',
            flags=Instrument.FLAG_GETSET, units='V', minval=-200, maxval=200, type=float)
        self.add_parameter('voltageB',
            flags=Instrument.FLAG_GETSET, units='V', minval=-200, maxval=200, type=float)
 
        self.add_parameter('currentA',
            flags=Instrument.FLAG_GETSET, units='A', minval=-10, maxval=10, type=float)
        self.add_parameter('currentB',
            flags=Instrument.FLAG_GETSET, units='A', minval=-10, maxval=10, type=float)
         
        self.add_parameter('statusA',
            flags=Instrument.FLAG_GETSET, type=bool)
        self.add_parameter('statusB',
            flags=Instrument.FLAG_GETSET, type=bool)

        self.add_function('reset')
        self.add_function('onA')
        self.add_function('offA')
        self.add_function('onB')
        self.add_function('offB')
 
        self.add_function('exec_tsl_script')
        self.add_function('exec_tsl_script_with_return')
        self.add_function('get_tsl_script_return')
        
        #self.add_function ('get_all')

        #self._visainstrument.write('beeper.beep(0.5,1000)')
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
        self._visainstrument.write("reset()")
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
        logging.info(__name__ + ' : get all')
        #self.do_get_voltageA()
        #self.get_voltageB()
        #self.get_currentA()
        #self.get_currentB()
    
    def exec_tsl_script(self,script):
        '''
        Writes the script to the device
        Input:
            TSL script (basically lua)
        Output:
            None
        '''
        logging.debug(__name__ + ' : execute TSL script on device')
        self._visainstrument.write(script)
        
    def exec_tsl_script_with_return(self,script):
        '''
        Writes the script to the device
        Input:
            TSL script (basically lua)
        Output:
            None
        '''
        logging.debug(__name__ + ' : execute TSL script on device and return data')
        return self._visainstrument.ask(script).strip()

 
    def get_tsl_script_return(self):
        '''
        Writes the script to the device
        Input:
            None
        Output:
            data, can be anything
        '''
        logging.debug(__name__ + ' : return data from executed TSL script')
        return self._visainstrument.read().strip()

 
    def do_get_voltageA(self):
        '''
        Reads the phase of the signal from the instrument

        Input:
            None

        Output:
            volt (float) : Voltage in Volts
        '''
        logging.debug(__name__ + ' : get voltage A')
        return float(self._visainstrument.ask('print(smua.measure.v())').strip())

    def do_set_voltageA(self, volt):
        '''
        Set the Amplitude of the signal

        Input:
            volt (float) : voltage in volt

        Output:
            None
        '''
        logging.debug(__name__ + ' : set voltage of channel A to %f' % volt)
        self._visainstrument.write('smua.source.levelv = %s' % volt)

    def do_get_voltageB(self):
        '''
        Reads the Amplitude of the signal from the instrument

        Input:
            None

        Output:
            volt (float) : Voltage in Volts
        '''
        logging.debug(__name__ + ' : get voltage A')
        return float(self._visainstrument.ask('print(smub.measure.v())').strip())

    def do_set_voltageB(self, volt):
        '''
        Set the Amplitude of the signal

        Input:
            volt (float) : voltage in volt

        Output:
            None
        '''
        logging.debug(__name__ + ' : set voltage of channel B to %f' % volt)
        self._visainstrument.write('smub.source.levelv = %s' % volt)

    def do_get_currentA(self):
        '''
        Reads the phase of the signal from the instrument

        Input:
            None

        Output:
            current (float) : current in amps
        '''
        logging.debug(__name__ + ' : get current A')
        return float(self._visainstrument.ask('print(smua.measure.i())').strip())

    def do_set_currentA(self, curr):
        '''
        Set the Amplitude of the signal

        Input:
            curr (float) : current in amps

        Output:
            None
        '''
        logging.debug(__name__ + ' : set current of channel A to %f' % curr)
        self._visainstrument.write('smua.source.leveli = %s' % curr)

    def do_get_currentB(self):
        '''
        Reads the phase of the signal from the instrument

        Input:
            None

        Output:
            current (float) : current in amps
        '''
        logging.debug(__name__ + ' : get current B')
        return float(self._visainstrument.ask('print(smub.measure.i())').strip())

    def do_set_currentB(self, curr):
        '''
        Set the Amplitude of the signal

        Input:
            curr (float) : current in amps

        Output:
            None
        '''
        logging.debug(__name__ + ' : set current of channel B to %f' % curr)
        self._visainstrument.write('smub.source.leveli = %s' % curr)

    def do_get_statusA(self):
        '''
        Reads the output status from the instrument

        Input:
            None

        Output:
            status (boolean)
        '''
        logging.debug(__name__ + ' : get status A')
        try:
            return int(float(self._visainstrument.ask('print(smua.source.output)').strip()))
        except:
            raise ValueError('Output status not specified : %s' % stat)
            return

    def do_set_statusA(self, status):
        '''
        Set the output status of the instrument

        Input:
            status (boolean)

        Output:
            None
        '''
        logging.debug(__name__ + ' : set status A to %s' %status)
        self._visainstrument.write('smua.source.output = %d' %status)

    def do_get_statusB(self):
        '''
        Reads the output status from the instrument

        Input:
            None

        Output:
            status (boolean) 
        '''
        try:
            return int(float(self._visainstrument.ask('print(smua.source.output)').strip()))
        except:
            raise ValueError('Output status not specified : %s' % stat)
            return

    def do_set_statusB(self, status):
        '''
        Set the output status of the instrument

        Input:
            status (boolean)

        Output:
            None
        '''
        logging.debug(__name__ + ' : set status A to %s' % status)
        self._visainstrument.write('smua.source.output = %d' %status)

    # shortcuts
    def offA(self):
        '''
        Set status to 'off'

        Input:
            None

        Output:
            None
        '''
        self.set_statusA(False)

    def onA(self):
        '''
        Set status to 'on'

        Input:
            None

        Output:
            None
        '''
        self.set_statusA(True)

    def offB(self):
        '''
        Set status to 'off'

        Input:
            None

        Output:
            None
        '''
        self.set_statusB(False)

    def onB(self):
        '''
        Set status to 'on'

        Input:
            None

        Output:
            None
        '''
        self.set_statusB(True)
