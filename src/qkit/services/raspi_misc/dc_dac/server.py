#!/usr/bin/env python2
# server.py by JB@KIT 01/2018

'''
Server script for DC DAC LTC2666 to be run on Raspberry Pi mounted in the DC DAC rack. 
Raspberry Pi 3 model pin configuration: MOSI: 19, MISO: 21, SCLK: 23, Chip select CE0: 24 (in use with dac0), CE1: 26 (dac1). 
DAC model: LTC2666-16

Internal reference: REFCOMP floating, RD bit = 0.
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

import numpy as np
import time,sys
import logging

import zerorpc

from DAC_LTC2666_communication import DAC_LTC2666
dacs = []
dac0 = DAC_LTC2666(cs = 0, word32 = True)   #load DAC on CS0 port
dacs.append(dac0)
dac1 = DAC_LTC2666(cs = 1, word32 = True)   #load DAC on CS1 port
dacs.append(dac1)
    

class DAC_Server(object):
    '''
    Main server class.
    '''
    def init_dac(self):
        '''
        Initialize dac boards.
        '''
        for dac in dacs:
            dac.init()
    def verify(self):
        '''
        Verify dac boards by checking acknowledge bytes.
        '''
        for i,dac in enumerate(dacs):
            if not dac.verify_connection():
                return 'No acknowledge received from DAC #{:d}'.format(i)
        return True
    def set_voltage(self, channel, voltage):
        '''
        Main method to set a dac voltage value via the server.
        - channel: integer within 0..15
        - voltgae: voltage to be set: -5V..5V
        '''
        return dacs[int(channel)/8].set_voltage((channel%8), voltage)
       

if __name__ == "__main__":   #if executed as main (and not imported)
    '''
    Start routine for dac server. HOST and PORT can be passed as arguments, otherwise defaults are used.
    '''
    HOST = 'localhost'
    PORT = 9931
    print sys.argv
    try:
        HOST = sys.argv[1]
        PORT = int(sys.argv[2])
    except IndexError:
        print 'Using defaults: {:s}, {:d}'.format(HOST, PORT)
    #time.sleep(0.1) 
    
    s = zerorpc.Server(DAC_Server())
    s.bind("tcp://{:s}:{:d}".format(HOST, PORT))
    print 'Server started...\n'
    s.run()