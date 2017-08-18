# filename: Virtual_VCA.py
# Tim Wolz <tim.wolz@student.kit.edu>, 5/2017

# virtual VCA instrument to be used as a wrapper for the DELFT tunnel electronics driver IVVI
# use: 
#  - set current range of downstream current source
#  - current unit is mA, independent of the specified and set range

# import and usage
"""
IVVI = qt.instruments.create('IVVI', 'IVVIDIG_main', address='COM6') #COM6 corresponds to adapter D in the UFO setup
vca = qt.instruments.create('vca', 'Virtual_VCA', dac_port = 2, freqrange= '0408')   #chosen dac output port of IVVI (use only positive voltage range, 0-4V), freqrange either '0408' or '0812'
vca.set_attenuation(15) # in dB
"""

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
import instruments
import types
import logging
import qt
import numpy as np
from scipy import interpolate

if 'IVVI' not in qt.instruments.get_instrument_names():
    logging.error('Instrument IVVI not found.')
    raise ImportError
else:
    IVVI = qt.instruments.get('IVVI')

volts=np.linspace(0,8,17)
attenuation0408=[0,  1.11278882e+00,  3.73766693e+00,  7.14756693e+00,
    1.00470419e+01,  1.30124250e+01,  1.53641026e+01,  1.76756578e+01,
    2.00411519e+01,  2.22864997e+01,  2.45740138e+01,  2.65537780e+01,
    2.84989597e+01,  3.03834811e+01,  3.21356836e+01,  3.40573527e+01,
    3.57549752e+01] # These are measurement values.
# ToDo include measurment values of 0812 vca for interpolation    
attenuation0812=[]


class Virtual_vca(Instrument):

    def __init__(self, name, dac_port, freqrange):
        """
        init virtual instrument object
        Inputs:
            - name: qt instrument name
            - dac_port: chosen dac output
            - freqange: frequency range of the vca as string either '0408' or '0812'
        """
        Instrument.__init__(self, name, tags=['virtual'])
        if freqrange is '0408':
            self.volts_interpol=interpolate.interp1d(attenuation0408, volts)
            self.att_interpol=interpolate.interp1d(volts, attenuation0408)
        '''
        ToDo:
        elif freqrange is '0812':
            self.volts_interpol=interpolate.interp1d(attenuation0812, volts)
            self.att_interpol=interpolate.interp1d(volts, attenuation0812)
        '''
        self.dac_port=dac_port
        self.add_parameter('attenuation', type=types.FloatType, flags=Instrument.FLAG_GETSET, units='dB', minval=0, maxval=30)
        
        
    def do_set_attenuation(self, att):
        '''
        sets the attenuation of the vca
        Input: att in dB
        '''
        mV=self.volts_interpol(att)*1000/2 #2 bc of amplifier
        IVVI.set_dac(self.dac_port,mV, dacrange=(0,4000))
    
    
    def do_get_attenuation(self):
        '''
        returns the attenuation of the vca
        '''
        mv=IVVI.get_dac(self.dac_port)
        try:
            return self.att_interpol(mv/1000)
        except IndexError as detail:
            logging.error('Electronics might be disconnected.')
            print detail
        except Exception as detail:
            logging.error(detail)