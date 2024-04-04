# Agilent_E8257D.py class, to perform the communication between the Wrapper and the device
# Pieter de Groot <pieterdegroot@gmail.com>, 2008
# Martijn Schaafsma <qtlab@mcschaafsma.nl>, 2008
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

import keysight_ktrfsiggen
import time
import numpy as np              #For keysight_ktrfsiggen arrays
from datetime import timedelta

class Keysight_N5183B(Instrument):
    '''
    This is the driver for the Keysight N5173B Signal Genarator

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Keysight_N5173B', address='<GBIP address>, reset=<bool>')
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the Keysight_N5173B, and communicates with the wrapper.

        Input:
            name (string)    : name of the instrumentgit c
            address (string) : GPIB address
            reset (bool)     : resets to default values, default=False
        '''
        logging.info(__name__ + ' : Initializing instrument Keysight_N5173B')
        Instrument.__init__(self, name, tags=['physical'])

        self._address = 'TCPIP0::'+address+'::hislip0::INSTR'         
        #idQuery = True                #Checks if instrument is supported by driver         
        #reset   = reset               #reset instrument when driver is initialized
        #options = "QueryInstrStatus=False, Simulate=True, Trace=False" 

        self._instrument = keysight_ktrfsiggen.KtRfSigGen(self._address, True, reset, "QueryInstrStatus=False, Simulate=False, Trace=False" )      

        # Implement parameters
        self.add_parameter('power',
            flags=Instrument.FLAG_GETSET, units='dBm', minval=-135, maxval=30, offset=True, type=float)
        #self.add_parameter('phase',
        #    flags=Instrument.FLAG_GETSET, units='rad', minval=-numpy.pi, maxval=numpy.pi, type=types.FloatType)
        self.add_parameter('frequency',
            flags=Instrument.FLAG_GETSET, units='Hz', minval=9e3, maxval=20e9, type=float)
        self.add_parameter('status',
            flags=Instrument.FLAG_GETSET, type=bool)
        self.add_parameter('mode',
            flags=Instrument.FLAG_GETSET, type=str)
        self.add_parameter('delay',
            flags=Instrument.FLAG_SET, type=float)
        self.add_parameter('width',
            flags=Instrument.FLAG_SET, type=float)
        
        

        self.add_function('reset')
        self.add_function('get_all')
    

        if (reset):
            self.reset()
        else:
            self.get_all()

        print('\n After reboot, pulse has to be set to TRIGGERED manually \n Pulse -> Pulse Source -> Triggered')

    
    def reset(self):
        '''
        Resets the instrument to default values

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : resetting instrument')
        self._instrument.utility.reset()
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
        self.get_power()
        #self.get_phase()
        self.get_frequency()
        self.get_status()

    def do_get_power(self):
        '''
        Reads the power of the signal from the instrument

        Input:
            None

        Output:
            ampl (float) : power in dBm
        '''
        logging.debug(__name__ + ' : get power')
        return float(self._instrument.rf.level)

    def do_set_power(self, amp):
        '''
        Set the power of the signal

        Input:
            amp (float) : power in dBm

        Output:
            None
        '''
        logging.debug(__name__ + ' : set power to %f' % amp)
        self._instrument.rf.configure(frequency = self._instrument.rf.frequency, power_level = amp)
    
    # #def do_get_phase(self):
    # #    '''
    # #    Reads the phase of the signal from the instrument
    # #
    # #    Input:
    # #        None
    # #
    # #    Output:
    # #        phase (float) : Phase in radians
    # #    '''
    # #    logging.debug(__name__ + ' : get phase')
    # #    return float(self._visainstrument.query('PHASE?'))

    # #def do_set_phase(self, phase):
    # #    '''
    # #    Set the phase of the signal
    # #
    # #    Input:
    # #        phase (float) : Phase in radians
    # #
    # #    Output:
    # #        None
    # #    '''
    # #    logging.debug(__name__ + ' : set phase to %f' % phase)
    # #    self._visainstrument.write('PHASE %s' % phase)

    def do_get_frequency(self):
        '''
        Reads the frequency of the signal from the instrument

        Input:
            None

        Output:
            freq (float) : Frequency in Hz
        '''
        logging.debug(__name__ + ' : get frequency')
        return float(self._instrument.rf.frequency)

    def do_set_frequency(self, freq):
        '''
        Set the frequency of the instrument

        Input:
            freq (float) : Frequency in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : set frequency to %f' % freq)
        self._instrument.rf.configure(frequency = freq, power_level = self._instrument.rf.level)

    def do_get_status(self):
        '''
        Reads the output status from the instrument

        Input:
            None

        Output:
            status (string) : 'On' or 'Off'
        '''
        logging.debug(__name__ + ' : get status')
        return self._instrument.rf.output_enabled


    def do_set_status(self, status):
        '''
        Set the output status of the instrument

        Input:
            status (string) : 'On' or 'Off'

        Output:
            None
        '''
        logging.debug(__name__ + ' : set status to %s' % status)
        
        if type(status)==bool:
            self._instrument.rf.output_enabled=status
        else:
            raise ValueError('set_status(): can only set True or False')
        
    def do_get_mode(self):
        '''
        Reads the mode of the pulse modulation

        Input:
            None

        Output:
            mode (string) : 'CONTINOUS','TRIGGERED' or 'GATED'
        '''
        logging.debug(__name__ + ' : get mode')

        if self._instrument.pulse_modulation.enabled==True:
            if str(self._instrument.pulse_modulation.source)=='PulseModulationSource.INTERNAL':
                return 'TRIGGERED'
            else:
                return 'GATED'
        else:
            return 'CONTINOUS' 

    def do_set_mode(self, mode):
        '''
        Mode for pulse modulation

        Input:
            mode (string) : 'CONTINOUS','TRIGGERED' or 'GATED'

        Output:
            None
        '''
        logging.debug(__name__ + ' : set mode to %s' % mode)

        if mode=='CONTINOUS':
            self._instrument.pulse_modulation.enabled = False
        elif mode=='TRIGGERED':
            self._instrument.pulse_modulation.source=keysight_ktrfsiggen.PulseModulationSource(0)
            time.sleep(1)   #device to slow
            self._instrument.pulse_modulation.enabled = True
        elif mode=='GATED':
            self._instrument.pulse_modulation.source=keysight_ktrfsiggen.PulseModulationSource(1)
            time.sleep(1)   #device to slow
            self._instrument.pulse_modulation.enabled = True
        else:
            raise ValueError('set_mode(): can only set CONTINOUS, TRIGGERED or GATED')
    
    def do_set_delay(self, delay):
        '''
        Set delay of the TRIGGERED mode

        Input:
            delay (float) : Time in seconds

        Output:
            None
        '''
        logging.debug(__name__ + ' : set delay to %f' % delay)
        self._instrument.pulse_generator.configure_external_trigger(keysight_ktrfsiggen.PulseExternalTriggerSlope(0), delay)
    
    def do_set_width(self, width):
        '''
        Set pulse width of the TRIGGERED mode

        Input:
            width (float) : Time in seconds

        Output:
            None
        '''
        logging.debug(__name__ + ' : set delay to %f' % delay)
        self._instrument.pulse_generator.width = timedelta(seconds=width)

    ## shortcuts
    def off(self):
        '''
        Set status to 'off'

        Input:
            None

        Output:
            None
        '''
        self.set_status(False)

    def on(self):
        '''
        Set status to 'on'

        Input:
            None

        Output:
            None
        '''
        self.set_status(True)

if __name__ == "__main__":
    # Dont forget to install keysight_ktrfsiggen library
    # get it here: https://www.keysight.com/de/de/lib/software-detail/driver/rf-signal-generators-python-instrument-drivers/version-1-0-0-linux.html


    #example for a sequence
    qkit.start()

    #initialize the instrument
    kira = qkit.instruments.create('kira', 'Keysight_N5183B', address='192.168.0.42')

    #set frequency and power of the RF Generator
    kira.set_frequency(10e6)
    kira.set_power(0)

    #get frequency and power of the RF Generator
    kira.get_power()
    kira.get_frequency()

    #Turn the RF Generator on and off
    kira.on()
    kira.off()

    #Set different modes for the RF Generator
    # Input for the Trigger is the Pulse Input with a delay of approximately 100ns
    # 'CONTINOUS'   permanent pulsing
    # 'TRIGGERED'   A pulse with given width and delay after initial trigger
    # 'GATED'       pulsing whenever the input is triggered
    kira.set_mode('MODE')

    # For the TRIGGERED mode additional input of delay and width is needed
    kira.set_delay(1)   #input is time in seconds
    kira.set_width(1)   #input is time in seconds      
