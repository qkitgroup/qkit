# filename: Virtual_Current_Source.py by JB@KIT 05/2018
'''
Virtual instrument to be used as a wrapper for the DC DAC LTC2666. 
The wrapper is used with a current source that outputs a current proportional to an 
input voltage, which is in turn controlled by the DC DAC LTC2666. 
The LTC2666 driver is called DC_DAC_LTC2666.py. 

Use:
  - set current range of current source (proportionality constant)
  - current unit is mA, independent of the specified range

Import and usage:

vcurr = qkit.instruments.create('vcurr', 'Virtual_Current_Source', host='129.00.00.00', port=9999)
vcurr.set_ch0_range(1)
vcoil.set_current(1.0)

Current ranges are given as a float number such that the resulting voltage is 
voltage = current * current_range e.g. 

current_range=1   ->    1V ^= 1mA
current_range=10  ->    1V ^= 10mA
current_range=0.01  ->  1V ^= 10uA

The DAC is 16bit, so the voltage resolution is 10V / 65536 = 0.15mV
'''

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
from qkit.instruments.DC_DAC_LTC2666 import DC_DAC_LTC2666
import logging
import types
import time
from qkit.gui.notebook.Progress_Bar import Progress_Bar
import numpy as np

class Virtual_Current_Source(DC_DAC_LTC2666):
    '''
    Instrument wrapper for DC DAC LTC2666, used as a set of dc current sources. 
    Inherits from DC_DAC_LTC2666.
    '''
    def __init__(self, name, host='ip-address', port=9931, nchannels = 16):
        '''
        This init method directly creates current source instruments, instead of voltage sources.
        '''
        Instrument.__init__(self, name, tags=['virtual'])

        self.channels = nchannels
        self.add_parameter('current', type=float, flags=Instrument.FLAG_GETSET, 
                units='mA', channels=(0, self.channels-1), channel_prefix='ch%d_')
        self.add_parameter('range', type=float, flags=Instrument.FLAG_GETSET, 
                channels=(0, self.channels-1), channel_prefix='ch%d_')
        self.currents = [0]*self.channels
        self.c_ranges = [1]*self.channels
            
        self.HOST, self.PORT = host, port
        self.init_connection()   #DC_DAC_LTC2666.py

    def do_set_range(self, crange, channel = 0):
        """
        Set the current range of channel. This does not change the current output directly 
        but takes effect only at setting a new current.
        """
        self.c_ranges[channel] = crange
        logging.info(__name__ + ' : Setting current range of channel {:d} to {:f}.'.format(channel, crange))

    def do_get_range(self, channel = 0):
        """
        Get the current range of channel.
        """
        return self.c_ranges[channel]

    def do_set_current(self, current, channel = 0, verbose=True):
        """
        Set current of channel in mA. 
        """
        try:
            voltage = current * self.c_ranges[channel]
            if voltage < -5. or voltage >= 5.:
                raise ArithmeticError
            else:
                self.do_set_voltage(voltage, channel)   #DC_DAC_LTC2666.py
                self.currents[channel] = current
                if verbose:
                    logging.info(__name__ + ' : Setting current of channel {:d} to {:f}mA.'.format(channel, current))
                
        except ArithmeticError as detail:
            logging.error('Invalid current setting, value exceeds voltage threshold! No changees made.')
            print detail

    def do_get_current(self, channel):
        '''
        Get the current current setting for channel.
        '''
        return self.currents[channel]
            
    def ramp_to(self, target = 0, channel = 0, steps = 20, dt = 0.1):
        """
        Ramp current to target
        Inputs:
            - target: target current value (mA)
            - channel: channel index (1..)
            - steps: number of steps
            - dt: wait time between two steps
        """
        p = Progress_Bar(steps,'Ramping current')
        for c in np.linspace(self.do_get_current(channel),target,steps):
            self.do_set_current(c, channel, verbose=False)
            p.iterate('{:.3g}mA'.format(c))
            time.sleep(dt)
        self.do_set_current(target, channel ,verbose=True)

