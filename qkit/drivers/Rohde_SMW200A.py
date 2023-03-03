# RuS_SWA200.py class, to perform the communication between the Wrapper and the device
#
# https://rohde-schwarz.github.io/RsSmw_PythonDocumentation/index.html
# https://github.com/Rohde-Schwarz/Examples/tree/main/SignalGenerators/Python/RsSmw_ScpiPackage
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
#from qkit import visa
from RsSmw import *

import logging
#import numpy

class Rohde_SMW200A(Instrument):
    '''
    This is the driver for the Rohde und Schwarz SMW200A Vector Source.
    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Rohde_SMW200A', address='<GBIP address>, reset=<bool>')
    '''

    def __init__(self, name, address, reset=True):
        '''
        Initializes the Rohde_SMW200A, and communicates with the wrapper.
        Input:
          name (string)    : name of the instrument
          address (string) : GPIB address
          reset (bool)     : resets to default values, default=False
        '''
        logging.info(__name__ + ' : Initializing instrument Rohde_SMW200A')
        Instrument.__init__(self, name, tags=['physical'])

        # Add some global constants
        self._address = address
        self._visainstrument = RsSmw('TCPIP::'+self._address+"::INSTR", 
                                     id_query=True, reset=False)

        self.add_parameter('power',
            flags=Instrument.FLAG_GETSET, units='dBm', minval=-145, maxval=30, type=float)
        #self.add_parameter('phase',
        #    flags=Instrument.FLAG_GETSET, units='rad', minval=-numpy.pi, maxval=numpy.pi, type=float)
        self.add_parameter('frequency',
            flags=Instrument.FLAG_GETSET, units='Hz', minval=1e5, maxval=20e9, type=float)
        self.add_parameter('status',
            flags=Instrument.FLAG_GETSET, type=str)
        self.add_parameter('mode',
            flags=Instrument.FLAG_GETSET, type=str)

        self.add_function('reset')
        self.add_function ('get_all')


        if (reset):
            self.reset()
        else:
            self.get_all()
        
        idn = self._visainstrument.utilities.query_str('*IDN?')
        print(f"\nHello, I am: {idn}")
        #print(f"\nI am using the VISA from: {self._visainstrument.utilities.visa_manufacturer}")
        
        # Print commands to the console with the logger
        #self._visainstrument.utilities.logger.mode = LoggingMode.On
        #self._visainstrument.utilities.logger.log_to_console = True
    
    def reset(self):
        '''
        Resets the instrument to default values
        Input:
            None
        Output:
            None
        '''
        logging.info(__name__ + ' : resetting instrument')
        self._visainstrument.utilities.reset()
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

    def do_get_mode(self):
        '''
        Reads the mode of the generator. Can be cw or sweep. 

        Returns
        -------
        Output:
            mode(string) : cw or sweep

        '''
        logging.debug(__name__ + ' : get mode')
        mode_enum = self._visainstrument.source.frequency.get_mode()
        if mode_enum.name == 'CW':
            mode = 'cw'
        elif mode_enum.name == 'SWEep':
            mode = 'sweep'
        else: 
            raise Exception('Mode strange.')
        return mode 
    
    def do_set_mode(self, mode):
        '''
        Sets the mode of the generator. Can be 'cw' or 'sweep'. 

        Returns
        -------
        Input:
            mode(string) : cw or sweep

        '''
        logging.debug(__name__ + ' : set mode')
        if mode=='cw':
            self._visainstrument.source.frequency.set_mode(enums.FreqMode.CW)
        elif mode=='sweep':
            self._visainstrument.source.frequency.set_mode(enums.FreqMode.SWEep)
        else:
            raise Exception('Mode not possible!')


    def do_get_power(self):
        '''
        Reads the power of the signal from the instrument in dBm. 
        Input:
            None
        Output:
            ampl (?) : power in ?
        '''
        logging.debug(__name__ + ' : get power')
        return self._visainstrument.source.power.level.immediate.get_amplitude()

    def do_set_power(self, amp):
        '''
        Set the power of the signal in dBm.
        Input:
            amp (float) : power in ??
        Output:
            None
        '''
        logging.debug(__name__ + ' : set power to %f' % amp)
        self._visainstrument.source.power.level.immediate.set_amplitude(amp)

    """
    def do_get_phase(self):
        '''
        Reads the phase of the signal from the instrument
        Input:
            None
        Output:
            phase (float) : Phase in radians
        '''
        logging.debug(__name__ + ' : get phase')
        return 0

    def do_set_phase(self, phase):
        '''
        Set the phase of the signal
        Input:
            phase (float) : Phase in radians
        Output:
            None
        '''
        logging.debug(__name__ + ' : set phase to %f' % phase)
        #self._visainstrument.write('PHASE %s' % phase)
    """

    def do_get_frequency(self):
        '''
        Reads the frequency of the signal from the instrument
        Input:
            None
        Output:
            freq (float) : Frequency in Hz
        '''
        logging.debug(__name__ + ' : get frequency')
        return self._visainstrument.source.frequency.fixed.get_value()

    def do_set_frequency(self, freq):
        '''
        Set the frequency of the instrument
        Input:
            freq (float) : Frequency in Hz
        Output:
            None
        '''
        logging.debug(__name__ + ' : set frequency to %f' % freq)
        self._visainstrument.source.frequency.fixed.set_value(freq)

    def do_get_status(self):
        '''
        Reads the output status from the instrument
        Input:
            None
        Output:
            status (string) : 'On' or 'Off'
        '''
        logging.debug(__name__ + ' : get status')
        if self._visainstrument.output.state.get_value() == True:
            status = 'on'
        else:
            status = 'off'
        return status


    def do_set_status(self, status):
        '''
        Set the output status (True/False) of the instrument.
        Input:
            status (bool) 
        Output:
            None
        '''
        if status == 'on':
            self._visainstrument.output.state.set_value(True)
        elif status == 'off':
            self._visainstrument.output.state.set_value(False)
        else:
            raise Exception('Use only "on" or "off"!') 
        logging.debug(__name__ + ' : set status to %s' % status)

    # shortcuts
    def off(self):
        '''
        Set status to 'off'
        Input:
            None
        Output:
            None
        '''
        self.set_status('off')

    def on(self):
        '''
        Set status to 'on'
        Input:
            None
        Output:
            None
        '''
        self.set_status('on')
        
        
        
    
if __name__ == "__main__":
    import qkit
    qkit.start()
    
    weva = qkit.instruments.create('weva', 'Rohde_SMW200A', address='192.168.1.30')
    weva.set_mode("cw")
    weva.set_frequency(2e9)
    weva.set_power(-40)
    weva.on()
    weva.off()
    weva.reset()