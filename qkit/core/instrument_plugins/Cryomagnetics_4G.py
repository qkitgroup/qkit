# Cryomagnetics_CS4, Cryomagnetics CS4 magnet power supply driver
# Reinier Heeres <reinier@heeres.eu>, 2008
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
import re
import math
import time
import re

class Cryomagnetics_4G(Instrument):

    UNITS = ['A', 'G']
    MARGIN = 0.001  # 1 Gauss
    RE_ANS = re.compile(r'(-?\d*\.?\d*)([a-zA-Z]+)')

    def __init__(self, name, address, reset=False, axes=('Z')):
        Instrument.__init__(self, name)

        self._axes = {}
        for i in range(len(axes)):
            self._axes[i+1] = axes[i]
        self._address = address
        self._visa = visa.instrument(self._address)

        self.add_parameter('identification',
            flags=Instrument.FLAG_GET)

        self.add_parameter('units',
            flags=Instrument.FLAG_GETSET,
            channels=axes,
            option_list=self.UNITS,
            type=types.StringType)

        self.add_parameter('rate0',
            flags=Instrument.FLAG_GETSET,
            type=types.FloatType,
            channels=axes,
            minval=0,
            units='A/s')

        self.add_parameter('rate1',
            flags=Instrument.FLAG_GETSET,
            type=types.FloatType,
            channels=axes,
            minval=0,
            units='A/s')

        self.add_parameter('heater',
            flags=Instrument.FLAG_GETSET,
            channels=axes,
            type=types.BooleanType,
            doc='''Persistent switch heater on?''')

        self.add_parameter('magnetout',
            flags=Instrument.FLAG_GET | Instrument.FLAG_SET,
            channels=axes,
            type=types.FloatType,
            units='kG', format='%.05f',
            doc='''Magnet current (or field in kG)''')

        self.add_parameter('supplyout',
            flags=Instrument.FLAG_GET,
            channels=axes,
            type=types.FloatType,
            units='kG', format='%.05f',
            doc='''Power supply current (or field in kG)''')

        self.add_parameter('sweep',
            flags=Instrument.FLAG_GETSET,
            channels=axes,
            option_list=['UP', 'UP FAST', 'DOWN', 'DOWN FAST', 'PAUSE', 'ZERO'],
            type=types.StringType)

        self.add_parameter('lowlim',
            flags=Instrument.FLAG_GETSET,
            channels=axes,
            type=types.FloatType,
            minval=-90.0, maxval=90.0,
            units='kG', format='%.05f')

        self.add_parameter('uplim',
            flags=Instrument.FLAG_GETSET,
            channels=axes,
            type=types.FloatType,
            minval=-90.0, maxval=90.0,
            units='kG', format='%.05f')

        self.add_parameter('field',
            flags=Instrument.FLAG_GETSET,
            channels=axes,
            type=types.FloatType,
            minval=-90, maxval=90.0,
            units='kG', format='%.02f',
            tags=['sweep'],
            doc='''Field in Gauss (or Amperes)''')

        self.add_function('local')
        self.add_function('remote')
        self.add_function('sweep_up')
        self.add_function('sweep_down')
        self.add_function('pause')
        self.add_function('zero')

        if reset:
            self.reset()
        else:
            self.get_all()

    def reset(self):
        self._visa.write('*RST')

    def get_all(self):
        self.get_identification()
        for ax in self._axes.values():
            self.get('units%s' % ax)
            self.get('rate0%s' % ax)
            self.get('rate1%s' % ax)
            self.get('heater%s' % ax)
            self.get('magnetout%s' % ax)
            self.get('supplyout%s' % ax)
            self.get('lowlim%s' % ax)
            self.get('uplim%s' % ax)
            self.get('field%s' % ax)
            self.get('sweep%s' % ax)

    def do_get_identification(self):
        return self._visa.ask('*IDN?')

    def _update_units(self, unit, channel):
        if unit == 'G':
            unit = 'kG'
        self.set_parameter_options('magnetout%s' % channel, units=unit)
        self.set_parameter_options('supplyout%s' % channel, units=unit)
        self.set_parameter_options('lowlim%s' % channel, units=unit)
        self.set_parameter_options('uplim%s' % channel, units=unit)

    def do_get_nchannels(self):
        ans = self._visa.ask('CHAN?')
        if ans not in ('1', '2'):
            return 2
        else:
            return 1

    def _select_channel(self, channel):
        for i, v in self._axes.iteritems():
            if v == channel:
                self._visa.write('CHAN %d' % i)
                return True
        raise ValueError('Unknown axis %s' % channel)

    def do_get_units(self, channel):
        self._select_channel(channel)
        ans = self._visa.ask('UNITS?')
        self._update_units(ans, channel)
        return ans

    def do_set_units(self, unit, channel):
        if unit not in self.UNITS:
            logging.error('Trying to set invalid unit: %s', unit)
            return False
        self._select_channel(channel)
        self._visa.write('UNITS %s' % unit)
        self._update_units(unit, channel)

    def _check_ans_unit(self, ans, channel):
        m = self.RE_ANS.match(ans)
        if not m:
            logging.warning('Unable to parse answer: %s', ans)
            return False

        val, unit = m.groups((0,1))
        try:
            val = float(val)
        except:
            val = None

        set_unit = self.get('units%s' % channel, query=False)
        if set_unit == 'G':
            set_unit = 'kG'
        if unit != set_unit:
            logging.warning('Returned units (%s) differ from set units (%s)!',
                unit, set_unit)
            return None

        return val

    def do_get_rate0(self, channel):
        self._select_channel(channel)
        ans = self._visa.ask('RATE? 0')
        return float(ans)

    def do_get_rate1(self, channel):
        self._select_channel(channel)
        ans = self._visa.ask('RATE? 1')
        return float(ans)

    def do_set_rate0(self, rate, channel):
        self._select_channel(channel)
        self._visa.write('RATE 0 %.03f\n' % rate)

    def do_set_rate1(self, rate, channel):
        self._select_channel(channel)
        self._visa.write('RATE 1 %.03f\n' % rate)

    def do_get_heater(self, channel):
        self._select_channel(channel)
        ans = self._visa.ask('PSHTR?')
        if len(ans) > 0 and ans[0] == '1':
            return True
        else:
            return False

    def do_set_heater(self, on, channel):
        if on:
            text = 'ON'
        else:
            text = 'OFF'

        self._select_channel(channel)
        self._visa.write('PSHTR %s' % text)

    def local(self):
        self._visa.write('LOCAL')

    def remote(self):
        self._visa.write('REMOTE')

    def do_get_magnetout(self, channel):
        self._select_channel(channel)
        ans = self._visa.ask('IMAG?')
        return self._check_ans_unit(ans, channel)

    def do_set_magnetout(self, val, channel):
        self._select_channel(channel)
        ans = self._visa.write('IMAG %f\n' % val)
        return True

    def do_get_supplyout(self, channel):
        self._select_channel(channel)
        ans = self._visa.ask('IOUT?')
        return self._check_ans_unit(ans, channel)

    def do_get_sweep(self, channel):
        self._select_channel(channel)
        ans = self._visa.ask('SWEEP?')
        return ans

    def do_set_sweep(self, val, channel):
        self._select_channel(channel)
        val = val.upper()
        if val not in ['UP', 'UP FAST', 'DOWN', 'DOWN FAST', 'PAUSE', 'ZERO']:
            logging.warning('Invalid sweep mode selected')
            return False
        self._visa.write('SWEEP %s' % val)

    def sweep_up(self, channel, fast=False):
        cmd = 'UP'
        if fast:
            cmd += ' FAST'
        return self.set('sweep%s' % channel, cmd)

    def sweep_down(self, channel, fast=False):
        cmd = 'DOWN'
        if fast:
            cmd += ' FAST'
        return self.set('sweep%s' % channel, cmd)

    def do_get_lowlim(self, channel):
        self._select_channel(channel)
        ans = self._visa.ask('LLIM?')
        return self._check_ans_unit(ans, channel)

    def do_set_lowlim(self, val, channel):
        self._select_channel(channel)
        self._visa.write('LLIM %f\n' % val)

    def do_get_uplim(self, channel):
        self._select_channel(channel)
        ans = self._visa.ask('ULIM?')
        return self._check_ans_unit(ans, channel)

    def do_set_uplim(self, val, channel):
        self._select_channel(channel)
        self._visa.write('ULIM %f\n' % val)

    def do_set_field(self, val, channel, wait=False):
        self._select_channel(channel)
        units = self.get('units%s' % channel, query=False)
        if units != 'G':
            logging.warning('Unable to set field when units not in Gauss!')
            return False

        if not self.get('heater%s' % channel, query=False):
            logging.warning('Unable to sweep field when heater off')
            return False

        cur_magnet = self.get('magnetout%s' % channel)
        cur_supply = self.get('supplyout%s' % channel)
        if math.fabs(cur_magnet - cur_supply) > self.MARGIN:
            logging.warning('Unable to set field when magnet (%f) and supply (%f) not equal!', cur_magnet, cur_supply)
            return False

        if val > cur_magnet:
            self.set('uplim%s' % channel, val)
            self.sweep_up(channel)
        else:
            self.set('lowlim%s' % channel, val)
            self.sweep_down(channel)

        if wait:
            while math.fabs(val - self.get('magnetout%s' % channel)) > self.MARGIN:
                time.sleep(0.050)

        return True

    def do_get_field(self, channel):
        self._select_channel(channel)
        unit = self.get('units%s' % channel, query=False)
        if unit != 'G':
            logging.warning('Unable to determine field if units are not Gauss')
            return None

        magnet_field = self.get('magnetout%s' % channel)
        return magnet_field

    def pause(self):
        for ax in self._axes.values():
            self.set('sweep%s' % ax, 'PAUSE')

    def zero(self):
        for ax in self._axes.values():
            self.set('sweep%s' % ax, 'ZERO')

