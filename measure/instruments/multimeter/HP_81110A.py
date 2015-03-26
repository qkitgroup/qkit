# HP_81110A.py class, to perform the communication between the Wrapper and the device
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

from instrument import Instrument
import visa
import types
import logging
import time

class HP_81110A(Instrument):
    '''
    This is the python driver for the HP 81110A
    pulse generator
    Also works with the Agilent 81130A, the former HP 81130A.

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'HP_81110A', address='<GPIB address>',
        reset=<bool>)
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the HP_81110A, and communicates with the wrapper.

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
        self._channels = self._get_number_of_channels()

        self.add_parameter('delay', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, self._channels), minval=0.0, maxval=999, units='sec',channel_prefix='ch%d_')
        self.add_parameter('width', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, self._channels), minval=-6.25e-9, maxval=999.5, units='sec',channel_prefix='ch%d_')
        self.add_parameter('high', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, self._channels), minval=-9.90, maxval=10.0, units='Volts',channel_prefix='ch%d_')
        self.add_parameter('low', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, self._channels), minval=-10.0, maxval=9.90, units='Volts',channel_prefix='ch%d_')
        self.add_parameter('status', type=types.StringType, channels=(1, self._channels),
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,channel_prefix='ch%d_')
        self.add_parameter('display', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET)

        self.add_function('reset')
        self.add_function('get_all')
        self.add_function('set_mode_triggered')
        self.add_function('set_mode_continuous')

        if reset:
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
        logging.info(__name__ + ' : Resetting instrument')
        self._visainstrument.write('*RST')

        """ Fix: The Agilent 81130A is kinda slow after a reset. """
        time.sleep(2)

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
        logging.info(__name__ + ' : reading all settings from instrument')

        for i in range(1,self._channels+1):
            self.get('ch%d_delay' % i)
            self.get('ch%d_width' % i)
            self.get('ch%d_low' % i)
            self.get('ch%d_high' % i)
            self.get('ch%d_status' % i)

        self.get_display()

    # communication with device
    def do_get_delay(self, channel):
        '''
        Reads the pulse delay from the specified channel

        Input:
            channel (int) : 1 or 2, the number of the designated channel

        Output:
            delay (float) : delay in seconds
        '''
        logging.debug(__name__ + ' : get delay for channel %d' % channel)
        return float(self._visainstrument.ask(':PULS:DEL' + str(channel) + "?"))

    def do_set_delay(self, val, channel):
        '''
        Sets the delay of the pulse of the specified channel

        Input:
            val (float)   : delay in seconds
            channel (int) : 1 or 2, the number of the designated channel

        Output:
            None
        '''
        logging.debug(__name__ + ' : set delay for channel %d to %f' % (channel, val))
        self._visainstrument.write(':PULS:DEL' + str(channel) + " " + str(val) + "S")

    def do_get_width(self, channel):
        '''
        Reads the pulse width from the device for the specified channel

        Input:
            channel (int) : 1 or 2, the number of the designated channel

        Output:
            width (float) : width in seconds
        '''
        logging.debug(__name__ + ' : get width for channel %d' % channel)
        return float(self._visainstrument.ask(':PULS:WIDT' + str(channel) + "?"))

    def do_set_width(self, val, channel):
        '''
        Sets the width of the pulse of the specified channel

        Input:
            val (float)   : width in seconds
            channel (int) : 1 or 2, the number of the designated channel

        Output:
            None
        '''
        logging.debug(__name__ + ' : set width for channel %d to %f' % (channel, val))
        self._visainstrument.write(':PULS:WIDT' + str(channel) + " " + str(val) + "S")

    def do_get_high(self, channel):
        '''
        Reads the upper value from the device for the specified channel

        Input:
            channel (int) : 1 or 2, the number of the designated channel

        Output:
            val (float) : upper bound in Volts
        '''
        logging.debug(__name__ + ' : get high for channel %d' % channel)
        return float(self._visainstrument.ask(':VOLT' + str(channel) + ':HIGH?'))

    def do_set_high(self, val, channel):
        '''
        Sets the upper value of the specified channel

        Input:
            val (float)   : high bound in Volts
            channel (int) : 1 or 2, the number of the designated channel

        Output:
            None
        '''
        logging.debug(__name__ + ' : set high for channel %d to %f' % (channel, val))
        self._visainstrument.write(':VOLT' + str(channel) + ":HIGH " + str(val) + "V")

    def do_get_low(self, channel):
        '''
        Reads the lower value from the device for the specified channel

        Input:
            channel (int) : 1 or 2, the number of the designated channel

        Output:
            val (float) : lower bound in Volts
        '''
        logging.debug(__name__ + ' : get low for channel %d' % channel)
        return float(self._visainstrument.ask(':VOLT' + str(channel) + ':LOW?'))

    def do_set_low(self, val, channel):
        '''
        Sets the lower value of the specified channel

        Input:
            val (float)   : low bound in Volts
            channel (int) : 1 or 2, the number of the designated channel

        Output:
            None
        '''
        logging.debug(__name__ + ' : set low for channel %d to %f' % (channel, val))
        self._visainstrument.write(':VOLT' + str(channel) + ":LOW " + str(val)        + "V")

    def do_get_status(self, channel):
        '''
        Reads the status from the device for the specified channel

        Input:
            channel (int) : 1 or 2, the number of the designated channel

        Output:
            status (string) : 'on' or 'off'
        '''
        logging.debug(__name__ + ' : getting status for channel %d' % channel)
        val = self._visainstrument.ask('OUTP' + str(channel) + '?')
        if (val=='1'):
            return 'on'
        elif (val=='0'):
            return 'off'
        return 'error'

    def do_set_status(self, val, channel):
        '''
        Sets the status of the specified channel

        Input:
            val (string)  : 'on' or 'off'
            channel (int) : 1 or 2, the number of the designated channel

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting status for channel %d to %s' % (channel, val))
        if ((val.upper()=='ON') | (val.upper()=='OFF')):
            self._visainstrument.write('OUTP' + str(channel) + " " + val)
        else:
            logging.error('Try tot set OUTP to ' + str(val))

    def do_get_display(self):
        '''
        Reads the display status from the device

        Input:
            None

        Output:
            status (string) : 'on' or 'off'
        '''
        logging.debug(__name__ + ' : getting display status')
        val = self._visainstrument.ask('DISP?')
        if (val=='1'):
            return 'on'
        elif (val=='0'):
            return 'off'
        return 'error'

    def do_set_display(self, val):
        '''
        Sets the display status of the device

        Input:
            val (string) : 'on' or 'off'

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting display status to %s' % val)
        if ((val.upper()=='ON') | (val.upper()=='OFF')):
            self._visainstrument.write('DISP ' + val)
        else:
            logging.error('Try tot set display to ' +val)

    def set_mode_triggered(self):
        '''
        Sets the instrument in 'triggered' mode

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting instrument to triggered mode')
        self._visainstrument.write(':ARM:SOUR EXT')

    def set_mode_continuous(self):
        '''
        Sets the instrument in 'triggered' mode

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting instrument to continuous mode')
        self._visainstrument.write(':ARM:SOUR IMM')

    def _get_number_of_channels(self):
        '''
        asks the device for the options installed and derives the number of channels
        Fixme: maybe there is a direct method to examine the number of channels.

        Input:
            None
        Output:
            Number of installed channels (int)

        '''
        opt = self._visainstrument.ask('*OPT?').split()
        return int(len(opt)-opt.count(0))
