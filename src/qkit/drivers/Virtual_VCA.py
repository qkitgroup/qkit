# filename: Virtual_VCA.py
# Tim Wolz <tim.wolz@.kit.edu>, 5/2017 updated 09/2018

# virtual VCA instrument to be used as a wrapper for several DACs
# so far the IVVI and DC_DAC are implemented

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
import types
import numpy as np
from scipy import interpolate

volts = np.linspace(0, 8, 17)
attenuation0408 = [0, 1.11278882e+00, 3.73766693e+00, 7.14756693e+00,
                   1.00470419e+01, 1.30124250e+01, 1.53641026e+01, 1.76756578e+01,
                   2.00411519e+01, 2.22864997e+01, 2.45740138e+01, 2.65537780e+01,
                   2.84989597e+01, 3.03834811e+01, 3.21356836e+01, 3.40573527e+01,
                   3.57549752e+01]  # These are measurement values, insertion loss not considered
# ToDo include measurment values of 0812 vca for interpolation
attenuation0812 = []


class Virtual_VCA(Instrument):
    """
    Wrapper for the VCA that allows to set the attenuation without knowing the underlying DAC mechanisms.
    """
    def __init__(self, name, dac_device, dac_port, freqrange):
        """
        inits the VCA (virtual instrument)
        :param name: qkit instrument name
        :param dac_device: either IVVI (must be set to positive values) or DC_DAC
        :param dac_port: chosen output port / channel of your DAC-device
        :param freqrange: frequency range of the vca as string either '0408' or '0812'
        """
        Instrument.__init__(self, name, tags=['virtual'])
        if freqrange is '0408':
            self.volts_interpol = interpolate.interp1d(attenuation0408, volts)
            self.att_interpol = interpolate.interp1d(volts, attenuation0408)

        # ToDo:
        # elif freqrange is '0812':
        #    self.volts_interpol=interpolate.interp1d(attenuation0812, volts)
        #    self.att_interpol=interpolate.interp1d(volts, attenuation0812)

        self.add_parameter('attenuation', type=float, flags=Instrument.FLAG_GETSET, units='dB', minval=0,
                           maxval=30)
        self._dac = _Dac(dac_device, dac_port)

    def do_set_attenuation(self, att):
        """
        sets the attenuation of the vca
        :param att in dB (float)
        """
        voltage = self.volts_interpol(att) / 2  # 2 bc of amplifier
        self._dac.set_dac_voltage(voltage)

    def do_get_attenuation(self):
        """
        returns the attenuation of the vca
        """
        voltage = self._dac.get_dac_voltage()
        return self.att_interpol(voltage*2)


class _Dac:
    """
    wrapper class so that Virtual_VCA works with several different Dacs.
    Please just append other devices here.
    """
    def __init__(self, dac_device, dac_port):
        self.dac_device = dac_device
        self.dac_port = dac_port

    def set_dac_voltage(self, voltage):
        if self.dac_device.get_type()[0:4] == 'IVVI':
            mv = voltage * 1000
            self.dac_device.set_dac(self.dac_port, mv, dacrange=(0, 4000))
        elif self.dac_device.get_type()[0:6] == 'DC_DAC':
            self.dac_device.do_set_voltage(voltage, self.dac_port)

    def get_dac_voltage(self):
        if self.dac_device.get_type()[0:4] == 'IVVI':
            voltage = self.dac_device.get_dac(self.dac_port, dacrange=(0, 4000)) / 1000
        elif self.dac_device.get_type()[0:6] == 'DC_DAC':
            voltage = self.dac_device.do_get_voltage(self.dac_port)
        return voltage
