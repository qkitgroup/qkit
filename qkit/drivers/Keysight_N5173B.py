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

#import types
import logging

from qkit import visa

from qkit.core.instrument_base import Instrument
from qkit.drivers.AbstractMicrowaveSource import AbstractMicrowaveSource


class Keysight_N5173B(AbstractMicrowaveSource):
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
            name (string)    : name of the instrument
            address (string) : GPIB address
            reset (bool)     : resets to default values, default=False
        '''
        logging.info(__name__ + ' : Initializing instrument Keysight_N5173B')
        super().__init__(name, tags=['physical'])

        self._address = address
        self._visainstrument = visa.instrument(self._address)
        if (reset):
            self.reset()
        else:
            self.get_all()


    def do_get_power(self):
        '''
        Reads the power of the signal from the instrument

        Input:
            None

        Output:
            ampl (float) : power in dBm
        '''
        logging.debug(__name__ + ' : get power')
        return float(self._visainstrument.query('POW:AMPL?'))

    def do_set_power(self, amp):
        '''
        Set the power of the signal

        Input:
            amp (float) : power in dBm

        Output:
            None
        '''
        logging.debug(__name__ + ' : set power to %f' % amp)
        self._visainstrument.write('POW:AMPL %s' % amp)
    
    #def do_get_phase(self):
    #    '''
    #    Reads the phase of the signal from the instrument
    #
    #    Input:
    #        None
    #
    #    Output:
    #        phase (float) : Phase in radians
    #    '''
    #    logging.debug(__name__ + ' : get phase')
    #    return float(self._visainstrument.query('PHASE?'))

    #def do_set_phase(self, phase):
    #    '''
    #    Set the phase of the signal
    #
    #    Input:
    #        phase (float) : Phase in radians
    #
    #    Output:
    #        None
    #    '''
    #    logging.debug(__name__ + ' : set phase to %f' % phase)
    #    self._visainstrument.write('PHASE %s' % phase)

    def do_get_frequency(self):
        '''
        Reads the frequency of the signal from the instrument

        Input:
            None

        Output:
            freq (float) : Frequency in Hz
        '''
        logging.debug(__name__ + ' : get frequency')
        return float(self._visainstrument.query('FREQ:CW?'))

    def do_set_frequency(self, freq):
        '''
        Set the frequency of the instrument

        Input:
            freq (float) : Frequency in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : set frequency to %f' % freq)
        self._visainstrument.write('FREQ:CW %s' % freq)

    def do_get_status(self):
        '''
        Reads the output status from the instrument

        Input:
            None

        Output:
            status (string) : 'On' or 'Off'
        '''
        logging.debug(__name__ + ' : get status')
        return bool(int(self._visainstrument.query('OUTP?')))


    def do_set_status(self, status):
        '''
        Set the output status of the instrument

        Input:
            status (string) : 'On' or 'Off'

        Output:
            None
        '''
        logging.debug(__name__ + ' : set status to %s' % status)
        
        if status == True:
            self._visainstrument.write('OUTP ON')
        elif status == False:
            self._visainstrument.write('OUTP OFF')
        else:
            raise ValueError('set_status(): can only set True or False')


    def reset(self):
        logging.info(__name__ + ' : resetting instrument')
        self._visainstrument.write('*RST')
        self.get_all()
