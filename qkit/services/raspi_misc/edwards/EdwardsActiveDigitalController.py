# qtlab driver/wrapper for EdwardsActiveDigitalController by JB@KIT 03/2015
# pressure readout device @ UFO: G1, G2
# model: D39591000 (enhanced)

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
#import numpy as np
import time,sys
#import atexit
#import serial
import socket
import sys

class EdwardsActiveDigitalController(Instrument):

    def __init__(self, name, host='ip-address', port=9955):

        Instrument.__init__(self, name, tags=['physical'])
        
        self.add_parameter('condenser_pressure',
            type=types.FloatType,
            flags=Instrument.FLAG_GET, units='mbar')
        self.add_parameter('still_pressure',
            type=types.FloatType,
            flags=Instrument.FLAG_GET, units='mbar')
            
        self.HOST, self.PORT = host, port

    def do_get_condenser_pressure(self):
        try:
            # Create a socket (SOCK_STREAM means a TCP socket)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #connect
            sock.connect((self.HOST, self.PORT))
            sock.sendall('get_p_cond' + '\n')
            # Receive data from the server and shut down
            rec = sock.recv(1024)
            sock.close()
            return rec
        except Exception as detail:
            print "Error: ", detail
            return 0
            
    def do_get_still_pressure(self):
        try:
            # Create a socket (SOCK_STREAM means a TCP socket)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #connect
            sock.connect((self.HOST, self.PORT))
            sock.sendall('get_p_still' + '\n')
            # Receive data from the server and shut down
            rec = sock.recv(1024)
            sock.close()
            return rec
        except Exception as detail:
            print "Error: ", detail
            return 0
    
    def get_all(self):
        self.get('condenser_pressure')
        self.get('still_pressure')
 