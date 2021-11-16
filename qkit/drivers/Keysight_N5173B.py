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
#import types
import logging

class Keysight_N5173B(Instrument):
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
        Instrument.__init__(self, name, tags=['physical'])

        self._address = address
        self._visainstrument = visa.instrument(self._address)

        # Implement parameters
        self.add_parameter('power',
            flags=Instrument.FLAG_GETSET, units='dBm', minval=-50, maxval=30, type=float)
        self.add_parameter('external_attenuation',
            flags=Instrument.FLAG_GETSET, units='dB', minval=0, type=float)
        self.ext_att = 0
        #self.add_parameter('phase',
        #    flags=Instrument.FLAG_GETSET, units='rad', minval=-numpy.pi, maxval=numpy.pi, type=types.FloatType)
        self.add_parameter('frequency',
            flags=Instrument.FLAG_GETSET, units='Hz', minval=9e3, maxval=20e9, type=float)
        self.add_parameter('status',
            flags=Instrument.FLAG_GETSET, type=bool)

        self.add_function('reset')
        self.add_function ('get_all')


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
        self._visainstrument.write('*RST')
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
        return float(self._visainstrument.query('POW:AMPL?')) - self.ext_att

    def do_set_power(self, amp):
        '''
        Set the power of the signal

        Input:
            amp (float) : power in dBm

        Output:
            None
        '''
        logging.debug(__name__ + ' : set power to %f' % (amp + self.ext_att))
        self._visainstrument.write('POW:AMPL %s' % (amp + self.ext_att))
    
    def do_set_external_attenuation(self, att=0):
        '''
        Sets an eventual external attenuation, that is later subtracted from power values.

        Input:
            att (float) : attenuation in dB (Default is 0)

        Output:
            None
        '''
        self.ext_att = att
    
    def do_get_external_attenuation(self):
        '''
        Gets an eventual external attenuation, that is subtracted from power values.

        Input:
            None

        Output:
            att (float) : attenuation in dB
        '''
        return self.ext_att
    
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


    # shortcuts
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
