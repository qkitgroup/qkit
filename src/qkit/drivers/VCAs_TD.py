# filename: VCAs_TD.py
# Jan Brehm <jan.brehm@kit.edu>, 09/2019

# virtual VCA instrument to be used as a wrapper for several DACs
# It controlls all VCAs in Time-Domain-Setup 3

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
import zerorpc


class VCAs_TD(Instrument):
    """
    Wrapper for the VCA that allows to set the attenuation without knowing the underlying DAC mechanisms.
    """
    def __init__(self, name, address="tcp://10.22.197.143:4242"):
        """
        inits the VCA (virtual instrument)
        :param name: qkit instrument name
        :param address: IP-address of Raspberry-Pi controlling the VCAs
        """
        Instrument.__init__(self, name, tags=['virtual'])


        self.add_parameter('attenuation_i_manip', type=float, flags=Instrument.FLAG_SET|Instrument.FLAG_SOFTGET, units='dB', minval=0,
                           maxval=20, offset=True)
        self.add_parameter('attenuation_q_manip', type=float, flags=Instrument.FLAG_SET|Instrument.FLAG_SOFTGET, units='dB', minval=0,
                           maxval=20, offset=True)
        self.add_parameter('attenuation_i_readout', type=float, flags=Instrument.FLAG_SET|Instrument.FLAG_SOFTGET, units='dB', minval=0,
                           maxval=20, offset=True) 
        self.add_parameter('attenuation_q_readout', type=float, flags=Instrument.FLAG_SET|Instrument.FLAG_SOFTGET, units='dB', minval=0,
                           maxval=20, offset=True)
        self.add_parameter('attenuation_rf_readout', type=float, flags=Instrument.FLAG_SET|Instrument.FLAG_SOFTGET, units='dB', minval=0,
                           maxval=30, offset=True)
        self.add_parameter('attenuation_rf_manip', type=float, flags=Instrument.FLAG_SET|Instrument.FLAG_SOFTGET, units='dB', minval=0,
                           maxval=30, offset=True)
        self.add_parameter('amplification_i_return', type=float, flags=Instrument.FLAG_SET|Instrument.FLAG_SOFTGET, units='dB', minval=-20,
                           maxval=33, offset=True)
        self.add_parameter('amplification_q_return', type=float, flags=Instrument.FLAG_SET|Instrument.FLAG_SOFTGET, units='dB', minval=-20,
                           maxval=33, offset=True)                                                               
        self._address=address         

        self._dac = zerorpc.Client()

    def do_set_attenuation_i_manip(self, att):
        """
        sets the attenuation of the vca for the I component of the manipulation signal after AWG
        :param att in dB (float) 0-20dB
        """
        self._dac.connect(self._address)
        self._dac.SetBBAtt("manipulation", "i", att)

    def do_set_attenuation_q_manip(self, att):
        """
        sets the attenuation of the vca for the Q component of the manipulation signal after AWG
        :param att in dB (float) 0-20dB
        """
        self._dac.connect(self._address)
        self._dac.SetBBAtt("manipulation", "q", att)

    def do_set_attenuation_i_readout(self, att):
        """
        sets the attenuation of the vca for the I component of the readout signal after AWG
        :param att in dB (float) 0-20dB
        """
        self._dac.connect(self._address)
        self._dac.SetBBAtt("readout", "i", att)
        
    def do_set_attenuation_q_readout(self, att):
        """
        sets the attenuation of the vca for the Q component of the readout signal after AWG
        :param att in dB (float) 0-20dB
        """
        self._dac.connect(self._address)
        self._dac.SetBBAtt("readout", "q", att)

    def do_set_attenuation_rf_readout(self, att):
        """
        sets the attenuation of the vca for the RF-readout signal after AWG and Mixer, before cryo
        :param att in dB (float) 0-30dB
        """
        self._dac.connect(self._address)
        self._dac.SetHFAtt("read", att)

    def do_set_attenuation_rf_manip(self, att):
        """
        sets the attenuation of the vca for the RF-manipulation signal after AWG and Mixer, before cryo
        :param att in dB (float) 0-30dB
        """
        self._dac.connect(self._address)
        self._dac.SetHFAtt("manip", att)

    def do_set_amplification_i_return(self, amp):
        """
        sets the amplification or attenuation of the vca for the I-signal after cryo and Mixer, before detection with ADC. The device can attenuate and amplify!
        :param att in dB (float) -20-33dB
        """
        self._dac.connect(self._address)
        self._dac.SetRXGain("inphase", amp)
    
    def do_set_amplification_q_return(self, amp):
        """
        sets the amplification or attenuation of the vca for the Q-signal after cryo and Mixer, before detection with ADC. The device can attenuate and amplify!
        :param att in dB (float) -20-33dB
        """
        self._dac.connect(self._address)
        self._dac.SetRXGain("quadrature", amp)
   
