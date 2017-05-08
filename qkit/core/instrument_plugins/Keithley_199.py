# Keithley_199.py driver for Keithley 199 DMM
# Reinier Heeres <reinier@heeres.eu>, 2009
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
import types
import visa

class Keithley_199(Instrument):

    def __init__(self, name, address=None):
        Instrument.__init__(self, name, tags=['measure'])

        self._address = address
        self._visains = visa.instrument(address)

        self.add_parameter('function', type=types.IntType,
                flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
                option_map={
                    0: 'DCV',
                    1: 'ACV',
                    2: 'Ohms',
                    3: 'DCI',
                    4: 'ACI',
                    5: 'ACVdB',
                    6: 'ACIdB',
                })

        self.add_parameter('range', type=types.FloatType,
                flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
                minval=0, maxval=7,
                )

        self.add_parameter('zero', type=types.IntType,
                flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
                option_map={
                    0: 'Disabled',
                    1: 'Enabled',
                    2: 'Value',
                })

        self.add_parameter('zero_value', type=types.FloatType,
                flags=Instrument.FLAG_GETSET)

        self.add_parameter('rate', type=types.IntType,
                flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
                option_map={
                    0: '4.5 digit',
                    1: '5.5 digit',
                })

        self.add_parameter('filter', type=types.IntType,
                flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
                )

        self.add_parameter('trigger', type=types.IntType,
                flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
                option_map={
                    0: 'Cont (talk)',
                    1: 'One-shot (talk)',
                    2: 'Cont (get)',
                    3: 'One-shot (get)',
                    4: 'Cont (X)',
                    5: 'One-shot (X)',
                    6: 'Cont (ext)',
                    7: 'One-shot (ext)',
                })

        self.add_parameter('delay', type=types.IntType,
                flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
                minval=0, maxval=999999, units='msec')

        self.add_parameter('interval', type=types.IntType,
                flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
                minval=15, maxval=999999, units='msec')

        self.add_parameter('error', type=types.IntType,
                flags=Instrument.FLAG_GET)

        self.add_parameter('value', type=types.FloatType,
                flags=Instrument.FLAG_GET,
                tags=['measure'])

        self.add_function('set_defaults')
        self.add_function('self_test')
        self.add_function('read')
        self.set_defaults()

    def set_defaults(self):
        '''Set default parameters.'''

        # Set data output without prefix, readings from ADC
        self._visains.write('G1B0')

        self.set_function(0)
        self.set_trigger(3)
        self.set_rate(1)
        self.set_delay(0)
        self.set_zero(0)

    def self_test(self):
        '''Perform a self test.'''
        self._visains.write('J')

    def do_set_function(self, func):
        '''Set the measurement function.'''
        self._visains.write('F%dX' % func)
        return True

    def do_set_range(self, range):
        '''Set the measurement range.'''
        self._visains.write('R%dX' % range)
        return True

    def do_set_zero(self, zero):
        '''Set whether to use zero calibration.'''
        self._visains.write('Z%dX' % zero)
        return True

    def do_get_zero_value(self):
        return self._visains.ask('U4')

    def do_set_zero_value(self, val):
        '''Set the zero calibration value.'''
        self._visains.write('V%EX' % val)

    def do_set_rate(self, rate):
        '''Set the rate and precision.'''
        self._visains.write('R%dX' % rate)
        return True

    def do_set_filter(self, val):
        '''Set filter type.'''
        self._visains.write('P%dX' % val)
        return True

    def do_set_trigger(self, val):
        '''Set trigger source.'''
        self._visains.write('T%dX' % val)
        return True

    def do_set_delay(self, val):
        '''Set delay after trigger before taking a measurement.'''
        self._visains.write('W%dX' % val)
        return True

    def do_set_interval(self, val):
        '''Set trigger interval.'''
        self._visains.write('Q%d' % val)
        return True

    def do_get_error(self):
        '''Read the error condition.'''
        return self._visains.ask('U1X')

    def read(self):
        '''Read a value if not in external trigger mode.'''
        mode = self.get_trigger(query=False)
        if mode in (0, 1):
            ret = self._visains.ask('')
        elif mode in (2, 3):
            ret = self._visains.ask('X')
        elif mode in (4, 5):
            ret = self._visains.ask('GET')
        return float(ret)

    def do_get_value(self):
        return self.read()

