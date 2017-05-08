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

class Cryomagnetics_CS4(Instrument):

    UNITS = ['A', 'T', 'G', 'kG']
    MARGIN = 0.002

    def __init__(self, name, address, reset=False):
        Instrument.__init__(self, name)

        self._address = address
        self._visa = visa.instrument(self._address)

        self.add_parameter('identification',
            flags=Instrument.FLAG_GET)

        self.add_parameter('units',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType)

        self.add_parameter('rate',
            flags=Instrument.FLAG_GETSET,
            type=types.FloatType,
            minval=0,
            units='A/s')

        self.add_parameter('heater',
            flags=Instrument.FLAG_GETSET,
            type=types.BooleanType)

        self.add_parameter('magnetout',
            flags=Instrument.FLAG_GET,
            type=types.FloatType,
            units='T', format='%.05f')

        self.add_parameter('supplyout',
            flags=Instrument.FLAG_GET,
            type=types.FloatType,
            units='T', format='%.05f')

        self.add_parameter('sweep',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType)

        self.add_parameter('lowlim',
            flags=Instrument.FLAG_GETSET,
            type=types.FloatType,
            minval=-9.0, maxval=9.0,
            units='T', format='%.05f')

        self.add_parameter('uplim',
            flags=Instrument.FLAG_GETSET,
            type=types.FloatType,
            minval=-9.0, maxval=9.0,
            units='T', format='%.05f')

        self.add_parameter('field',
            flags=Instrument.FLAG_GETSET,
            type=types.FloatType,
            minval=-9000.0, maxval=9000.0,
            units='mT', format='%.02f',
            tags=['sweep'])

        self.add_function('local')
        self.add_function('remote')
        self.add_function('sweep_up')
        self.add_function('sweep_down')

        if reset:
            self.reset()
        else:
            self.get_all()

    def reset(self):
        self._visa.write('*RST')

    def get_all(self):
        self.get_units()
        self.get_rate()
        self.get_heater()
        self.get_magnetout()
        self.get_supplyout()
        self.get_lowlim()
        self.get_uplim()
        self.get_field()

    def do_get_identification(self):
        return self._visa.ask('*IDN?')

    def _update_units(self, unit):
        self.set_parameter_options('magnetout', units=unit)
        self.set_parameter_options('supplyout', units=unit)
        self.set_parameter_options('lowlim', units=unit)
        self.set_parameter_options('uplim', units=unit)

    def do_get_units(self):
        ans = self._visa.ask('UNITS?')
        self._update_units(ans)
        return ans

    def do_set_units(self, unit):
        if unit not in self.UNITS:
            logging.error('Trying to set invalid unit: %s', unit)
            return False
        self._visa.write('UNITS %s' % unit)
        self._update_units(unit)

    def _check_ans_unit(self, ans):
        try:
            val, unit = ans.split(' ')
        except:
            logging.warning('Unable to parse answer: %s', ans)
            return False

        set_unit = self.get_units(query=False)
        if unit != set_unit:
            logging.warning('Returned units (%s) differ from set units (%s)!',
                unit, set_unit)
            return False

        return float(val)

    #FIXME: allow all 4 parameter ranges
    def do_get_rate(self):
        ans = self._visa.ask('RATE? 0')
        return float(ans)

    def do_set_rate(self, rate):
        self._visa.write('RATE 0 %.03f' % rate)

    def do_get_heater(self):
        ans = self._visa.ask('PSHTR?')
        if len(ans) > 0 and ans[0] == '1':
            return True
        else:
            return False

    def do_set_heater(self, on):
        if on:
            text = 'ON'
        else:
            text = 'OFF'

        self._visa.write('PSHTR %s' % text)

    def local(self):
        self._visa.write('LOCAL')

    def remote(self):
        self._visa.write('REMOTE')

    def do_get_magnetout(self):
        ans = self._visa.ask('IMAG?')
        return self._check_ans_unit(ans)

    def do_get_supplyout(self):
        ans = self._visa.ask('IMAG?')
        return self._check_ans_unit(ans)

    def do_get_sweep(self):
        ans = self._visa.ask('SWEEP?')
        if len(ans) > 6:
            return ans[6:]
        else:
            return ''

    def do_set_sweep(self, val):
        val = val.upper()
        if val not in ['UP', 'UP FAST', 'DOWN', 'DOWN FAST']:
            logging.warning('Invalid sweep mode selected')
            return False
        self._visa.write('SWEEP %s' % val)

    def sweep_up(self, fast=False):
        if fast:
            return self.set_sweep('UP FAST')
        else:
            return self.set_sweep('UP')

    def sweep_down(self, fast=False):
        if fast:
            return self.set_sweep('DOWN FAST')
        else:
            return self.set_sweep('DOWN')

    def do_get_lowlim(self):
        ans = self._visa.ask('LLIM?')
        return self._check_ans_unit(ans)

    def do_set_lowlim(self, val):
        self._visa.write('LLIM %f' % val)

    def do_get_uplim(self):
        ans = self._visa.ask('ULIM?')
        return self._check_ans_unit(ans)

    def do_set_uplim(self, val):
        self._visa.write('ULIM %f' % val)

    def do_set_field(self, val, wait=True):
        units = self.get_units(query=False)
        if units != 'T':
            logging.warning('Unable to set field when units not in Tesla!')
            return False

        if not self.get_heater(query=False):
            logging.warning('Unable to sweep field when heater off')
            return False

        cur_magnet = self.get_magnetout()
        cur_supply = self.get_supplyout()
        if math.fabs(cur_magnet - cur_supply) > self.MARGIN:
            logging.warning('Unable to set field when magnet (%f) and supply (%f) not equal!', cur_magnet, cur_supply)
            return False

        valtesla = val / 1000.0
        if valtesla > cur_magnet:
            self.set_uplim(valtesla)
            self.sweep_up()
        else:
            self.set_lowlim(valtesla)
            self.sweep_down()

        if wait:
            while math.fabs(valtesla - self.get_magnetout()) > self.MARGIN:
                time.sleep(0.050)

        return True

    def do_get_field(self):
        unit = self.get_units(query=False)
        if unit != 'T':
            logging.warning('Unable to determine field if units are not T')
            return None

        magnet_field = self.get_magnetout()
        return magnet_field * 1000.0

