# edw_server.py by JB@KIT 03/2015
# TCP server using EdwardsBridgeReadout USB interface

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

try:
    import SocketServer
except ImportError:
    import socketserver as SocketServer

import os,sys
sys.path.append('../')
from EdwardsBridgeReadout import Edwards_p_gauge   #import readout class

p = Edwards_p_gauge()

class TCPHandler_Edwards(SocketServer.BaseRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        try:
            # self.request is the TCP socket connected to the client
            self.data = self.request.recv(1024).strip()
            if str(self.data) == 'get_p_cond':
                print 'condenser line pressure request from', str(format(self.client_address[0]))
                self.request.sendall(str(p.get_condenser_pressure()))
            elif str(self.data) == 'get_p_still':
                print 'still line pressure request from', str(format(self.client_address[0]))
                self.request.sendall(str(p.get_still_pressure()))
            else:
                print 'request string not recognized'
                self.request.sendall(0)
        except Exception as m:
            print 'Error in TCP server handler:', m

if __name__ == "__main__":
    HOST, PORT = 'ip-address', 9955

    # Create the server, binding to localhost on port 9955
    server = SocketServer.TCPServer((HOST, PORT), TCPHandler_Edwards)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()

