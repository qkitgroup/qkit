# Winspec.py, spectrometer using winspec (with supported camera)
# Reinier Heeres <reinier@heeres.eu>, 2010
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
import logging

from lib.com_support import winspec
from lib.dll_support import andor

import qt

class Winspec(Instrument):

    def __init__(self, name, address=None, reset=False):
        Instrument.__init__(self, name, tags=['measure'])

        self.add_parameter('target_temperature', type=types.IntType,
                flags=Instrument.FLAG_GETSET,
                units='C')

        self.add_parameter('temperature', type=types.IntType,
                flags=Instrument.FLAG_GET,
                units='C')

        self.add_parameter('exposure_time', type=types.FloatType,
                flags=Instrument.FLAG_GETSET,
                units='s')

        grbase = winspec.get_ngratings() * winspec.get_current_turret()
        gratings = {}
        for i in range(winspec.get_ngratings()):
            gr = winspec.get_grating_grooves(grbase + i + 1)
            name = winspec.get_grating_name(grbase + i + 1)
            gratings[i+1] = '%s (%s)' % (gr, name)

        self.add_parameter('grating', type=types.IntType,
                flags=Instrument.FLAG_GETSET,
                format_map=gratings)

        self.add_parameter('wavelength', type=types.FloatType,
                flags=Instrument.FLAG_GETSET,
                units='nm')

        self.add_function('take_spectrum')
#        self.add_function('take_spectra')
        self.add_function('save_spectrum')
        self.add_function('plus_1nm')
        self.add_function('minus_1nm')

        if reset:
            self.reset()
        else:
            self.get_all()

    def reset(self):
        return True

    def get_all(self):
        self.get_target_temperature()
        self.get_temperature()
        self.get_exposure_time()
        self.get_grating()
        self.get_wavelength()
        return True

    def do_get_target_temperature(self):
        return winspec.get_target_temperature()

    def do_set_target_temperature(self, val):
        return winspec.set_target_temperature(val)

    def do_get_temperature(self):
        return winspec.get_temperature()

    def do_get_exposure_time(self):
        return winspec.get_exposure_time()

    def do_set_exposure_time(self, val):
        return winspec.set_exposure_time(val)

    def do_get_wavelength(self):
        return winspec.get_wavelength()

    def do_set_wavelength(self, val):
        return winspec.set_wavelength(val)

    def do_get_grating(self):
        return winspec.get_grating()

    def do_set_grating(self, val):
        return winspec.set_grating(val)

    def take_spectrum(self, ret=False):
        spec = winspec.get_spectrum()
        qt.plot(spec, name='winspec_spectrum', clear=True)
        if ret:
            return spec

    # Not working yet... The msleep gives threading problems
    def take_spectra(self, n=100):
        for i in range(n):
            self.take_spectrum()
            qt.msleep(0.05)
        return

    def save_spectrum(self, ret=False):
        spec = winspec.get_spectrum()
        specd = qt.Data(name='spectrum')
        specd.add_coordinate('Wavelength', units='nm')
        specd.add_value('Counts')
        specd.create_file()
        specd.add_data_point(spec)
        specd.close_file()
        qt.plot(specd, name='saved_spectrum', clear=True)
        if ret:
            return spec

    def plus_1nm(self):
        return self.set_wavelength(self.get_wavelength() + 1.0)

    def minus_1nm(self):
        return self.set_wavelength(self.get_wavelength() - 1.0)
