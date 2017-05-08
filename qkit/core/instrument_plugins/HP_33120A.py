# HP_33120A.py class, to perform the communication between the Wrapper and the device
# Pieter de Groot <pieterdegroot@gmail.com>, 2008
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
import logging
from time import sleep

#TODO
#1 put modes/shapes/status as parameter with list of options?
#   burst_state { on, off }
#   trigger_state { cont, external, gpib }
#   function_shape { see below }
#2 put above in get_all()

class HP_33120A(Instrument):
    '''
    This is the python driver for the HP 33120A
    arbitrary waveform generator

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'HP_33120A', address='<GPIB address>',
        reset=<bool>)
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the HP_33120A, and communicates with the wrapper.

        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address
            reset (bool)     : resets to default values, default=false

        Output:
            None
        '''
        Instrument.__init__(self, name, tags=['physical'])

        self._address = address
        self._visainstrument = visa.instrument(self._address)

        self.add_parameter('frequency',
                type=types.FloatType,
                flags=Instrument.FLAG_GETSET,
                minval=10e-3, maxval=1e6,
                units='Hz')
        self.add_parameter('amplitude',
                type=types.FloatType,
                flags=Instrument.FLAG_GETSET,
                minval=-10, maxval=10,
                units='V')
        self.add_parameter('offset',
                type=types.FloatType,
                flags=Instrument.FLAG_GETSET,
                minval=-10, maxval=10,
                units='V')
        self.add_parameter('burst_count',
                type=types.IntType,
                flags=Instrument.FLAG_GETSET,
                minval=1, maxval=10000,
                units='#')
        self.add_parameter('burst_status',
                type=types.StringType,
                flags=Instrument.FLAG_GETSET,
                option_list=(
                    'on',
                    'off'
                ))


        self.add_function('reset')
        self.add_function('get_all')
        self.add_function('send_trigger')

        if reset:
            self.reset()
        else:
            self.get_all()

    def get_all(self):
        self.get_frequency()
        sleep(0.1)
        self.get_amplitude()
        sleep(0.1)
        self.get_offset()
        sleep(0.1)
        self.get_burst_count()
        sleep(0.1)

    def reset(self):
        logging.info(__name__ + ' : Resetting instrument')
        self._visainstrument.write('*RST')
        sleep(0.1)
        self.get_all()

    def get_error(self):
        logging.debug(__name__ + ' : Getting one error from error list')
        return self._visainstrument.ask('SYST:ERR?')

# Trigger

    def set_trigger_continuous(self):
        logging.debug(__name__ + ' : Set trigger to continuous')
        self._visainstrument.write('TRIG:SOUR IMM')

    def set_trigger_external(self):
        logging.debug(__name__ + ' : Set trigger to external')
        self._visainstrument.write('TRIG:SOUR EXT')

    def set_trigger_gpib(self):
        logging.debug(__name__ + ' : Set trigger to gpib')
        self._visainstrument.write('TRIG:SOUR BUS')

    def get_trigger_state(self):
        logging.debug(__name__ + ' : Getting trigger state')
        return self._visainstrument.ask('TRIG:SOUR?')

    def send_trigger(self):
        logging.debug(__name__ + ' : Sending Trigger')
        self._visainstrument.write('*TRG')

# Burst

    def do_set_burst_count(self, cnt):
        logging.debug(__name__ + ' : Setting burst count')
        self._visainstrument.write('BM:NCYC %d' % cnt)

    def do_get_burst_count(self):
        logging.debug(__name__ + ' : Getting burst count')
        return float(self._visainstrument.ask('BM:NCYC?'))

    def do_set_burst_status(self, stat):
        '''
        stat: { ON OFF }
        '''
        logging.debug(__name__ + ' : Setting burst status')
        self._visainstrument.write('BM:STAT %s' % stat)

    def do_get_burst_status(self):
        '''
        stat: { ON OFF }
        '''
        logging.debug(__name__ + ' : Getting burst status')
        return self._visainstrument.ask('BM:STAT?')

# Shape

    def set_function_shape(self, shape):
        '''
        shape : { SIN, SQU, TRI, RAMP, NOIS, DC, USER }
        '''
        logging.debug(__name__ + ' : Sending Trigger')
        self._visainstrument.write('SOUR:FUNC:SHAP %s' % shape)

    def get_function_shape(self):
        logging.debug(__name__ + ' : Getting function shape')
        return self._visainstrument.ask('SOUR:FUNC:SHAP?')

# Parameters

    def do_set_frequency(self, freq):
        logging.debug(__name__ + ' : Setting frequency')
        self._visainstrument.write('SOUR:FREQ %f' % freq)

    def do_get_frequency(self):
        logging.debug(__name__ + ' : Getting frequency')
        return self._visainstrument.ask('SOUR:FREQ?')

    def do_set_amplitude(self, amp):
        logging.debug(__name__ + ' : Setting amplitude')
        self._visainstrument.write('SOUR:VOLT %f' % amp)

    def do_get_amplitude(self):
        logging.debug(__name__ + ' : Getting amplitude')
        return self._visainstrument.ask('SOUR:VOLT?')

    def do_set_offset(self, offset):
        logging.debug(__name__ + ' : Setting offset')
        self._visainstrument.write('SOUR:VOLT:OFFS %f' % offset)

    def do_get_offset(self):
        logging.debug(__name__ + ' : Getting offset')
        return self._visainstrument.ask('SOUR:VOLT:OFFS?')

