# Agilent_VNA_E5071C driver, P. Macha, modified by M. Weides July 2013, J. Braumueller 2015
# Adapted to Keysight VNA by A. Schneider and L. Gurenhaupt 2016
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
import numpy as np


class DummyVNA(Instrument):
    """
    simple dummy VNA class to test changes in the spectroscopy script without having a real device. Feel free to extend
    the functionality, for example noise that scales with power and averages.
    get_tracedata generates a random S21 trace with an overcoupled resonator dip
    frequency changes should behave like a real VNA, i.e., span is kept constant when start stop centerfreq are changed
    No Docstrings. If you don't know what the functions do, you should go into the lab first and measure with a real
    VNA.
    """
    def __init__(self, name):
        Instrument.__init__(self, name, tags=['virtual'])
        self.nop = 1001
        self.startfreq = 4e9
        self.stopfreq = 5e9
        self.sweeptime_averages = 1
        self.span = self.stopfreq - self.startfreq
        self.centerfreq = (self.startfreq + self.stopfreq) / 2
        self._ready = False
        self.add_parameter('power', type=float, minval=-85, maxval=10, units='dBm',offset=True,flags=Instrument.FLAG_GET_AFTER_SET|Instrument.FLAG_GETSET)
        self.add_function('get_freqpoints')
        self.add_function('get_tracedata')
        self.add_function('get_sweeptime_averages')
        self.add_function('pre_measurement')
        self.add_function('start_measurement')
        self.add_function('ready')
        self.add_function('post_measurement')
        self.power = 0
        
    def do_get_power(self):
        return  self.power
    
    def do_set_power(self,value):
        print("Setting VNA power to ",value)
        self.power = value

    def set_startfreq(self, startfreq):
        self.startfreq = startfreq
        self.span = self.stopfreq - self.startfreq
        self.centerfreq = (self.stopfreq + self.startfreq) / 2

    def get_startfreq(self):
        return self.startfreq

    def set_stopfreq(self, stopfreq):
        self.stopfreq = stopfreq
        self.span = self.stopfreq - self.startfreq
        self.centerfreq = (self.stopfreq + self.startfreq) / 2

    def get_stopfreq(self):
        return self.stopfreq

    def set_centerfreq(self, centerfreq):
        self.centerfreq = centerfreq
        self.startfreq = centerfreq - self.span / 2
        self.stopfreq = centerfreq + self.span / 2

    def get_centerfreq(self):
        return self.centerfreq

    def get_span(self):
        return self.span

    def set_span(self, span):
        self.span = span
        self.startfreq = self.centerfreq - span / 2
        self.stopfreq = self.centerfreq + span / 2

    def get_nop(self):
        return self.nop

    def set_nop(self, nop):
        self.nop = nop

    def get_freqpoints(self):
        return np.linspace(self.startfreq, self.stopfreq, self.nop)

    def get_sweeptime_averages(self,query=True):
        return self.sweeptime_averages

    def get_sweeptime(self,query=True):
        return 1

    def get_averages(self):
        return 1

    def get_Average(self):
        return False

    def get_tracedata(self, RealImag=None):

        def S21_notch(f, fr, Ql, Qc):
            return 1. - Ql / Qc / (1. + 2j * Ql * (f - fr) / fr)

        Qi = np.random.normal(2000, 500)
        Qc = np.random.normal(1500, 500)  # for a nice signal the resonance is overcoupled
        fr = np.random.normal((self.stopfreq + self.startfreq) / 2, self.span / 8)
        Ql = Qi * Qc / (Qi + Qc)
        S21_data = S21_notch(self.get_freqpoints(), fr, Ql, Qi) + np.random.normal(0., 0.01, self.nop)

        if not RealImag:
            amp = np.abs(S21_data)
            pha = np.angle(S21_data)
            return amp, pha
        else:
            I = S21_data.real
            Q = S21_data.imag
            return I, Q

    def get_all(self):
        pass

    def pre_measurement(self):
        pass

    def post_measurement(self):
        pass

    def start_measurement(self):
        pass

    def ready(self):
        self._ready = not self._ready
        return self._ready

    def avg_clear(self):
        pass
