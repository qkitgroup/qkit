# Oxford_Triton.py
# MP@KIT 09/2016
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

class Oxford_Triton(Instrument):
    '''
    This is the python driver for the Oxford Triton 200 fridge

    Usage:
    Initialise with
    <name> = instruments.create('<name>', address='<GPIB address>', reset=<bool>)

    '''

    def __init__(self, name, address, channel_index = 1):
        '''
        Initializes

        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address
        '''

        logging.info(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])

        self._address = address
        self._visainstrument = visa.instrument(self._address)

        # Implement parameters
        self.add_parameter('temperature', type=types.FloatType,
            flags=Instrument.FLAG_GET, channels=(1,2,3,4,5,6,7,8),
            minval=0, maxval=350,
            units='K', tags=['sweep'])

        self.add_parameter('resistance', type=types.FloatType,
            flags=Instrument.FLAG_GET, channels=(1,2,3,4,5,6,7,8),
            minval=0, maxval=200000,
            units='Ohm', tags=['sweep'])

        # FIND OUT OVC PRESSURE CHANNEL
        self.add_parameter('pressure', type=types.FloatType,
            flags=Instrument.FLAG_GET, channels=(1,2,3,4,5,6),
            minval=0, maxval=5,
            units='bar', tags=['sweep'])

        self.add_parameter('valve', type=types.BoleanType,
            flags=Instrument.FLAG_GETSET, channels=(1,2,3,4,5,6,7,8,9))

        self.add_parameter('pulse_tube', type=types.BooleanType,
            flags=Instrument.FLAG_GETSET)

        self.add_parameter('still_power', type=types.FloatType,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=1,
            units='W', tags=['sweep'])

        self.add_parameter('base_power', type=types.FloatType,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=1,
            units='W', tags=['sweep'])

        self.add_parameter('warm_up_heater', type=types.BoleanType,
            flags=Instrument.FLAG_GETSET)

        # Implement functions
        self.add_function('start_pre_cooling')
        self.add_function('empty_pre_cooling')
        self.add_function('start_condensing')
        self.add_function('cool_down')
        self.add_function('warm_up')

        self.get_all()

    def get_all(self):
        for i in range(8):
            self.get_temperature(i+1)
        for i in range(6):
            self.get_pressure(i+1)
        for i in range(9):
            self.get_valve_status(i+1)
        self.get_still_power()
        self.get_base_power()
        self.get_warm_up_heater()


    ###
    #Communication with device
    ###


    def start_pre_cooling(self):
        '''
        Starts pre cooling

        Input:
            None

        Output:
            bool as confirmation
        '''
        logging.debug(__name__ + ' : start pre-cooling')
        self._visainstrument.write('')
        ret = self._visainstrument.ask('')
        return ret

    def empty_pre_cooling(self):
        '''
        Emptys pre cooling

        Input:
            None

        Output:
            bool as confirmation
        '''
        logging.debug(__name__ + ' : empty pre-cool circuit')
        self._visainstrument.write('')
        ret = self._visainstrument.ask('')
        return ret

    def start_condensing(self):
        '''
        Starts condensing

        Input:
            None

        Output:
            bool as confirmation
        '''
        logging.debug(__name__ + ' : start condensing')
        self._visainstrument.write('')
        ret = self._visainstrument.ask('')
        return ret

    def cool_down(self):
        '''
        Starts full cool down

        Input:
            None

        Output:
            bool as confirmation
        '''
        logging.debug(__name__ + ' : cool down')
        self._visainstrument.write('')
        ret = self._visainstrument.ask('')
        return ret

    def warm_up(self):
        '''
        Starts warm up

        Input:
            None

        Output:
            bool as confirmation
        '''
        logging.debug(__name__ + ' : warm up')
        #self.set_warm_up_heater(True)
        self._visainstrument.write('')
        ret = self._visainstrument.ask('')
        return ret


    ###
    # GET and SET functions
    ###


    def do_get_temperature(self, channel = 8):
        '''
        Get temperature of thermometer at channel

        Input:
            channel (int), default = 8, RuOx at MC
        Output:
            temperature (float)
        '''
        logging.debug(__name__ + ' : getting temperature of channel %i' %(channel))
        return int(self._visainstrument.ask('' %(channel)))

    def do_get_resistance(self, channel = 8):
        '''
        Get resistance of thermometer at channel

        Input:
            channel (int), default = 8, RuOx at MC
        Output:
            resistance (float)
        '''
        logging.debug(__name__ + ' : getting resistance of channel %i' %(channel))
        return int(self._visainstrument.ask('' %(channel)))

    def do_get_pressure(self, pressure_meter = 1):
        '''
        Get pressure at pressure_meter

        Input:
            pressure_meter (int), default=1, tank
        Output:
            pressure (float)
        '''

        logging.debug(__name__ + ' : getting pressure at gauge %i' %(pressure_meter))
        return int(self._visainstrument.ask('' %(pressure_meter)))

    def do_get_valvue(self, valve_number):
        '''
        Get valve status at valve_number

        Input:
            valve number (int)
        Output:
            status (bool)
        '''

        logging.debug(__name__ + ' : getting valve %s status' %(valve_number))
        return int(self._visainstrument.ask('' %(valve_number)))

    def do_set_valve(self, valve_number, status):
        '''
        Set valve status at valve_number to status

        Input:
            valve number (int)
            status (bool)
        Output:
            bool as confirmation
        '''

        logging.debug(__name__ + ' : setting valve %i to %s' %(valve_number ,status))
        self._visainstrument.write('' %(valve_number, status))
        return self._visainstrument.ask('' %(valve_number)) == status

    def do_get_pulse_tube(self):
        '''
        Get pulse tube status

        Input:
            None
        Output:
            status (bool)
        '''

        logging.debug(__name__ + ' : getting pulse tube status')
        return int(self._visainstrument.ask(''))

    def do_set_pulse_tube(self, status):
        '''
        Set pulst tube to status

        Input:
            status (bool)
        Output:
            bool as confirmation
        '''

        logging.debug(__name__ + ' : setting pulse tube to %i' %(status))
        self._visainstrument.write('' %(status))
        return self._visainstrument.ask('') == status

    def do_get_still_power(self):
        '''
        Get still heater power

        Input:
            None
        Output:
            power (float)
        '''

        logging.debug(__name__ + ' : getting still power')
        return float(self._visainstrument.ask(''))

    def do_set_still_power(self, power):
        '''
        Set still heater to power

        Input:
            power (float)
        Output:
            bool as confirmation
        '''

        logging.debug(__name__ + ' : setting still heater power to %f' %(power))
        self._visainstrument.write('' %(power))
        return self._visainstrument.ask('') == power

    def do_get_base_power(self):
        '''
        Get base heater power

        Input:
            None
        Output:
            power (float)
        '''

        logging.debug(__name__ + ' : getting base power')
        return float(self._visainstrument.ask(''))

    def do_set_base_power(self, power):
        '''
        Set base heater to power

        Input:
            power (float)
        Output:
            bool as confirmation
        '''

        logging.debug(__name__ + ' : setting base heater power to %f' %(power))
        self._visainstrument.write('' %(power))
        return self._visainstrument.ask('') == power

    def do_get_warm_up_heater(self):
        '''
        Get status of warm up heater

        Input:
            None
        Output:
            status (bool)
        '''

        logging.debug(__name__ + ' : getting warm up heater status')
        return int(self._visainstrument.ask(''))

    def do_set_warm_up_heater(self, status):
        '''
        Set warm up heater to status

        Input:
            status (bool)
        Output:
            bool as confirmation
        '''

        logging.debug(__name__ + ' : setting warm up heater to %i' %(status))
        self._visainstrument.write('' %(status))
        return self._visainstrument.ask('') == status