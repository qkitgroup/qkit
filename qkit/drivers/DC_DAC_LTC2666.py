#JB@KIT 01/2018
'''
qkit instrument driver for DC DAC LTC2666 (client)
 +- 5V dc digital to analog converter, 8 (16) channels, 16 bit amplitude resolution
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
import types
import logging
import zerorpc

class DC_DAC_LTC2666(Instrument):
    '''
    Instrument class for DC DAC LTC2666.
    '''
    def __init__(self, name, host='ip-address', port=9931, nchannels = 16):
        '''
        Initialize qkit parameters and connect to the zerorpc server as a client.
        '''
        Instrument.__init__(self, name, tags=['physical'])
        
        self.channels = nchannels
        self.add_parameter('voltage', type=float, flags=Instrument.FLAG_GETSET, 
                units='V', channels=(0, self.channels-1), channel_prefix='ch%d_',minval=-5.,maxval=5)
        self.voltages = [0]*self.channels
        
        self.HOST, self.PORT = host, port
        self.init_connection()
    
    def init_connection(self):
        '''
        initiate connection to zerorpc server
        '''
        logging.debug(__name__ + ': initiating connection to DAC server {:s} on port {:d}'.format(self.HOST, self.PORT))
        self.c = zerorpc.Client()
        self.c.connect("tcp://{:s}:{:d}".format(self.HOST, self.PORT))

    def do_set_voltage(self, voltage, channel):
        '''
        Set dac voltage in range -5V..5V.
        '''
        if voltage>5-10./2**16:
            voltage = 5-10./2**16 #we can not set exactly +5V, but only one bit less
        for i in range(10):
          try:
              self.c.set_voltage(channel, voltage)
              self.voltages[channel]=voltage
              break
          except Exception as detail:
              if i==9:
                  logging.error('{:s}'.format(detail))
                  
    def do_get_voltage(self, channel):
        '''
        Get the current voltage setting for channel.
        '''
        return self.voltages[channel]
            
    def close_connection(self):
        logging.debug(__name__ + ': closing connection to DAC server {:s} on port {:d}'.format(self.HOST, self.PORT))
        self.c.close()
