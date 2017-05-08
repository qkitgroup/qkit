# WinspecAndor.py, spectrometer combining winspec and Andor camera
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

class WinspecAndor(Instrument):

    def __init__(self, name, address=None, reset=False):
        Instrument.__init__(self, name, tags=['measure'])

        self.add_parameter('cooler_on', type=types.BooleanType,
                flags=Instrument.FLAG_GETSET)

        self.add_parameter('target_temperature', type=types.IntType,
                flags=Instrument.FLAG_SET|Instrument.FLAG_SOFTGET,
                units='C')

        self.add_parameter('temperature', type=types.IntType,
                flags=Instrument.FLAG_GET,
                units='C')

        self.add_parameter('exposure_time', type=types.FloatType,
                flags=Instrument.FLAG_SET,
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

        self.initialize_andor()
        self.add_function('take_spectrum')
#        self.add_function('take_spectra')
        self.add_function('save_spectrum')
        self.add_function('plus_1nm')
        self.add_function('minus_1nm')
        self.add_function('initialize_andor')
        self.add_function('cooldown_andor')
        self.add_function('warmup_andor')
        self.add_function('shutdown_andor')

        if reset:
            self.reset()
        else:
            self.get_all()

    def reset(self):
        self.initialize_andor()
        return True

    def get_all(self):
        self.get_cooler_on()
        self.get_temperature()
        self.get_grating()
        self.get_wavelength()
        return True

    def do_get_cooler_on(self):
        return andor.is_cooler_on()

    def do_set_cooler_on(self, val):
        return andor.set_cooler(val)

    def do_set_target_temperature(self, val):
        return andor.set_temperature(val)

    def do_get_temperature(self):
        return andor.get_temperature()

    def do_set_exposure_time(self, val):
        return andor.set_exposure_time(val)

    def do_get_wavelength(self):
        return winspec.get_wavelength()

    def do_set_wavelength(self, val):
        return winspec.set_wavelength(val)

    def do_get_grating(self):
        return winspec.get_grating()

    def do_set_grating(self, val):
        return winspec.set_grating(val)

    def take_spectrum(self, ret=False):
        spec = andor.get_spectrum()
        qt.plot(spec, name='andor_spectrum', clear=True)
        if ret:
            return spec

    # Not working yet... The msleep gives threading problems
    def take_spectra(self, n=100):
        for i in range(n):
            self.take_spectrum()
            qt.msleep(0.05)
        return
        
    def save_spectrum(self, ret=False):
        spec = andor.get_spectrum()
        specd = qt.Data(name='spectrum')
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

    def initialize_andor(self):
        andor.initialize()
        andor.set_read_mode(0)
        self.set_exposure_time(0.1)
        
    def cooldown_andor(self):
        andor.set_cooler_on(True)
        andor.set_target_temperature(-80)
        self.get_all()

    def warmup_andor(self):
        andor.set_target_temperature(0)
        andor.set_cooler_on(False)
        self.get_all()
        
    def shutdown_andor(self):
        andor.shutdown()
